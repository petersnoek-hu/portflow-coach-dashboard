// Portflow coach dashboard: small enhancements; every page also works without JavaScript.

(() => {
  "use strict";

  // Portflow status in the top bar (spec 003, F13 and F14) --------------------------------

  const statusEl = () => document.getElementById("portflow-status");
  const reloadWatchEl = () => document.getElementById("portflow-reload-watch");
  let fingerprint = null;
  let wasBusy = null;
  let wasFetching = null;

  // Spec 041, F7: after Verversen, update the parts of the page that come from the fetched
  // evaluations (marked with data-live) without reloading, after every student of this page.
  // The server makes the HTML; this only swaps the parts that changed.
  const REFRESH_KEY = "refreshStarted";
  const liveSnapshot = new Map();
  document.querySelectorAll("[data-live]").forEach((el) => liveSnapshot.set(el.dataset.live, el.outerHTML));
  let liveRound = null;
  let liveDone = new Set();
  let liveBusy = false;
  let liveAgain = null;   // null, or whether the queued update is the final one

  function pageStudents() {
    return new Set(Array.from(document.querySelectorAll("[data-student-id]"), (el) => Number(el.dataset.studentId)));
  }

  async function liveUpdate(final) {
    if (liveBusy) { liveAgain = Boolean(liveAgain) || final; return; }
    liveBusy = true;
    let ok = true;
    try {
      const response = await fetch(location.href, { headers: { "X-Requested-With": "fetch" }, cache: "no-store" });
      if (!response.ok) throw new Error(String(response.status));
      const doc = new DOMParser().parseFromString(await response.text(), "text/html");
      // A student who was added in this round and is on this screen: only a reload shows the new row.
      const cells = new Set(Array.from(document.querySelectorAll("[data-live^='cell-']"), (el) => el.dataset.live));
      if (final && Array.from(doc.querySelectorAll("[data-live^='cell-']")).some((el) => !cells.has(el.dataset.live))) {
        location.reload();
        return;
      }
      doc.querySelectorAll("[data-live]").forEach((fresh) => {
        const key = fresh.dataset.live;
        const html = fresh.outerHTML;
        if (liveSnapshot.get(key) === html) return;
        const old = document.querySelector(`[data-live="${CSS.escape(key)}"]`);
        if (!old) return;
        const active = document.activeElement;
        if (active && old.contains(active) && active.matches("input, textarea, select")) return;   // keep what is typed
        const opened = Array.from(old.querySelectorAll("details"), (d) => d.open);
        const node = document.importNode(fresh, true);
        node.querySelectorAll("details").forEach((d, i) => { if (i < opened.length) d.open = opened[i]; });
        old.replaceWith(node);
        liveSnapshot.set(key, html);
      });
    } catch {
      ok = false;
    } finally {
      liveBusy = false;
    }
    if (!ok && final) { location.reload(); return; }   // could not update in place: show the new data anyway
    if (liveAgain !== null) {
      const again = liveAgain;
      liveAgain = null;
      liveUpdate(again);
    }
  }

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

  let pollTimer = null;
  let polling = false;
  let pollAgain = false;   // a check was asked for while one was running: do it right after

  async function poll() {
    if (polling) { pollAgain = true; return; }
    polling = true;
    clearTimeout(pollTimer);
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

      // Spec 041, F7: which students of this round are done. On the first check after loading a
      // page, only a Verversen of the last ten minutes counts (the page may be its result).
      const firstCheck = liveRound === null;
      const recent = Date.now() - Number(sessionStorage.getItem(REFRESH_KEY) || 0) < 600000;
      if (firstCheck || status.fetch_round !== liveRound) {
        liveDone = new Set(firstCheck && !recent ? status.fetch_students : []);
        liveRound = status.fetch_round;
      }
      const roundEnded = !status.fetch_running && (wasFetching === true || (firstCheck && recent && status.fetch_round));
      wasFetching = status.fetch_running;

      // Spec 005, F9: a page without students (nothing fetched yet) reloads once the round is done.
      if (roundEnded && document.querySelector("[data-reload-after-fetch]")) {
        sessionStorage.removeItem(REFRESH_KEY);
        location.reload();
        return;
      }
      const onPage = pageStudents();
      const fresh = status.fetch_students.filter((id) => !liveDone.has(id));
      fresh.forEach((id) => liveDone.add(id));
      if (fresh.some((id) => onPage.has(id))) liveUpdate(false);
      if (roundEnded) {
        sessionStorage.removeItem(REFRESH_KEY);
        liveUpdate(true);   // also the parts about more students: Te beoordelen, the counter in the menu
      }

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
    polling = false;
    pollTimer = setTimeout(poll, pollAgain ? 0 : delay);
    pollAgain = false;
  }

  if (statusEl()) {
    closePanelOnEscapeOrOutsideClick();
    poll();
  }

  // Spec 041 (before: spec 019, F14): "Verversen" fetches only the students on the screen: the list
  // on Overzicht and Beheer › Studenten (after filters and search), the table on Evaluaties, the
  // student of a student page or an evaluation page. A page without students sends none and no
  // "scherm": then everyone is fetched (F4).
  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!form.matches("form.refresh")) return;
    sessionStorage.setItem(REFRESH_KEY, String(Date.now()));
    form.querySelectorAll("input[name=student], input[name=scherm]").forEach((el) => el.remove());
    const add = (value) => {
      const input = document.createElement("input");
      input.type = "hidden"; input.name = "student"; input.value = value;
      form.appendChild(input);
    };
    document.querySelectorAll("#student-table tr[data-student-id], .compact-table tr[data-student-id]").forEach((row) => {
      if (!row.hidden && !row.closest(".table-group")?.hidden) add(row.dataset.studentId);
    });
    if (document.querySelector("#student-table, .compact-table, [data-refresh-scope]")) {
      const screen = document.createElement("input");
      screen.type = "hidden"; screen.name = "scherm"; screen.value = "1";
      form.appendChild(screen);
    }
    // Spec 041, F7: start the round in the background, so the page (search, scroll, open parts)
    // stays as it is; the status check then follows the round and updates the page.
    event.preventDefault();
    form.querySelector("button")?.setAttribute("disabled", "");
    fetch(form.action, { method: "POST", body: new FormData(form), headers: { "X-Requested-With": "fetch" } })
      .then(() => { clearTimeout(pollTimer); poll(); })
      .catch(() => form.submit());
  }, true);
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

  // Timeline of evaluations (spec 029, F2): show the chosen students at once; the button is for no-JS.
  const who = document.getElementById("timeline-who");
  if (!who) return;
  who.querySelectorAll("[data-js-hide]").forEach((el) => { el.hidden = true; });
  who.addEventListener("change", () => who.submit());
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

  // Spec 028: fold the filters away or show them without reloading; the state is kept (F5).
  const foldForm = document.getElementById("filters-fold");
  const foldButton = document.querySelector(".filters-toggle");
  foldButton?.addEventListener("click", (event) => {
    event.preventDefault();
    const main = document.querySelector("main.content");
    const compact = !main.classList.contains("filters-compact");
    main.classList.toggle("filters-compact", compact);
    foldButton.setAttribute("aria-expanded", String(!compact));
    foldButton.value = compact ? "uitgebreid" : "compact";
    const data = new FormData(foldForm);
    data.set("stand", compact ? "compact" : "uitgebreid");
    fetch(foldForm.action, { method: "POST", body: data, headers: { "X-Requested-With": "fetch" } });
  });

  const listColumnForm = document.getElementById("list-column-form");   // spec 010, F5
  listColumnForm?.addEventListener("change", () => listColumnForm.submit());

  const colourForm = document.getElementById("colour-form");   // F23
  colourForm?.addEventListener("change", () => colourForm.submit());

  const columnForm = document.getElementById("column-form");
  columnForm?.addEventListener("change", () => columnForm.submit());

  // Custom columns (F8): save when the field loses focus after a change, or with Enter.
  card.querySelectorAll(".custom-cell [name=waarde]").forEach((input) => {   // spec 024: also the choice list
    input.addEventListener("change", () => input.form.submit());
  });

  const table = document.getElementById("students");
  const count = document.getElementById("table-count");
  const search = document.getElementById("table-search");

  // Spec 019: small saves without reloading the overview.
  async function post(form) {
    const response = await fetch(form.action, {
      method: "POST", body: new FormData(form), headers: { "X-Requested-With": "fetch" },
    });
    if (!response.ok) throw new Error(await response.text() || "Opslaan is niet gelukt.");
    if (response.status === 205) location.reload();   // spec 025: the invulling was filled as well
    return response;
  }

  // F4, F5: hide a student, or show again. With "Alle studenten die ik niet heb verborgen"
  // the row disappears; with every other choice of who it is dimmed.
  const who = document.querySelector("#table-filters select[name=wie]");
  card.querySelectorAll(".hide-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const row = form.closest(".student-row");
      const hide = form.dataset.hideAction === "hide";
      post(form).then(() => {
        if (hide && who?.value === "zichtbaar") {
          const group = row.closest(".table-group");
          row.remove();
          const header = group?.querySelector(".group-count");
          const left = group ? group.querySelectorAll(".student-row").length : 0;
          if (header) header.textContent = `${left} student${left === 1 ? "" : "en"}`;
          if (group && left === 0) group.remove();
          if (!table.querySelector(".student-row")) { location.reload(); return; }
          updateCount();
        } else {
          row.classList.toggle("is-hidden-student", hide);
        }
      }).catch((error) => alert(error.message));
    });
  });

  // Spec 022: the lists in the student list save right away. The sort value follows the choice;
  // a guild change reloads in place, because the guild master column changes along.
  card.querySelectorAll(".inline-pick select").forEach((select) => {
    select.addEventListener("change", () => {
      const form = select.form;
      post(form).then(() => {
        if (form.hasAttribute("data-reload")) { location.reload(); return; }
        // The first-name and full-name columns save the same field: keep both lists in step.
        form.closest("tr").querySelectorAll(".inline-pick").forEach((other) => {
          if (other.action !== form.action) return;
          const list = other.querySelector("select");
          list.value = select.value;
          const cell = other.closest("td");
          const text = list.value ? list.selectedOptions[0].textContent.trim().toLowerCase() : "~";
          if (cell.dataset.col === "semester") cell.dataset.sortValue = list.value || "99";
          else if (!cell.dataset.col.startsWith("guildmaster")) cell.dataset.sortValue = text;
        });
      }).catch((error) => { alert(error.message); location.reload(); });
    });
  });

  // Spec 021: make me coach or guild master; reload in place, because more cells can change.
  card.querySelectorAll(".make-me-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      post(form).then(() => location.reload()).catch((error) => alert(error.message));
    });
  });

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

