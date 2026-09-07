import { copyText } from "./live-token-contract.mjs";
import { LiveTokenContractAddress } from "./token-contract-address.mjs";

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

function setupDocumentationNavigation(documentRef) {
  const details = documentRef.querySelector(".mobile-docs-nav");
  const links = [...documentRef.querySelectorAll('.docs-rail a[href^="#"], .mobile-docs-nav a[href^="#"]')];
  for (const link of links) {
    link.addEventListener("click", () => {
      const target = documentRef.querySelector(link.getAttribute("href"));
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
      if (link.getAttribute("href") === `#${visible.target.id}`) link.setAttribute("aria-current", "location");
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
setupDocumentationNavigation(document);
setupExampleCopy(document);
const component = new LiveTokenContractAddress(document.querySelector("#liveTokenContract"), config, document);
component.mount();
addEventListener("pagehide", () => component.unmount(), { once: true });
