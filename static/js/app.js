(function () {
  "use strict";
  document.documentElement.classList.add("js");

  var info = JSON.parse(document.getElementById("model-info").textContent);
  var form = document.getElementById("predictor");
  var result = form.querySelector(".result");
  var streamEl = document.getElementById("result-stream");
  var split = document.getElementById("split");
  var techBar = split.querySelector(".split-tech");
  var acadBar = split.querySelector(".split-acad");
  var pTech = document.getElementById("p-tech");
  var pAcad = document.getElementById("p-acad");
  var reasonEl = document.getElementById("reason");
  var chartEl = document.getElementById("compare-chart");

  var FIELDS = ["math", "science", "arts", "hours"];
  var COLUMN = { math: "Math_Marks", science: "Science_Marks", arts: "Arts_Marks", hours: "Study_Hours_Per_Week" };
  var NAMES = { math: "maths", science: "science", arts: "arts", hours: "study hours" };
  var ROWS = [
    { key: "math", label: "Maths", max: 100 },
    { key: "science", label: "Science", max: 100 },
    { key: "arts", label: "Arts", max: 100 },
    { key: "hours", label: "Study hours", max: 60, unit: " h" }
  ];

  // ---------- Inputs ----------
  function range(name) { return document.getElementById(name + "-range"); }
  function num(name) { return document.getElementById(name + "-num"); }

  function paintFill(el) {
    var pct = ((el.value - el.min) / (el.max - el.min)) * 100;
    el.style.setProperty("--fill", pct + "%");
  }

  function values() {
    var gender = form.querySelector('input[name="gender"]:checked');
    var v = { gender: gender ? gender.value : "Female" };
    FIELDS.forEach(function (f) { v[f] = Number(range(f).value); });
    return v;
  }

  FIELDS.forEach(function (f) {
    var r = range(f), n = num(f);
    paintFill(r);
    r.addEventListener("input", function () { n.value = r.value; paintFill(r); schedule(); });
    n.addEventListener("input", function () {
      if (n.value === "") return;
      var val = Math.max(Number(n.min), Math.min(Number(n.max), Math.round(Number(n.value))));
      if (isNaN(val)) return;
      r.value = val; paintFill(r); schedule();
    });
    n.addEventListener("blur", function () { n.value = r.value; });
  });
  form.querySelectorAll('input[name="gender"]').forEach(function (g) { g.addEventListener("change", schedule); });
  form.addEventListener("submit", function (e) { e.preventDefault(); predict(); });

  // ---------- Prediction ----------
  var timer = null, inflight = null, lastStream = result.dataset.stream;

  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(predict, 140);
    drawChart();
  }

  function predict() {
    if (inflight) inflight.abort();
    inflight = new AbortController();
    result.classList.add("loading");
    fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values()),
      signal: inflight.signal
    })
      .then(function (res) { return res.json().then(function (body) { return { ok: res.ok, body: body }; }); })
      .then(function (r) {
        result.classList.remove("loading");
        if (!r.ok) { reasonEl.textContent = r.body.error || "Something in the form needs fixing."; return; }
        render(r.body);
      })
      .catch(function (err) {
        if (err.name === "AbortError") return;
        result.classList.remove("loading");
        reasonEl.textContent = "Pathway could not reach the server. Check your connection and move a slider to try again.";
      });
  }

  function render(data) {
    var t = data.probabilities.Technical, a = data.probabilities.Academic;
    if (data.stream !== lastStream) {
      streamEl.classList.remove("swap");
      void streamEl.offsetWidth; // restart the animation
      streamEl.classList.add("swap");
      lastStream = data.stream;
    }
    result.dataset.stream = data.stream;
    streamEl.textContent = data.stream;
    techBar.style.flexBasis = t + "%";
    acadBar.style.flexBasis = a + "%";
    pTech.textContent = Math.round(t) + "%";
    pAcad.textContent = Math.round(a) + "%";
    split.setAttribute("aria-label", "Technical " + t + " percent, Academic " + a + " percent");
    reasonEl.textContent = explain(data);
  }

  // Plain-language reason: which subjects sit closer to which stream's average.
  function explain(data) {
    var v = values(), avg = info.averages, toTech = [], toAcad = [];
    ["math", "science", "arts"].forEach(function (f) {
      var c = COLUMN[f];
      var dT = Math.abs(v[f] - avg.Technical[c]), dA = Math.abs(v[f] - avg.Academic[c]);
      if (dT < dA) toTech.push(NAMES[f]); else toAcad.push(NAMES[f]);
    });
    function list(xs) { return xs.length > 1 ? xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1] : xs[0]; }
    function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
    var parts = [];
    if (toTech.length) parts.push("Your " + list(toTech) + (toTech.length > 1 ? " are" : " is") + " closer to Technical students.");
    if (toAcad.length) parts.push((toTech.length ? cap(list(toAcad)) : "Your " + list(toAcad)) + (toAcad.length > 1 ? " are" : " is") + " closer to Academic students.");
    if (data.confidence < 65) parts.push("This is a close call, so both streams are realistic for you.");
    return parts.join(" ");
  }

  // ---------- Comparison chart (inline SVG) ----------
  var SVG = "http://www.w3.org/2000/svg";
  function el(name, attrs, text) {
    var n = document.createElementNS(SVG, name);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  }

  function drawChart() {
    var w = Math.max(300, chartEl.clientWidth);
    var narrow = w < 560;
    var labelW = narrow ? 0 : 130, padR = 24, rowH = narrow ? 78 : 64, top = narrow ? 8 : 18;
    var x0 = labelW, x1 = w - padR, h = top + ROWS.length * rowH + 6;
    var v = values();
    var svg = el("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h, role: "img",
      "aria-label": "Your marks compared with the average Technical and Academic student" });

    ROWS.forEach(function (row, i) {
      var cy = top + i * rowH + (narrow ? 50 : rowH / 2);
      var sx = function (val) { return x0 + (val / row.max) * (x1 - x0); };
      var c = COLUMN[row.key];
      var tVal = info.averages.Technical[c], aVal = info.averages.Academic[c], you = v[row.key];

      if (narrow) svg.appendChild(el("text", { x: 0, y: cy - 30, class: "row-label" }, row.label));
      else svg.appendChild(el("text", { x: 0, y: cy + 5, class: "row-label" }, row.label));

      svg.appendChild(el("line", { x1: x0, x2: x1, y1: cy, y2: cy, class: "track" }));
      svg.appendChild(el("text", { x: x0, y: cy + 22, class: "tick" }, "0"));
      svg.appendChild(el("text", { x: x1, y: cy + 22, class: "tick", "text-anchor": "end" }, row.max + (row.unit || "")));

      var tc = el("circle", { cx: sx(tVal), cy: cy, r: 8, class: "avg-tech" });
      tc.appendChild(el("title", {}, "Average Technical student: " + tVal));
      svg.appendChild(tc);
      var ac = el("circle", { cx: sx(aVal), cy: cy, r: 8, class: "avg-acad" });
      ac.appendChild(el("title", {}, "Average Academic student: " + aVal));
      svg.appendChild(ac);

      svg.appendChild(el("circle", { cx: sx(you), cy: cy, r: 9, class: "you" }));
      svg.appendChild(el("text", { x: sx(you), y: cy - 16, class: "you-val", "text-anchor": "middle" }, you + (row.unit || "")));
    });

    chartEl.replaceChildren(svg);
  }

  // ---------- Header border on scroll ----------
  var header = document.querySelector(".site-header");
  function onScroll() { header.classList.toggle("scrolled", window.scrollY > 8); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  var resizeTimer;
  window.addEventListener("resize", function () { clearTimeout(resizeTimer); resizeTimer = setTimeout(drawChart, 120); });

  drawChart();
  reasonEl.textContent = lastStream ? explain({ confidence: Math.max(
    parseFloat(pTech.textContent), parseFloat(pAcad.textContent)) }) : "";
})();
