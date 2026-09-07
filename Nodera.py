from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import base64
from dataclasses import replace
from html import escape
import hmac
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from token_docs import (
    build_content_security_policy,
    load_token_docs_settings,
    render_token_docs_page,
)
from site_settings import (
    PublicSiteSettings,
    has_admin_password,
    read_site_settings,
    save_site_settings,
    verify_admin_password,
)


TOKEN_DOCS_ASSET_ROOT = Path(__file__).resolve().parent / "token_docs" / "static"
TOKEN_DOCS_ASSETS = {
    "/assets/token-docs/favicon.svg": ("favicon.svg", "image/svg+xml"),
    "/assets/token-docs/token-docs.css": ("token-docs.css", "text/css; charset=utf-8"),
    "/assets/token-docs/token-contract.types.mjs": ("token-contract.types.mjs", "text/javascript; charset=utf-8"),
    "/assets/token-docs/token-contract.validation.mjs": ("token-contract.validation.mjs", "text/javascript; charset=utf-8"),
    "/assets/token-docs/token-contract.service.mjs": ("token-contract.service.mjs", "text/javascript; charset=utf-8"),
    "/assets/token-docs/live-token-contract.mjs": ("live-token-contract.mjs", "text/javascript; charset=utf-8"),
    "/assets/token-docs/token-contract-address.mjs": ("token-contract-address.mjs", "text/javascript; charset=utf-8"),
    "/assets/token-docs/token-docs-page.mjs": ("token-docs-page.mjs", "text/javascript; charset=utf-8"),
    "/assets/token-docs/home-token-ca.mjs": ("home-token-ca.mjs", "text/javascript; charset=utf-8"),
}


