let currentClassCode = "";
let currentSearchPoint = "";
let currentPublishYear = "";
let currentLanguage = "";
let currentPage = 1;
let currentSize = 20;
const facetExpandState = {};

function getApiUrl(path) {
  return new URL(path, window.location.origin).toString();
}

function splitMultiValue(s) {
  if (!s) return [];
  return String(s).split(/[;；，、]\s*/g).map((x) => x.trim()).filter(Boolean);
}

function mapSearchPointLabelToKey(label) {
  if (label === "题名") return "title";
  if (label === "责任者") return "authors";
  if (label === "摘要") return "abstract";
  return "";
}

function gotoSearch(term) {
  const url = new URL("/static/index.html", window.location.origin);
  url.searchParams.set("q", term);
  window.location.href = url.toString();
}

function renderClickableValues(container, values, onClick) {
  const parts = splitMultiValue(values);
  if (!parts.length) { container.textContent = "未知"; return; }
  parts.forEach((part, idx) => {
    const a = document.createElement("a");
    a.href = `/static/index.html?q=${encodeURIComponent(part)}`;
    a.className = "linklike";
    a.textContent = part;
    a.onclick = (e) => { e.preventDefault(); onClick(part); };
    container.appendChild(a);
    if (idx !== parts.length - 1) container.appendChild(document.createTextNode("；"));
  });
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

function escapeRegExp(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlight(text, term) {
  if (!text) return "";
  if (!term) return escapeHtml(text);
  const t = String(term).trim();
  if (!t) return escapeHtml(text);
  const safeText = escapeHtml(String(text));
  const re = new RegExp(escapeRegExp(t), "gi");
  return safeText.replace(re, (m) => `<span class="hl">${m}</span>`);
}

function syncUrl(q, page) {
  const url = new URL(window.location.href);
  if (q) url.searchParams.set("q", q); else url.searchParams.delete("q");
  if (currentClassCode) url.searchParams.set("class_code", currentClassCode); else url.searchParams.delete("class_code");
  if (currentSearchPoint) url.searchParams.set("search_point", currentSearchPoint); else url.searchParams.delete("search_point");
  if (currentPublishYear) url.searchParams.set("publish_year", currentPublishYear); else url.searchParams.delete("publish_year");
  if (currentLanguage) url.searchParams.set("language", currentLanguage); else url.searchParams.delete("language");
  if (page && page > 1) url.searchParams.set("page", String(page)); else url.searchParams.delete("page");
  history.replaceState(null, "", url.toString());
}

function buildPageWindow(page, totalPages, maxLen = 9) {
  if (totalPages <= maxLen) return Array.from({ length: totalPages }, (_, i) => i + 1);
  const half = Math.floor(maxLen / 2);
  let start = page - half;
  let end = page + half;
  if (start < 1) { start = 1; end = maxLen; }
  if (end > totalPages) { end = totalPages; start = totalPages - maxLen + 1; }
  const arr = [];
  for (let i = start; i <= end; i += 1) arr.push(i);
  return arr;
}

function renderRightPager(total, page, size) {
  const pager = document.getElementById("rightPager");
  pager.innerHTML = "";
  const totalPages = Math.max(1, Math.ceil((total || 0) / (size || 20)));

  const addBtn = (label, targetPage, disabled, isActive = false) => {
    const btn = document.createElement("div");
    btn.className = "pager-btn";
    if (isActive) btn.classList.add("active");
    if (disabled) btn.classList.add("disabled");
    btn.textContent = label;
    if (!disabled) btn.onclick = () => doSearch(targetPage, true);
    pager.appendChild(btn);
  };

  addBtn("↑", 1, page <= 1);
  addBtn("▲", page - 1, page <= 1);
  buildPageWindow(page, totalPages, 9).forEach((p) => addBtn(String(p), p, false, p === page));
  addBtn("▼", page + 1, page >= totalPages);
  addBtn("↓", totalPages, page >= totalPages);
}

function setModeSearch() {
  document.getElementById("homeBox").style.display = "none";
  document.getElementById("searchWrap").style.display = "grid";
}

function setModeHome() {
  document.getElementById("homeBox").style.display = "block";
  document.getElementById("searchWrap").style.display = "none";
}

async function loadHomeResources() {
  setModeHome();
  const res = await fetch(getApiUrl("/resources/home?size=20"));
  const items = await res.json();
  const homeList = document.getElementById("homeList");
  const homeEmpty = document.getElementById("homeEmpty");
  homeList.innerHTML = "";

  if (!Array.isArray(items) || !items.length) {
    homeEmpty.style.display = "block";
    return;
  }

  homeEmpty.style.display = "none";
  items.forEach((item) => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    const detailUrl = new URL("/static/detail.html", window.location.origin);
    detailUrl.searchParams.set("id", item.id);
    a.href = detailUrl.toString();
    a.textContent = item.title || "(无标题)";
    li.appendChild(a);
    homeList.appendChild(li);
  });
}

function buildFacetTree(nodes) {
  const root = document.getElementById("facetTree");
  root.innerHTML = "";
  if (!nodes.length) { root.textContent = "暂无分类统计"; return; }
  nodes.forEach((node) => root.appendChild(buildFacetNode(node, 0)));
}

function buildFacetNode(node, level) {
  const wrapper = document.createElement("div");
  wrapper.className = "mp_cc_cNodec";

  const title = document.createElement("div");
  title.className = "mp_cc_cNodeTi";
  if (node.code === currentClassCode) title.classList.add("active");
  title.style.marginLeft = `${Math.max(0, level * 8)}px`;

  const hasChildren = !!(node.children && node.children.length);
  const icon = document.createElement("span");
  icon.className = "mp-icon";
  icon.textContent = hasChildren ? (facetExpandState[node.code] === false ? "▶" : "▼") : "⊙";
  title.appendChild(icon);

  const text = document.createElement("span");
  text.textContent = `${node.name}(${node.count})`;
  title.appendChild(text);

  title.onclick = (e) => {
    e.stopPropagation();
    currentClassCode = currentClassCode === node.code ? "" : node.code;
    doSearch(1);
  };

  wrapper.appendChild(title);

  if (hasChildren) {
    const childrenBox = document.createElement("div");
    childrenBox.className = "mp_cc_cNoden";
    if (facetExpandState[node.code] === false) childrenBox.classList.add("collapsed");
    node.children.forEach((child) => {
      childrenBox.appendChild(buildFacetNode(child, level + 1));
    });

    icon.onclick = (e) => {
      e.stopPropagation();
      facetExpandState[node.code] = facetExpandState[node.code] === false ? true : false;
      doSearch(1, true);
    };
    wrapper.appendChild(childrenBox);
  }

  return wrapper;
}

function renderAggBlock(title, buckets, type) {
  const block = document.createElement("div");
  block.className = "agg-block";
  const head = document.createElement("div");
  head.className = "agg-title";
  head.textContent = `${title}(${buckets.reduce((acc, i) => acc + (i.count || 0), 0)})`;
  block.appendChild(head);

  const ul = document.createElement("ul");
  ul.className = "agg-list";
  buckets.forEach((item) => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = "javascript:void(0)";
    a.className = "agg-link";
    const key = String(item.key);

    if (type === "search_points") {
      const mapped = mapSearchPointLabelToKey(key);
      if (mapped && mapped === currentSearchPoint) a.classList.add("active");
      a.onclick = () => {
        if (!mapped) return;
        currentSearchPoint = currentSearchPoint === mapped ? "" : mapped;
        doSearch(1);
      };
    } else if (type === "publish_years") {
      if (key === currentPublishYear) a.classList.add("active");
      a.onclick = () => {
        if (key === "未知") return;
        currentPublishYear = currentPublishYear === key ? "" : key;
        doSearch(1);
      };
    } else if (type === "languages") {
      if (key === currentLanguage) a.classList.add("active");
      a.onclick = () => {
        currentLanguage = currentLanguage === key ? "" : key;
        doSearch(1);
      };
    } else {
      a.onclick = () => { };
    }

    a.innerHTML = `<span class="bullet">●</span>${escapeHtml(key)}(${item.count})`;
    li.appendChild(a);
    ul.appendChild(li);
  });
  block.appendChild(ul);
  return block;
}

