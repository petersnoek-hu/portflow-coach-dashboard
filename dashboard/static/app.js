// Portflow coach dashboard: small enhancements; every page also works without JavaScript.

(() => {
  "use strict";

  // Portflow status in the top bar (spec 003, F13 and F14) --------------------------------

  const statusEl = () => document.getElementById("portflow-status");
  const reloadWatchEl = () => document.getElementById("portflow-reload-watch");
  let fingerprint = null;
  let wasBusy = null;
  let wasFetching = null;

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

      // "Uit Portflow kiezen" (spec 004, F5): once a login/refresh attempt that was
      // running finishes (success or failure), reload so the page shows the result
      // (the share list, or an updated message) without an extra click.
      const busyNow = status.state === "logging_in" || status.state === "refreshing";
      if (reloadWatchEl() && wasBusy === true && !busyNow) {
        location.reload();
        return;
      }
      wasBusy = busyNow;

      // Spec 005, F9: once a fetch round finishes, show the new data without a manual reload.
      if (wasFetching === true && !status.fetch_running && document.querySelector("[data-reload-after-fetch]")) {
        location.reload();
        return;
      }
      wasFetching = status.fetch_running;

      const typing = statusEl()?.contains(document.activeElement) && document.activeElement.matches("input, textarea");
      if (fingerprint !== null && status.fingerprint !== fingerprint && !typing) {
        replace("portflow-status", status.status_html, true);
        replace("portflow-banner", status.banner_html);
        replace("sidebar-user", status.user_html);
        replace("topbar-avatar", status.avatar_html);
        replace("refresh", status.refresh_html);
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

(() => {
  "use strict";

  // "Uit Portflow kiezen": the loading indicator that fetches the share list as an HTML
  // fragment (spec 004, F6 technical), plus search, select all/none and the submit
  // button once the list is there (F9, F11).

  function enhancePickList() {
    const list = document.getElementById("portflow-candidates");
    const submit = document.getElementById("portflow-submit");
    if (!list || !submit) return;

    const rows = () => Array.from(list.querySelectorAll(".pick-row"));
    const checkbox = (row) => row.querySelector("input[type=checkbox]");

    function visibleRows(query) {
      return rows().filter((row) => {
        const visible = !query || row.dataset.pickName.includes(query);
        row.hidden = !visible;
        return visible;
      });
    }

    // "student|studenten" by default; the Coaches and Gildemeesters pages pass their own words.
    const [single, plural] = (list.dataset.pickNoun || "student|studenten").split("|");
    const capital = (word) => word.charAt(0).toUpperCase() + word.slice(1);

    function updateSubmit() {
      const count = rows().filter((row) => checkbox(row).checked).length;
      submit.textContent = count === 0 ? `${capital(plural)} toevoegen` : `${count} ${count === 1 ? single : plural} toevoegen`;
      submit.disabled = count === 0;
    }

    const search = document.getElementById("portflow-search");
    search?.addEventListener("input", () => visibleRows(search.value.trim().toLowerCase()));

    list.addEventListener("change", (event) => {
      if (event.target.matches("input[type=checkbox]")) updateSubmit();
    });

    document.querySelectorAll("[data-pick-select]").forEach((button) => {
      button.addEventListener("click", () => {
        const checked = button.dataset.pickSelect === "all";
        visibleRows(search?.value.trim().toLowerCase() || "").forEach((row) => {
          const input = checkbox(row);
          if (!input.disabled) input.checked = checked;
        });
        updateSubmit();
      });
    });

    updateSubmit();
  }

  const loading = document.getElementById("portflow-list-loading");
  if (loading) {
    fetch(loading.dataset.fragmentUrl, { headers: { Accept: "text/html" } })
      .then((response) => {
        if (!response.ok) throw new Error("fragment fetch failed");
        return response.text();
      })
      .then((html) => {
        const template = document.createElement("template");
        template.innerHTML = html.trim();
        loading.replaceWith(template.content);
        enhancePickList();
      })
      .catch(() => {
        loading.innerHTML =
          `<p class="muted">Niet gelukt. <a href="${location.pathname}/lijst">Opnieuw proberen</a>.</p>`;
      });
  } else {
    enhancePickList();
  }
})();

(() => {
  "use strict";

  // Student overview (spec 001): submit filters on change (F13-F16), search while typing
  // with ⌘K (F17), sort by clicking a column header (F18) and keep the counter right (F19).

  const card = document.getElementById("student-table");
  if (!card) return;

  card.querySelectorAll(".js-hide").forEach((el) => { el.hidden = true; });

  const filters = document.getElementById("table-filters");
  filters?.addEventListener("change", (event) => {
    if (event.target.matches("select, input[type=checkbox]")) filters.submit();
  });
  filters?.addEventListener("submit", () => {
    // Do not put the (client-side) search or empty filters in the address.
    filters.querySelectorAll("select, input").forEach((el) => {
      if (el.id === "table-search" || (!el.value && el.tagName === "SELECT") || (el.type === "checkbox" && !el.checked)) {
        el.disabled = true;
      }
    });
  });

  const listColumnForm = document.getElementById("list-column-form");   // spec 010, F5
  listColumnForm?.addEventListener("change", () => listColumnForm.submit());

  const colourForm = document.getElementById("colour-form");   // F23
  colourForm?.addEventListener("change", () => colourForm.submit());

  const columnForm = document.getElementById("column-form");
  columnForm?.addEventListener("change", () => columnForm.submit());

  // Custom columns (F8): save when the field loses focus after a change, or with Enter.
  card.querySelectorAll(".custom-cell input[name=waarde]").forEach((input) => {
    input.addEventListener("change", () => input.form.submit());
  });

  const table = document.getElementById("students");
  const count = document.getElementById("table-count");
  const search = document.getElementById("table-search");

  function updateCount() {
    if (!table || !count) return;
    const visible = table.querySelectorAll(".student-row:not([hidden])").length;
    count.textContent = `${visible} van ${count.dataset.total} studenten`;
  }

  search?.addEventListener("input", () => {
    const query = search.value.trim().toLowerCase();
    table?.querySelectorAll(".table-group").forEach((group) => {
      let any = false;
      group.querySelectorAll(".student-row").forEach((row) => {
        row.hidden = Boolean(query) && !row.dataset.search.includes(query);
        any = any || !row.hidden;
      });
      group.hidden = !any;
    });
    updateCount();
  });

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k" && search) {
      event.preventDefault();
      search.focus();
      search.select();
    }
  });

  function sortValue(row, key, index) {
    if (row.dataset[`sort${key.charAt(0).toUpperCase()}${key.slice(1)}`] !== undefined) {
      return row.dataset[`sort${key.charAt(0).toUpperCase()}${key.slice(1)}`];
    }
    const cell = row.children[index];
    const value = cell?.dataset.sortValue ?? "";
    return value !== "" && !Number.isNaN(Number(value)) ? Number(value) : value;
  }

  table?.querySelectorAll("thead th[data-sort]").forEach((th, index) => {
    th.querySelector("button")?.addEventListener("click", () => {
      const ascending = th.getAttribute("aria-sort") !== "ascending";
      table.querySelectorAll("thead th").forEach((other) => other.removeAttribute("aria-sort"));
      th.setAttribute("aria-sort", ascending ? "ascending" : "descending");
      const key = th.dataset.sort.replace(/[-_]([a-z])/g, (_, c) => c.toUpperCase());
      const byData = ["name", "profile", "coach", "coachFull", "guildMaster", "guildMasterFull", "track"].includes(key);
      table.querySelectorAll(".table-group").forEach((group) => {
        const rows = Array.from(group.querySelectorAll(".student-row"));
        rows.sort((a, b) => {
          const va = sortValue(a, byData ? key : "", index);
          const vb = sortValue(b, byData ? key : "", index);
          const order = typeof va === "number" && typeof vb === "number" ? va - vb : String(va).localeCompare(String(vb), "nl");
          return (ascending ? order : -order) || a.dataset.sortName.localeCompare(b.dataset.sortName, "nl");
        });
        rows.forEach((row) => group.appendChild(row));
      });
    });
  });
})();

