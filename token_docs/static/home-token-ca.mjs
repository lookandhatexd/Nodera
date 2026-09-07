import { copyText } from "./live-token-contract.mjs";

function readConfig(documentRef) {
  const element = documentRef.querySelector("#homeTokenConfig");
  if (!element) throw new Error("Site settings are missing.");
  return JSON.parse(element.textContent);
}

function legacyCopy(documentRef, text) {
  if (!documentRef?.body || typeof documentRef.execCommand !== "function") return false;
  const field = documentRef.createElement("textarea");
  field.value = text;
  field.setAttribute("readonly", "");
  field.setAttribute("aria-hidden", "true");
  field.style.position = "fixed";
  field.style.opacity = "0";
  documentRef.body.append(field);
  field.select();
  let copied = false;
  try { copied = documentRef.execCommand("copy"); } catch { copied = false; }
  field.remove();
  return copied;
}

function createHomeContractView(root) {
  const get = (selector) => root.querySelector(selector);
  const elements = {
    status: get("#homeCaStatus"),
    statusDetail: get("#homeCaStatusDetail"),
    loading: get("#homeCaLoading"),
    error: get("#homeCaError"),
    record: get("#homeCaRecord"),
    announcement: get("#homeCaAnnouncementText"),
    chain: get("#homeCaChain"),
    address: get("#homeCaAddress"),
    updated: get("#homeCaUpdated"),
    copy: get("#homeCaCopy"),
    liveAnnouncement: get("#homeCaLiveAnnouncement"),
  };

  return {
    elements,
    render(record) {
      const hasRecord = Boolean(record);
      root.dataset.state = hasRecord ? "published" : "announcement";
      root.setAttribute("aria-busy", "false");
      elements.loading.hidden = true;
      elements.error.hidden = true;
      elements.record.hidden = !hasRecord;
      elements.announcement.hidden = hasRecord;
      elements.copy.disabled = !hasRecord;
      elements.status.textContent = hasRecord ? "Contract Address" : "Contract Address to be announced";
      elements.statusDetail.textContent = hasRecord ? "" : "The public address will appear here when it is published.";
      if (!hasRecord) return;
      elements.chain.textContent = record.chain;
      elements.address.textContent = record.contractAddress;
      elements.updated.textContent = record.updatedAt ? record.updatedAt : "Published from admin";
      elements.updated.dateTime = record.updatedAt || "";
    },
  };
}

class HomeTokenContractAddress {
  constructor(root, config, documentRef = globalThis.document) {
    this.root = root;
    this.documentRef = documentRef;
    this.view = createHomeContractView(root);
    this.copyResetTimer = null;
    this.record = config.contractAddressEnabled && config.contractAddress
      ? {
        contractAddress: config.contractAddress,
        chain: config.contractChain || "Solana",
        updatedAt: config.contractUpdatedAt || "",
      }
      : null;
    this.copyHandler = () => this.copyAddress();
  }

  mount() {
    this.view.elements.copy.addEventListener("click", this.copyHandler);
    this.view.render(this.record);
  }

  async copyAddress() {
    if (!this.record) return;
    const button = this.view.elements.copy;
    const label = button.querySelector("span");
    if (this.copyResetTimer !== null) clearTimeout(this.copyResetTimer);
    try {
      await copyText(this.record.contractAddress, {
        legacyCopy: (text) => legacyCopy(this.documentRef, text),
      });
      label.textContent = "Copied";
      this.view.elements.liveAnnouncement.textContent = "Contract Address copied.";
    } catch (error) {
      label.textContent = "Copy blocked";
      this.view.elements.liveAnnouncement.textContent = error.message;
      const range = this.documentRef.createRange?.();
      if (range) {
        range.selectNodeContents(this.view.elements.address);
        const selection = globalThis.getSelection?.();
        selection?.removeAllRanges();
        selection?.addRange(range);
      }
    }
    button.focus({ preventScroll: true });
    this.copyResetTimer = setTimeout(() => { label.textContent = "Copy CA"; }, 2_000);
  }

  unmount() {
    this.view.elements.copy.removeEventListener("click", this.copyHandler);
    if (this.copyResetTimer !== null) clearTimeout(this.copyResetTimer);
  }
}

const root = document.querySelector("#homeTokenCa");
if (root) {
  const component = new HomeTokenContractAddress(root, readConfig(document), document);
  component.mount();
  addEventListener("pagehide", () => component.unmount(), { once: true });
}
