import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

import { copyText, LiveTokenContractController } from "../token_docs/static/live-token-contract.mjs";
import { fetchTokenContract } from "../token_docs/static/token-contract.service.mjs";
import { TokenContractError, TokenContractErrorCode } from "../token_docs/static/token-contract.types.mjs";
import { validateTokenContractResponse } from "../token_docs/static/token-contract.validation.mjs";

const EVM_A = "0x1111111111111111111111111111111111111111";
const EVM_B = "0x2222222222222222222222222222222222222222";
const SOLANA = "11111111111111111111111111111111";
const NOW = new Date("2026-09-06T12:01:00Z");

const validResponse = (overrides = {}) => ({
  contractAddress: EVM_A,
  chain: "Ethereum",
  explorerUrl: `https://etherscan.io/address/${EVM_A}`,
  updatedAt: "2026-09-06T12:00:00Z",
  ...overrides,
});

const fetchResponse = (payload, options = {}) => ({
  ok: options.ok ?? true,
  status: options.status ?? 200,
  json: options.json ?? (async () => payload),
});

class FakeView {
  constructor() { this.states = []; }
  render(state) { this.states.push(state); this.state = state; }
}

class FakeDocument {
  constructor() { this.visibilityState = "visible"; this.listeners = new Set(); }
  addEventListener(type, listener) { if (type === "visibilitychange") this.listeners.add(listener); }
  removeEventListener(type, listener) { if (type === "visibilitychange") this.listeners.delete(listener); }
  setVisibility(value) { this.visibilityState = value; for (const listener of this.listeners) listener(); }
}

class FakeScheduler {
  constructor() { this.tasks = new Map(); this.sequence = 0; }
  setTimeout(callback, delay) { const id = ++this.sequence; this.tasks.set(id, { callback, delay }); return id; }
  clearTimeout(id) { this.tasks.delete(id); }
  runNext() { const entry = this.tasks.entries().next().value; if (!entry) return null; const [id, task] = entry; this.tasks.delete(id); task.callback(); return task; }
}

const flush = () => new Promise((resolvePromise) => setImmediate(resolvePromise));

function createController(service) {
  const view = new FakeView();
  const documentRef = new FakeDocument();
  const scheduler = new FakeScheduler();
  const controller = new LiveTokenContractController({ service, view, documentRef, scheduler, refreshIntervalMs: 60_000, now: () => NOW });
  return { controller, view, documentRef, scheduler };
}

test("1. accepts a valid EVM response", () => {
  const result = validateTokenContractResponse(validResponse());
  assert.equal(result.contractAddress, EVM_A);
  assert.equal(result.chain, "Ethereum");
});

test("2. accepts a valid Solana response", () => {
  const result = validateTokenContractResponse(validResponse({ contractAddress: SOLANA, chain: "Solana", explorerUrl: `https://solscan.io/account/${SOLANA}` }));
  assert.equal(result.contractAddress, SOLANA);
});

test("3. applies conservative validation to a supported non-EVM response", () => {
  const result = validateTokenContractResponse(validResponse({ contractAddress: "cosmos1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqnrql8a", chain: "Cosmos Hub", explorerUrl: "https://www.mintscan.io/cosmos/address/cosmos1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqnrql8a" }));
  assert.equal(result.chain, "Cosmos Hub");
});

test("4. controller exposes an initial loading state", async () => {
  let resolveService;
  const service = () => new Promise((resolvePromise) => { resolveService = resolvePromise; });
  const { controller, view } = createController(service);
  const mounted = controller.mount();
  assert.equal(view.state.kind, "loading");
  resolveService(validateTokenContractResponse(validResponse()));
  await mounted;
  controller.unmount();
});

test("5. successful load renders one atomic validated record", async () => {
  const expected = validateTokenContractResponse(validResponse());
  const { controller, view } = createController(async () => expected);
  await controller.mount();
  assert.equal(view.state.kind, "success");
  assert.equal(view.state.record, expected);
  assert.equal(view.state.fetchedAt.toISOString(), NOW.toISOString());
  controller.unmount();
});

test("6. network failure is classified", async () => {
  await assert.rejects(
    fetchTokenContract({ endpoint: "https://api.example.test/token", fetchImpl: async () => { throw new Error("offline"); } }),
    (error) => error.code === TokenContractErrorCode.NETWORK,
  );
});

