import { createServer } from "node:http";

const port = Number(process.argv[2] || 8877);
const EVM_A = "0x1111111111111111111111111111111111111111";
const EVM_B = "0x2222222222222222222222222222222222222222";
const counters = new Map();
let scenario = "valid";
let scenarioCount = 0;

function send(response, status, payload, contentType = "application/json") {
  const body = typeof payload === "string" ? payload : JSON.stringify(payload);
  response.writeHead(status, {
    "Content-Type": `${contentType}; charset=utf-8`,
    "Content-Length": Buffer.byteLength(body),
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "no-store",
  });
  response.end(body);
}

createServer((request, response) => {
  const url = new URL(request.url, `http://127.0.0.1:${port}`);
  if (url.pathname === "/__control") {
    scenario = url.searchParams.get("mode") || "valid";
    scenarioCount = 0;
    return send(response, 200, { scenario });
  }
  if (url.pathname === "/scenario") {
    scenarioCount += 1;
    if (scenario === "valid") {
      return send(response, 200, { contractAddress: EVM_A, chain: "Ethereum", explorerUrl: `https://etherscan.io/address/${EVM_A}`, updatedAt: "2026-09-06T12:00:00Z" });
    }
    if (scenario === "changed") {
      const address = scenarioCount === 1 ? EVM_A : EVM_B;
      return send(response, 200, { contractAddress: address, chain: "Ethereum", explorerUrl: `https://etherscan.io/address/${address}`, updatedAt: scenarioCount === 1 ? "2026-09-06T12:00:00Z" : "2026-09-06T12:02:00Z" });
    }
    if (scenario === "stale") {
      if (scenarioCount === 1) return send(response, 200, { contractAddress: EVM_A, chain: "Ethereum", explorerUrl: `https://etherscan.io/address/${EVM_A}`, updatedAt: "2026-09-06T12:00:00Z" });
      return send(response, 503, { error: "temporary test failure" });
    }
    if (scenario === "refreshing") {
      if (scenarioCount === 1) return send(response, 200, { contractAddress: EVM_A, chain: "Ethereum", explorerUrl: `https://etherscan.io/address/${EVM_A}`, updatedAt: "2026-09-06T12:00:00Z" });
      return;
    }
    if (scenario === "solana") {
      const address = "11111111111111111111111111111111";
      return send(response, 200, { contractAddress: address, chain: "Solana", explorerUrl: `https://solscan.io/account/${address}`, updatedAt: "2026-09-06T12:00:00Z" });
    }
    if (scenario === "long") {
      return send(response, 200, { contractAddress: `chain_${"a".repeat(120)}`, chain: "Unknown Chain", explorerUrl: "", updatedAt: "2026-09-06T12:00:00Z" });
    }
    if (scenario === "invalid") {
      return send(response, 200, { contractAddress: "0x1234", chain: "Ethereum", explorerUrl: "javascript:alert(1)", updatedAt: "not-a-date" });
    }
    if (scenario === "malformed") return send(response, 200, "{broken", "application/json");
    if (scenario === "slow") return;
    return send(response, 503, { error: "mock endpoint unavailable" });
  }
  const count = (counters.get(url.pathname) || 0) + 1;
  counters.set(url.pathname, count);
  if (url.pathname === "/valid") {
    return send(response, 200, { contractAddress: EVM_A, chain: "Ethereum", explorerUrl: `https://etherscan.io/address/${EVM_A}`, updatedAt: "2026-09-06T12:00:00Z" });
  }
  if (url.pathname === "/changed") {
    const address = count === 1 ? EVM_A : EVM_B;
    return send(response, 200, { contractAddress: address, chain: "Ethereum", explorerUrl: `https://etherscan.io/address/${address}`, updatedAt: count === 1 ? "2026-09-06T12:00:00Z" : "2026-09-06T12:02:00Z" });
  }
  if (url.pathname === "/stale") {
    if (count === 1) return send(response, 200, { contractAddress: EVM_A, chain: "Ethereum", explorerUrl: `https://etherscan.io/address/${EVM_A}`, updatedAt: "2026-09-06T12:00:00Z" });
    return send(response, 503, { error: "temporary test failure" });
  }
  if (url.pathname === "/solana") {
    const address = "11111111111111111111111111111111";
    return send(response, 200, { contractAddress: address, chain: "Solana", explorerUrl: `https://solscan.io/account/${address}`, updatedAt: "2026-09-06T12:00:00Z" });
  }
  if (url.pathname === "/long") {
    return send(response, 200, { contractAddress: `chain_${"a".repeat(120)}`, chain: "Unknown Chain", explorerUrl: "", updatedAt: "2026-09-06T12:00:00Z" });
  }
  if (url.pathname === "/invalid") {
    return send(response, 200, { contractAddress: "0x1234", chain: "Ethereum", explorerUrl: "javascript:alert(1)", updatedAt: "not-a-date" });
  }
  if (url.pathname === "/malformed") return send(response, 200, "{broken", "application/json");
  if (url.pathname === "/slow") return;
  return send(response, 503, { error: "mock endpoint unavailable" });
}).listen(port, "127.0.0.1", () => {
  process.stdout.write(`Token docs mock endpoint listening at http://127.0.0.1:${port}\n`);
});