HTML = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f1f4e8">
  <link rel="icon" href="/assets/token-docs/favicon.svg" type="image/svg+xml">
  <meta name="description" content="Agenvora coordinates AI agents, controls context and budgets, verifies outputs, and settles useful work in $AGNV.">
  <title>Agenvora — Auditable agent orchestration</title>
  <style>
    :root {
      color-scheme: light;

      --color-canvas: #f1f4e8;
      --color-canvas-subtle: #e7eed8;
      --color-surface-primary: #fbfcf7;
      --color-surface-elevated: #ffffff;
      --color-surface-inverse: #073f31;
      --color-surface-inverse-raised: #0b4b3a;
      --color-code-surface: #082f25;

      --color-text-primary: #10261f;
      --color-text-secondary: #29483e;
      --color-text-muted: #52645d;
      --color-text-placeholder: #5e6e68;
      --color-text-inverse: #f6faf2;
      --color-text-inverse-secondary: #b7c8c0;
      --color-text-on-brand: #123c2f;

      --color-action-primary: #c8f169;
      --color-action-primary-hover: #b6de58;
      --color-action-primary-active: #9fc742;
      --color-action-primary-border: #073f31;
      --color-route-active: #0d7c66;
      --color-route-active-hover: #0a6c59;
      --color-route-active-pressed: #075849;
      --color-route-active-inverse: #8bd7c5;

      --color-border-subtle: #c9d5c0;
      --color-border-strong: #758c80;
      --color-border-inverse-subtle: #2a6a58;
      --color-border-inverse-strong: #5e9383;
      --color-focus: #0a806a;
      --color-focus-inverse: #c8f169;
      --color-link: #08735e;
      --color-link-hover: #055947;
      --color-link-inverse: #8bd7c5;
      --color-link-inverse-hover: #b7f2e3;

      --color-success-text: #147343;
      --color-success-bg: #e1f5e8;
      --color-success-border: #147343;
      --color-warning-text: #815700;
      --color-warning-bg: #fff1c9;
      --color-warning-border: #815700;
      --color-error-text: #b8323c;
      --color-error-bg: #fce8ea;
      --color-error-border: #b8323c;
      --color-info-text: #145f9a;
      --color-info-bg: #e2f1fb;
      --color-info-border: #145f9a;

      --color-disabled-bg: #cfd8c7;
      --color-disabled-text: #5e6e68;
      --color-busy-text: #4d5e57;
      --color-disabled-border: #aab7a3;
      --color-selection-bg: #d6fa7a;
      --color-selection-text: #10261f;
      --color-overlay: rgba(7, 63, 49, .70);
      --color-tap-highlight: rgba(13, 124, 102, .16);

      --color-code-text: #f6faf2;
      --color-code-muted: #b7c8c0;
      --color-code-key: #a9cbf4;
      --color-code-value: #d7e0ba;
      --color-code-success: #91d0ae;

      --font-display: Georgia, "Times New Roman", serif;
      --font-sans: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
      --font-mono: "SFMono-Regular", "Cascadia Code", Consolas, "Liberation Mono", monospace;
      --font-size-xs: .6875rem;
      --font-size-sm: .8125rem;
      --font-size-ui: .875rem;
      --font-size-body: 1rem;
      --font-size-lead: 1.125rem;
      --font-size-h3: 1.25rem;
      --font-size-subtitle: 1.375rem;
      --font-size-micro: .625rem;
      --font-size-code-compact: .75rem;
      --font-size-title: clamp(2rem, 3.6vw, 3rem);
      --font-size-display: clamp(2.75rem, 5.4vw, 4.75rem);
      --font-size-display-wide: clamp(2.75rem, 5.6vw, 4rem);
      --font-size-display-stack: clamp(3rem, 8vw, 4rem);
      --font-size-display-mobile: clamp(2.75rem, 11vw, 3.375rem);
      --font-size-settlement: clamp(2.25rem, 4vw, 3.5rem);
      --font-size-number: clamp(4.5rem, 8vw, 7rem);
      --font-size-number-compact: 5rem;
      --font-size-quote-compact: 2.5rem;
      --line-display: 1.04;
      --line-heading: 1.10;
      --line-ui: 1.35;
      --line-body: 1.60;
      --tracking-display: -.035em;
      --tracking-heading: -.025em;
      --tracking-caps: .07em;

      --space-1: 4px;
      --space-2: 8px;
      --space-3: 12px;
      --space-4: 16px;
      --space-5: 20px;
      --space-6: 24px;
      --space-8: 32px;
      --space-10: 40px;
      --space-12: 48px;
      --space-16: 64px;
      --space-20: 80px;
      --space-24: 96px;

      --radius-none: 0;
      --radius-small: 4px;
      --radius-control: 5px;
      --radius-panel: 8px;
      --border-thin: 1px;
      --border-keyline: 2px;
      --shadow-none: none;
      --shadow-dialog: 0 16px 36px rgba(7, 63, 49, .12);

      --container-max: 1240px;
      --container-pad: clamp(20px, 4vw, 56px);
      --measure-body: 65ch;
      --measure-copy: 45ch;
      --measure-hero: 13ch;
      --dialog-max: 580px;
      --trace-min: 520px;
      --flow-min: 680px;
      --breakpoint-xs: 360px;
      --breakpoint-mobile: 760px;
      --breakpoint-nav: 840px;
      --breakpoint-stack: 900px;
      --breakpoint-wide: 1100px;

      --duration-instant: 0ms;
      --duration-fast: 120ms;
      --duration-state: 200ms;
      --duration-slow: 320ms;
      --ease-out: cubic-bezier(0, 0, .2, 1);
      --ease-in-out: cubic-bezier(.4, 0, .2, 1);

      /* Compact aliases retained for the existing single-file component layer. */
      --canvas: var(--color-canvas);
      --surface: var(--color-surface-primary);
      --raised: var(--color-surface-elevated);
      --inset: var(--color-canvas-subtle);
      --ink: var(--color-text-primary);
      --text: var(--color-text-secondary);
      --muted: var(--color-text-muted);
      --line: var(--color-border-subtle);
      --line-strong: var(--color-border-strong);
      --action: var(--color-action-primary);
      --action-hover: var(--color-action-primary-hover);
      --on-action: var(--color-text-on-brand);
      --success: var(--color-success-text);
      --danger: var(--color-error-text);
      --code: var(--color-code-surface);
      --code-text: var(--color-code-text);
      --code-muted: var(--color-code-muted);
      --code-line: var(--color-border-inverse-subtle);
      --sans: var(--font-sans);
      --mono: var(--font-mono);
      --text-xs: var(--font-size-xs);
      --text-sm: var(--font-size-sm);
      --text-ui: var(--font-size-ui);
      --text-body: var(--font-size-body);
      --text-lead: var(--font-size-lead);
      --text-title: var(--font-size-title);
      --text-display: var(--font-size-display);
      --s1: var(--space-1);
      --s2: var(--space-2);
      --s3: var(--space-3);
      --s4: var(--space-4);
      --s6: var(--space-6);
      --s8: var(--space-8);
      --s12: var(--space-12);
      --s16: var(--space-16);
      --s24: var(--space-24);
      --radius: var(--radius-small);
      --panel-radius: var(--radius-panel);
      --max: var(--container-max);
      --pad: var(--container-pad);
      --fast: var(--duration-fast);
      --state: var(--duration-state);
      --ease: var(--ease-out);
    }
    * { box-sizing: border-box; scrollbar-width: thin; scrollbar-color: var(--color-border-strong) var(--color-canvas-subtle); }
    *::-webkit-scrollbar { width: 10px; height: 10px; }
    *::-webkit-scrollbar-track { background: var(--color-canvas-subtle); }
    *::-webkit-scrollbar-thumb { border: 2px solid var(--color-canvas-subtle); border-radius: var(--radius-small); background: var(--color-border-strong); }
    *::-webkit-scrollbar-button { width: 0; height: 0; display: none; }
    *::-webkit-scrollbar-button:horizontal:decrement, *::-webkit-scrollbar-button:horizontal:increment,
    *::-webkit-scrollbar-button:vertical:decrement, *::-webkit-scrollbar-button:vertical:increment { width: 0; height: 0; border: 0; background: transparent; }
    html { scroll-behavior: smooth; scrollbar-color: var(--line-strong) var(--canvas); }
    body { margin: 0; background: var(--color-canvas); color: var(--color-text-primary); font: 400 var(--font-size-body)/var(--line-body) var(--font-sans); -webkit-font-smoothing: antialiased; }
    button, input, textarea { font: inherit; }
    button, a, input { touch-action: manipulation; -webkit-tap-highlight-color: var(--color-tap-highlight); }
    button { cursor: pointer; }
    a { color: var(--color-link); text-underline-offset: .25em; text-decoration-thickness: 1px; }
    a:hover { color: var(--color-link-hover); }
    button, a { transition: background-color var(--fast), color var(--fast), border-color var(--fast); }
    input, textarea { caret-color: var(--ink); }
    ::selection { background: var(--color-selection-bg); color: var(--color-selection-text); }
    :focus-visible { outline: 2px solid var(--color-focus); outline-offset: 3px; }
    [hidden] { display: none !important; }
    h1, h2, h3, p { margin: 0; }
    h1, h2, h3 { text-wrap: balance; overflow-wrap: break-word; }
    h1 { font-size: var(--font-size-display); line-height: var(--line-display); letter-spacing: var(--tracking-display); }
    h2 { font-size: var(--font-size-title); font-weight: 600; line-height: var(--line-heading); letter-spacing: var(--tracking-heading); }
    .hero h1, .chapter h2, .final-cta h2 { font-family: var(--font-display); font-weight: 400; }
    h3 { font-size: var(--font-size-h3); font-weight: 600; line-height: 1.3; letter-spacing: -.015em; }
    p { color: var(--text); text-wrap: pretty; }
    svg { display: block; }
    .icon { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round; flex-shrink: 0; }
    .icon-library { position: absolute; width: 0; height: 0; overflow: hidden; }
    .wrap { width: min(calc(100% - var(--pad) * 2), var(--max)); margin-inline: auto; }
    .wrap > *, .split > *, .hero-grid > *, .workbench-body > *, .ledger-row > * { min-width: 0; }
    .mono, .micro, output, .numeric { font-family: var(--mono); font-variant-numeric: tabular-nums; }
    .micro { font-size: var(--text-xs); line-height: 1.5; letter-spacing: .07em; text-transform: uppercase; }
    .muted { color: var(--muted); }
    .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; border: 0; }
    .skip { position: fixed; left: 16px; top: 12px; z-index: 100; padding: 12px 16px; transform: translateY(-150%); background: var(--color-surface-inverse); color: var(--color-text-inverse); }
    .skip:focus { transform: none; }
    section[id] { scroll-margin-top: 0; }
    main[id] { scroll-margin-top: 100px; }
    .protocol-bar { border-bottom: 1px solid var(--color-border-subtle); background: var(--color-canvas-subtle); color: var(--color-text-muted); font-size: var(--font-size-xs); }
    .protocol-bar .wrap { display: flex; justify-content: space-between; gap: 16px; padding-block: 6px; }
    .protocol-bar b { color: var(--ink); font-weight: 500; }
    header { position: sticky; top: 0; z-index: 40; background: var(--color-canvas); border-bottom: 1px solid var(--color-border-subtle); }
    nav { display: flex; align-items: center; min-height: 72px; gap: 32px; }
    .brand { display: inline-flex; align-items: center; gap: 12px; color: var(--color-text-primary); text-decoration: none; font-size: var(--font-size-lead); font-weight: 750; letter-spacing: -.025em; }
    .brand:hover { color: var(--color-text-primary); }
    .brand-mark { display: grid; grid-template-columns: repeat(2, 8px); gap: 3px; transform: rotate(-45deg); margin: 4px; }
    .brand-mark i { width: 8px; height: 8px; background: currentColor; }
    .nav-links { display: flex; align-items: center; gap: 28px; margin-left: auto; }
    .nav-links > a { display: inline-flex; align-items: center; min-height: 44px; color: var(--color-text-muted); font-size: var(--font-size-ui); text-decoration: none; }
    .nav-links > a:hover, .nav-links > a[aria-current="location"] { color: var(--color-link); text-decoration: underline; }
    .button { display: inline-flex; align-items: center; justify-content: center; gap: 10px; min-height: 48px; padding: 10px 18px; border: 1px solid var(--color-border-strong); border-radius: var(--radius-control); background: transparent; color: var(--color-text-primary); font: 600 var(--font-size-ui)/var(--line-ui) var(--font-sans); text-decoration: none; }
    .button:hover { background: var(--color-canvas-subtle); border-color: var(--color-text-primary); color: var(--color-text-primary); }
    .button:active { background: var(--color-border-subtle); }
    .button.primary { background: var(--color-action-primary); border-color: var(--color-action-primary-border); color: var(--color-text-on-brand); }
    .button.primary:hover { background: var(--color-action-primary-hover); border-color: var(--color-action-primary-border); color: var(--color-text-on-brand); }
    .button.primary:active { background: var(--color-action-primary-active); border-color: var(--color-action-primary-border); }
    .button:disabled, .text-button:disabled { background: var(--color-disabled-bg); border-color: var(--color-disabled-border); color: var(--color-disabled-text); cursor: not-allowed; }
    .button[aria-busy="true"], .text-button[aria-busy="true"] { color: var(--color-busy-text); cursor: progress; }
    .nav-links .button { min-height: 44px; padding: 8px 14px; }
    .menu { display: none; width: 44px; height: 44px; padding: 12px; align-items: center; justify-content: center; border: 1px solid var(--color-border-strong); border-radius: var(--radius-control); background: transparent; color: var(--color-text-primary); margin-left: auto; }
    .menu:hover { background: var(--color-canvas-subtle); }
    .hero { padding: clamp(64px, 7vw, 96px) 0 0; }
    .hero-grid { display: block; }
    .hero-copy { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(320px, .55fr); column-gap: clamp(48px, 7vw, 104px); align-items: start; }
    .hero-copy h1 { grid-column: 1; grid-row: 1 / 5; max-width: var(--measure-hero); }
    .hero-mobile-break { display: none; }
    .hero-copy > p { grid-column: 2; max-width: var(--measure-copy); margin-top: 10px; font-size: var(--font-size-lead); line-height: 1.65; }
    .hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }
    .hero-copy .hero-actions, .hero-copy .hero-proof-note { grid-column: 2; }
    .hero-proof-note { display: flex; align-items: center; gap: 8px; margin-top: 20px; font-size: var(--font-size-sm); color: var(--color-text-muted); }
    .hero-proof-note .icon { width: 16px; height: 16px; }
    .home-ca-window { grid-column: 1 / -1; display: grid; grid-template-columns: minmax(190px, .55fr) minmax(0, 1.8fr) minmax(180px, auto); margin-top: 48px; border: 1px solid var(--color-border-strong); border-radius: var(--radius-panel); background: var(--color-surface-primary); overflow: hidden; }
    .home-ca-window > * { min-width: 0; }
    .home-ca-identity { padding: 20px 24px; border-right: 1px solid var(--color-border-subtle); }
    .home-ca-identity h2 { margin-top: 6px; font-size: var(--font-size-body); line-height: 1.3; letter-spacing: -.015em; }
    .home-ca-status { display: flex; align-items: flex-start; gap: 8px; margin-top: 14px; color: var(--color-text-muted); font-size: var(--font-size-xs); line-height: 1.45; }
    .home-ca-status-marker { width: 8px; height: 8px; margin-top: 5px; border-radius: 50%; background: var(--color-border-strong); flex: 0 0 auto; }
    .home-ca-window[data-state="success"] .home-ca-status-marker,
    .home-ca-window[data-state="published"] .home-ca-status-marker { background: var(--color-success-text); }
    .home-ca-window[data-state="loading"] .home-ca-status-marker,
    .home-ca-window[data-state="refreshing"] .home-ca-status-marker { background: var(--color-info-text); animation: home-ca-pulse 1.2s ease-in-out infinite; }
    .home-ca-window[data-state="stale"] .home-ca-status-marker { background: var(--color-warning-text); }
    .home-ca-window[data-state="error"] .home-ca-status-marker,
    .home-ca-window[data-state="invalid"] .home-ca-status-marker,
    .home-ca-window[data-state="configuration"] .home-ca-status-marker { background: var(--color-error-text); }
    .home-ca-status strong { display: block; color: var(--color-text-primary); font-weight: 600; }
    .home-ca-status span { display: block; margin-top: 2px; }
    .home-ca-evidence { display: flex; min-height: 126px; padding: 20px 24px; align-items: center; background: var(--color-surface-inverse); color: var(--color-text-inverse); }
    .home-ca-loading, .home-ca-error, .home-ca-record, .home-ca-announcement { width: 100%; min-width: 0; }
    .home-ca-loading { color: var(--color-text-inverse-secondary); font-size: var(--font-size-ui); }
    .home-ca-loading strong { display: block; margin-bottom: 6px; color: var(--color-text-inverse); font-weight: 600; }
    .home-ca-error strong { display: block; color: var(--color-text-inverse); font-size: var(--font-size-ui); }
    .home-ca-error p, .home-ca-warning { margin-top: 6px; color: var(--color-text-inverse-secondary); font-size: var(--font-size-xs); line-height: 1.5; }
    .home-ca-announcement { color: var(--color-text-inverse); font-size: var(--font-size-ui); line-height: 1.5; }
    .home-ca-warning { padding-left: 10px; border-left: 2px solid var(--color-warning-bg); color: var(--color-warning-bg); }
    .home-ca-meta { display: flex; flex-wrap: wrap; gap: 6px 18px; align-items: baseline; color: var(--color-text-inverse-secondary); font-size: var(--font-size-xs); }
    .home-ca-meta strong { color: var(--color-text-inverse); font-weight: 600; }
    .home-ca-address { display: block; max-width: 100%; margin-top: 12px; color: var(--color-action-primary); font: 500 var(--font-size-ui)/1.55 var(--font-mono); overflow-wrap: anywhere; word-break: break-word; user-select: all; }
    .home-ca-tools { display: grid; align-content: center; gap: 6px; padding: 18px; border-left: 1px solid var(--color-border-subtle); }
    .home-ca-tools .button { min-width: 148px; }
    .home-ca-tools .text-button { justify-content: flex-start; padding-inline: 10px; text-align: left; }
    .home-ca-tools a.text-button { color: var(--color-link); }
    .home-ca-tools .icon { width: 16px; height: 16px; }
    @keyframes home-ca-pulse { 50% { opacity: .35; } }
    .final-cta :focus-visible, .code-window :focus-visible { outline-color: var(--color-focus-inverse); }
    .code-window, .code-tabs, pre { scrollbar-color: var(--color-route-active-inverse) var(--color-surface-inverse-raised); }
    .code-window::-webkit-scrollbar-track, .code-tabs::-webkit-scrollbar-track, pre::-webkit-scrollbar-track { background: var(--color-surface-inverse-raised); }
    .code-window::-webkit-scrollbar-thumb, .code-tabs::-webkit-scrollbar-thumb, pre::-webkit-scrollbar-thumb { border-color: var(--color-surface-inverse-raised); background: var(--color-route-active-inverse); }
    .scroll-hint { display: none; align-items: center; gap: 8px; color: var(--color-text-muted); font-size: var(--font-size-xs); padding: 10px 20px; border-top: 1px solid var(--color-border-subtle); }
    .hero-notes { display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; margin-top: 48px; padding: 22px 0; border-top: 1px solid var(--color-border-subtle); }
    .hero-note { display: flex; align-items: baseline; gap: 12px; font-size: var(--text-sm); }
    .hero-note span { color: var(--muted); }
    .hero-note b { font-weight: 500; }
    .provider-band { margin-top: 16px; background: var(--color-surface-primary); border-block: 1px solid var(--color-border-subtle); }
    .provider-grid { display: grid; grid-template-columns: 1.3fr repeat(5, 1fr); align-items: stretch; }
    .provider-label { padding: 24px 20px 24px 0; align-self: center; color: var(--muted); font-size: var(--text-sm); max-width: 22ch; }
    .provider { position: relative; display: grid; grid-template-columns: 24px minmax(0, 1fr); gap: 12px; align-items: center; min-width: 0; padding: 24px 16px; border: 0; border-left: 1px solid var(--color-border-subtle); background: transparent; color: var(--color-text-primary); text-align: left; }
    .provider-icon { width: 24px; height: 24px; color: var(--color-text-primary); fill: currentColor; flex: 0 0 auto; }
    .provider-copy { min-width: 0; }
    .provider strong { display: block; font-size: var(--text-ui); font-weight: 550; }
    .provider .provider-kind { display: block; margin-top: 5px; font: var(--text-xs)/1.4 var(--mono); color: var(--muted); }
    .provider:hover, .provider[aria-pressed="true"] { background: var(--color-canvas-subtle); }
    .provider[aria-pressed="true"] { color: var(--color-link); }
    .provider[aria-pressed="true"]::after { content: ""; position: absolute; bottom: 0; left: 16px; right: 16px; height: 2px; background: var(--color-route-active); }
    .provider-feedback { min-height: 45px; padding-block: 12px; color: var(--muted); font-size: var(--text-sm); }
    .provider-feedback b { color: var(--ink); font-weight: 500; }
    .chapter { padding: var(--space-24) 0; border-bottom: 1px solid var(--color-border-subtle); }
    .principles-chapter { background: var(--color-surface-primary); }
    #budget, .economy { background: var(--color-canvas-subtle); }
    .chapter-head { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: end; margin-bottom: 40px; }
    .chapter-head h2 { max-width: 19ch; }
    .chapter-head p { max-width: 54ch; }
    .workbench { border: 1px solid var(--color-border-strong); border-radius: var(--radius-panel); background: var(--color-surface-elevated); }
    .workbench-bar { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; padding: 16px 24px; border-bottom: 1px solid var(--line); }
    .stage-rail { overflow-x: auto; overscroll-behavior-inline: contain; border-bottom: 1px solid var(--line); }
    .stage-track { position: relative; min-width: 520px; --stage-position: 0%; }
    .stage-tabs { display: grid; grid-template-columns: repeat(5, 1fr); }
    .stage-tab { display: flex; align-items: center; gap: 12px; min-height: 66px; padding: 16px 24px 20px; border: 0; background: transparent; color: var(--muted); text-align: left; }
    .stage-tab span { font: var(--text-xs)/1 var(--mono); }
    .stage-tab strong { color: inherit; font-size: var(--text-ui); font-weight: 550; }
    .stage-tab:hover { background: var(--color-canvas-subtle); color: var(--color-text-primary); }
    .stage-tab[aria-selected="true"] { color: var(--color-link); background: var(--color-canvas-subtle); }
    .stage-tab:focus-visible { outline-offset: -3px; }
    .run-spine { position: absolute; left: 10%; right: 10%; bottom: 10px; height: 2px; background: var(--color-border-subtle); pointer-events: none; }
    .run-spine::before { content: ""; position: absolute; inset: 0 auto 0 0; width: var(--stage-position); background: var(--color-route-active); transition: width var(--duration-state) var(--ease-out); }
    .checkpoint { position: absolute; left: var(--stage-position); top: -5px; width: 12px; height: 12px; border: 2px solid var(--color-surface-inverse); background: var(--color-action-primary); transform: translateX(-50%); transition: left var(--duration-state) var(--ease-out); }
    .workbench-body { display: grid; grid-template-columns: minmax(0, 1.8fr) minmax(300px, 1fr); }
    .map-area { min-width: 0; border-right: 1px solid var(--line); }
    .orchestration { max-width: 100%; overflow-x: auto; padding: 40px 24px 28px; overscroll-behavior-inline: contain; background: var(--color-surface-primary); }
    .flow-map { min-width: 680px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; align-items: stretch; }
    .flow-node { position: relative; padding: 14px 10px; background: var(--color-surface-elevated); border: 1px solid var(--color-border-strong); border-radius: var(--radius-small); transition: border-color var(--duration-state), background-color var(--duration-state); }
    .flow-node:not(:last-child)::after { content: ""; position: absolute; top: 45%; left: calc(100% + 1px); width: 20px; height: 1px; background: var(--line-strong); }
    .flow-node .micro { display: block; color: var(--muted); }
    .flow-node strong { display: block; min-height: 40px; margin: 12px 0; font-size: var(--text-sm); font-weight: 500; line-height: 1.5; }
    .flow-state { display: block; font-size: var(--text-xs); color: var(--muted); }
    .flow-node[data-state="complete"] .flow-state { color: var(--color-success-text); }
    .flow-node[data-state="active"] { border-color: var(--color-route-active); background: var(--color-canvas-subtle); }
    .flow-node[data-state="active"] .flow-state { color: var(--color-route-active); font-weight: 600; }
    .flow-node[data-state="active"]::before { content: ""; position: absolute; width: 10px; height: 10px; top: -6px; left: calc(50% - 5px); border: 2px solid var(--color-surface-inverse); background: var(--color-action-primary); }
    .map-caption { display: grid; grid-template-columns: repeat(3, 1fr); padding: 0 24px; background: var(--surface); border-top: 1px solid var(--line); }
    .map-caption div { padding: 18px 12px 18px 0; }
    .map-caption span { display: block; font-size: var(--text-xs); color: var(--muted); }
    .map-caption b { display: block; margin-top: 6px; font-size: var(--text-sm); font-weight: 500; }
    .agent-register { padding: 12px 24px 16px; border-top: 1px solid var(--line); }
    .agent-register div { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; font-size: var(--text-xs); }
    .agent-register span { color: var(--muted); }
    .stage-detail { display: flex; flex-direction: column; }
    .detail-copy { padding: 24px; }
    .stage-code { display: flex; align-items: center; gap: 8px; color: var(--color-link); }
    .stage-code::before { content: ""; width: 8px; height: 8px; background: var(--color-route-active); }
    .detail-copy h3 { margin-top: 16px; }
    .detail-copy p { margin-top: 12px; font-size: var(--text-ui); }
    .detail-ledger { margin-top: auto; }
    .detail-ledger div { display: grid; grid-template-columns: 76px minmax(0, 1fr); align-items: start; gap: 16px; padding: 14px 24px; border-top: 1px solid var(--line); font-size: var(--text-xs); }
    .detail-ledger span { color: var(--muted); }
    .detail-ledger b { text-align: right; font-weight: 400; overflow-wrap: anywhere; }
    .split { display: grid; grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr); gap: 80px; }
    .section-copy h2 { max-width: 18ch; }
    .section-copy > p { margin-top: 24px; max-width: 45ch; }
    .principles { align-items: start; }
    .principle { padding: 24px 0; border-top: 1px solid var(--line-strong); }
    .principle:first-child { padding-top: 0; border-top: 0; }
    .principle:last-child { padding-bottom: 0; }
    .principle h3 { font-size: var(--font-size-lead); }
    .principle p { margin-top: 8px; max-width: 55ch; }
    .principle-intro { position: sticky; top: 130px; }
    .check-list { padding: 0; margin: 28px 0 0; list-style: none; }
    .check-list li { display: flex; gap: 12px; align-items: flex-start; padding: 10px 0; font-size: var(--text-ui); color: var(--text); }
    .check-list svg { margin-top: 2px; }
    .budget-grid { align-items: start; }
    .calculator { min-width: 0; background: var(--color-surface-elevated); border: 1px solid var(--color-border-strong); border-radius: var(--radius-panel); }
    .calculator-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 24px; border-bottom: 1px solid var(--line); background: var(--surface); border-radius: var(--radius-panel) var(--radius-panel) 0 0; }
    .text-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; padding: 8px; border: 1px solid transparent; background: transparent; color: var(--color-link); text-decoration: underline; text-underline-offset: .25em; font-size: var(--font-size-sm); }
    .text-button:hover { background: var(--inset); border-radius: var(--radius); }
    .calculator-body { padding: 24px; }
    .quote { display: flex; flex-wrap: wrap; align-items: end; justify-content: space-between; gap: 16px; padding-bottom: 24px; border-bottom: 1px solid var(--line-strong); }
    .quote-label { color: var(--muted); font-size: var(--text-sm); }
    .quote strong { font: 500 clamp(2rem, 3vw, 2.75rem)/1.15 var(--mono); letter-spacing: -.03em; }
    .quote strong b { font-size: var(--text-ui); letter-spacing: 0; font-weight: 400; }
    .ranges { margin-top: 20px; }
    .range { padding: 10px 0; }
    .range label { display: flex; justify-content: space-between; gap: 16px; align-items: baseline; font-size: var(--text-ui); }
    .range output { font-size: var(--text-sm); font-weight: 500; }
    input[type="range"] { display: block; width: 100%; min-width: 0; height: 44px; margin: 0; appearance: none; background: transparent; cursor: pointer; accent-color: var(--color-route-active); }
    input[type="range"]::-webkit-slider-runnable-track { height: 3px; background: var(--line); border-radius: var(--radius-small); }
    input[type="range"]::-webkit-slider-thumb { width: 18px; height: 18px; appearance: none; border: 2px solid var(--color-surface-inverse); background: var(--color-surface-elevated); border-radius: var(--radius-small); margin-top: -7.5px; }
    input[type="range"]::-moz-range-track { height: 3px; background: var(--line); }
    input[type="range"]::-moz-range-thumb { width: 15px; height: 15px; border: 2px solid var(--color-surface-inverse); background: var(--color-surface-elevated); border-radius: var(--radius-small); }
    .budget-output { border-top: 1px solid var(--line-strong); padding-top: 20px; }
    .budget-receipt { display: flex; justify-content: space-between; gap: 16px; align-items: baseline; }
    .budget-receipt small { font-size: var(--text-sm); color: var(--muted); }
    .budget-receipt strong { font: 500 var(--text-ui)/1.4 var(--mono); }
    #budgetSummary { margin-top: 8px; color: var(--muted); font-size: var(--text-sm); }
    .allocation-chart { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 20px; }
    .allocation-chart > div { min-width: 0; }
    .bar-track { display: block; height: 4px; background: var(--inset); margin-bottom: 8px; }
    .bar-track i { display: block; width: 100%; height: 100%; background: var(--ink); transform: scaleX(var(--amount)); transform-origin: left; transition: transform var(--state) var(--ease); }
    .allocation-chart span:not(.bar-track) { color: var(--muted); font-size: var(--text-xs); }
    .calculation-note { margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--line); color: var(--muted); font-size: var(--text-xs); }
    .economy { background: var(--surface); }
    .economy-grid { display: grid; grid-template-columns: minmax(0, .8fr) minmax(0, 1.2fr); gap: 80px; }
    .supply-panel { display: flex; flex-direction: column; justify-content: space-between; gap: 32px; }
    .supply-panel h3 { font-size: var(--font-size-subtitle); max-width: 23ch; font-weight: 500; }
    .supply { font-size: var(--font-size-number); font-weight: 500; line-height: 1; letter-spacing: -.04em; }
    .supply span { display: block; margin-top: 12px; font: var(--text-sm)/1.5 var(--mono); letter-spacing: 0; color: var(--muted); }
    .allocation-head { display: flex; justify-content: space-between; gap: 24px; padding: 16px 0; border-block: 1px solid var(--line-strong); }
    .allocation-head h3 { font-size: var(--text-ui); letter-spacing: 0; }
    .alloc-row { display: grid; grid-template-columns: 24px minmax(0, 1.7fr) minmax(40px, 1fr) 42px; gap: 16px; align-items: center; min-height: 58px; padding: 12px 0; border-bottom: 1px solid var(--line); }
    .alloc-row > span { font: var(--text-xs)/1.4 var(--mono); color: var(--muted); }
    .alloc-row b { font-size: var(--text-ui); font-weight: 400; }
    .alloc-row i { height: 3px; background: var(--ink); }
    .alloc-row strong { font: 500 var(--text-ui)/1.4 var(--mono); text-align: right; }
    .economy-note { margin-top: 20px; color: var(--muted); font-size: var(--text-sm); }
    .utility-register { display: grid; grid-template-columns: repeat(5, 1fr); gap: 24px; margin-top: 56px; padding-top: 24px; border-top: 1px solid var(--line-strong); }
    .utility-item h3 { font-size: var(--text-ui); }
    .utility-item p { margin-top: 10px; font-size: var(--text-sm); color: var(--muted); }
    .protocol-grid { align-items: start; }
    .protocol-copy .button { margin-top: 24px; }
    .code-window { min-width: 0; border: 1px solid var(--color-border-inverse-strong); border-radius: var(--radius-panel); background: var(--color-code-surface); color: var(--color-code-text); }
    .code-window ::selection { background: var(--color-selection-bg); color: var(--color-selection-text); }
    .code-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 16px 8px 24px; border-bottom: 1px solid var(--code-line); }
    .code-head > span { color: var(--code-muted); font-size: var(--text-xs); }
    .copy-code { display: flex; align-items: center; gap: 8px; min-height: 44px; padding: 8px 12px; background: transparent; color: var(--color-code-text); border: 1px solid var(--color-border-inverse-strong); border-radius: var(--radius-control); font-size: var(--font-size-sm); }
    .copy-code:hover { background: var(--color-surface-inverse-raised); }
    .copy-code:disabled { background: var(--color-surface-inverse-raised); border-color: var(--color-border-inverse-strong); color: var(--color-code-muted); cursor: not-allowed; }
    .copy-code[aria-busy="true"] { color: var(--color-code-text); cursor: progress; }
    .code-tabs { display: flex; border-bottom: 1px solid var(--code-line); overflow-x: auto; padding: 0 12px; }
    .code-tab { position: relative; min-height: 52px; padding: 12px; border: 0; color: var(--code-muted); background: transparent; font: var(--text-sm)/1.4 var(--mono); }
    .code-tab[aria-selected="true"], .code-tab:hover { color: var(--code-text); }
    .code-tab[aria-selected="true"]::after { content: ""; height: 2px; background: var(--code-text); position: absolute; bottom: 0; left: 12px; right: 12px; }
    pre { min-height: 285px; margin: 0; padding: 24px; overflow: auto; font: var(--text-sm)/1.85 var(--mono); scrollbar-color: var(--code-muted) var(--code); }
    pre .key { color: var(--color-code-key); }
    pre .value { color: var(--color-code-value); }
    .code-meta { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 20px; padding: 20px 24px; border-top: 1px solid var(--code-line); }
    .code-meta small { display: block; font-size: var(--text-xs); color: var(--code-muted); }
    .code-meta b { display: block; margin-top: 6px; font: var(--text-xs)/1.4 var(--mono); }
    .code-meta .ok { color: var(--color-code-success); }
    .copy-status { padding: 12px 24px; border-top: 1px solid var(--code-line); color: var(--code-text); font-size: var(--text-sm); }
    .final-cta { padding: 80px 0; background: var(--color-surface-inverse); color: var(--color-text-inverse); }
    .final-grid { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, .75fr); gap: 64px; align-items: center; }
    .final-grid h2 { max-width: 23ch; font-size: var(--font-size-title); }
    .final-grid p { margin-top: 16px; color: var(--color-text-inverse-secondary); }
    .final-grid .hero-actions { margin-top: 0; justify-content: end; }
    .final-cta .button:not(.primary) { border-color: var(--color-border-inverse-strong); color: var(--color-text-inverse); }
    .final-cta .button:not(.primary):hover { background: var(--color-surface-inverse-raised); border-color: var(--color-text-inverse); color: var(--color-text-inverse); }
    footer { background: var(--color-canvas-subtle); border-top: 1px solid var(--color-border-subtle); }
    .footer-main { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; padding-block: 48px; }
    .footer-main .brand { align-self: start; justify-self: start; }
    .footer-links { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
    .footer-links strong { display: block; margin-bottom: 12px; color: var(--muted); font-size: var(--text-sm); font-weight: 400; }
    .footer-links a { display: flex; align-items: center; gap: 6px; width: fit-content; min-height: 44px; color: var(--color-link); font-size: var(--font-size-ui); text-decoration: underline; }
    .footer-links a:hover { color: var(--color-link-hover); }
    .footer-bottom { display: flex; justify-content: space-between; gap: 16px; padding-block: 20px; border-top: 1px solid var(--line-strong); color: var(--muted); font-size: var(--text-xs); }
    dialog { width: min(var(--dialog-max), calc(100% - 32px)); max-height: calc(100dvh - 32px); padding: 0; border: 1px solid var(--color-border-strong); border-radius: var(--radius-panel); background: var(--color-surface-elevated); color: var(--color-text-primary); box-shadow: var(--shadow-dialog); overscroll-behavior: contain; }
    dialog::backdrop { background: var(--color-overlay); }
    body:has(dialog[open]) { overflow: hidden; }
    .dialog-head { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 68px; padding: 12px 16px 12px 24px; border-bottom: 1px solid var(--line); }
    .dialog-head h2 { font-size: var(--font-size-h3); letter-spacing: -.015em; }
    .dialog-head h2:focus-visible { outline-offset: 4px; }
    .dialog-close { display: grid; place-items: center; flex-shrink: 0; width: 44px; height: 44px; border: 1px solid transparent; border-radius: var(--radius-control); background: transparent; color: var(--color-text-primary); }
    .dialog-close:hover { background: var(--inset); }
    .access-form, .draft-result { padding: 24px; }
    .access-form > p, .draft-result > p { font-size: var(--text-ui); }
    .access-form label, .draft-result label { display: block; margin-top: 20px; font-size: var(--text-ui); font-weight: 500; }
    .access-form input, .access-form textarea, .draft-result textarea { width: 100%; max-width: 100%; margin-top: 8px; padding: 12px; border: 1px solid var(--color-border-strong); border-radius: var(--radius-control); background: var(--color-surface-primary); color: var(--color-text-primary); font-size: var(--font-size-body); line-height: 1.5; resize: vertical; }
    input::placeholder, textarea::placeholder { color: var(--color-text-placeholder); opacity: 1; }
    [aria-invalid="true"] { border-color: var(--color-error-border) !important; }
    [aria-invalid="true"]:focus-visible { outline-color: var(--color-focus); }
    .field-error { margin-top: 8px; padding: 8px 10px; border: 1px solid var(--color-error-border); background: var(--color-error-bg); color: var(--color-error-text); font-size: var(--font-size-sm); }
    .access-actions { display: flex; justify-content: space-between; flex-wrap: wrap; align-items: center; gap: 12px; margin-top: 24px; }
    .form-note { margin-top: 16px; color: var(--muted); font-size: var(--text-sm); }
    .access-status { font-size: var(--text-sm); }
    .draft-result h3 { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
    .draft-result h3 .icon { color: var(--color-success-text); }
    .draft-result textarea { font: var(--text-sm)/1.6 var(--mono); min-height: 180px; }
    .draft-result .recovery { margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--line); color: var(--muted); font-size: var(--text-sm); }
    .noscript-note { padding: 16px var(--pad); background: var(--inset); font-size: var(--text-ui); }
    @media (max-width: 1100px) {
      :root { --font-size-display: var(--font-size-display-wide); }
      .hero-copy { column-gap: 48px; grid-template-columns: minmax(0, 1.25fr) minmax(300px, .75fr); }
      .hero-copy > p { font-size: var(--text-body); }
      .split, .economy-grid { gap: 48px; }
      .workbench-body { grid-template-columns: minmax(0, 1fr); }
      .map-area { border-right: 0; }
      .stage-detail { display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid var(--line); }
      .detail-ledger { border-left: 1px solid var(--line); margin-top: 0; }
      .detail-ledger div:first-child { border-top: 0; }
      .provider-grid { grid-template-columns: repeat(5, 1fr); }
      .provider-label { grid-column: 1 / -1; max-width: none; padding: 14px 0; }
      .provider { border-top: 1px solid var(--line); padding: 16px; }
      .provider:first-of-type { border-left: 0; }
      .utility-register { gap: 16px; }
    }
    @media (max-width: 900px) {
      :root { --font-size-display: var(--font-size-display-stack); }
      nav { gap: 20px; }
      .nav-links { gap: 16px; }
      .hero { padding-top: 56px; }
      .hero-copy { display: block; }
      .hero-copy h1 { max-width: 15ch; }
      .hero-copy > p { max-width: 55ch; }
      .home-ca-window { grid-template-columns: minmax(180px, .55fr) minmax(0, 1.45fr); margin-top: 40px; }
      .home-ca-tools { grid-column: 1 / -1; display: flex; flex-wrap: wrap; align-items: center; padding: 12px 18px; border-top: 1px solid var(--color-border-subtle); border-left: 0; }
      .home-ca-tools .button { min-width: 0; }
      .hero-notes { margin-top: 40px; gap: 24px; }
      .hero-note { display: block; }
      .hero-note b { display: block; margin-top: 4px; }
      .split, .economy-grid { grid-template-columns: 1fr; gap: 36px; }
      .section-copy h2 { max-width: 23ch; }
      .section-copy > p { max-width: 60ch; }
      .principle-intro { position: static; }
      .principle-list { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
      .principle { padding: 0; border-top: 0; }
      .supply-panel { flex-direction: row; align-items: end; }
      .supply-panel h3 { max-width: 24ch; }
      .supply { font-size: var(--font-size-number-compact); white-space: nowrap; }
      .utility-register { grid-template-columns: repeat(3, 1fr); gap: 32px; }
      .final-grid { grid-template-columns: 1fr; gap: 32px; }
      .final-grid .hero-actions { justify-content: start; }
    }
    @media (max-width: 840px) {
      nav { min-height: 60px; gap: 12px; flex-wrap: wrap; }
      .menu { display: flex; }
      .nav-links { display: none; flex: 0 0 100%; margin: 0; gap: 0; padding-bottom: 16px; }
      .nav-links.open { display: grid; }
      .nav-links > a { min-height: 48px; border-top: 1px solid var(--color-border-subtle); }
      .nav-links .button { margin-top: 12px; }
    }
    @media (max-width: 760px) {
      :root { --pad: 20px; --font-size-title: clamp(2rem, 6.5vw, 2.5rem); --font-size-display: var(--font-size-display-mobile); }
      .protocol-bar .wrap { justify-content: center; font-size: var(--font-size-xs); letter-spacing: .04em; }
      .protocol-bar .protocol-tagline { display: none; }
      .brand { font-size: var(--font-size-body); }
      .hero { padding-top: 36px; }
      .hero-copy h1 { max-width: 13ch; line-height: 1.06; }
      .hero-mobile-break { display: initial; }
      .hero-copy > p { margin-top: 20px; font-size: var(--text-body); line-height: 1.6; }
      .hero-actions { margin-top: 24px; gap: 10px; }
      .hero-actions .button { padding-inline: 14px; }
      .hero-proof-note { margin-top: 16px; }
      .home-ca-window { grid-template-columns: 1fr; margin-top: 32px; }
      .home-ca-identity { padding: 18px 20px; border-right: 0; border-bottom: 1px solid var(--color-border-subtle); }
      .home-ca-status { margin-top: 10px; }
      .home-ca-evidence { min-height: 144px; padding: 20px; }
      .home-ca-tools { display: grid; grid-template-columns: 1fr 1fr; padding: 12px; }
      .home-ca-tools .button, .home-ca-tools .text-button { min-height: 48px; justify-content: center; text-align: center; }
      .home-ca-tools a.text-button { grid-column: 1 / -1; }
      .hero-notes { grid-template-columns: 1fr; gap: 0; margin-top: 28px; padding: 0; }
      .hero-note { display: flex; justify-content: space-between; gap: 16px; padding: 14px 0; border-bottom: 1px solid var(--line); }
      .hero-note b { margin: 0; }
      .hero-note:last-child { border-bottom: 0; }
      .provider-band { margin-top: 32px; }
      .provider-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .provider { min-height: 76px; padding: 16px 12px; }
      .provider:nth-of-type(odd) { border-left: 0; }
      .provider:last-child { grid-column: 1 / -1; }
      .provider-feedback { padding-block: 16px; }
      .chapter { padding: 64px 0; }
      .chapter-head { grid-template-columns: 1fr; gap: 20px; margin-bottom: 32px; }
      .chapter-head p { max-width: 58ch; }
      .stage-tab { padding: 16px 14px 20px; gap: 8px; }
      .workbench-bar { padding: 16px; }
      .workbench .scroll-hint { display: flex; }
      .orchestration { padding: 28px 16px; }
      .map-caption { grid-template-columns: 1fr; padding-inline: 16px; }
      .map-caption div { display: flex; justify-content: space-between; gap: 12px; padding: 12px 0; border-top: 1px solid var(--line); }
      .map-caption div:first-child { border-top: 0; }
      .map-caption b { margin: 0; text-align: right; }
      .agent-register { padding-inline: 16px; }
      .agent-register div { flex-direction: column; gap: 2px; padding: 10px 0; }
      .stage-detail { display: flex; }
      .detail-copy { padding: 24px 16px; }
      .detail-ledger { border-left: 0; }
      .detail-ledger div { padding: 14px 16px; }
      .detail-ledger div:first-child { border-top: 1px solid var(--line); }
      .principle-list { grid-template-columns: 1fr; gap: 24px; }
      .principle { padding-top: 24px; border-top: 1px solid var(--line); }
      .principle:first-child { padding-top: 24px; border-top: 1px solid var(--line); }
      .calculator-head { padding: 8px 16px; }
      .calculator-head .micro { max-width: 20ch; }
      .calculator-body { padding: 20px 16px; }
      .quote { align-items: start; flex-direction: column; gap: 12px; }
      .quote strong { font-size: var(--font-size-quote-compact); }
      .allocation-chart { gap: 8px; }
      .allocation-chart span:not(.bar-track) { font-size: var(--text-xs); }
      .supply-panel { flex-direction: column; align-items: start; gap: 24px; }
      .supply { font-size: var(--font-size-number-compact); }
      .alloc-row { grid-template-columns: 20px minmax(0, 1fr) 38px; gap: 10px; }
      .alloc-row i { grid-column: 2; grid-row: 2; }
      .alloc-row strong { grid-column: 3; grid-row: 1; }
      .alloc-row b { font-size: var(--text-ui); }
      .utility-register { grid-template-columns: 1fr; gap: 0; margin-top: 32px; padding-top: 0; }
      .utility-item { padding: 20px 0; border-bottom: 1px solid var(--line); }
      .utility-item p { margin-top: 6px; font-size: var(--text-ui); }
      .code-head { padding-left: 16px; }
      .code-head > span { max-width: 22ch; }
      pre { padding: 20px 16px; font-size: var(--font-size-code-compact); }
      .code-meta { gap: 20px 28px; padding: 20px 16px; }
      .copy-status { padding-inline: 16px; }
      .final-cta { padding: 64px 0; }
      .footer-main { grid-template-columns: 1fr; gap: 32px; padding-block: 40px; }
      .footer-links { gap: 24px; }
      .footer-bottom { flex-direction: column; gap: 8px; }
      .dialog-head { padding-left: 20px; }
      .access-form, .draft-result { padding: 20px; }
    }
    @media (max-width: 420px) {
      .hero-actions { flex-direction: column; }
      .hero-actions .button { width: 100%; }
    }
    @media (max-width: 360px) {
      .hero-note { font-size: var(--font-size-sm); }
      .allocation-chart { grid-template-columns: 1fr 1fr; gap: 16px; }
    }
    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      *, *::before, *::after { transition-duration: 0s !important; animation-duration: 0s !important; scroll-behavior: auto !important; }
    }
  </style>
</head>
<body>
  <svg class="icon-library" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><defs>
    <symbol id="icon-arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>
    <symbol id="icon-down" viewBox="0 0 24 24"><path d="M12 5v14M6 13l6 6 6-6"/></symbol>
    <symbol id="icon-external" viewBox="0 0 24 24"><path d="M7 17 17 7M7 7h10v10"/></symbol>
    <symbol id="icon-check" viewBox="0 0 24 24"><path d="m5 12 4 4L19 6"/></symbol>
    <symbol id="icon-copy" viewBox="0 0 24 24"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V4H4v12h4"/></symbol>
    <symbol id="icon-close" viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></symbol>
    <symbol id="icon-menu" viewBox="0 0 24 24"><path d="M4 7h16M4 17h16"/></symbol>
    <symbol id="icon-shield" viewBox="0 0 24 24"><path d="m12 3 8 3v5c0 5-5 8-8 10-3-2-8-5-8-10V6z"/><path d="m8 11 3 3 5-5"/></symbol>
    <symbol id="logo-openai" viewBox="118.557 119.958 484.139 479.818"><path d="M304.246 294.611V249.028c0-3.839 1.441-6.719 4.798-8.636l91.648-52.78c12.475-7.197 27.35-10.554 42.702-10.554 57.577 0 94.046 44.624 94.046 92.124 0 3.358 0 7.197-.481 11.036l-95.005-55.66c-5.757-3.357-11.517-3.357-17.274 0l-120.434 70.053Zm213.999 177.534V363.224c0-6.719-2.881-11.517-8.637-14.875l-120.434-70.053 39.345-22.553c3.358-1.917 6.238-1.917 9.596 0l91.647 52.78c26.392 15.356 44.143 47.982 44.143 79.648 0 36.465-21.59 70.054-55.66 83.97v.004ZM275.937 376.182l-39.345-23.03c-3.357-1.917-4.798-4.798-4.798-8.637V238.956c0-51.339 39.345-90.207 92.606-90.207 20.155 0 38.864 6.719 54.702 18.714l-94.524 54.701c-5.756 3.357-8.636 8.155-8.636 14.875v139.147l-.005-.004Zm84.689 48.94-56.38-31.667v-67.172l56.38-31.667 56.376 31.667v67.172l-56.376 31.667Zm36.226 145.867c-20.154 0-38.863-6.719-54.701-18.713l94.523-54.702c5.757-3.357 8.637-8.155 8.637-14.875V343.552l39.827 23.03c3.357 1.917 4.798 4.797 4.798 8.637v105.559c0 51.339-39.827 90.207-93.084 90.207v.004ZM283.134 463.99l-91.648-52.779c-26.392-15.357-44.143-47.982-44.143-79.649 0-36.946 22.072-70.053 56.137-83.969v109.398c0 6.719 2.881 11.517 8.637 14.875l119.957 69.571-39.345 22.553c-3.357 1.917-6.238 1.917-9.595 0Zm-5.275 78.69c-54.22 0-94.046-40.785-94.046-91.166 0-3.839.481-7.678.958-11.517l94.524 54.701c5.756 3.358 11.517 3.358 17.273 0l120.434-69.571v45.583c0 3.839-1.44 6.719-4.798 8.636l-91.647 52.78c-12.476 7.197-27.351 10.554-42.703 10.554h.005Zm118.993 57.096c58.059 0 106.518-41.263 117.558-95.964 53.739-13.916 88.286-64.297 88.286-115.636 0-33.589-14.393-66.214-40.304-89.726 2.399-10.077 3.839-20.154 3.839-30.226 0-68.613-55.66-119.957-119.957-119.957-12.952 0-25.428 1.917-37.904 6.238-21.595-21.113-51.344-34.547-83.97-34.547-58.058 0-106.517 41.262-117.557 95.963-53.739 13.916-88.286 64.297-88.286 115.636 0 33.589 14.393 66.214 40.304 89.726-2.399 10.077-3.839 20.154-3.839 30.227 0 68.613 55.66 119.956 119.956 119.956 12.953 0 25.429-1.917 37.905-6.238 21.59 21.113 51.339 34.548 83.969 34.548Z"/></symbol>
    <symbol id="logo-anthropic" viewBox="0 0 24 24"><path d="M17.304 3.541h-3.672l6.696 16.918H24Zm-10.608 0L0 20.459h3.744l1.37-3.553h7.005l1.369 3.553h3.744L10.536 3.541Zm-.371 10.223 2.291-5.945 2.292 5.945Z"/></symbol>
    <symbol id="logo-gemini" viewBox="0 0 24 24"><path d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81"/></symbol>
    <symbol id="icon-open-models" viewBox="0 0 24 24"><path d="m12 2 10 5-10 5L2 7l10-5ZM3.9 10.2 12 14.25l8.1-4.05 1.9.95-10 5-10-5 1.9-.95Zm0 4L12 18.25l8.1-4.05 1.9.95-10 5-10-5 1.9-.95Z"/></symbol>
    <symbol id="icon-custom-agents" viewBox="0 0 24 24"><path d="M10 2h4v4h-4V2ZM3 18h4v4H3v-4Zm14 0h4v4h-4v-4Zm-6-12h2v5h5v5h-2v-3H8v3H6v-5h5V6Z"/></symbol>
  </defs></svg>
  <a class="skip" href="/?section=main">Skip to content</a>
  <noscript><div class="noscript-note">This page is readable without JavaScript. Interactive examples need JavaScript. For builder access, <a href="mailto:builders@agenvora.ai">email builders@agenvora.ai</a>.</div></noscript>
  <div class="protocol-bar"><div class="wrap micro"><span>Route, verify, and settle AI agent work.</span></div></div>
  <header>
    <nav class="wrap" aria-label="Primary navigation">
      <a class="brand" href="/" aria-label="Agenvora home"><span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span>AGENVORA</a>
      <button class="menu" type="button" aria-label="Open navigation" aria-expanded="false" aria-controls="navLinks"><svg class="icon" aria-hidden="true"><use href="#icon-menu"></use></svg></button>
      <div class="nav-links" id="navLinks">
        <a href="/?section=orchestration">Orchestration</a><a href="/?section=budget">Budget</a><a href="/?section=protocol">Protocol</a><a href="/?section=economy">$AGNV</a><a href="/docs/token">Token docs</a>
        <button class="button" type="button" data-open-access>Request builder access <svg class="icon" aria-hidden="true"><use href="#icon-external"></use></svg></button>
      </div>
    </nav>
  </header>
  <main id="main" tabindex="-1">
    <section class="hero" id="top" aria-labelledby="heroTitle">
      <div class="hero-grid wrap">
        <div class="hero-copy">
          <h1 id="heroTitle">Coordinate agents.<br class="hero-mobile-break"> Verify the work.</h1>
          <p>One objective, coordinated across your AI stack. Route tasks, control context and budgets, verify every result, and settle useful contributions in $AGNV.</p>
          <div class="hero-actions"><button class="button primary" type="button" data-open-access>Request builder access <svg class="icon" aria-hidden="true"><use href="#icon-external"></use></svg></button><a class="button" href="/?section=orchestration">Explore the workflow <svg class="icon" aria-hidden="true"><use href="#icon-down"></use></svg></a></div>
          <div class="hero-proof-note"><svg class="icon" aria-hidden="true"><use href="#icon-shield"></use></svg> Budget first. Settlement after verification.</div>
        </div>
        <div class="hero-notes" aria-label="Protocol principles">
          <div class="hero-note"><span class="micro">Input</span><b>One objective</b></div>
          <div class="hero-note"><span class="micro">Control</span><b>Budget before execution</b></div>
          <div class="hero-note"><span class="micro">Exit</span><b>Verified settlement</b></div>
        </div>
      </div>
      <div class="provider-band"><div class="provider-grid wrap">
        <div class="provider-label">Route the tools you already use.</div>
        <button class="provider" type="button" aria-pressed="true" data-provider="OpenAI" data-provider-copy="Reasoning and generation routed with a defined context allowance."><svg class="provider-icon" aria-hidden="true"><use href="#logo-openai"></use></svg><span class="provider-copy"><strong>OpenAI</strong><span class="provider-kind">API</span></span></button>
        <button class="provider" type="button" aria-pressed="false" data-provider="Anthropic" data-provider-copy="Long-context analysis without duplicating the full workflow state."><svg class="provider-icon" aria-hidden="true"><use href="#logo-anthropic"></use></svg><span class="provider-copy"><strong>Anthropic</strong><span class="provider-kind">API</span></span></button>
        <button class="provider" type="button" aria-pressed="false" data-provider="Gemini" data-provider-copy="Multimodal research returned into the shared evidence record."><svg class="provider-icon" aria-hidden="true"><use href="#logo-gemini"></use></svg><span class="provider-copy"><strong>Gemini</strong><span class="provider-kind">API</span></span></button>
        <button class="provider" type="button" aria-pressed="false" data-provider="Open models" data-provider-copy="Local workloads follow the same budget and verification policy."><svg class="provider-icon" aria-hidden="true"><use href="#icon-open-models"></use></svg><span class="provider-copy"><strong>Open models</strong><span class="provider-kind">Runtime</span></span></button>
        <button class="provider" type="button" aria-pressed="false" data-provider="Custom agents" data-provider-copy="Specialist endpoints register explicit inputs, outputs, and settlement rules."><svg class="provider-icon" aria-hidden="true"><use href="#icon-custom-agents"></use></svg><span class="provider-copy"><strong>Custom agents</strong><span class="provider-kind">Endpoint</span></span></button>
      </div></div>
      <p class="provider-feedback wrap" id="providerFeedback" aria-live="polite"><b>OpenAI</b> — Reasoning and generation routed with a defined context allowance.</p>
    </section>

    <section class="chapter" id="orchestration" aria-labelledby="orchestrationTitle"><div class="wrap">
      <div class="chapter-head"><h2 id="orchestrationTitle">One objective. Five controlled handoffs.</h2><p>Explore a sample workflow, one stage at a time. Each handoff narrows the task, limits what agents see, and leaves evidence for what follows.</p></div>
      <div class="workbench">
        <div class="workbench-bar"><span class="micro">Market brief workflow</span><span class="micro muted">Choose a stage to inspect</span></div>
        <div class="stage-rail"><div class="stage-track">
          <div class="stage-tabs" role="tablist" aria-label="Orchestration stages">
            <button class="stage-tab" id="stage-0" type="button" role="tab" aria-selected="true" aria-controls="stagePanel" data-stage="0"><span>01</span><strong>Plan</strong></button>
            <button class="stage-tab" id="stage-1" type="button" role="tab" aria-selected="false" aria-controls="stagePanel" tabindex="-1" data-stage="1"><span>02</span><strong>Route</strong></button>
            <button class="stage-tab" id="stage-2" type="button" role="tab" aria-selected="false" aria-controls="stagePanel" tabindex="-1" data-stage="2"><span>03</span><strong>Execute</strong></button>
            <button class="stage-tab" id="stage-3" type="button" role="tab" aria-selected="false" aria-controls="stagePanel" tabindex="-1" data-stage="3"><span>04</span><strong>Verify</strong></button>
            <button class="stage-tab" id="stage-4" type="button" role="tab" aria-selected="false" aria-controls="stagePanel" tabindex="-1" data-stage="4"><span>05</span><strong>Settle</strong></button>
          </div><div class="run-spine" aria-hidden="true"><i class="checkpoint"></i></div>
        </div></div>
        <div class="workbench-body">
          <div class="map-area">
            <div class="orchestration" role="region" tabindex="0" aria-label="Five-stage orchestration map" aria-describedby="mapScrollHint">
              <div class="flow-map">
                <div class="flow-node" data-node-stage="0" data-state="active"><small class="micro">Stage 1: Plan</small><strong>Bound the<br>objective</strong><span class="flow-state">Inspecting</span></div>
                <div class="flow-node" data-node-stage="1"><small class="micro">Stage 2: Route</small><strong>Match each<br>specialist</strong><span class="flow-state">Next</span></div>
                <div class="flow-node" data-node-stage="2"><small class="micro">Stage 3: Execute</small><strong>Share only<br>what is needed</strong><span class="flow-state">Next</span></div>
                <div class="flow-node" data-node-stage="3"><small class="micro">Stage 4: Verify</small><strong>Review evidence<br>and tests</strong><span class="flow-state">Next</span></div>
                <div class="flow-node" data-node-stage="4"><small class="micro">Stage 5: Settle</small><strong>Release verified<br>payment</strong><span class="flow-state">Next</span></div>
              </div>
            </div>
            <div class="scroll-hint" id="mapScrollHint"><svg class="icon" aria-hidden="true"><use href="#icon-arrow"></use></svg> Scroll the map to inspect all five handoffs</div>
            <div class="map-caption"><div><span>Context policy</span><b>Minimum necessary</b></div><div><span>Budget ceiling</span><b class="mono">15.00 $AGNV</b></div><div><span>Completion rule</span><b>Evidence + tests</b></div></div>
            <div class="agent-register" aria-label="Specialist contributions"><div><b>Research with OpenAI</b><span>Sources + facts</span></div><div><b>Analysis with Anthropic</b><span>Claims + risks</span></div><div><b>Writing with Gemini</b><span>Draft brief</span></div></div>
          </div>
          <div class="stage-detail" id="stagePanel" role="tabpanel" tabindex="0" aria-labelledby="stage-0">
            <div class="detail-copy"><div class="stage-code micro" id="stageCode">Stage 1: Plan</div><h3 id="stageTitle">Bound the objective.</h3><p id="stageCopy">Turn the request into eight tasks with explicit inputs, token ceilings, and completion rules before any provider is called.</p></div>
            <div class="detail-ledger"><div><span>Handoff</span><b id="stageHandoff">Objective → task graph</b></div><div><span>Evidence</span><b id="stageEvidence">Run manifest</b></div><div><span>Active route</span><b id="providerValue">OpenAI API</b></div><div><span>Route note</span><b id="providerCopy">Defined context allowance</b></div></div>
          </div>
        </div>
      </div>
      <div class="sr-only" id="stageAnnouncement" aria-live="polite"></div>
    </div></section>

    <section class="chapter principles-chapter" aria-labelledby="principlesTitle"><div class="split principles wrap">
      <div class="section-copy principle-intro"><h2 id="principlesTitle">Less context. More accountability.</h2><p>An agent should not need to know every model, carry the whole thread, or trust an unverified output. The protocol makes each operational boundary visible.</p></div>
      <div class="principle-list">
        <article class="principle"><h3>Route by fit</h3><p>Send each bounded task to the best-fit model or specialist already in your stack.</p></article>
        <article class="principle"><h3>Share only what is needed</h3><p>Each agent receives the minimum context required for its part of the run.</p></article>
        <article class="principle"><h3>Verify before release</h3><p>Evidence, schemas, claims, and tests become explicit settlement gates.</p></article>
        <article class="principle"><h3>Attribute every contribution</h3><p>The run record shows what each agent received, produced, and earned.</p></article>
      </div>
    </div></section>

    <section class="chapter" id="budget" aria-labelledby="budgetTitle"><div class="split budget-grid wrap">
      <div class="section-copy"><h2 id="budgetTitle">Set the ceiling before the calls.</h2><p>Configure a workflow before execution. See how agent count, task count, and shared context change the estimate.</p><ul class="check-list"><li><svg class="icon" aria-hidden="true"><use href="#icon-check"></use></svg> Maximum spend is explicit</li><li><svg class="icon" aria-hidden="true"><use href="#icon-check"></use></svg> Context remains measurable</li><li><svg class="icon" aria-hidden="true"><use href="#icon-check"></use></svg> Payment follows verification</li></ul></div>
      <div class="calculator">
        <div class="calculator-head"><span class="micro">Workflow budget</span><button class="text-button" type="button" id="resetBudget">Reset values</button></div>
        <div class="calculator-body">
          <div class="quote"><span class="quote-label">Estimated settlement</span><strong id="settlementValue">12.40 <b>$AGNV</b></strong></div>
          <div class="ranges">
            <div class="range"><label for="agentsRange"><span>Specialist agents</span><output for="agentsRange" id="agentsOutput">4</output></label><input id="agentsRange" type="range" min="2" max="8" value="4" step="1" aria-describedby="budgetCalculationNote"></div>
            <div class="range"><label for="tasksRange"><span>Bounded tasks</span><output for="tasksRange" id="tasksOutput">8</output></label><input id="tasksRange" type="range" min="3" max="18" value="8" step="1" aria-describedby="budgetCalculationNote"></div>
            <div class="range"><label for="contextRange"><span>Context allowance</span><output for="contextRange" id="contextOutput">55%</output></label><input id="contextRange" type="range" min="25" max="100" value="55" step="5" aria-valuetext="55 percent" aria-describedby="budgetCalculationNote"></div>
          </div>
          <div class="budget-output"><div class="budget-receipt"><small>Context envelope</small><strong id="tokenEstimate">22.4K / 32K</strong></div><p id="budgetSummary">4 agents across 8 tasks, sharing 55% of the available context window.</p>
            <div class="allocation-chart" aria-label="Relative contribution weights"><div><span class="bar-track"><i id="barResearch" style="--amount:.604"></i></span><span>Research</span></div><div><span class="bar-track"><i id="barAnalysis" style="--amount:.764"></i></span><span>Analysis</span></div><div><span class="bar-track"><i id="barWriting" style="--amount:.6775"></i></span><span>Writing</span></div><div><span class="bar-track"><i id="barValidation" style="--amount:.52"></i></span><span>Verify</span></div></div>
          </div>
          <p class="calculation-note" id="budgetCalculationNote">Estimates and contribution weights, not a price quote. Settlement remains gated by verification.</p>
          <div class="sr-only" id="budgetAnnouncement" aria-live="polite"></div>
        </div>
      </div>
    </div></section>

    <section class="chapter" id="protocol" aria-labelledby="protocolTitle"><div class="split protocol-grid wrap">
      <div class="section-copy protocol-copy"><h2 id="protocolTitle">Open the run contract. Inspect the work.</h2><p>The protocol makes a run's boundaries explicit: what every agent receives, which policy approves it, and why settlement is released.</p><ul class="check-list"><li><svg class="icon" aria-hidden="true"><use href="#icon-check"></use></svg> Reproducible run manifests</li><li><svg class="icon" aria-hidden="true"><use href="#icon-check"></use></svg> Provider-neutral routing policies</li><li><svg class="icon" aria-hidden="true"><use href="#icon-check"></use></svg> Verification receipts per settlement</li></ul><button class="button" type="button" data-open-access>Request builder access <svg class="icon" aria-hidden="true"><use href="#icon-external"></use></svg></button><p class="form-note">These examples show the protocol's routing, verification, and settlement flow. Request access to explore the repository.</p></div>
      <div class="code-window">
        <div class="code-head"><span class="micro">Protocol example</span><button class="copy-code" type="button" id="copyCode"><svg class="icon" aria-hidden="true"><use href="#icon-copy"></use></svg><span>Copy</span></button></div>
        <div class="code-tabs" role="tablist" aria-label="Protocol files">
          <button class="code-tab" type="button" role="tab" id="tab-run" aria-selected="true" aria-controls="code-run" data-code="run">run.ts</button>
          <button class="code-tab" type="button" role="tab" id="tab-policy" aria-selected="false" aria-controls="code-policy" tabindex="-1" data-code="policy">policy.json</button>
          <button class="code-tab" type="button" role="tab" id="tab-verify" aria-selected="false" aria-controls="code-verify" tabindex="-1" data-code="verify">verify.ts</button>
        </div>
        <pre id="code-run" data-code-panel="run" role="tabpanel" aria-labelledby="tab-run" tabindex="0"><code><span class="key">const</span> run = <span class="key">await</span> agenvora.run({
  goal: <span class="value">"Ship a market brief"</span>,
  budget: { token: <span class="value">"AGNV"</span>, max: 15 },
  policy: {
    context: <span class="value">"minimum-necessary"</span>,
    settlement: <span class="value">"verified-output"</span>
  }
});</code></pre>
        <pre id="code-policy" data-code-panel="policy" role="tabpanel" aria-labelledby="tab-policy" tabindex="0" hidden><code>{
  <span class="value">"context"</span>: <span class="value">"minimum-necessary"</span>,
  <span class="value">"maxSettlement"</span>: 15,
  <span class="value">"verification"</span>: [<span class="value">"evidence"</span>, <span class="value">"claims"</span>, <span class="value">"tests"</span>]
}</code></pre>
        <pre id="code-verify" data-code-panel="verify" role="tabpanel" aria-labelledby="tab-verify" tabindex="0" hidden><code><span class="key">const</span> receipt = <span class="key">await</span> verify(run.output, {
  manifest: run.manifest,
  checks: [<span class="value">"schema"</span>, <span class="value">"claims"</span>, <span class="value">"tests"</span>]
});

<span class="key">if</span> (receipt.passed) <span class="key">await</span> settle(run);</code></pre>
        <div class="code-meta"><div><small>License</small><b>Apache 2.0</b></div><div><small>Verification checks</small><b class="ok">12 passing</b></div><div><small>Result</small><b>Verified receipt</b></div></div>
        <p class="copy-status" id="copyStatus" role="status" hidden></p>
      </div>
    </div></section>

    <section class="chapter economy" id="economy" aria-labelledby="economyTitle"><div class="wrap">
      <div class="chapter-head"><h2 id="economyTitle">Requested work. Verified contribution.</h2><p>$AGNV connects the two. Utility and allocation describe the protocol model.</p></div>
      <div class="economy-grid">
        <div class="supply-panel"><h3>Allocated for a working agent network.</h3><div class="supply numeric">1B<span>$AGNV / Fixed supply</span></div></div>
        <div class="allocation-panel"><div class="allocation-head"><h3>Allocation register</h3><span class="micro muted">Total / 100%</span></div>
          <div class="alloc-row"><span>01</span><b>Agent &amp; network rewards</b><i style="width:100%" aria-hidden="true"></i><strong>35%</strong></div>
          <div class="alloc-row"><span>02</span><b>Ecosystem &amp; treasury</b><i style="width:71.4%" aria-hidden="true"></i><strong>25%</strong></div>
          <div class="alloc-row"><span>03</span><b>Core contributors</b><i style="width:42.8%" aria-hidden="true"></i><strong>15%</strong></div>
          <div class="alloc-row"><span>04</span><b>Strategic partners</b><i style="width:34.3%" aria-hidden="true"></i><strong>12%</strong></div>
          <div class="alloc-row"><span>05</span><b>Protocol liquidity</b><i style="width:22.8%" aria-hidden="true"></i><strong>8%</strong></div>
          <div class="alloc-row"><span>06</span><b>Community launch</b><i style="width:14.3%" aria-hidden="true"></i><strong>5%</strong></div>
          <p class="economy-note">Token allocation for network operations.</p>
        </div>
      </div>
      <div class="utility-register" aria-label="AGNV utility">
        <article class="utility-item"><h3>Agent execution</h3><p>Pay agents for completed, attributable work.</p></article>
        <article class="utility-item"><h3>Task budgets</h3><p>Express maximum workflow spend before APIs are called.</p></article>
        <article class="utility-item"><h3>Priority access</h3><p>Prioritize time-sensitive work when capacity is constrained.</p></article>
        <article class="utility-item"><h3>Agent staking</h3><p>Support accountability for agents that take verified tasks.</p></article>
        <article class="utility-item"><h3>Network governance</h3><p>Participate in future rules, incentives, and standards.</p></article>
      </div>
      <section class="home-ca-window" id="homeTokenCa" data-state="loading" aria-labelledby="homeCaTitle" aria-busy="true">
        <div class="home-ca-identity">
          <p class="micro muted">CA</p>
          <h2 id="homeCaTitle">Contract address</h2>
          <div class="home-ca-status">
            <span class="home-ca-status-marker" aria-hidden="true"></span>
            <span><strong id="homeCaStatus">Contract Address to be announced</strong><span id="homeCaStatusDetail">The public address will appear here when it is published.</span></span>
          </div>
        </div>
        <div class="home-ca-evidence">
          <div class="home-ca-loading" id="homeCaLoading"><strong>Contract Address to be announced.</strong></div>
          <div class="home-ca-error" id="homeCaError" hidden><strong id="homeCaErrorTitle">Contract data unavailable</strong><p id="homeCaErrorMessage">No validated address is available.</p></div>
          <div class="home-ca-record" id="homeCaRecord" hidden>
            <div class="home-ca-meta"><span>Chain&nbsp; <strong id="homeCaChain"></strong></span><span>Updated&nbsp; <time id="homeCaUpdated"></time></span></div>
            <code class="home-ca-address" id="homeCaAddress" tabindex="0" aria-label="Complete Contract Address"></code>
          </div>
          <p class="home-ca-announcement" id="homeCaAnnouncementText" hidden>Contract Address to be announced.</p>
        </div>
        <div class="home-ca-tools">
          <button class="button primary" id="homeCaCopy" type="button" disabled><svg class="icon" aria-hidden="true"><use href="#icon-copy"></use></svg><span>Copy CA</span></button>
          <a class="text-button" href="/docs/token?section=verify-before-use">Verification &amp; safety</a>
        </div>
        <p class="sr-only" id="homeCaLiveAnnouncement" aria-live="polite" aria-atomic="true"></p>
      </section>
    </div></section>

    <section class="final-cta" aria-labelledby="startTitle"><div class="final-grid wrap"><div><h2 id="startTitle">Give every agent a job, a budget, and a reason to deliver.</h2><p>Explore the protocol with the Agenvora builder network.</p></div><div class="hero-actions"><button class="button primary" type="button" data-open-access>Request builder access <svg class="icon" aria-hidden="true"><use href="#icon-external"></use></svg></button><a class="button" href="/?section=protocol">Review the protocol <svg class="icon" aria-hidden="true"><use href="#icon-arrow"></use></svg></a></div></div></section>
  </main>
  <footer>
    <div class="footer-main wrap"><a class="brand" href="/"><span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span>AGENVORA</a>
      <div class="footer-links"><div><strong>Protocol</strong><a href="/?section=orchestration">Orchestration</a><a href="/?section=budget">Budget</a><a href="/?section=economy">$AGNV</a><a href="/?section=protocol">Repository</a></div><div><strong>Connect</strong><a href="/docs/token">Token documentation</a><a href="mailto:builders@agenvora.ai">Builders</a><a href="mailto:hello@agenvora.ai">Email</a><a id="twitterLink" href="__TWITTER_URL__" target="_blank" rel="noopener noreferrer">X / Twitter <svg class="icon" aria-hidden="true"><use href="#icon-external"></use></svg></a></div></div>
    </div><div class="footer-bottom wrap"><span>© 2026 Agenvora Foundation</span><span>Agenvora protocol</span></div>
  </footer>

  <dialog id="accessDialog" aria-labelledby="accessTitle">
    <div class="dialog-head"><h2 id="accessTitle" tabindex="-1">Request builder access</h2><button class="dialog-close" type="button" aria-label="Close access request"><svg class="icon" aria-hidden="true"><use href="#icon-close"></use></svg></button></div>
    <form class="access-form" id="accessForm" novalidate>
      <p>Tell the maintainers what you want to orchestrate. We’ll prepare an email draft you can review and send from your email app.</p>
      <label for="accessEmail">Work email</label><input id="accessEmail" name="email" type="email" inputmode="email" autocomplete="email" spellcheck="false" required maxlength="254" placeholder="you@company.com" aria-describedby="emailError"><p class="field-error" id="emailError" hidden></p>
      <label for="accessUse">Agent workflow</label><textarea id="accessUse" name="use" rows="4" required maxlength="3000" placeholder="What should your agents accomplish together?" aria-describedby="useError"></textarea><p class="field-error" id="useError" hidden></p>
      <div class="access-actions"><button class="text-button" type="button" data-close-access>Cancel</button><button class="button primary" type="submit">Prepare email draft <svg class="icon" aria-hidden="true"><use href="#icon-arrow"></use></svg></button></div>
      <p class="form-note">No information is sent from this page. Your draft stays here until you close or reload the browser tab.</p>
    </form>
    <div class="draft-result" id="draftResult" hidden>
      <h3 id="draftTitle" tabindex="-1"><svg class="icon" aria-hidden="true"><use href="#icon-check"></use></svg> Email draft prepared</h3>
      <p>Review your request below, then open your email app to send it to <a href="mailto:builders@agenvora.ai">builders@agenvora.ai</a>.</p>
      <label for="draftMessage">Prepared message</label><textarea id="draftMessage" rows="7" readonly></textarea>
      <div class="access-actions"><button class="text-button" type="button" id="editDraft">Edit details</button><a class="button primary" id="openEmail" href="mailto:builders@agenvora.ai">Open email app <svg class="icon" aria-hidden="true"><use href="#icon-external"></use></svg></a></div>
      <p class="recovery">No email app available? Copy the draft and send it from your webmail.</p>
      <button class="text-button" type="button" id="copyDraft"><svg class="icon" aria-hidden="true"><use href="#icon-copy"></use></svg><span>Copy draft</span></button>
      <p class="access-status" id="accessStatus" role="status"></p>
    </div>
  </dialog>

  <script>
    const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
    const menu = document.querySelector('.menu');
    const navLinks = document.querySelector('#navLinks');
    function bindSectionLinks() {
      document.querySelectorAll('a[href*="?section="]').forEach(link => link.addEventListener('click', event => {
        const url = new URL(link.href, location.href);
        const section = url.searchParams.get('section');
        if (url.pathname !== location.pathname || !section) return;
        const target = document.getElementById(section);
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({ behavior: motionPreference.matches ? 'auto' : 'smooth' });
        history.replaceState(null, '', location.pathname);
      }));
      const section = new URLSearchParams(location.search).get('section');
      if (section) requestAnimationFrame(() => {
        document.getElementById(section)?.scrollIntoView({ behavior: 'auto' });
        history.replaceState(null, '', location.pathname);
      });
    }
    bindSectionLinks();
    function closeMenu() {
      navLinks.classList.remove('open');
      menu.setAttribute('aria-expanded', 'false');
      menu.setAttribute('aria-label', 'Open navigation');
    }
    menu.addEventListener('click', () => {
      const open = navLinks.classList.toggle('open');
      menu.setAttribute('aria-expanded', String(open));
      menu.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    });
    navLinks.querySelectorAll('a, button').forEach(item => item.addEventListener('click', closeMenu));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && navLinks.classList.contains('open')) {
        closeMenu();
        menu.focus();
      }
    });
    document.addEventListener('click', event => {
      if (navLinks.classList.contains('open') && !event.target.closest('nav')) closeMenu();
    });
    document.querySelector('nav').addEventListener('focusout', event => {
      if (navLinks.classList.contains('open') && event.relatedTarget && !event.currentTarget.contains(event.relatedTarget)) closeMenu();
    });
    matchMedia('(min-width: 761px)').addEventListener('change', closeMenu);

    const providerButtons = [...document.querySelectorAll('.provider')];
    providerButtons.forEach(button => button.addEventListener('click', () => {
      providerButtons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      document.querySelector('#providerValue').textContent = button.dataset.provider + ' ' + button.querySelector('.provider-kind').textContent;
      document.querySelector('#providerCopy').textContent = button.dataset.providerCopy;
      document.querySelector('#providerFeedback').textContent = button.dataset.provider + ' selected. ' + button.dataset.providerCopy;
    }));

    const stageData = [
      { code: 'Stage 1: Plan', title: 'Bound the objective.', copy: 'Turn the request into eight tasks with explicit inputs, token ceilings, and completion rules before any provider is called.', handoff: 'Objective → task graph', evidence: 'Run manifest' },
      { code: 'Stage 2: Route', title: 'Choose by task fit.', copy: 'Match research, analysis, writing, and validation work to available specialists without making one model carry the whole run.', handoff: 'Task graph → routes', evidence: 'Routing policy' },
      { code: 'Stage 3: Execute', title: 'Share minimum context.', copy: 'Each specialist receives only the state required to complete its bounded task, while reusable evidence stays in the shared run record.', handoff: 'Routes → contributions', evidence: 'Context ledger' },
      { code: 'Stage 4: Verify', title: 'Test the contribution.', copy: 'Outputs pass schema, claim, evidence, and test checks before the run can release settlement.', handoff: 'Contributions → receipt', evidence: 'Verification checks' },
      { code: 'Stage 5: Settle', title: 'Pay useful work.', copy: 'Measured contributions settle in $AGNV only after the configured verification policy returns a passing receipt.', handoff: 'Receipt → settlement', evidence: 'Verification receipt' }
    ];
    const stageTabs = [...document.querySelectorAll('.stage-tab')];
    const flowNodes = [...document.querySelectorAll('[data-node-stage]')];
    const stagePanel = document.querySelector('#stagePanel');
    function revealInScroller(element, scroller) {
      const elementBox = element.getBoundingClientRect();
      const scrollBox = scroller.getBoundingClientRect();
      if (elementBox.left < scrollBox.left) scroller.scrollLeft -= scrollBox.left - elementBox.left + 8;
      else if (elementBox.right > scrollBox.right) scroller.scrollLeft += elementBox.right - scrollBox.right + 8;
    }
    function setStage(index, focus = false) {
      stageTabs.forEach((tab, tabIndex) => {
        const active = tabIndex === index;
        tab.setAttribute('aria-selected', String(active));
        tab.tabIndex = active ? 0 : -1;
      });
      flowNodes.forEach((node, nodeIndex) => {
        node.dataset.state = nodeIndex === index ? 'active' : nodeIndex < index ? 'complete' : '';
        node.querySelector('.flow-state').textContent = nodeIndex === index ? 'Inspecting' : nodeIndex < index ? 'Completed' : 'Next';
      });
      document.querySelector('.stage-track').style.setProperty('--stage-position', (index * 25) + '%');
      const data = stageData[index];
      for (const [id, key] of [['stageCode', 'code'], ['stageTitle', 'title'], ['stageCopy', 'copy'], ['stageHandoff', 'handoff'], ['stageEvidence', 'evidence']]) {
        document.getElementById(id).textContent = data[key];
      }
      stagePanel.setAttribute('aria-labelledby', stageTabs[index].id);
      document.querySelector('#stageAnnouncement').textContent = data.code + '. ' + data.title + ' Evidence: ' + data.evidence + '.';
      if (focus) stageTabs[index].focus({ preventScroll: true });
      revealInScroller(stageTabs[index], document.querySelector('.stage-rail'));
      revealInScroller(flowNodes[index], document.querySelector('.orchestration'));
    }
    function connectTabKeys(tabs, onSelect) {
      tabs.forEach((tab, index) => tab.addEventListener('keydown', event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 :
          (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
        onSelect(next, true);
      }));
    }
    stageTabs.forEach((tab, index) => tab.addEventListener('click', () => setStage(index)));
    connectTabKeys(stageTabs, setStage);

    const budgetControls = {
      agents: document.querySelector('#agentsRange'),
      tasks: document.querySelector('#tasksRange'),
      context: document.querySelector('#contextRange')
    };
    function updateBudget() {
      const agents = Number(budgetControls.agents.value);
      const tasks = Number(budgetControls.tasks.value);
      const context = Number(budgetControls.context.value);
      const settlement = .655 + agents * 1.35 + tasks * .58 + context * .031;
      const tokenEstimate = Math.min(32, tasks * 1.65 + agents * .8 + context * .11);
      document.querySelector('#agentsOutput').textContent = agents;
      document.querySelector('#tasksOutput').textContent = tasks;
      document.querySelector('#contextOutput').textContent = context + '%';
      budgetControls.context.setAttribute('aria-valuetext', context + ' percent');
      document.querySelector('#settlementValue').firstChild.textContent = settlement.toFixed(2) + ' ';
      document.querySelector('#tokenEstimate').textContent = tokenEstimate.toFixed(1) + 'K / 32K';
      document.querySelector('#budgetSummary').textContent = agents + ' agents across ' + tasks + ' tasks, sharing ' + context + '% of the available context window.';
      const base = Math.min(100, 30 + tasks * 3.8);
      const weights = {
        barResearch: Math.round(base),
        barAnalysis: Math.round(Math.min(100, base + agents * 4)),
        barWriting: Math.round(Math.min(100, 32 + context * .65)),
        barValidation: Math.round(Math.min(100, 24 + agents * 7))
      };
      for (const [id, weight] of Object.entries(weights)) {
        document.getElementById(id).style.setProperty('--amount', weight / 100);
      }
    }
    function announceBudget() {
      document.querySelector('#budgetAnnouncement').textContent = 'Estimated settlement ' + document.querySelector('#settlementValue').textContent + '. Context ' + document.querySelector('#tokenEstimate').textContent + '.';
    }
    Object.values(budgetControls).forEach(control => {
      control.addEventListener('input', updateBudget);
      control.addEventListener('change', announceBudget);
    });
    document.querySelector('#resetBudget').addEventListener('click', () => {
      budgetControls.agents.value = 4; budgetControls.tasks.value = 8; budgetControls.context.value = 55;
      updateBudget(); announceBudget(); budgetControls.agents.focus({ preventScroll: true });
    });
    updateBudget();

    const codeTabs = [...document.querySelectorAll('.code-tab')];
    const codePanels = [...document.querySelectorAll('[data-code-panel]')];
    const copyCode = document.querySelector('#copyCode');
    const copyStatus = document.querySelector('#copyStatus');
    function setCode(index, focus = false) {
      const tab = codeTabs[index];
      codeTabs.forEach(item => {
        const active = item === tab;
        item.setAttribute('aria-selected', String(active));
        item.tabIndex = active ? 0 : -1;
      });
      codePanels.forEach(panel => panel.hidden = panel.dataset.codePanel !== tab.dataset.code);
      copyStatus.hidden = true;
      copyStatus.textContent = '';
      copyCode.querySelector('span').textContent = 'Copy';
      if (focus) tab.focus({ preventScroll: true });
      revealInScroller(tab, document.querySelector('.code-tabs'));
    }
    codeTabs.forEach((tab, index) => tab.addEventListener('click', () => setCode(index)));
    connectTabKeys(codeTabs, setCode);

    async function copyText(text, button, status, selectFallback, successMessage) {
      if (button.disabled) return;
      const label = button.querySelector('span');
      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      label.textContent = 'Copying…';
      try {
        await navigator.clipboard.writeText(text);
        label.textContent = 'Copied';
        status.textContent = successMessage;
      } catch {
        selectFallback();
        label.textContent = 'Try again';
        status.textContent = 'Clipboard access is unavailable. The text is selected; use your browser’s Copy command.';
      } finally {
        button.disabled = false;
        button.removeAttribute('aria-busy');
        status.hidden = false;
      }
    }
    copyCode.addEventListener('click', event => {
      const button = event.currentTarget;
      const panel = codePanels.find(item => !item.hidden);
      copyText(panel.innerText, button, copyStatus, () => {
        panel.focus({ preventScroll: true });
        const range = document.createRange();
        range.selectNodeContents(panel);
        const selection = window.getSelection();
        selection.removeAllRanges(); selection.addRange(range);
      }, 'Protocol example copied. This reference contract is not a production SDK.');
    });

    const accessDialog = document.querySelector('#accessDialog');
    const accessForm = document.querySelector('#accessForm');
    const draftResult = document.querySelector('#draftResult');
    const accessStatus = document.querySelector('#accessStatus');
    const draftMessage = document.querySelector('#draftMessage');
    const emailInput = document.querySelector('#accessEmail');
    const useInput = document.querySelector('#accessUse');
    let accessTrigger = null;
    document.querySelectorAll('[data-open-access]').forEach(button => button.addEventListener('click', () => {
      accessTrigger = button;
      closeMenu();
      if (!accessDialog.open) accessDialog.showModal();
      document.querySelector('#accessTitle').focus({ preventScroll: true });
    }));
    function restoreAccessFocus() {
      const target = accessTrigger && accessTrigger.getClientRects().length ? accessTrigger : menu;
      target.focus({ preventScroll: true });
    }
    accessDialog.querySelectorAll('.dialog-close, [data-close-access]').forEach(button => button.addEventListener('click', () => accessDialog.close()));
    accessDialog.addEventListener('keydown', event => {
      if (event.key !== 'Tab') return;
      const focusable = [...accessDialog.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])')]
        .filter(element => element.getClientRects().length && !element.hidden);
      if (!focusable.length) { event.preventDefault(); return; }
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });
    accessDialog.addEventListener('cancel', event => {
      event.preventDefault();
      accessDialog.close();
      restoreAccessFocus();
    });
    accessDialog.addEventListener('click', event => {
      if (event.target !== accessDialog) return;
      const rect = accessDialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) accessDialog.close();
    });
    accessDialog.addEventListener('close', restoreAccessFocus);
    function fieldError(input, error, text) {
      input.setAttribute('aria-invalid', String(Boolean(text)));
      error.textContent = text;
      error.hidden = !text;
    }
    [emailInput, useInput].forEach(input => input.addEventListener('input', () => {
      const error = document.getElementById(input.getAttribute('aria-describedby'));
      fieldError(input, error, '');
    }));
    accessForm.addEventListener('submit', event => {
      event.preventDefault();
      const email = emailInput.value.trim(), use = useInput.value.trim();
      const emailError = !email ? 'Enter your work email.' : !emailInput.validity.valid ? 'Use a valid email address, such as you@company.com.' : '';
      const useError = !use ? 'Describe the workflow you want your agents to complete.' : !useInput.validity.valid ? 'Keep the workflow description under 3,000 characters.' : '';
      fieldError(emailInput, document.querySelector('#emailError'), emailError);
      fieldError(useInput, document.querySelector('#useError'), useError);
      if (emailError || useError) { (emailError ? emailInput : useInput).focus(); return; }
      const subject = 'Agenvora repository access request';
      const message = 'Work email: ' + email + '\n\nAgent workflow:\n' + use;
      draftMessage.value = 'To: builders@agenvora.ai\nSubject: ' + subject + '\n\n' + message;
      document.querySelector('#openEmail').href = 'mailto:builders@agenvora.ai?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(message);
      accessForm.hidden = true; draftResult.hidden = false;
      accessStatus.textContent = 'Draft ready. Nothing has been sent.';
      document.querySelector('#copyDraft span').textContent = 'Copy draft';
      document.querySelector('#draftTitle').focus({ preventScroll: true });
    });
    document.querySelector('#editDraft').addEventListener('click', () => {
      draftResult.hidden = true; accessForm.hidden = false; useInput.focus();
    });
    document.querySelector('#copyDraft').addEventListener('click', event => {
      copyText(draftMessage.value, event.currentTarget, accessStatus, () => {
        draftMessage.focus(); draftMessage.select();
      }, 'Draft copied. Paste it into your email app and send when you are ready.');
    });
    document.querySelector('#openEmail').addEventListener('click', () => {
      accessStatus.textContent = 'Send the draft in your email app. If it does not open, use Copy draft below.';
    });

    if ('IntersectionObserver' in window) {
      const sectionLinks = [...navLinks.querySelectorAll('a')];
      const observer = new IntersectionObserver(entries => {
        for (const entry of entries) if (entry.isIntersecting) {
          sectionLinks.forEach(link => {
            if (new URL(link.href, location.href).searchParams.get('section') === entry.target.id) link.setAttribute('aria-current', 'location');
            else link.removeAttribute('aria-current');
          });
        }
      }, { rootMargin: '-12% 0px -65% 0px' });
      document.querySelectorAll('section[id]').forEach(section => observer.observe(section));
    }
  </script>
  <script id="homeTokenConfig" type="application/json">__HOME_TOKEN_CONFIG__</script>
  <script type="module" src="/assets/token-docs/home-token-ca.mjs?v=3"></script>
