/**
 * @typedef {Object} TokenContractResponse
 * @property {string} contractAddress
 * @property {string} chain
 * @property {string} explorerUrl
 * @property {string} updatedAt
 */

/**
 * @typedef {TokenContractResponse & {
 *   explorerUrl: string | null,
 *   explorerSource: "endpoint" | "trusted-fallback" | "unavailable"
 * }} ValidatedTokenContract
 */

export const TokenContractErrorCode = Object.freeze({
  CONFIGURATION: "configuration",
  NETWORK: "network",
  TIMEOUT: "timeout",
  ABORTED: "aborted",
  HTTP: "http",
  MALFORMED_JSON: "malformed-json",
  INVALID_RESPONSE: "invalid-response",
  COPY: "copy",
});

export class TokenContractError extends Error {
  constructor(code, message, options = {}) {
    super(message, options);
    this.name = "TokenContractError";
    this.code = code;
    this.status = options.status ?? null;
  }
}
