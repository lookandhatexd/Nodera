"""Server-rendered shell for the token documentation route."""

from html import escape
import json
from urllib.parse import urlsplit

from .config import TokenDocsSettings


def _safe_json_script(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def build_content_security_policy(settings: TokenDocsSettings) -> str:
    connect_sources = ["'self'"]
    try:
        endpoint = urlsplit(settings.contract_endpoint)
        if endpoint.scheme in {"http", "https"} and endpoint.netloc:
            origin = f"{endpoint.scheme}://{endpoint.netloc}"
            if origin not in connect_sources:
                connect_sources.append(origin)
    except ValueError:
        pass
    return "; ".join(
        [
            "default-src 'self'",
            "base-uri 'none'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "img-src 'self' data:",
            "style-src 'self'",
            "script-src 'self'",
            f"connect-src {' '.join(connect_sources)}",
        ]
    )


def render_token_docs_page(settings: TokenDocsSettings) -> str:
    token_name = escape(settings.token_name)
    token_symbol = escape(settings.token_symbol)
    config = _safe_json_script(
        {
            "tokenName": settings.token_name,
            "tokenSymbol": settings.token_symbol,
            "contractEndpoint": settings.contract_endpoint,
            "twitterUrl": settings.twitter_url,
            "refreshIntervalMs": settings.refresh_interval_ms,
            "requestTimeoutMs": settings.request_timeout_ms,
        }
    )

    twitter_url = escape(settings.twitter_url or "#", quote=True)

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#f1f4e8">
  <meta name="description" content="Official contract-address documentation and safety guidance for {token_name}.">
  <title>{token_name} Documentation — Agenvora</title>
  <link rel="stylesheet" href="/assets/token-docs/token-docs.css">
  <script id="tokenDocsConfig" type="application/json">{config}</script>
  <script type="module" src="/assets/token-docs/token-docs-page.mjs"></script>
</head>
<body>
  <svg class="icon-library" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><defs>
    <symbol id="docs-icon-external" viewBox="0 0 24 24"><path d="M7 17 17 7M7 7h10v10"/></symbol>
    <symbol id="docs-icon-copy" viewBox="0 0 24 24"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V4H4v12h4"/></symbol>
    <symbol id="docs-icon-check" viewBox="0 0 24 24"><path d="m5 12 4 4L19 6"/></symbol>
    <symbol id="docs-icon-shield" viewBox="0 0 24 24"><path d="m12 3 8 3v5c0 5-5 8-8 10-3-2-8-5-8-10V6z"/><path d="m8 11 3 3 5-5"/></symbol>
    <symbol id="docs-icon-refresh" viewBox="0 0 24 24"><path d="M20 7v5h-5M4 17v-5h5"/><path d="M6.1 9A7 7 0 0 1 18.3 6.7L20 8M4 16l1.7 1.3A7 7 0 0 0 17.9 15"/></symbol>
    <symbol id="docs-icon-alert" viewBox="0 0 24 24"><path d="M12 3 2.8 20h18.4L12 3Z"/><path d="M12 9v5M12 17.5v.1"/></symbol>
    <symbol id="docs-icon-menu" viewBox="0 0 24 24"><path d="M4 7h16M4 17h16"/></symbol>
    <symbol id="docs-icon-arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>
  </defs></svg>

  <a class="skip-link" href="#docsContent">Skip to documentation</a>
  <noscript><div class="noscript-note">Contract data requires JavaScript. The safety and usage guidance below remains available.</div></noscript>

  <div class="protocol-bar"><div class="site-wrap protocol-inner"><span>Official {token_symbol} contract details and verification guidance</span></div></div>
  <header class="site-header">
    <nav class="site-wrap site-nav" aria-label="Primary navigation">
      <a class="brand" href="/" aria-label="Agenvora home"><span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span>AGENVORA</a>
      <button class="site-menu" type="button" aria-label="Open navigation" aria-expanded="false" aria-controls="siteNavLinks"><svg class="icon" aria-hidden="true"><use href="#docs-icon-menu"></use></svg></button>
      <div class="site-nav-links" id="siteNavLinks">
        <a href="/#orchestration">Orchestration</a>
        <a href="/#budget">Budget</a>
        <a href="/#economy">Token model</a>
        <a href="/docs/token" aria-current="page">Token docs</a>
        <a class="button button-secondary" href="mailto:builders@agenvora.ai">Builder contact <svg class="icon" aria-hidden="true"><use href="#docs-icon-external"></use></svg></a>
      </div>
    </nav>
  </header>

  <main class="docs-main" id="docsContent" tabindex="-1">
    <div class="docs-layout site-wrap">
      <nav class="docs-rail docs-rail-left" aria-label="Documentation sections">
        <p class="rail-title">Token documentation</p>
        <a href="#official-contract" aria-current="location">Contract address</a>
        <a href="#token-overview">Token details</a>
        <a href="#add-token">Add the token</a>
        <a href="#integration">Integration</a>
        <a href="#validation">Validation rules</a>
        <span class="rail-divider"></span>
        <a href="/#protocol">Product overview</a>
        <a href="/#economy">Token model</a>
      </nav>

      <article class="docs-article">
        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Agenvora</a><span class="breadcrumb-separator" aria-hidden="true">/</span><span>Token documentation</span></nav>
        <header class="docs-intro">
          <h1>{token_name} Documentation</h1>
          <p>This page publishes the configured Contract Address, its network, and the endpoint update time. Treat the address and network as one record, and verify critical transactions independently.</p>
        </header>

        <section class="docs-section contract-section" id="official-contract" aria-labelledby="contractTitle">
          <div class="section-heading">
            <h2 id="contractTitle">Official Contract Address</h2>
            <p>The complete website-published value from the configured endpoint. It is never shortened into the only visible copy.</p>
          </div>

          <div class="contract-component" id="liveTokenContract" data-state="loading" aria-busy="true">
            <div class="contract-toolbar">
            <div class="status-lockup">
                <span class="status-marker" aria-hidden="true"></span>
                <strong id="contractStatus">Contract Address</strong>
              </div>
              <button class="utility-button" id="refreshContract" type="button" disabled><svg class="icon" aria-hidden="true"><use href="#docs-icon-refresh"></use></svg><span>Refresh</span></button>
            </div>

            <div class="stale-warning" id="staleWarning" hidden>
              <svg class="icon" aria-hidden="true"><use href="#docs-icon-alert"></use></svg>
              <p><strong>May be outdated.</strong> <span id="staleWarningText">The latest refresh failed. Retry before using this address.</span></p>
            </div>

            <div class="contract-body">
              <div class="contract-loading" id="contractLoading" aria-hidden="true">
                <span class="loading-line loading-line-short"></span><span class="loading-line"></span><span class="loading-line loading-line-medium"></span>
              </div>

              <div class="contract-error" id="contractError" role="alert" hidden>
                <svg class="icon" aria-hidden="true"><use href="#docs-icon-alert"></use></svg>
                <div><strong id="contractErrorTitle">Contract data unavailable</strong><p id="contractErrorMessage">No validated address is available.</p></div>
              </div>

              <div class="contract-record" id="contractRecord" hidden>
                <div class="address-well">
                  <div class="network-line"><span>Network</span><strong id="contractChain">Not available</strong></div>
                  <div class="address-row">
                    <code id="contractAddress">No validated address loaded.</code>
                    <button class="button button-primary copy-address" id="copyContract" type="button"><svg class="icon" aria-hidden="true"><use href="#docs-icon-copy"></use></svg><span>Copy address</span></button>
                  </div>
                </div>
                <div class="contract-actions">
                  <a class="explorer-link" id="explorerLink" target="_blank" rel="noopener noreferrer"><span>View on explorer</span><svg class="icon" aria-hidden="true"><use href="#docs-icon-external"></use></svg></a>
                  <span class="format-disclaimer">Format checks do not prove token authenticity or contract safety.</span>
                </div>
              </div>
            </div>
            <div class="contract-announcement sr-only" id="contractAnnouncement" aria-live="polite" aria-atomic="true"></div>
          </div>
        </section>

        <aside class="security-callout" id="verify-before-use" aria-labelledby="securityTitle">
          <svg class="icon security-icon" aria-hidden="true"><use href="#docs-icon-shield"></use></svg>
          <div>
            <h2 id="securityTitle">Verify before use</h2>
            <p>Always verify the Contract Address through official sources before interacting with {token_name}. Never trust addresses sent through unsolicited messages, unofficial social accounts, advertisements, or direct messages.</p>
            <ul>
              <li>Match the transaction network to <strong id="securityChain">the network displayed above</strong>.</li>
              <li>Sending assets to the wrong address or network may result in permanent loss.</li>
              <li>The endpoint is this website's published value—not an audit, guarantee, or proof of authenticity.</li>
            </ul>
          </div>
        </aside>

        <details class="mobile-docs-nav">
          <summary>On this page</summary>
          <nav aria-label="Mobile documentation navigation">
            <a href="#official-contract">Official Contract Address</a>
            <a href="#verify-before-use">Verify before use</a>
            <a href="#token-overview">Token details</a>
            <a href="#add-token">How to add the token</a>
            <a href="#integration">Integration</a>
            <a href="#validation">Validation rules</a>
          </nav>
        </details>

        <section class="docs-section open-section" id="token-overview" aria-labelledby="overviewTitle">
          <h2 id="overviewTitle">Token details</h2>
          <dl class="spec-register">
            <div><dt>Name</dt><dd>{token_name}</dd></div>
            <div><dt>Symbol</dt><dd class="mono">{token_symbol}</dd></div>
            <div><dt>Published network</dt><dd id="overviewChain">Loaded from the endpoint</dd></div>
          </dl>
        </section>

        <section class="docs-section open-section" id="add-token" aria-labelledby="addTitle">
          <h2 id="addTitle">How to add the token</h2>
          <p>Wallet terminology varies. Use a manual import flow only when your wallet supports the network shown above.</p>
          <ol class="instruction-list">
            <li><strong>Select the exact network.</strong><span>Choose <span id="instructionChain">the displayed network</span> in your wallet before pasting an address.</span></li>
            <li><strong>Open the wallet's manual token import.</strong><span>Do not assume every wallet or network supports a custom-token workflow.</span></li>
            <li><strong>Paste the complete Contract Address.</strong><span>Use the Copy address control above; never retype or copy a shortened value.</span></li>
            <li><strong>Verify wallet-resolved details.</strong><span>Confirm independently before approving a transaction. This page does not supply unverified decimals or token-standard values.</span></li>
          </ol>
        </section>

        <section class="docs-section open-section" id="integration" aria-labelledby="integrationTitle">
          <h2 id="integrationTitle">Integration</h2>
          <p>Fetch the published record at runtime and validate every field before displaying or using it. Do not ship a copied Contract Address in application code.</p>
          <div class="code-well">
            <div class="code-toolbar"><span>JavaScript / runtime fetch</span><button class="code-copy" id="copyExample" type="button"><svg class="icon" aria-hidden="true"><use href="#docs-icon-copy"></use></svg><span>Copy example</span></button></div>
            <pre tabindex="0"><code id="integrationCode">const response = await fetch("[ENDPOINT_URL]", {{
  cache: "no-store",
  headers: {{ Accept: "application/json" }}
}});

if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
const tokenContract = await response.json();
// Validate address, chain, explorerUrl, and updatedAt before use.</code></pre>
            <p class="code-status" id="exampleCopyStatus" role="status" hidden></p>
          </div>
          <h3>Response type</h3>
          <div class="type-block"><pre tabindex="0"><code>type TokenContractResponse = {{
  contractAddress: string;
  chain: string;
  explorerUrl: string;
  updatedAt: string;
}};</code></pre></div>
        </section>

        <section class="docs-section open-section" id="validation" aria-labelledby="validationTitle">
          <h2 id="validationTitle">What this page validates</h2>
          <div class="validation-register">
            <div><strong>EVM-compatible chains</strong><p>Require a 20-byte hexadecimal address with a `0x` prefix.</p></div>
            <div><strong>Solana</strong><p>Requires valid Base58 characters that decode to a 32-byte public key.</p></div>
            <div><strong>Other chains</strong><p>Use conservative length, whitespace, and control-character checks without assuming EVM rules.</p></div>
            <div><strong>Explorer and time</strong><p>Links must be HTTPS without credentials. Timestamps must be valid ISO 8601 values.</p></div>
          </div>
        </section>
      </article>

      <nav class="docs-rail docs-rail-right" aria-label="On this page">
        <p class="rail-title">On this page</p>
        <a href="#official-contract">Official Contract Address</a>
        <a href="#verify-before-use">Verify before use</a>
        <a href="#token-overview">Token details</a>
        <a href="#add-token">How to add the token</a>
        <a href="#integration">Integration</a>
        <a href="#validation">Validation rules</a>
      </nav>
    </div>
  </main>

  <footer class="site-footer">
    <div class="site-wrap footer-main"><a class="brand" href="/"><span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span>AGENVORA</a>
      <div class="footer-links"><div><strong>Product</strong><a href="/#orchestration">Orchestration</a><a href="/#budget">Budget</a><a href="/#economy">Token model</a><a href="/#protocol">Repository</a></div><div><strong>Documentation</strong><a href="/docs/token" aria-current="page">Token documentation</a><a href="mailto:builders@agenvora.ai">Builders</a><a href="mailto:hello@agenvora.ai">Email</a><a href="{twitter_url}" target="_blank" rel="noopener noreferrer">X / Twitter <svg class="icon" aria-hidden="true"><use href="#docs-icon-external"></use></svg></a></div></div>
    </div><div class="site-wrap footer-bottom"><span>© 2026 Agenvora Foundation</span><span>Published contract details / verify independently</span></div>
  </footer>
</body>
</html>'''
