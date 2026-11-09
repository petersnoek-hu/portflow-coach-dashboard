// Portflow coach dashboard: small enhancements; every page also works without JavaScript.

(() => {
  "use strict";

  // Portflow status in the top bar (spec 003, F13 and F14) --------------------------------

  const statusEl = () => document.getElementById("portflow-status");
  let fingerprint = null;

  function closePanelOnEscapeOrOutsideClick() {
    document.addEventListener("keydown", (event) => {
      const panel = statusEl();
      if (event.key === "Escape" && panel?.open) panel.open = false;
    });
    document.addEventListener("click", (event) => {
      const panel = statusEl();
      if (panel?.open && !panel.contains(event.target)) panel.open = false;
    });
  }

  function replace(id, html, keepOpen) {
    const old = document.getElementById(id);
    if (!old) return;
    const wasOpen = old.open;
    const template = document.createElement("template");
    template.innerHTML = html.trim();
    const fresh = id === "portflow-status" ? template.content.firstElementChild : null;
    if (fresh) {
      if (keepOpen && wasOpen) fresh.open = true;
      old.replaceWith(fresh);
    } else {
      old.innerHTML = html;
    }
  }

  async function poll() {
    let delay = 60000;
    try {
      const path = encodeURIComponent(location.pathname);
      const response = await fetch(`/portflow/status?pad=${path}`, { headers: { Accept: "application/json" } });
      const status = await response.json();
      delay = status.poll_ms;
      const typing = statusEl()?.contains(document.activeElement) && document.activeElement.matches("input, textarea");
      if (fingerprint !== null && status.fingerprint !== fingerprint && !typing) {
        replace("portflow-status", status.status_html, true);
        replace("portflow-banner", status.banner_html);
        replace("sidebar-user", status.user_html);
        replace("topbar-avatar", status.avatar_html);
      }
      if (!typing) fingerprint = status.fingerprint;
    } catch {
      // The app may be restarting; try again later.
    }
    setTimeout(poll, delay);
  }

  if (statusEl()) {
    closePanelOnEscapeOrOutsideClick();
    poll();
  }
})();
