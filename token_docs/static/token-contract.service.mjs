import { TokenContractError, TokenContractErrorCode } from "./token-contract.types.mjs";
import { validateTokenContractResponse } from "./token-contract.validation.mjs";

export function resolveContractEndpoint(endpoint, baseUrl = globalThis.location?.href) {
  if (typeof endpoint !== "string" || !endpoint || endpoint === "[ENDPOINT_URL]" || /^\[[A-Z0-9_]+\]$/.test(endpoint)) {
    throw new TokenContractError(TokenContractErrorCode.CONFIGURATION, "Contract Address to be announced.");
  }
  let url;
  try {
    url = baseUrl ? new URL(endpoint, baseUrl) : new URL(endpoint);
  } catch (cause) {
    throw new TokenContractError(TokenContractErrorCode.CONFIGURATION, "Contract data endpoint is not a valid URL.", { cause });
  }
  const localhost = ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
  if (url.protocol !== "https:" && !(url.protocol === "http:" && localhost)) {
    throw new TokenContractError(TokenContractErrorCode.CONFIGURATION, "Contract data endpoint must use HTTPS.");
  }
  if (url.username || url.password) {
    throw new TokenContractError(TokenContractErrorCode.CONFIGURATION, "Contract data endpoint must not contain credentials.");
  }
  return url.href;
}

export async function fetchTokenContract({
  endpoint,
  timeoutMs = 8_000,
  signal,
  fetchImpl = globalThis.fetch,
  baseUrl,
} = {}) {
  const url = resolveContractEndpoint(endpoint, baseUrl);
  if (typeof fetchImpl !== "function") {
    throw new TokenContractError(TokenContractErrorCode.NETWORK, "This browser cannot request contract data.");
  }

  const requestController = new AbortController();
  let timedOut = false;
  const abortFromCaller = () => requestController.abort(signal?.reason);
  if (signal?.aborted) abortFromCaller();
  else signal?.addEventListener("abort", abortFromCaller, { once: true });
  const timeoutId = setTimeout(() => {
    timedOut = true;
    requestController.abort();
  }, Math.max(1, timeoutMs));

  try {
    let response;
    try {
      response = await fetchImpl(url, {
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
        credentials: "omit",
        redirect: "follow",
        signal: requestController.signal,
      });
    } catch (cause) {
      if (timedOut) throw new TokenContractError(TokenContractErrorCode.TIMEOUT, "The contract endpoint timed out.", { cause });
      if (signal?.aborted || requestController.signal.aborted) {
        throw new TokenContractError(TokenContractErrorCode.ABORTED, "The contract request was cancelled.", { cause });
      }
      throw new TokenContractError(TokenContractErrorCode.NETWORK, "The contract endpoint could not be reached.", { cause });
    }

    if (!response.ok) {
      throw new TokenContractError(TokenContractErrorCode.HTTP, `The contract endpoint returned HTTP ${response.status}.`, { status: response.status });
    }

    let payload;
    try {
      payload = await response.json();
    } catch (cause) {
      throw new TokenContractError(TokenContractErrorCode.MALFORMED_JSON, "The contract endpoint returned malformed JSON.", { cause });
    }
    return validateTokenContractResponse(payload);
  } finally {
    clearTimeout(timeoutId);
    signal?.removeEventListener("abort", abortFromCaller);
  }
}