(() => {
  "use strict";

  // Spec 020, U3: while updating, ask the app for its version until the new one answers.
  const box = document.getElementById("updating");
  const step = document.getElementById("updating-step");
  if (!box || !step) return;
  const oldVersion = box.dataset.version;
  const attempt = box.dataset.attempt;
  const stuck = document.getElementById("updating-stuck");
  const STUCK_AFTER_MS = 3 * 60 * 1000;
  let lastAnswer = Date.now();
  const poll = async () => {
    try {
      const answer = await fetch("/versie", { cache: "no-store" }).then((r) => r.json());
      lastAnswer = Date.now();
      if (stuck) stuck.hidden = true;
      const done = answer.result && answer.result.attempt === attempt && answer.result.ok;   // a beta keeps the number
      if (answer.version !== oldVersion || done) {
        window.location.href = "/instellingen#versie";
        return;
      }
      const failed = answer.result && answer.result.attempt === attempt && !answer.result.ok;
      if (answer.update.error || failed) {
        step.textContent = failed ? answer.result.message : answer.update.error;
        box.querySelector("h2").textContent = "Bijwerken is niet gelukt";
        return;
      }
      if (answer.update.step) step.textContent = answer.update.step;
    } catch (error) {
      step.textContent = "Opnieuw starten";   // the app is restarting: keep asking
      if (stuck && Date.now() - lastAnswer > STUCK_AFTER_MS) stuck.hidden = false;   // spec 020, U3
    }
    window.setTimeout(poll, 2000);
  };
  window.setTimeout(poll, 1500);
})();

