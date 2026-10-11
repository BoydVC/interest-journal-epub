(function () {
  const DATA = window.__CHAPTERS__ || { chapters: [], sources: [], title: "Interest Journal" };
  const chapters = DATA.chapters || [];
  let filter = "all";
  let idx = 0;

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  // Lightweight markdown → HTML (headings, lists, bold, links, code, hr, paragraphs)
  function md(src) {
    let t = String(src || "").replace(/\r\n/g, "\n");
    const lines = t.split("\n");
    const out = [];
    let inList = null;
    let inPre = false;
    let preBuf = [];

    function closeList() {
      if (inList) { out.push(inList === "ul" ? "</ul>" : "</ol>"); inList = null; }
    }

    for (let i = 0; i < lines.length; i++) {
      let line = lines[i];
      if (line.startsWith("```")) {
        if (inPre) {
          out.push("<pre><code>" + esc(preBuf.join("\n")) + "</code></pre>");
          preBuf = []; inPre = false;
        } else {
          closeList(); inPre = true;
        }
        continue;
      }
      if (inPre) { preBuf.push(line); continue; }

      if (/^\s*$/.test(line)) { closeList(); continue; }

      if (/^---+\s*$/.test(line) || /^\*\*\*+\s*$/.test(line)) {
        closeList(); out.push("<hr>"); continue;
      }

      const hm = line.match(/^(#{1,3})\s+(.+)$/);
      if (hm) {
        closeList();
        const n = hm[1].length;
        out.push(`<h${n}>${inline(hm[2])}</h${n}>`);
        continue;
      }

      const ul = line.match(/^\s*[-*]\s+(.+)$/);
      if (ul) {
        if (inList !== "ul") { closeList(); out.push("<ul>"); inList = "ul"; }
        out.push("<li>" + inline(ul[1]) + "</li>");
        continue;
      }

      const ol = line.match(/^\s*\d+\.\s+(.+)$/);
      if (ol) {
        if (inList !== "ol") { closeList(); out.push("<ol>"); inList = "ol"; }
        out.push("<li>" + inline(ol[1]) + "</li>");
        continue;
      }

      // truncation marker
      if (line.includes("[Excerpt truncated")) {
        closeList();
        out.push('<div class="trunc-note">' + esc(line.replace(/^\*?\[?/, "").replace(/\]?\*?$/, "")) + "</div>");
        continue;
      }

      closeList();
      out.push("<p>" + inline(line) + "</p>");
    }
    closeList();
    if (inPre) out.push("<pre><code>" + esc(preBuf.join("\n")) + "</code></pre>");
    return out.join("\n");
  }

  function inline(s) {
    let t = esc(s);
    t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
    t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    t = t.replace(/(^|[^\*])\*([^*]+)\*(?!\*)/g, "$1<em>$2</em>");
    t = t.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1<\/a>');
    return t;
  }

  function showView(name) {
    $$(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + name));
    $$(".tab").forEach((t) => {
      const on = t.dataset.view === name;
      t.classList.toggle("active", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
    });
  }

  function go(hash) {
    const h = (hash || location.hash || "#cover").replace(/^#/, "");
    if (h.startsWith("ch/")) {
      const id = decodeURIComponent(h.slice(3));
      const i = chapters.findIndex((c) => c.id === id);
      if (i >= 0) { idx = i; renderReader(); showView("reader"); return; }
    }
    const view = ["cover", "toc", "reader", "about"].includes(h) ? h : "cover";
    showView(view);
    if (view === "reader" && chapters[idx]) renderReader();
  }

  function renderCover() {
    $("#coverSub").textContent = DATA.subtitle || "Interest Journal excerpts";
    const n = chapters.length;
    const trunc = chapters.filter((c) => c.truncated).length;
    const dates = chapters.map((c) => c.date).filter(Boolean).sort();
    const range = dates.length ? `${dates[0]} → ${dates[dates.length - 1]}` : "—";
    $("#coverMeta").textContent = `${n} chapters · ${range}`;
    $("#chapCount").textContent = `${n} chapters`;
    $("#coverStats").innerHTML = [
      ["Chapters", n],
      ["Truncated excerpts", trunc],
      ["Source files", (DATA.sources || []).length],
      ["Built", DATA.built || "—"]
    ].map(([k, v]) => `<li><span>${esc(k)}</span><strong>${esc(v)}</strong></li>`).join("");
    $("#footInfo").textContent = DATA.title || "";
  }

  function renderFilters() {
    const kinds = ["all", ...new Set(chapters.map((c) => c.kind))];
    $("#kindFilters").innerHTML = kinds.map((k) =>
      `<button type="button" class="chip${k === filter ? " active" : ""}" data-kind="${esc(k)}">${esc(k)}</button>`
    ).join("");
  }

  function renderToc() {
    const list = filter === "all" ? chapters : chapters.filter((c) => c.kind === filter);
    $("#tocList").innerHTML = list.map((c) => `
      <button type="button" class="toc-card" data-id="${esc(c.id)}">
        <div class="toc-date">${esc((c.date || "—").slice(5) || c.date || "—")}<br>${esc((c.date || "").slice(0, 4))}</div>
        <div>
          <h3>${esc(c.title)}</h3>
          <p>${esc(c.filename)} · ${c.bytes_excerpt.toLocaleString()} B excerpt${c.truncated ? " (truncated)" : ""}</p>
        </div>
        <div>
          <span class="badge kind-${esc(c.kind)}">${esc(c.kind)}</span>
          ${c.truncated ? '<div style="margin-top:.35rem"><span class="badge warn">truncated</span></div>' : ""}
        </div>
      </button>
    `).join("") || '<p class="lede">No chapters in this filter.</p>';
  }

  function renderReader() {
    const c = chapters[idx];
    if (!c) return;
    $("#readerTitle").textContent = c.title;
    $("#readerSub").textContent = `${c.date || "—"} · ${c.filename} · ${c.source_path}`;
    let body = md(c.body);
    if (c.truncated) {
      body = '<div class="trunc-note">Excerpt truncated for EPUB size — full source: ' +
        esc(c.source_path) + "</div>" + body;
    }
    $("#readerBody").innerHTML = body;
    $("#btnPrev").disabled = idx <= 0;
    $("#btnNext").disabled = idx >= chapters.length - 1;
  }

  function renderAbout() {
    $("#sourceList").innerHTML = (DATA.sources || []).map((s) => `<li>${esc(s)}</li>`).join("")
      || "<li>(none)</li>";
  }

  // events
  $$(".tab").forEach((t) => t.addEventListener("click", () => {
    location.hash = t.dataset.view;
  }));
  $("#btnOpenToc")?.addEventListener("click", () => { location.hash = "toc"; });
  $("#kindFilters").addEventListener("click", (e) => {
    const b = e.target.closest("[data-kind]");
    if (!b) return;
    filter = b.dataset.kind;
    renderFilters();
    renderToc();
  });
  $("#tocList").addEventListener("click", (e) => {
    const card = e.target.closest("[data-id]");
    if (!card) return;
    const i = chapters.findIndex((c) => c.id === card.dataset.id);
    if (i < 0) return;
    idx = i;
    location.hash = "ch/" + encodeURIComponent(chapters[idx].id);
  });
  $("#btnPrev").addEventListener("click", () => {
    if (idx > 0) { idx--; location.hash = "ch/" + encodeURIComponent(chapters[idx].id); }
  });
  $("#btnNext").addEventListener("click", () => {
    if (idx < chapters.length - 1) { idx++; location.hash = "ch/" + encodeURIComponent(chapters[idx].id); }
  });

  // fix download links for file:// offline
  function fixDownloads() {
    const isFile = location.protocol === "file:";
    $$("#btnDownload, #btnDownload2").forEach((a) => {
      if (isFile) {
        a.href = "interest-journal.epub";
        a.removeAttribute("download");
        a.title = "Open beside this HTML (dist/interest-journal.epub)";
      }
    });
  }

  window.addEventListener("hashchange", () => go());
  renderCover();
  renderFilters();
  renderToc();
  renderAbout();
  fixDownloads();
  go();
})();