(() => {
  "use strict";

  // Student bewerken (spec 011, F2): show the guild that follows from the chosen primary role.
  const role = document.getElementById("primary-role");
  const guild = document.getElementById("guild-of-role");
  if (!role || !guild) return;
  role.addEventListener("change", () => {
    const option = role.options[role.selectedIndex];
    guild.textContent = option.value ? option.dataset.guild : "–";
  });
})();

(() => {
  "use strict";

  // Excel import preview (spec 013, F6): search, select all/none and the count on the button.
  const list = document.getElementById("import-rows");
  const submit = document.getElementById("import-submit");
  if (!list || !submit) return;
  const boxes = () => Array.from(list.querySelectorAll("input[data-import-new]"));
  const search = document.getElementById("import-search");

  function update() {
    const count = boxes().filter((box) => box.checked).length;
    submit.textContent = `Importeren (${count} toevoegen, ${submit.dataset.existing} bijwerken)`;
  }
  search?.addEventListener("input", () => {
    const query = search.value.trim().toLowerCase();
    list.querySelectorAll(".import-row").forEach((row) => { row.hidden = Boolean(query) && !row.dataset.search.includes(query); });
  });
  document.querySelectorAll("[data-import-select]").forEach((button) => {
    button.addEventListener("click", () => {
      boxes().forEach((box) => { if (!box.closest(".import-row").hidden) box.checked = button.dataset.importSelect === "all"; });
      update();
    });
  });
  list.addEventListener("change", update);
})();