(() => {
  "use strict";

  // Spec 034, F1: fetch the evidence of this student when the page opens, then replace the block.
  const block = document.getElementById("evidence-block");
  if (!block) return;
  const status = document.getElementById("evidence-status");
  if (status) status.textContent = "Bewijsstukken ophalen…";
  fetch(block.dataset.fetch, { method: "POST", headers: { "X-Requested-With": "fetch" } })
    .then((response) => (response.ok ? response.text() : Promise.reject(response.status)))
    .then((html) => {
      block.outerHTML = html;
      // Spec 039: the evaluation page lists the evidence per skill too; show them once fetched.
      if (document.querySelector("[data-evidence-pending]")) window.location.reload();
    })
    .catch(() => { if (status) status.textContent = "Ophalen is niet gelukt; probeer het later opnieuw."; });
})();

(() => {
  "use strict";

  // Spec 035, F4: a click on a feedback request or reply opens the side panel with the conversation;
  // spec 037: also an evaluation block, a level cell or an evidence dot (data-panel-title).
  const panel = document.getElementById("feedback-panel");
  if (!panel) return;
  const open = (target, link, failed) => {
    const body = target.querySelector(".side-panel-body");
    target.querySelector("h2").textContent = link.dataset.panelTitle || "Feedback";
    body.textContent = "Laden…";
    target.hidden = false;
    fetch(link.href, { headers: { "X-Requested-With": "fetch" } })
      .then((response) => (response.ok ? response.text() : Promise.reject(response.status)))
      .then((html) => { body.innerHTML = html; })
      .catch(() => { body.textContent = failed; });
  };
  document.addEventListener("click", (event) => {
    const mark = event.target.closest("[data-feedback]");
    if (mark) {
      event.preventDefault();
      open(panel, mark, "Dit kon niet worden geladen.");
      return;
    }
    if (event.target.closest("[data-close-panel]")) panel.hidden = true;
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const viewer = document.getElementById("file-viewer");
    if (viewer && !viewer.hidden) return;   // spec 038: Esc first closes "Groot bekijken"
    panel.hidden = true;
  });
})();