test("7. timeout aborts an unresponsive request", async () => {
  const fetchImpl = async (_url, { signal }) => new Promise((_resolve, reject) => signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")), { once: true }));
  await assert.rejects(
    fetchTokenContract({ endpoint: "https://api.example.test/token", fetchImpl, timeoutMs: 5 }),
    (error) => error.code === TokenContractErrorCode.TIMEOUT,
  );
});

test("8. caller cancellation aborts the request", async () => {
  const abortController = new AbortController();
  const fetchImpl = async (_url, { signal }) => new Promise((_resolve, reject) => signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")), { once: true }));
  const pending = fetchTokenContract({ endpoint: "https://api.example.test/token", fetchImpl, signal: abortController.signal });
  abortController.abort();
  await assert.rejects(pending, (error) => error.code === TokenContractErrorCode.ABORTED);
});

test("9. non-2xx response is rejected", async () => {
  await assert.rejects(
    fetchTokenContract({ endpoint: "https://api.example.test/token", fetchImpl: async () => fetchResponse(null, { ok: false, status: 503 }) }),
    (error) => error.code === TokenContractErrorCode.HTTP && error.status === 503,
  );
});

test("10. malformed JSON is rejected", async () => {
  const json = async () => { throw new SyntaxError("bad json"); };
  await assert.rejects(
    fetchTokenContract({ endpoint: "https://api.example.test/token", fetchImpl: async () => fetchResponse(null, { json }) }),
    (error) => error.code === TokenContractErrorCode.MALFORMED_JSON,
  );
});

test("11. missing contractAddress is rejected", () => {
  const payload = validResponse(); delete payload.contractAddress;
  assert.throws(() => validateTokenContractResponse(payload), (error) => error.code === TokenContractErrorCode.INVALID_RESPONSE);
});

test("12. missing chain is rejected", () => {
  const payload = validResponse(); delete payload.chain;
  assert.throws(() => validateTokenContractResponse(payload), (error) => error.code === TokenContractErrorCode.INVALID_RESPONSE);
});

test("13. invalid Contract Address is rejected by chain", () => {
  assert.throws(() => validateTokenContractResponse(validResponse({ contractAddress: "0x1234" })), /not valid for Ethereum/);
  assert.throws(() => validateTokenContractResponse(validResponse({ contractAddress: "O0Il", chain: "Solana" })), /Solana/);
});

test("14. invalid explorer URL uses a trusted chain mapping", () => {
  const result = validateTokenContractResponse(validResponse({ explorerUrl: "not a url" }));
  assert.equal(result.explorerSource, "trusted-fallback");
  assert.equal(result.explorerUrl, `https://etherscan.io/address/${EVM_A}`);
});

test("15. unsafe explorer protocol is never rendered and safely falls back", () => {
  const result = validateTokenContractResponse(validResponse({ explorerUrl: "javascript:alert(1)" }));
  assert.equal(new URL(result.explorerUrl).protocol, "https:");
  const unknown = validateTokenContractResponse(validResponse({ contractAddress: "addr-safe-123", chain: "Unknown Chain", explorerUrl: "data:text/html,bad" }));
  assert.equal(unknown.explorerUrl, null);
});

test("16. invalid updatedAt timestamp is rejected", () => {
  assert.throws(() => validateTokenContractResponse(validResponse({ updatedAt: "2026-02-30T12:00:00Z" })), /invalid calendar date/);
});

test("17. copy success uses the complete validated value", async () => {
  let copied = "";
  const method = await copyText(EVM_A, { clipboard: { writeText: async (value) => { copied = value; } } });
  assert.equal(method, "clipboard");
  assert.equal(copied, EVM_A);
});

test("18. copy failure returns explicit non-blocking recovery", async () => {
  await assert.rejects(
    copyText(EVM_A, { clipboard: { writeText: async () => { throw new Error("blocked"); } }, legacyCopy: async () => false }),
    (error) => error.code === TokenContractErrorCode.COPY && /Select the full value/.test(error.message),
  );
});

test("19. manual retry recovers an initial failure", async () => {
  let calls = 0;
  const record = validateTokenContractResponse(validResponse());
  const { controller, view } = createController(async () => { calls += 1; if (calls === 1) throw new TokenContractError(TokenContractErrorCode.NETWORK, "offline"); return record; });
  await controller.mount();
  assert.equal(view.state.kind, "error");
  await controller.refresh("manual");
  assert.equal(view.state.kind, "success");
  assert.equal(calls, 2);
  controller.unmount();
});

test("20. polling waits for the configured 60000ms interval", async () => {
  let calls = 0;
  const record = validateTokenContractResponse(validResponse());
  const { controller, scheduler } = createController(async () => { calls += 1; return record; });
  await controller.mount();
  assert.equal([...scheduler.tasks.values()][0].delay, 60_000);
  scheduler.runNext(); await flush();
  assert.equal(calls, 2);
  controller.unmount();
});

test("21. changed endpoint address replaces the rendered atomic record", async () => {
  let calls = 0;
  const records = [validResponse(), validResponse({ contractAddress: EVM_B, explorerUrl: `https://etherscan.io/address/${EVM_B}`, updatedAt: "2026-09-06T12:02:00Z" })].map(validateTokenContractResponse);
  const { controller, view } = createController(async () => records[calls++]);
  await controller.mount();
  await controller.refresh("manual");
  assert.equal(view.state.record.contractAddress, EVM_B);
  assert.equal(view.state.record.explorerUrl, `https://etherscan.io/address/${EVM_B}`);
  assert.equal(view.state.changed, true);
  controller.unmount();
});

test("22. polling pauses while the document is hidden", async () => {
  const record = validateTokenContractResponse(validResponse());
  const { controller, documentRef, scheduler } = createController(async () => record);
  await controller.mount();
  assert.equal(scheduler.tasks.size, 1);
  documentRef.setVisibility("hidden");
  assert.equal(scheduler.tasks.size, 0);
  controller.unmount();
});

test("23. returning to the tab refreshes immediately", async () => {
  let calls = 0;
  const record = validateTokenContractResponse(validResponse());
  const { controller, documentRef } = createController(async () => { calls += 1; return record; });
  await controller.mount();
  documentRef.setVisibility("hidden");
  documentRef.setVisibility("visible");
  await flush();
  assert.equal(calls, 2);
  controller.unmount();
});

test("24. refresh failure preserves the complete last verified record", async () => {
  let calls = 0;
  const record = validateTokenContractResponse(validResponse());
  const { controller, view } = createController(async () => { calls += 1; if (calls > 1) throw new TokenContractError(TokenContractErrorCode.NETWORK, "offline"); return record; });
  await controller.mount();
  await controller.refresh("manual");
  assert.equal(view.state.kind, "stale");
  assert.equal(view.state.record, record);
  assert.equal(view.state.fetchedAt.toISOString(), NOW.toISOString());
  controller.unmount();
});

test("25. stale state includes a clear may-be-outdated warning", async () => {
  let calls = 0;
  const record = validateTokenContractResponse(validResponse());
  const { controller, view } = createController(async () => { if (calls++ === 0) return record; throw new TokenContractError(TokenContractErrorCode.TIMEOUT, "timeout"); });
  await controller.mount();
  await controller.refresh("manual");
  assert.match(view.state.announcement, /may be outdated/i);
  assert.equal(view.state.error.code, TokenContractErrorCode.TIMEOUT);
  controller.unmount();
});

test("26. long addresses are bounded and styled to wrap without page overflow", async () => {
  const longAddress = `chain_${"a".repeat(120)}`;
  assert.equal(validateTokenContractResponse(validResponse({ chain: "Unknown Chain", contractAddress: longAddress, explorerUrl: "" })).contractAddress, longAddress);
  const currentFile = fileURLToPath(import.meta.url);
  const css = await readFile(resolve(dirname(currentFile), "../token_docs/static/token-docs.css"), "utf8");
  assert.match(css, /\.address-row code[^}]*overflow-wrap:\s*anywhere/s);
  assert.match(css, /body[^}]*overflow-x:\s*clip/s);
});