</body>
</html>'''


ADMIN_HTML = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f1f4e8">
  <title>Agenvora — Admin settings</title>
  <style>
    :root { color-scheme: light; --canvas: #f1f4e8; --surface: #fbfcf7; --ink: #10261f; --text: #29483e; --muted: #52645d; --line: #c9d5c0; --strong: #758c80; --action: #c8f169; --action-ink: #123c2f; --danger: #b8323c; --danger-bg: #fce8ea; --success: #147343; --success-bg: #e1f5e8; --radius: 5px; }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--canvas); color: var(--ink); font: 400 16px/1.6 "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif; }
    a { color: #08735e; text-underline-offset: .25em; }
    :focus-visible { outline: 2px solid #0a806a; outline-offset: 3px; }
    .admin-header { border-bottom: 1px solid var(--line); background: var(--surface); }
    .admin-nav, .admin-main { width: min(calc(100% - 40px), 920px); margin-inline: auto; }
    .admin-nav { display: flex; min-height: 72px; align-items: center; justify-content: space-between; gap: 24px; }
    .brand { color: var(--ink); font-size: 1.125rem; font-weight: 750; letter-spacing: -.025em; text-decoration: none; }
    .admin-nav a:last-child { min-height: 44px; display: inline-flex; align-items: center; }
    .admin-main { padding-block: clamp(48px, 8vw, 96px); }
    .admin-main h1 { max-width: 18ch; margin: 0; font: 400 clamp(2.5rem, 6vw, 4rem)/1.04 Georgia, "Times New Roman", serif; letter-spacing: -.035em; }
    .intro { max-width: 54ch; margin-top: 20px; color: var(--text); }
    .settings-panel { margin-top: 40px; border: 1px solid var(--strong); border-radius: 8px; background: var(--surface); }
    .settings-panel form { display: grid; gap: 24px; padding: clamp(20px, 5vw, 40px); }
    .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; border: 0; }
    .field { display: grid; gap: 8px; }
    label { color: var(--ink); font-weight: 600; }
    input[type="text"], input[type="url"] { width: 100%; min-height: 48px; padding: 10px 12px; border: 1px solid var(--strong); border-radius: var(--radius); background: #fff; color: var(--ink); font: 400 1rem/1.4 "SFMono-Regular", Consolas, monospace; }
    .field-note { margin: 0; color: var(--muted); font-size: .8125rem; }
    .toggle-row { display: flex; align-items: center; gap: 14px; padding: 16px; border: 1px solid var(--line); border-radius: var(--radius); background: #fff; }
    .toggle-row input { position: absolute; opacity: 0; pointer-events: none; }
    .toggle { position: relative; width: 48px; height: 28px; flex: 0 0 auto; border-radius: 999px; background: var(--line); cursor: pointer; transition: background-color 120ms ease; }
    .toggle::after { position: absolute; top: 4px; left: 4px; width: 20px; height: 20px; border-radius: 50%; background: white; content: ""; transition: transform 120ms ease; }
    .toggle-row input:checked + .toggle { background: #0d7c66; }
    .toggle-row input:checked + .toggle::after { transform: translateX(20px); }
    .toggle-copy { display: grid; gap: 2px; }
    .toggle-copy small { color: var(--muted); font-weight: 400; }
    .actions { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding-top: 8px; border-top: 1px solid var(--line); }
    .button { display: inline-flex; min-height: 48px; align-items: center; justify-content: center; padding: 10px 18px; border: 1px solid #073f31; border-radius: var(--radius); background: var(--action); color: var(--action-ink); font: 600 .875rem/1.35 "Segoe UI", sans-serif; cursor: pointer; }
    .button:hover { background: #b6de58; }
    .notice { padding: 12px 16px; border: 1px solid; border-radius: var(--radius); }
    .notice[hidden] { display: none; }
    .notice-success { border-color: var(--success); background: var(--success-bg); color: var(--success); }
    .notice-error { border-color: var(--danger); background: var(--danger-bg); color: var(--danger); }
    @media (max-width: 560px) { .admin-nav, .admin-main { width: min(calc(100% - 32px), 920px); } .actions { align-items: stretch; flex-direction: column; } .button { width: 100%; } }
  </style>
</head>
<body>
  <header class="admin-header"><nav class="admin-nav" aria-label="Admin navigation"><a class="brand" href="/">AGENVORA</a><a href="/">View site</a></nav></header>
  <main class="admin-main">
    <h1>Site settings</h1>
    <p class="intro">Update the public Contract Address and X/Twitter link without rebuilding the application. Changes are stored in SQLite and appear on the next page load.</p>
    <div class="notice notice-success" __ADMIN_MESSAGE_HIDDEN__ role="status">__ADMIN_MESSAGE__</div>
    <div class="notice notice-error" __ADMIN_ERROR_HIDDEN__ role="alert">__ADMIN_ERROR__</div>
    <section class="settings-panel" aria-labelledby="settingsTitle">
      <h2 id="settingsTitle" class="sr-only">Public settings form</h2>
      <form method="post" action="/admin">
        <div class="field"><label for="contractAddress">Contract Address</label><input id="contractAddress" name="contract_address" type="text" value="__ADMIN_CA__" maxlength="128" spellcheck="false" autocomplete="off" placeholder="Solana public key" aria-describedby="contractAddressNote"><p class="field-note" id="contractAddressNote">Solana address. Leave it saved but switch publishing off until the address is ready.</p></div>
        <div class="toggle-row"><input id="contractAddressEnabled" name="contract_address_enabled" type="checkbox" value="on" __ADMIN_CHECKED__><label class="toggle" for="contractAddressEnabled" aria-label="Publish Contract Address"></label><span class="toggle-copy"><strong>Publish Contract Address</strong><small>When off, the site shows “Contract Address to be announced.”</small></span></div>
        <div class="field"><label for="twitterUrl">X / Twitter URL</label><input id="twitterUrl" name="twitter_url" type="url" value="__ADMIN_TWITTER__" placeholder="https://x.com/agenvora" spellcheck="false" autocomplete="url"></div>
        <div class="actions"><span class="field-note">Protected settings · SQLite</span><button class="button" type="submit">Save settings</button></div>
      </form>
    </section>
  </main>
</body>
</html>'''