(() => {
  "use strict";

  // Spec 038, F1a: "Groot bekijken" shows a file over almost the whole screen; close with the
  // close button, Esc or a click next to it. F6: a file that cannot be shown gets a message.
  const viewer = document.getElementById("file-viewer");
  if (!viewer) return;
  const body = document.getElementById("file-viewer-body");
  const close = () => { viewer.hidden = true; body.replaceChildren(); };
  const media = (display, src, name) => {
    if (display === "image") return Object.assign(document.createElement("img"), { src, alt: name });
    if (display === "video") return Object.assign(document.createElement("video"), { src, controls: true, autoplay: true });
    return Object.assign(document.createElement("iframe"), { src, title: name });
  };
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-file-large]");
    if (button) {
      document.querySelectorAll("#feedback-panel video").forEach((video) => video.pause());
      document.getElementById("file-viewer-title").textContent = button.dataset.fileName || "Bestand";
      body.replaceChildren(media(button.dataset.fileDisplay, button.dataset.fileLarge, button.dataset.fileName || ""));
      viewer.hidden = false;
      return;
    }
    if (event.target.closest("[data-close-viewer]") || event.target === viewer) close();
  });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !viewer.hidden) close(); });
  // An image or video that cannot be fetched: a short message in its place (an iframe shows the
  // message page of the server itself).
  document.addEventListener("error", (event) => {
    const element = event.target;
    if (!(element instanceof HTMLElement) || !element.matches("[data-file-media]")) return;
    const message = Object.assign(document.createElement("p"), {
      className: "muted", textContent: "Dit bestand kan niet in het dashboard worden getoond." });
    element.replaceWith(message);
  }, true);
})();