(() => {
  "use strict";

  // Alles verwijderen (spec 014, F3): the button works only after typing the word.
  const word = document.getElementById("reset-word");
  const submit = document.getElementById("reset-submit");
  if (!word || !submit || submit.disabled) return;
  const check = () => { submit.disabled = word.value.trim().toUpperCase() !== word.dataset.word; };
  word.addEventListener("input", check);
  check();
})();

(() => {
  "use strict";

  // Student bewerken, guilds (spec 016, F4): add and remove guild rows.
  document.documentElement.classList.add("js");
  const rows = document.getElementById("guild-rows");
  if (!rows) return;
  const add = document.getElementById("guild-add");
  const all = () => Array.from(rows.querySelectorAll(".guild-row"));
  const empty = all().find((row) => row.classList.contains("is-empty"));
  const template = empty?.cloneNode(true);
  if (empty && all().length > 1) empty.remove();   // with JavaScript the extra empty row is not needed

  rows.addEventListener("click", (event) => {
    const button = event.target.closest("[data-guild-remove]");
    if (!button) return;
    const row = button.closest(".guild-row");
    if (all().length > 1) row.remove();
    else row.querySelectorAll("select").forEach((select) => { select.value = ""; });
  });
  add?.addEventListener("click", () => {
    const row = template.cloneNode(true);
    row.querySelectorAll("select").forEach((select) => { select.value = ""; });
    add.before(row);
    row.querySelector("select")?.focus();
  });
})();

(() => {
  "use strict";

  // Project form (spec 012, F11): fill the display name while typing, until the user edits it.
  const display = document.getElementById("project-display");
  if (!display) return;
  const form = display.form;
  const value = (name) => form.querySelector(`[name=${name}]`).value.trim();
  const fill = () => {
    if (display.dataset.edited) return;
    const number = value("nummer");
    const base = value("opdrachtgever") ? `${value("opdrachtgever")} - ${value("naam")}` : value("naam");
    display.value = base ? (number ? `${base} (${number.padStart(2, "0")})` : base) : "";
  };
  display.addEventListener("input", () => { display.dataset.edited = display.value ? "1" : ""; });
  ["nummer", "naam", "opdrachtgever"].forEach((name) => form.querySelector(`[name=${name}]`).addEventListener("input", fill));
})();