def render_admin_page(settings: PublicSiteSettings, message: str = "", error: str = "") -> str:
    return (
        ADMIN_HTML
        .replace("__ADMIN_CA__", escape(settings.contract_address, quote=True))
        .replace("__ADMIN_TWITTER__", escape(settings.twitter_url, quote=True))
        .replace("__ADMIN_CHECKED__", "checked" if settings.contract_address_enabled else "")
        .replace("__ADMIN_MESSAGE__", escape(message))
        .replace("__ADMIN_ERROR__", escape(error))
        .replace("__ADMIN_MESSAGE_HIDDEN__", "" if message else "hidden")
        .replace("__ADMIN_ERROR_HIDDEN__", "" if error else "hidden")
    )


def render_home_page(settings: PublicSiteSettings):
    """Render the homepage from the current database-backed public settings."""

    config = json.dumps(
        settings.to_public_config(),
        ensure_ascii=True,
        separators=(",", ":"),
    ).replace("</", "<\\/")
    twitter_url = escape(settings.twitter_url or "#", quote=True)
    return HTML.replace("__HOME_TOKEN_CONFIG__", config).replace("__TWITTER_URL__", twitter_url)


class SiteHandler(BaseHTTPRequestHandler):
    def send_bytes(self, status, body, content_type, cache_control="no-store", extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache_control)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        if extra_headers:
            for name, value in extra_headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def require_admin(self):
        configured_password = os.environ.get("AGEN_VORA_ADMIN_PASSWORD", "")
        if not configured_password and not has_admin_password():
            self.send_bytes(503, b"Admin access is disabled until an admin password is configured.", "text/plain; charset=utf-8")
            return False

        authorization = self.headers.get("Authorization", "")
        valid = False
        if authorization.startswith("Basic "):
            try:
                decoded = base64.b64decode(authorization[6:], validate=True).decode("utf-8")
                username, password = decoded.split(":", 1)
                expected_username = os.environ.get("AGEN_VORA_ADMIN_USERNAME", "admin")
                password_valid = hmac.compare_digest(password, configured_password) if configured_password else verify_admin_password(password)
                valid = hmac.compare_digest(username, expected_username) and password_valid
            except (ValueError, UnicodeDecodeError):
                valid = False
        if valid:
            return True

        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Agenvora admin", charset="UTF-8"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def read_form(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid form body.") from error
        if length > 64 * 1024:
            raise ValueError("Form body is too large.")
        body = self.rfile.read(length).decode("utf-8")
        return {key: values[-1] if values else "" for key, values in parse_qs(body, keep_blank_values=True).items()}

    def do_POST(self):
        request_path = urlsplit(self.path).path
        if request_path not in ("/admin", "/admin/"):
            self.send_error(404, "Not found")
            return
        if not self.require_admin():
            return
        try:
            form = self.read_form()
            save_site_settings(
                form.get("contract_address", ""),
                form.get("contract_address_enabled") in {"on", "1", "true"},
                form.get("twitter_url", ""),
            )
        except (UnicodeDecodeError, ValueError) as error:
            body = render_admin_page(read_site_settings(), error=str(error)).encode("utf-8")
            self.send_bytes(422, body, "text/html; charset=utf-8")
            return
        self.send_response(303)
        self.send_header("Location", "/admin?saved=1")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self):
        request_path = urlsplit(self.path).path
        if request_path in ("/admin", "/admin/"):
            if not self.require_admin():
                return
            query = parse_qs(urlsplit(self.path).query)
            message = "Settings saved." if query.get("saved") == ["1"] else ""
            body = render_admin_page(read_site_settings(), message=message).encode("utf-8")
            self.send_bytes(200, body, "text/html; charset=utf-8")
            return
        if request_path in ("/", "/index.html"):
            body = render_home_page(read_site_settings()).encode("utf-8")
            self.send_bytes(
                200,
                body,
                "text/html; charset=utf-8",
                extra_headers={"Permissions-Policy": "clipboard-write=(self)"},
            )
            return
        if request_path == "/docs/token/":
            self.send_response(308)
            self.send_header("Location", "/docs/token")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        if request_path == "/docs/token":
            public_settings = read_site_settings()
            settings = replace(
                load_token_docs_settings(),
                contract_endpoint="/api/contract" if public_settings.contract_address_enabled else "",
                twitter_url=public_settings.twitter_url,
            )
            body = render_token_docs_page(settings).encode("utf-8")
            self.send_bytes(
                200,
                body,
                "text/html; charset=utf-8",
                extra_headers={
                    "Content-Security-Policy": build_content_security_policy(settings),
                    "Permissions-Policy": "clipboard-write=(self)",
                    "Cross-Origin-Opener-Policy": "same-origin",
                    "X-Frame-Options": "DENY",
                },
            )
            return
        if request_path == "/api/contract":
            settings = read_site_settings()
            if not settings.contract_address_enabled or not settings.contract_address:
                self.send_bytes(404, b'{"error":"Contract Address to be announced."}', "application/json; charset=utf-8")
                return
            body = json.dumps(
                {
                    "contractAddress": settings.contract_address,
                    "chain": settings.chain,
                    "explorerUrl": "",
                    "updatedAt": settings.updated_at,
                },
                separators=(",", ":"),
            ).encode("utf-8")
            self.send_bytes(
                200,
                body,
                "application/json; charset=utf-8",
            )
            return
        if request_path in TOKEN_DOCS_ASSETS:
            filename, content_type = TOKEN_DOCS_ASSETS[request_path]
            body = (TOKEN_DOCS_ASSET_ROOT / filename).read_bytes()
            self.send_bytes(200, body, content_type, cache_control="public, max-age=300")
            return
        if request_path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        self.send_error(404, "Not found")

    def log_message(self, format, *args):
        print(f"[agenvora] {self.address_string()} - {format % args}")


def main():
    parser = argparse.ArgumentParser(description="Run the Agenvora website")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), SiteHandler)
    print(f"Agenvora is live at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Agenvora.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