(() => {
  "use strict";

  // Spec 001, F6: place the details of a level cell relative to the window, below the cell when
  // there is room and above it otherwise. Inside a table that scrolls sideways an absolutely
  // positioned tooltip is clipped and gives the table a scroll bar (seen on the bottom rows).
  const GAP = 4;
  const place = (cell) => {
    const tip = cell.querySelector(".level-details");
    if (!tip) return;
    tip.classList.add("is-floating");
    const box = cell.querySelector(".level")?.getBoundingClientRect() || cell.getBoundingClientRect();
    const width = tip.offsetWidth;
    const height = tip.offsetHeight;
    const below = box.bottom + GAP + height <= window.innerHeight;
    const top = below ? box.bottom + GAP : Math.max(GAP, box.top - GAP - height);
    const left = Math.min(Math.max(GAP, box.left + box.width / 2 - width / 2), window.innerWidth - width - GAP);
    tip.style.top = `${top}px`;
    tip.style.left = `${left}px`;
  };
  const reset = (cell) => {
    const tip = cell?.querySelector(".level-details.is-floating");
    if (!tip) return;
    tip.classList.remove("is-floating");
    tip.style.top = "";
    tip.style.left = "";
  };
  document.addEventListener("mouseover", (event) => {
    const cell = event.target.closest(".col-skill");
    if (cell && !cell.contains(event.relatedTarget)) requestAnimationFrame(() => place(cell));
  });
  document.addEventListener("mouseout", (event) => {
    const cell = event.target.closest(".col-skill");
    if (cell && !cell.contains(event.relatedTarget)) reset(cell);
  });
  document.addEventListener("focusin", (event) => {
    const cell = event.target.closest(".col-skill");
    if (cell) requestAnimationFrame(() => place(cell));
  });
  document.addEventListener("focusout", (event) => reset(event.target.closest(".col-skill")));
  // While the page or the table scrolls, keep a visible tooltip next to its cell.
  document.addEventListener("scroll", () => {
    document.querySelectorAll(".level-details.is-floating").forEach((tip) => place(tip.closest(".col-skill")));
  }, true);
})();

