import { TokenContractError, TokenContractErrorCode } from "./token-contract.types.mjs";

const EVM_ADDRESS = /^0x[a-fA-F0-9]{40}$/;
const BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const CONTROL_CHARACTER = /[\u0000-\u001f\u007f]/;
const ISO_8601 = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?(Z|[+-]\d{2}:\d{2})$/;

const EVM_CHAINS = new Set([
  "ethereum",
  "base",
  "arbitrum",
  "arbitrum one",
  "optimism",
  "polygon",
  "avalanche c-chain",
  "bnb chain",
  "binance smart chain",
]);

const TRUSTED_EXPLORERS = new Map([
  ["ethereum", "https://etherscan.io/address/"],
  ["base", "https://basescan.org/address/"],
  ["arbitrum", "https://arbiscan.io/address/"],
  ["arbitrum one", "https://arbiscan.io/address/"],
  ["optimism", "https://optimistic.etherscan.io/address/"],
  ["polygon", "https://polygonscan.com/address/"],
  ["avalanche c-chain", "https://snowtrace.io/address/"],
  ["bnb chain", "https://bscscan.com/address/"],
  ["binance smart chain", "https://bscscan.com/address/"],
  ["solana", "https://solscan.io/account/"],
]);

function invalid(message) {
  throw new TokenContractError(TokenContractErrorCode.INVALID_RESPONSE, message);
}

export function validateChain(value) {
  if (typeof value !== "string") invalid("The endpoint field “chain” must be a string.");
  const chain = value.trim();
  if (!chain) invalid("The endpoint field “chain” is required.");
  if (chain.length > 64) invalid("The endpoint field “chain” is too long.");
  if (CONTROL_CHARACTER.test(chain)) invalid("The endpoint field “chain” contains control characters.");
  return chain;
}

function decodedBase58Length(value) {
  const bytes = [0];
  for (const character of value) {
    const digit = BASE58_ALPHABET.indexOf(character);
    if (digit < 0) return -1;
    let carry = digit;
    for (let index = bytes.length - 1; index >= 0; index -= 1) {
      carry += bytes[index] * 58;
      bytes[index] = carry & 0xff;
      carry >>= 8;
    }
    while (carry > 0) {
      bytes.unshift(carry & 0xff);
      carry >>= 8;
    }
  }
  let leadingZeroes = 0;
  while (leadingZeroes < value.length && value[leadingZeroes] === "1") leadingZeroes += 1;
  const significantBytes = bytes.length === 1 && bytes[0] === 0 ? 0 : bytes.length;
  return leadingZeroes + significantBytes;
}

export function validateContractAddress(value, chain) {
  if (typeof value !== "string") invalid("The endpoint field “contractAddress” must be a string.");
  if (!value) invalid("The endpoint field “contractAddress” is required.");
  if (value !== value.trim()) invalid("The Contract Address must not contain leading or trailing whitespace.");
  if (value.length > 128) invalid("The Contract Address exceeds the supported length.");
  if (CONTROL_CHARACTER.test(value)) invalid("The Contract Address contains control characters.");

  const normalizedChain = chain.toLocaleLowerCase("en-US");
  if (EVM_CHAINS.has(normalizedChain)) {
    if (!EVM_ADDRESS.test(value)) invalid(`The Contract Address is not valid for ${chain}.`);
    return value;
  }
  if (normalizedChain === "solana") {
    if (!/^[1-9A-HJ-NP-Za-km-z]+$/.test(value) || decodedBase58Length(value) !== 32) {
      invalid("The Contract Address is not a valid 32-byte Solana public key.");
    }
    return value;
  }

  if (value.length < 3) invalid("The Contract Address is too short for an unknown network.");
  if (/\s/.test(value)) invalid("The Contract Address for an unknown network must not contain whitespace.");
  return value;
}

export function validateUpdatedAt(value) {
  if (typeof value !== "string") invalid("The endpoint field “updatedAt” must be a string.");
  if (value !== value.trim()) invalid("The endpoint field “updatedAt” contains surrounding whitespace.");
  const match = ISO_8601.exec(value);
  if (!match) invalid("The endpoint field “updatedAt” must be an ISO 8601 timestamp.");
  const [, yearText, monthText, dayText, hourText, minuteText, secondText, , zone] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const second = Number(secondText);
  if (month < 1 || month > 12 || day < 1 || day > new Date(Date.UTC(year, month, 0)).getUTCDate()) {
    invalid("The endpoint field “updatedAt” contains an invalid calendar date.");
  }
  if (hour > 23 || minute > 59 || second > 59) invalid("The endpoint field “updatedAt” contains an invalid time.");
  if (zone !== "Z") {
    const [offsetHour, offsetMinute] = zone.slice(1).split(":").map(Number);
    if (offsetHour > 14 || offsetMinute > 59 || (offsetHour === 14 && offsetMinute !== 0)) {
      invalid("The endpoint field “updatedAt” contains an invalid UTC offset.");
    }
  }
  if (!Number.isFinite(Date.parse(value))) invalid("The endpoint field “updatedAt” is not a valid timestamp.");
  return value;
}

function trustedExplorerUrl(chain, address) {
  const prefix = TRUSTED_EXPLORERS.get(chain.toLocaleLowerCase("en-US"));
  return prefix ? `${prefix}${encodeURIComponent(address)}` : null;
}

export function validateExplorerUrl(value, chain, address) {
  if (typeof value === "string" && value === value.trim() && value) {
    try {
      const url = new URL(value);
      if (url.protocol === "https:" && !url.username && !url.password) {
        return { explorerUrl: url.href, explorerSource: "endpoint" };
      }
    } catch {
      // A trusted chain mapping may still provide a safe link below.
    }
  }
  const fallback = trustedExplorerUrl(chain, address);
  if (fallback) return { explorerUrl: fallback, explorerSource: "trusted-fallback" };
  return { explorerUrl: null, explorerSource: "unavailable" };
}

/** @returns {import("./token-contract.types.mjs").ValidatedTokenContract} */
export function validateTokenContractResponse(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) invalid("The endpoint response must be a JSON object.");
  const chain = validateChain(value.chain);
  const contractAddress = validateContractAddress(value.contractAddress, chain);
  const updatedAt = validateUpdatedAt(value.updatedAt);
  const explorer = validateExplorerUrl(value.explorerUrl, chain, contractAddress);
  return Object.freeze({ contractAddress, chain, updatedAt, ...explorer });
}

export const validationInternals = Object.freeze({ decodedBase58Length, EVM_CHAINS, TRUSTED_EXPLORERS });
