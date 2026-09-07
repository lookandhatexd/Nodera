import { fetchTokenContract } from "./token-contract.service.mjs";
import { copyText, LiveTokenContractController } from "./live-token-contract.mjs";
import { TokenContractErrorCode } from "./token-contract.types.mjs";

const absoluteTime = new Intl.DateTimeFormat(globalThis.document?.documentElement?.lang || "en-US", {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  timeZoneName: "short",
});

function formatTime(value) {
  const date = value instanceof Date ? value : new Date(value);
  return Number.isFinite(date.getTime()) ? absoluteTime.format(date) : "Not available";
}

function relativeTime(value, now = new Date()) {
  const seconds = Math.max(0, Math.round((now.getTime() - value.getTime()) / 1000));
  if (seconds < 5) return "Checked just now";
  if (seconds < 60) return `Checked ${seconds} seconds ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `Checked ${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  const hours = Math.round(minutes / 60);
  return `Checked ${hours} hour${hours === 1 ? "" : "s"} ago`;
}

function errorPresentation(error, online = true) {
  if (error?.code === TokenContractErrorCode.CONFIGURATION) {
    return ["Contract Address to be announced", ""];
  }
  if (error?.code === TokenContractErrorCode.TIMEOUT) {
    return ["Contract Address unavailable", "The address could not be loaded in time. Retry when connectivity is stable."];
  }
  if (error?.code === TokenContractErrorCode.HTTP) {
    return ["Contract Address unavailable", "The address source is temporarily unavailable. Retry when it is available again."];
  }
  if ([TokenContractErrorCode.INVALID_RESPONSE, TokenContractErrorCode.MALFORMED_JSON].includes(error?.code)) {
    return ["Contract Address unavailable", "The published address could not be read safely."];
  }
  if (!online) return ["You appear to be offline", "Reconnect to the internet, then retry."];
  return ["Contract Address unavailable", "The published address could not be loaded. Retry when the connection is available."];
}

function legacyCopy(documentRef, text) {
  if (!documentRef?.body || typeof documentRef.execCommand !== "function") return false;
  const field = documentRef.createElement("textarea");
  field.value = text;
  field.setAttribute("readonly", "");
  field.setAttribute("aria-hidden", "true");
  field.className = "copy-fallback-field";
  documentRef.body.append(field);
  field.select();
  let copied = false;
  try { copied = documentRef.execCommand("copy"); } catch { copied = false; }
  field.remove();
  return copied;
}

export function createTokenContractView(root, documentRef = globalThis.document) {
  const get = (selector) => root.querySelector(selector);
  const elements = {
    status: get("#contractStatus"),
    refresh: get("#refreshContract"),
    refreshLabel: get("#refreshContract span"),
    loading: get("#contractLoading"),
    error: get("#contractError"),
    errorTitle: get("#contractErrorTitle"),
    errorMessage: get("#contractErrorMessage"),
    record: get("#contractRecord"),
    chain: get("#contractChain"),
    address: get("#contractAddress"),
    explorer: get("#explorerLink"),
    explorerLabel: get("#explorerLink span"),
    announcement: get("#contractAnnouncement"),
    stale: get("#staleWarning"),
    staleText: get("#staleWarningText"),
    trace: [],
  };

  function updateExternalContext(record) {
    for (const selector of ["#securityChain", "#overviewChain", "#instructionChain"]) {
      const element = documentRef.querySelector(selector);
      if (element) element.textContent = record?.chain || (selector === "#securityChain" ? "the network displayed above" : "the displayed network");
    }
  }

  return {
    elements,
    render(state) {
      root.dataset.state = state.kind;
      root.setAttribute("aria-busy", String(["loading", "refreshing"].includes(state.kind)));
      const hasRecord = Boolean(state.record);
      const blockingError = !hasRecord && ["error", "invalid", "configuration"].includes(state.kind);
      elements.loading.hidden = state.kind !== "loading";
      elements.error.hidden = !blockingError;
      elements.record.hidden = !hasRecord;
      elements.stale.hidden = state.kind !== "stale";
      if (elements.refresh) {
        elements.refresh.disabled = ["loading", "refreshing", "configuration"].includes(state.kind);
        elements.refreshLabel.textContent = state.kind === "refreshing" ? "Checking" : ["error", "invalid", "stale"].includes(state.kind) ? "Retry" : "Refresh";
      }

      const copy = {
        idle: ["Contract Address", ""],
        loading: ["Contract Address", ""],
        success: ["Contract Address", ""],
        refreshing: ["Contract Address", ""],
        stale: ["Contract Address", ""],
        configuration: ["Contract Address to be announced", ""],
        invalid: ["Contract data unavailable", ""],
        error: ["Contract data unavailable", ""],
      }[state.kind] || ["Contract Address", ""];
      elements.status.textContent = copy[0];

      if (blockingError) {
        const [title, message] = errorPresentation(state.error, globalThis.navigator?.onLine !== false);
        elements.errorTitle.textContent = title;
        elements.errorMessage.textContent = message;
      }
      if (state.kind === "stale") {
        elements.staleText.textContent = `Latest refresh failed. This complete ${state.record.chain} record was last checked ${formatTime(state.fetchedAt)} and may be outdated.`;
      }
      if (hasRecord) {
        elements.chain.textContent = state.record.chain;
        elements.address.textContent = state.record.contractAddress;
        elements.explorer.hidden = !state.record.explorerUrl;
        if (state.record.explorerUrl) {
          elements.explorer.href = state.record.explorerUrl;
          elements.explorerLabel.textContent = `View on ${state.record.chain} explorer`;
          elements.explorer.setAttribute("aria-label", `View the full Contract Address on the ${state.record.chain} explorer (opens in a new tab)`);
        } else {
          elements.explorer.removeAttribute("href");
        }
      }
      updateExternalContext(state.record);
      if (state.announcement) elements.announcement.textContent = state.announcement;
    },
  };
}

export class LiveTokenContractAddress {
  constructor(root, config, documentRef = globalThis.document) {
    this.root = root;
    this.config = config;
    this.documentRef = documentRef;
    this.view = createTokenContractView(root, documentRef);
    this.copyResetTimer = null;
    this.controller = new LiveTokenContractController({
      service: ({ signal }) => fetchTokenContract({
        endpoint: config.contractEndpoint,
        timeoutMs: config.requestTimeoutMs,
        signal,
      }),
      view: this.view,
      refreshIntervalMs: config.refreshIntervalMs,
      documentRef,
    });
    this.refreshHandler = () => this.controller.refresh("manual");
    this.copyHandler = () => this.copyAddress();
  }

  mount() {
    this.view.elements.refresh?.addEventListener("click", this.refreshHandler);
    this.root.querySelector("#copyContract").addEventListener("click", this.copyHandler);
    return this.controller.mount();
  }

  async copyAddress() {
    const record = this.controller.state.record;
    if (!record) return;
    const button = this.root.querySelector("#copyContract");
    const label = button.querySelector("span");
    if (this.copyResetTimer !== null) clearTimeout(this.copyResetTimer);
    try {
      await copyText(record.contractAddress, {
        legacyCopy: (text) => legacyCopy(this.documentRef, text),
      });
      label.textContent = "Copied full address";
      this.view.elements.announcement.textContent = `${record.chain} Contract Address copied.`;
    } catch (error) {
      label.textContent = "Copy blocked";
      this.view.elements.announcement.textContent = error.message;
      const range = this.documentRef.createRange?.();
      if (range) {
        range.selectNodeContents(this.view.elements.address);
        const selection = globalThis.getSelection?.();
        selection?.removeAllRanges();
        selection?.addRange(range);
      }
    }
    button.focus({ preventScroll: true });
    this.copyResetTimer = setTimeout(() => { label.textContent = "Copy address"; }, 2_000);
  }

  unmount() {
    this.controller.unmount();
    this.view.elements.refresh.removeEventListener("click", this.refreshHandler);
    this.root.querySelector("#copyContract").removeEventListener("click", this.copyHandler);
    if (this.copyResetTimer !== null) clearTimeout(this.copyResetTimer);
  }
}