test("service requests fresh JSON without credentials or framework caching", async () => {
  let observed;
  await fetchTokenContract({
    endpoint: "https://api.example.test/token",
    fetchImpl: async (url, options) => { observed = { url, options }; return fetchResponse(validResponse()); },
  });
  assert.equal(observed.options.cache, "no-store");
  assert.equal(observed.options.credentials, "omit");
  assert.equal(observed.options.headers.Accept, "application/json");
});

test("duplicate refresh calls share one in-flight request", async () => {
  let resolveService;
  let calls = 0;
  const record = validateTokenContractResponse(validResponse());
  const { controller } = createController(() => { calls += 1; return new Promise((resolvePromise) => { resolveService = resolvePromise; }); });
  const first = controller.mount();
  const second = controller.refresh("manual");
  assert.equal(first, second);
  assert.equal(calls, 1);
  resolveService(record);
  await first;
  controller.unmount();
});

test("an obsolete hidden-tab request cannot overwrite a newer response", async () => {
  const resolvers = [];
  const { controller, documentRef, view } = createController(() => new Promise((resolvePromise) => resolvers.push(resolvePromise)));
  const initial = controller.mount();
  documentRef.setVisibility("hidden");
  documentRef.setVisibility("visible");
  resolvers[1](validateTokenContractResponse(validResponse({ contractAddress: EVM_B, explorerUrl: `https://etherscan.io/address/${EVM_B}` })));
  await flush();
  resolvers[0](validateTokenContractResponse(validResponse()));
  await initial;
  assert.equal(view.state.record.contractAddress, EVM_B);
  controller.unmount();
});
