import { TokenContractError, TokenContractErrorCode } from "./token-contract.types.mjs?v=3";

function sameRecord(left, right) {
  return Boolean(left && right)
    && left.contractAddress === right.contractAddress
    && left.chain === right.chain
    && left.explorerUrl === right.explorerUrl
    && left.updatedAt === right.updatedAt;
}

export class LiveTokenContractController {
  constructor({
    service,
    view,
    refreshIntervalMs = 60_000,
    documentRef = globalThis.document,
    now = () => new Date(),
    scheduler = globalThis,
  }) {
    if (typeof service !== "function") throw new TypeError("A contract service is required.");
    if (!view || typeof view.render !== "function") throw new TypeError("A contract view is required.");
    this.service = service;
    this.view = view;
    this.refreshIntervalMs = Math.max(1, Number(refreshIntervalMs) || 60_000);
    this.documentRef = documentRef;
    this.now = now;
    this.scheduler = scheduler;
    this.lastVerified = null;
    this.state = { kind: "idle", record: null };
    this.activeRequest = null;
    this.timerId = null;
    this.requestVersion = 0;
    this.destroyed = false;
    this.visibilityHandler = () => this.handleVisibilityChange();
  }

  mount() {
    if (this.destroyed) return Promise.resolve();
    this.documentRef?.addEventListener?.("visibilitychange", this.visibilityHandler);
    return this.refresh("initial");
  }

  unmount() {
    this.destroyed = true;
    this.clearPoll();
    this.requestVersion += 1;
    this.activeRequest?.controller.abort("unmount");
    this.activeRequest = null;
    this.documentRef?.removeEventListener?.("visibilitychange", this.visibilityHandler);
  }

  isVisible() {
    return !this.documentRef || this.documentRef.visibilityState !== "hidden";
  }

  clearPoll() {
    if (this.timerId !== null) this.scheduler.clearTimeout(this.timerId);
    this.timerId = null;
  }

  schedulePoll() {
    this.clearPoll();
    if (this.destroyed || !this.isVisible() || this.state.kind === "configuration") return;
    this.timerId = this.scheduler.setTimeout(() => {
      this.timerId = null;
      this.refresh("poll");
    }, this.refreshIntervalMs);
  }

  handleVisibilityChange() {
    this.clearPoll();
    if (!this.isVisible()) {
      this.requestVersion += 1;
      this.activeRequest?.controller.abort("hidden");
      this.activeRequest = null;
      if (this.lastVerified) this.commit({ kind: "success", ...this.lastVerified, announcement: "" });
      return;
    }
    this.refresh("visibility");
  }

  commit(nextState) {
    this.state = nextState;
    this.view.render(nextState);
  }

  refresh(reason = "manual") {
    if (this.destroyed) return Promise.resolve(null);
    if (!this.isVisible() && reason === "poll") return Promise.resolve(null);
    if (this.activeRequest) return this.activeRequest.promise;
    this.clearPoll();

    const previous = this.lastVerified;
    const priorKind = this.state.kind;
    this.commit(previous
      ? { kind: "refreshing", ...previous, reason, announcement: reason === "manual" ? "Checking the contract endpoint for updates." : "" }
      : { kind: "loading", record: null, reason, announcement: reason === "initial" ? "Loading contract data." : "" });

    const controller = new AbortController();
    const version = ++this.requestVersion;
    const promise = this.service({ signal: controller.signal })
      .then((record) => {
        if (this.destroyed || version !== this.requestVersion) return null;
        const fetchedAt = this.now();
        const changed = Boolean(previous) && !sameRecord(previous.record, record);
        this.lastVerified = { record, fetchedAt };
        let announcement = "";
        if (!previous) announcement = `${record.chain} Contract Address loaded and passed format checks.`;
        else if (changed) announcement = `The published ${record.chain} Contract Address changed and passed format checks.`;
        else if (priorKind === "stale") announcement = "The contract endpoint recovered. The last verified record remains current.";
        else if (reason === "manual") announcement = "Contract data checked. The published record is unchanged.";
        this.commit({ kind: "success", record, fetchedAt, reason, changed, announcement });
        return record;
      })
      .catch((error) => {
        if (this.destroyed || version !== this.requestVersion) return null;
        const normalized = error instanceof TokenContractError
          ? error
          : new TokenContractError(TokenContractErrorCode.NETWORK, "The contract endpoint could not be reached.", { cause: error });
        if (normalized.code === TokenContractErrorCode.ABORTED) return null;
        if (previous) {
          this.commit({
            kind: "stale",
            ...previous,
            error: normalized,
            reason,
            announcement: "The latest contract refresh failed. The last verified address may be outdated.",
          });
        } else {
          const kind = normalized.code === TokenContractErrorCode.CONFIGURATION
            ? "configuration"
            : [TokenContractErrorCode.INVALID_RESPONSE, TokenContractErrorCode.MALFORMED_JSON].includes(normalized.code)
              ? "invalid"
              : "error";
          this.commit({ kind, record: null, error: normalized, reason, announcement: normalized.message });
        }
        return null;
      })
      .finally(() => {
        if (version === this.requestVersion) {
          this.activeRequest = null;
          this.schedulePoll();
        }
      });

    this.activeRequest = { controller, promise, version };
    return promise;
  }
}

export async function copyText(text, { clipboard = globalThis.navigator?.clipboard, legacyCopy } = {}) {
  if (typeof text !== "string" || !text) {
    throw new TokenContractError(TokenContractErrorCode.COPY, "There is no validated text to copy.");
  }
  if (clipboard && typeof clipboard.writeText === "function") {
    try {
      await clipboard.writeText(text);
      return "clipboard";
    } catch {
      // Continue to the explicitly supplied safe fallback.
    }
  }
  if (typeof legacyCopy === "function" && await legacyCopy(text)) return "fallback";
  throw new TokenContractError(TokenContractErrorCode.COPY, "Copying was blocked. Select the full value and use your browser’s Copy command.");
}