function buildRightAggregations(total, facets) {
  const container = document.getElementById("rightAgg");
  container.innerHTML = "";

  container.appendChild(renderAggBlock("查看站内搜索结果", [{ key: "命中记录", count: total }], "overview"));
  container.appendChild(renderAggBlock("检索点细分", facets.search_points || [], "search_points"));
  container.appendChild(renderAggBlock("按出版日期细分", facets.publish_years || [], "publish_years"));
  container.appendChild(renderAggBlock("按语种细分", facets.languages || [], "languages"));
}

async function doSearch(page = 1, keepTreeState = false) {
  const q = document.getElementById("q").value.trim();
  if (!q && !currentClassCode && !currentSearchPoint && !currentPublishYear && !currentLanguage) {
    currentPage = 1;
    syncUrl("", 1);
    await loadHomeResources();
    return;
  }

  setModeSearch();
  const url = new URL(getApiUrl("/resources/search"));
  if (q) url.searchParams.set("q", q);
  if (currentClassCode) url.searchParams.set("class_code", currentClassCode);
  if (currentSearchPoint) url.searchParams.set("search_point", currentSearchPoint);
  if (currentPublishYear) url.searchParams.set("publish_year", currentPublishYear);
  if (currentLanguage) url.searchParams.set("language", currentLanguage);
  url.searchParams.set("page", String(page));
  url.searchParams.set("size", "20");

  const t0 = performance.now();
  const res = await fetch(url);
  const payload = await res.json();
  const items = payload.items || [];
  const total = typeof payload.total === "number" ? payload.total : items.length;
  currentPage = payload.page || page || 1;
  currentSize = payload.size || 20;
  const facets = payload.facets || {};
  const cnlFacets = facets.cnl || [];
  const t1 = performance.now();

  if (!keepTreeState) {
    cnlFacets.forEach((root) => {
      if (facetExpandState[root.code] == null) facetExpandState[root.code] = true;
    });
  }

  buildFacetTree(cnlFacets);
  buildRightAggregations(total, facets);
  renderRightPager(total, currentPage, currentSize);

  const facetTotal = cnlFacets.reduce((acc, n) => acc + (n.count || 0), 0);
  document.getElementById("facetHeader").textContent = `中图分类法(${facetTotal})`;

  const elapsedMs = t1 - t0;
  const timeText = elapsedMs < 10 ? "小于0.01秒" : `${(elapsedMs / 1000).toFixed(2)}秒`;
  let filterText = "";
  if (currentClassCode) filterText += `<span class="filter-tip">分类：${escapeHtml(currentClassCode)}</span>`;
  if (currentSearchPoint) filterText += `<span class="filter-tip">检索点：${escapeHtml(currentSearchPoint)}</span>`;
  if (currentPublishYear) filterText += `<span class="filter-tip">年份：${escapeHtml(currentPublishYear)}</span>`;
  if (currentLanguage) filterText += `<span class="filter-tip">语种：${escapeHtml(currentLanguage)}</span>`;
  document.getElementById("summary").innerHTML =
    `在"外文电子图书库文山学院"中，命中：${total} 条，耗时：${timeText}` + filterText;

  syncUrl(q, currentPage);

  const container = document.getElementById("results");
  container.innerHTML = "";
  if (!items.length) {
    container.textContent = "没有检索到记录。";
    return;
  }

  items.forEach((item, idx) => {
    const div = document.createElement("div");
    div.className = "resource";
    const row = document.createElement("div");
    row.className = "resource-row";

    const cover = document.createElement("img");
    cover.className = "cover-img";
    cover.alt = "封面";
    cover.src = "/mirror/index/2.jpg";
    cover.onerror = () => { cover.removeAttribute("src"); cover.style.background = "#fafafa"; };

    const content = document.createElement("div");
    content.className = "content";

    const titleLine = document.createElement("div");
    titleLine.className = "title-line";
    const idxSpan = document.createElement("span");
    idxSpan.className = "index-no";
    // 计算连续编号：(当前页码-1) * 每页大小 + 当前索引 + 1
    const continuousIndex = (currentPage - 1) * currentSize + idx + 1;
    idxSpan.textContent = `${continuousIndex}.`;
    titleLine.appendChild(idxSpan);

    const titleLink = document.createElement("a");
    const detailUrl = new URL("/static/detail.html", window.location.origin);
    detailUrl.searchParams.set("id", item.id);
    if (q) detailUrl.searchParams.set("q", q);
    titleLink.href = detailUrl.toString();
    titleLink.className = "title-link";
    titleLink.innerHTML = highlight(item.title || "(无标题)", q);
    titleLine.appendChild(titleLink);

    const meta = document.createElement("div");
    meta.className = "meta";

    const authorsRow = document.createElement("div");
    const authorsLabel = document.createElement("span");
    authorsLabel.className = "label";
    authorsLabel.textContent = "责任者：";
    const authorsVals = document.createElement("span");
    renderClickableValues(authorsVals, item.authors, gotoSearch);
    authorsRow.appendChild(authorsLabel);
    authorsRow.appendChild(authorsVals);

    const keywordsRow = document.createElement("div");
    const keywordsLabel = document.createElement("span");
    keywordsLabel.className = "label";
    keywordsLabel.textContent = "主题词：";
    const keywordsVals = document.createElement("span");
    renderClickableValues(keywordsVals, item.keywords, gotoSearch);
    keywordsRow.appendChild(keywordsLabel);
    keywordsRow.appendChild(keywordsVals);

    const publishRow = document.createElement("div");
    const publishLabel = document.createElement("span");
    publishLabel.className = "label";
    publishLabel.textContent = "出版日期：";
    const publishVal = document.createElement("span");
    publishVal.textContent = item.publish_date || item.publish_year || "未知";
    publishRow.appendChild(publishLabel);
    publishRow.appendChild(publishVal);

    meta.appendChild(authorsRow);
    meta.appendChild(keywordsRow);
    meta.appendChild(publishRow);

    content.appendChild(titleLine);
    content.appendChild(meta);
    row.appendChild(cover);
    row.appendChild(content);
    div.appendChild(row);
    container.appendChild(div);
  });
}

function initFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const q = (params.get("q") || "").trim();
  const classCode = (params.get("class_code") || "").trim();
  const searchPoint = (params.get("search_point") || "").trim();
  const publishYear = (params.get("publish_year") || "").trim();
  const language = (params.get("language") || "").trim();
  const page = Number(params.get("page") || "1");

  if (q) document.getElementById("q").value = q;
  if (classCode) currentClassCode = classCode;
  if (searchPoint) currentSearchPoint = searchPoint;
  if (publishYear) currentPublishYear = publishYear;
  if (language) currentLanguage = language;

  const startPage = Number.isFinite(page) && page >= 1 ? page : 1;
  if (q || classCode || searchPoint || publishYear || language) doSearch(startPage);
  else loadHomeResources();
}

document.getElementById("q").addEventListener("keydown", (e) => {
  if (e.key === "Enter") doSearch(1);
});

initFromQuery();