(() => {
  "use strict";

  // Spec 040, F4: the AI advice is made in the background; the card shows the progress and
  // replaces itself until it is done. The buttons work without a page reload.
  const replaceCard = (html) => {
    const card = document.getElementById("ai-advies");
    if (!card) return;
    card.outerHTML = html;
    watch();
  };
  let timer = null;
  const watch = () => {
    clearTimeout(timer);
    const card = document.getElementById("ai-advies");
    if (!card || !card.hasAttribute("data-advice-busy")) return;
    timer = setTimeout(() => {
      fetch(card.dataset.advice, { headers: { "X-Requested-With": "fetch" } })
        .then((r) => (r.ok ? r.text() : Promise.reject(r.status)))
        .then(replaceCard)
        .catch(() => { timer = setTimeout(watch, 3000); });
    }, 1500);
  };
  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!form.matches("[data-advice-form]")) return;
    event.preventDefault();
    form.querySelector("button").disabled = true;
    fetch(form.action, { method: "POST", body: new FormData(form), headers: { "X-Requested-With": "fetch" } })
      .then((r) => (r.ok ? r.text() : Promise.reject(r.status)))
      .then(replaceCard)
      .catch(() => form.submit());
  });
  // F24: "Advies vragen" only once every requested skill has a level and an explanation.
  const judged = (form) => [...form.querySelectorAll(".ai-judgment select, .ai-judgment textarea")]
    .every((field) => field.value.trim() !== "");
  const updateAsk = (event) => {
    const form = event.target.closest && event.target.closest("[data-judgment-form]");
    if (!form) return;
    const card = document.getElementById("ai-advies");
    const ok = judged(form);
    form.querySelector('button[type="submit"]').disabled = !ok || (card && card.hasAttribute("data-advice-busy"));
    const hint = form.querySelector("[data-judgment-hint]");
    if (hint) hint.hidden = ok;
  };
  document.addEventListener("input", updateAsk);
  document.addEventListener("change", updateAsk);
  watch();

  // Spec 040, F12, step 3: downloading the model, with a progress bar.
  const pull = document.querySelector("[data-pull-status]");
  if (pull) {
    const bar = pull.querySelector("progress");
    const text = pull.querySelector("[data-pull-text]");
    const box = pull.querySelector(".wizard-progress");
    const show = (s) => {
      box.hidden = false;
      bar.value = s.total ? Math.round((s.done / s.total) * 100) : 0;
      const gb = (n) => (n / 1e9).toFixed(1).replace(".", ",");
      const name = s.model && pull.dataset.pullHash ? `${s.model}: ` : "";
      text.textContent = s.error || name + (s.total ? `${s.status} · ${gb(s.done)} van ${gb(s.total)} GB` : s.status);
    };
    const buttons = () => pull.querySelectorAll("[data-pull-form] button");
    const poll = () => {
      fetch(pull.dataset.pullStatus).then((r) => r.json()).then((s) => {
        show(s);
        if (s.running) setTimeout(poll, 1000);
        else if (!s.error) window.location.hash = pull.dataset.pullHash || "stap-3", window.location.reload();
        else buttons().forEach((b) => { b.disabled = false; });
      }).catch(() => setTimeout(poll, 3000));
    };
    // F28: in Instellingen there is a form per tested model and one for a name of your own.
    pull.querySelectorAll("[data-pull-form]").forEach((form) => form.addEventListener("submit", (event) => {
      event.preventDefault();
      buttons().forEach((b) => { b.disabled = true; });
      fetch(form.action, { method: "POST", body: new FormData(form), headers: { "X-Requested-With": "fetch" } })
        .then((r) => r.json())
        .then((s) => { if (s.error && !s.running) { show(s); buttons().forEach((b) => { b.disabled = false; }); } else poll(); })
        .catch(poll);
    }));
    if (!box.hidden) poll();
  }

  // Spec 042, F4: copy the whole AI log as plain text.
  document.querySelectorAll("[data-copy-log]").forEach((button) => {
    button.addEventListener("click", () => {
      const source = document.getElementById(button.dataset.copyLog);
      const done = button.parentElement.querySelector("[data-copy-done]");
      const shown = () => { if (done) { done.hidden = false; setTimeout(() => { done.hidden = true; }, 3000); } };
      const fallback = () => {
        source.hidden = false;
        source.select();
        try { document.execCommand("copy"); shown(); } finally { source.hidden = true; }
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(source.value).then(shown, fallback);
      } else {
        fallback();
      }
    });
  });

  // Spec 040, F29: show the chosen number of cores next to the slider.
  document.querySelectorAll("[data-cores-output]").forEach((slider) => {
    const output = document.getElementById(slider.dataset.coresOutput);
    slider.addEventListener("input", () => { output.textContent = `${slider.value} van ${slider.max}`; });
  });

  // Spec 040, F12, step 4: the trial question.
  const trial = document.querySelector("[data-trial]");
  if (trial) {
    const result = document.querySelector("[data-trial-result]");
    trial.addEventListener("click", () => {
      trial.disabled = true;
      result.hidden = false;
      result.className = "wizard-check";
      const started = Date.now();
      result.textContent = "Bezig… (de eerste keer laadt Ollama het model; dat kan een minuut duren)";
      const tick = setInterval(() => {
        result.textContent = `Bezig… ${Math.round((Date.now() - started) / 1000)} s (de eerste keer laadt Ollama het model; dat kan een minuut duren)`;
      }, 1000);
      fetch(trial.dataset.trial, { method: "POST", headers: { "X-Requested-With": "fetch" } })
        .then((r) => r.json())
        .then((r) => {
          clearInterval(tick);
          if (r.ok) {
            window.location.hash = "stap-4";
            window.location.reload();
          } else {
            result.className = "wizard-check is-todo";
            result.textContent = r.message;
            trial.disabled = false;
          }
        })
        .catch(() => { clearInterval(tick); result.textContent = "De proefvraag is niet gelukt."; trial.disabled = false; });
    });
  }
})();

