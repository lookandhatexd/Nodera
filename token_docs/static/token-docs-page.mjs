import { copyText } from "./live-token-contract.mjs";
import { LiveTokenContractAddress } from "./token-contract-address.mjs?v=3";

function readConfig(documentRef) {
  const element = documentRef.querySelector("#tokenDocsConfig");
  if (!element) throw new Error("Token documentation configuration is missing.");
  return JSON.parse(element.textContent);
}

function setupSiteNavigation(documentRef) {
  const menu = documentRef.querySelector(".site-menu");
  const links = documentRef.querySelector("#siteNavLinks");
  if (!menu || !links) return;
  const close = (restore = false) => {
    links.classList.remove("open");
    menu.setAttribute("aria-expanded", "false");
    menu.setAttribute("aria-label", "Open navigation");
    if (restore) menu.focus();
  };
  menu.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    menu.setAttribute("aria-expanded", String(open));
    menu.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
  });
  links.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => close(false)));
  documentRef.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && links.classList.contains("open")) close(true);
  });
  documentRef.addEventListener("click", (event) => {
    if (links.classList.contains("open") && !event.target.closest(".site-nav")) close(false);
  });
}

function setupSectionNavigation(documentRef) {
  const links = [...documentRef.querySelectorAll('a[href*="?section="]')];
  for (const link of links) {
    link.addEventListener("click", (event) => {
      const url = new URL(link.href, globalThis.location.href);
      const section = url.searchParams.get("section");
      if (url.pathname !== globalThis.location.pathname || !section) return;
      const target = documentRef.getElementById(section);
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ behavior: globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      history.replaceState(null, "", globalThis.location.pathname);
    });
  }
  const section = new URLSearchParams(globalThis.location.search).get("section");
  if (section) requestAnimationFrame(() => {
    documentRef.getElementById(section)?.scrollIntoView({ behavior: "auto" });
    history.replaceState(null, "", globalThis.location.pathname);
  });
}

function setupDocumentationNavigation(documentRef) {
  const details = documentRef.querySelector(".mobile-docs-nav");
  const links = [...documentRef.querySelectorAll('.docs-rail a[href*="?section="], .mobile-docs-nav a[href*="?section="]')];
  for (const link of links) {
    link.addEventListener("click", () => {
      const targetId = new URL(link.href, globalThis.location.href).searchParams.get("section");
      const target = targetId ? documentRef.getElementById(targetId) : null;
      if (details?.open) details.open = false;
      if (target) {
        target.setAttribute("tabindex", "-1");
        setTimeout(() => target.focus({ preventScroll: true }), 0);
      }
    });
  }
  if (!("IntersectionObserver" in globalThis)) return;
  const sections = [...documentRef.querySelectorAll("#official-contract, #verify-before-use, #token-overview, #add-token, #integration, #validation")];
  const observer = new IntersectionObserver((entries) => {
    const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
    if (!visible) return;
    for (const link of links) {
      if (new URL(link.href, globalThis.location.href).searchParams.get("section") === visible.target.id) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    }
  }, { rootMargin: "-20% 0px -70% 0px", threshold: 0 });
  sections.forEach((section) => observer.observe(section));
}

function setupExampleCopy(documentRef) {
  const button = documentRef.querySelector("#copyExample");
  const code = documentRef.querySelector("#integrationCode");
  const status = documentRef.querySelector("#exampleCopyStatus");
  if (!button || !code || !status) return;
  let resetTimer = null;
  button.addEventListener("click", async () => {
    if (resetTimer !== null) clearTimeout(resetTimer);
    try {
      await copyText(code.textContent);
      button.querySelector("span").textContent = "Copied";
      status.textContent = "Runtime fetch example copied.";
    } catch (error) {
      button.querySelector("span").textContent = "Copy blocked";
      status.textContent = error.message;
    }
    status.hidden = false;
    resetTimer = setTimeout(() => { button.querySelector("span").textContent = "Copy example"; }, 2_000);
  });
}

const config = readConfig(document);
setupSiteNavigation(document);
setupSectionNavigation(document);
setupDocumentationNavigation(document);
setupExampleCopy(document);
const component = new LiveTokenContractAddress(document.querySelector("#liveTokenContract"), config, document);
component.mount();
addEventListener("pagehide", () => component.unmount(), { once: true });