(() => {
  "use strict";

  // Spec 020, B1-B5: the dropdown "Versie" in Instellingen; a beta shows the commits of a branch.
  const channel = document.getElementById("version-channel");
  const panel = document.getElementById("channel-beta");
  if (!channel || !panel) return;
  const release = document.getElementById("channel-release");
  const branchSelect = document.getElementById("beta-branch");
  const status = document.getElementById("beta-status");
  const list = document.getElementById("beta-commits");
  const install = document.getElementById("beta-install");
  const warning = document.getElementById("beta-warning");
  const branchField = document.getElementById("beta-branch-field");
  const ERROR = "Ophalen is niet gelukt. Controleer je internetverbinding en probeer het over een poosje opnieuw.";
  let loadedBranches = false;
  let request = 0;

  const resetChoice = () => { install.disabled = true; warning.hidden = true; install.hidden = false; };

  const showCommits = async () => {
    const mine = ++request;   // an older answer must not replace a newer choice
    list.replaceChildren();
    resetChoice();
    branchField.value = branchSelect.value;
    status.textContent = "Commits ophalen…";
    try {
      const response = await fetch(`${panel.dataset.commitsUrl}?branch=${encodeURIComponent(branchSelect.value)}`);
      const data = await response.json();
      if (mine !== request) return;
      if (!response.ok) { status.textContent = data.error || ERROR; return; }
      status.textContent = data.commits.length ? "" : "Deze branch heeft geen commits.";
      data.commits.forEach((commit) => {
        const item = document.createElement("li");
        const label = document.createElement("label");
        const radio = document.createElement("input");
        radio.type = "radio"; radio.name = "commit"; radio.value = commit.commit;
        radio.addEventListener("change", () => { resetChoice(); install.disabled = false; });
        const code = document.createElement("code");
        code.textContent = commit.short;
        const message = document.createElement("span");
        message.textContent = commit.message;
        const when = document.createElement("span");
        when.className = "muted";
        when.textContent = commit.installed ? `${commit.date} · geïnstalleerd` : commit.date;
        label.append(radio, code, message, when);
        item.append(label);
        list.append(item);
      });
    } catch (error) {
      if (mine === request) status.textContent = ERROR;
    }
  };

  const loadBranches = async () => {
    status.textContent = "Branches ophalen…";
    try {
      const response = await fetch(panel.dataset.branchesUrl);
      const data = await response.json();
      if (!response.ok) { status.textContent = data.error || ERROR; return; }
      data.branches.forEach((name) => branchSelect.append(new Option(name, name)));
      branchSelect.value = data.branches.includes(data.default) ? data.default : data.branches[0];
      loadedBranches = true;
      showCommits();
    } catch (error) {
      status.textContent = ERROR;
    }
  };

  channel.addEventListener("change", () => {
    const beta = channel.value === "beta";
    panel.hidden = !beta;
    release.hidden = beta;
    if (beta && !loadedBranches) loadBranches();
  });
  branchSelect.addEventListener("change", showCommits);
  install.addEventListener("click", () => { warning.hidden = false; install.hidden = true; });
  document.getElementById("beta-cancel").addEventListener("click", () => { warning.hidden = true; install.hidden = false; });
})();
