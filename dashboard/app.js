/* Observation dashboard. Plain JS, hash routing, no dependencies.
 *
 * Routes
 *   #/                          headline figures and the ranked tasks
 *   #/opportunity/<id>          cost, what to do, proof, document, how it was calculated
 *   #/process/<id>              what happens, proof, related tasks, how it was matched
 *   #/message/<id>?q=<quote>    raw message with the quote highlighted
 *
 * The quote travels in the hash query so a message link can be copied and still
 * highlight. sessionStorage carries it as a fallback for long quotes.
 */
(function () {
  "use strict";

  var app = document.getElementById("app");
  var DATA = null;
  var MSG_LIMIT = 200;
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"];

  // ---------------------------------------------------------------- utils

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function num(v, places) {
    var n = Number(v);
    if (!isFinite(n)) n = 0;
    return n.toLocaleString("en-US", { minimumFractionDigits: places, maximumFractionDigits: places });
  }
  function money(v) {
    var n = Number(v);
    if (!isFinite(n)) n = 0;
    return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }
  // Per-task figures round down, so a task at $29.75 never displays as the $30 threshold.
  function moneyDown(v) {
    var n = Number(v);
    if (!isFinite(n)) n = 0;
    return money(Math.floor(n));
  }
  function int(v) { return num(v, 0); }
  function dateOnly(iso) {
    if (!iso) return "undated";
    return String(iso).slice(0, 10);
  }
  function monthYear(iso) {
    if (!iso) return null;
    var s = String(iso);
    var m = Number(s.slice(5, 7));
    if (!(m >= 1 && m <= 12)) return s.slice(0, 10);
    return MONTHS[m - 1] + " " + s.slice(0, 4);
  }
  function firstSentence(text) {
    var s = String(text || "").trim();
    var m = /^[\s\S]*?[.!?](?=\s|$)/.exec(s);
    return m ? m[0] : s;
  }
  function spanYearsWord() {
    var years = Math.round(Number(DATA.span_months || 0) / 12);
    if (years >= 1 && years < WORDS.length) return WORDS[years] + " year";
    return num(Number(DATA.span_months || 0), 0) + " month";
  }
  function windowText(p) {
    var first = p.first_match ? dateOnly(p.first_match) : null;
    var last = p.last_match ? dateOnly(p.last_match) : null;
    if (first && last) return esc(first) + " to " + esc(last);
    if (first || last) return "dated from " + esc(first || last) + " only";
    return "no dated matches, window floored at 1 month";
  }
  function corpusInstances(p, o) {
    if (o && o.instances_per_month_corpus_span != null) return Number(o.instances_per_month_corpus_span);
    if (p && p.instances_per_month_corpus_span != null) return Number(p.instances_per_month_corpus_span);
    var s = Number(DATA.span_months || 1);
    return s ? Number((p || {}).match_count || 0) / s : 0;
  }

  function oppHref(id) { return "#/opportunity/" + encodeURIComponent(id); }
  function procHref(id) { return "#/process/" + encodeURIComponent(id); }
  function msgHref(id, quote) {
    var h = "#/message/" + encodeURIComponent(id);
    if (quote) h += "?q=" + encodeURIComponent(quote);
    return h;
  }
  function rememberQuote(id, quote) {
    try { sessionStorage.setItem("quote:" + id, quote || ""); } catch (e) { /* private mode */ }
  }
  function recallQuote(id) {
    try { return sessionStorage.getItem("quote:" + id) || ""; } catch (e) { return ""; }
  }

  function processById(id) {
    var ps = DATA.processes || [];
    for (var i = 0; i < ps.length; i++) if (ps[i].process_id === id) return ps[i];
    return null;
  }
  function opportunityById(id) {
    var os = DATA.opportunities || [];
    for (var i = 0; i < os.length; i++) if (os[i].opportunity_id === id) return os[i];
    return null;
  }
  function rankedOpportunities() {
    var os = (DATA.opportunities || []).slice();
    os.sort(function (a, b) { return Number(b.dollars_per_month || 0) - Number(a.dollars_per_month || 0); });
    return os;
  }
  function rankOf(id) {
    var os = rankedOpportunities();
    for (var i = 0; i < os.length; i++) if (os[i].opportunity_id === id) return i + 1;
    return null;
  }
  function meta(id) {
    var m = (DATA.messages || {})[id] || {};
    return { from: m.from || "unknown sender", date: m.date, subject: m.subject || "(no subject)", mailbox: m.mailbox, folder: m.folder, raw: m.raw_available !== false };
  }
  function threshold() {
    var t = Number(DATA.artifact_threshold);
    return isFinite(t) ? t : 1500;
  }
  function rate() {
    var r = Number(DATA.rate_per_hour);
    return isFinite(r) ? r : 85;
  }

  // ---------------------------------------------------------------- markdown

  function inline(s) {
    var out = esc(s);
    out = out.replace(/`([^`]+)`/g, function (m, c) { return "<code>" + c + "</code>"; });
    out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    out = out.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<em>$2</em>");
    out = out.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" rel="noopener">$1</a>');
    return out;
  }

  function tableRow(line) {
    var t = line.trim().replace(/^\|/, "").replace(/\|$/, "");
    return t.split(/(?<!\\)\|/).map(function (c) { return c.trim().replace(/\\\|/g, "|"); });
  }

  function markdown(src) {
    var lines = String(src || "").replace(/\r\n?/g, "\n").split("\n");
    var html = [];
    var para = [];
    var list = null;      // "ul" or "ol"
    var inCode = false;
    var code = [];

    function flushPara() {
      if (para.length) { html.push("<p>" + inline(para.join(" ")) + "</p>"); para = []; }
    }
    function closeList() {
      if (list) { html.push("</" + list + ">"); list = null; }
    }

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (inCode) {
        if (/^```/.test(line)) { html.push("<pre>" + esc(code.join("\n")) + "</pre>"); code = []; inCode = false; }
        else code.push(line);
        continue;
      }
      if (/^```/.test(line)) { flushPara(); closeList(); inCode = true; continue; }
      var m;
      if (!line.trim()) { flushPara(); closeList(); continue; }
      // Table: a pipe row followed by a separator row.
      if (/^\s*\|/.test(line) && i + 1 < lines.length && /^\s*\|?\s*:?-{2,}/.test(lines[i + 1])) {
        flushPara(); closeList();
        var head = tableRow(line);
        var body = [];
        i += 2;
        while (i < lines.length && /^\s*\|/.test(lines[i])) { body.push(tableRow(lines[i])); i++; }
        i--;
        html.push('<div class="table-wrap"><table><thead><tr>' +
          head.map(function (c) { return "<th>" + inline(c) + "</th>"; }).join("") + "</tr></thead><tbody>" +
          body.map(function (r) { return "<tr>" + r.map(function (c) { return "<td>" + inline(c) + "</td>"; }).join("") + "</tr>"; }).join("") +
          "</tbody></table></div>");
        continue;
      }
      if ((m = /^(#{1,6})\s+(.*)$/.exec(line))) {
        flushPara(); closeList();
        var lvl = Math.min(6, m[1].length + 2);
        html.push("<h" + lvl + ">" + inline(m[2]) + "</h" + lvl + ">");
        continue;
      }
      if (/^(-{3,}|\*{3,})\s*$/.test(line)) { flushPara(); closeList(); html.push("<hr>"); continue; }
      if ((m = /^\s*[-*+]\s+(.*)$/.exec(line))) {
        flushPara();
        if (list !== "ul") { closeList(); list = "ul"; html.push("<ul>"); }
        html.push("<li>" + inline(m[1]) + "</li>");
        continue;
      }
      if ((m = /^\s*\d+[.)]\s+(.*)$/.exec(line))) {
        flushPara();
        if (list !== "ol") { closeList(); list = "ol"; html.push("<ol>"); }
        html.push("<li>" + inline(m[1]) + "</li>");
        continue;
      }
      if ((m = /^>\s?(.*)$/.exec(line))) {
        flushPara(); closeList();
        html.push("<blockquote><p>" + inline(m[1]) + "</p></blockquote>");
        continue;
      }
      if (list && /^\s{2,}\S/.test(line)) {
        var last = html.pop();
        html.push(last.replace(/<\/li>$/, " " + inline(line.trim()) + "</li>"));
        continue;
      }
      para.push(line.trim());
    }
    flushPara(); closeList();
    if (inCode) html.push("<pre>" + esc(code.join("\n")) + "</pre>");
    return html.join("\n");
  }

  // ---------------------------------------------------------------- shared pieces

  function backLink(href, text) {
    return '<a class="back" href="' + href + '">' + esc(text) + "</a>";
  }

  function ruleText(rule) {
    if (!rule) return "No match rule recorded.";
    var plain = [];
    if (rule.subject_regex) plain.push("the subject matches /" + rule.subject_regex + "/");
    if (rule.body_any && rule.body_any.length) plain.push("the body contains any of " + rule.body_any.map(function (k) { return '"' + k + '"'; }).join(", "));
    if (rule.from_any && rule.from_any.length) plain.push("the sender is one of " + rule.from_any.join(", "));
    return plain.length ? "An email counts when " + plain.join(", or ") + ". Duplicates are excluded and code does the counting." : "Empty rule, matches nothing.";
  }

  function proof(evidence) {
    if (!evidence || !evidence.length) return '<p class="empty">No quotes survived validation.</p>';
    return '<div class="proof">' + evidence.map(function (ev) {
      var id = ev.message_id;
      var m = meta(id);
      var from = ev.from || m.from;
      var date = ev.date || m.date;
      var href = msgHref(id, ev.quote);
      return '<a class="quote" href="' + href + '" data-quote-id="' + esc(id) + '">' +
        '<span class="quote-text">' + esc(ev.quote) + "</span>" +
        '<span class="quote-cite">' + esc(from) + ", " + esc(dateOnly(date)) + '<span class="open">Open email</span></span>' +
        "</a>";
    }).join("") + "</div>";
  }

  function messageList(ids, total) {
    ids = ids || [];
    if (!ids.length) return '<p class="empty">No emails matched.</p>';
    var shown = ids.slice(0, MSG_LIMIT);
    var items = shown.map(function (id) {
      var m = meta(id);
      return '<li><a href="' + msgHref(id) + '">' +
        '<span class="date">' + esc(dateOnly(m.date)) + "</span>" +
        '<span class="subject">' + esc(m.subject) + "</span>" +
        '<span class="from">' + esc(m.from) + "</span>" +
        "</a></li>";
    }).join("");
    var note = "";
    var t = Number(total);
    if (isFinite(t) && t > shown.length) note = '<p class="quiet">Showing the first ' + int(shown.length) + " of " + int(t) + ".</p>";
    else if (ids.length > shown.length) note = '<p class="quiet">Showing the first ' + int(shown.length) + " of " + int(ids.length) + ".</p>";
    return '<ul class="msg-list">' + items + "</ul>" + note;
  }

  function footer() {
    var t = DATA.totals || {};
    return '<footer class="foot">' + int(t.messages) + " emails, " + int(t.duplicates) + " duplicates removed, " +
      money(rate()) + " per hour, documents drafted for tasks worth " + money(threshold()) + " or more a month where a written document would help.</footer>";
  }

  // ---------------------------------------------------------------- views

  function viewHome() {
    var t = DATA.totals || {};
    var opps = rankedOpportunities();
    var running = 0;
    var rows = opps.map(function (o, i) {
      running += Number(o.dollars_per_month || 0);
      var p = processById(o.process_id) || {};
      var href = oppHref(o.opportunity_id);
      var doc = o.artifact_markdown ? ' <a class="doc" href="' + href + '#artifact">Document ready</a>' : "";
      return "<tr>" +
        '<td class="rank">' + (i + 1) + "</td>" +
        '<td class="task"><a class="task-title" href="' + href + '">' + esc(o.title) + "</a>" + doc +
        '<a class="task-proc" href="' + procHref(o.process_id) + '">' + esc(p.name || o.process_id) + "</a></td>" +
        '<td class="num times"><a href="' + href + '#matched">' + num(o.instances_per_month, 1) + "</a></td>" +
        '<td class="num"><a class="dollars" href="' + href + '">' + moneyDown(o.dollars_per_month) + "</a></td>" +
        '<td class="num running">' + money(running) + "</td>" +
        "</tr>";
    }).join("");

    return "" +
      '<header class="hero">' +
      "<h1>Where Enron loses time</h1>" +
      '<p class="lead">We read ' + int(t.messages) + " emails from four Enron employees and found the work they repeat. " +
      "Click any number to see the emails behind it.</p>" +
      '<div class="figures">' +
      '<div class="figure"><a class="big" href="#/#ranked">' + money(t.dollars_per_month) + '</a><div class="label">per month</div>' +
      '<div class="aside">' + money(t.dollars_per_month_corpus_span) + " if averaged over the full " + spanYearsWord() + " archive</div></div>" +
      '<div class="figure"><a class="big" href="#/#ranked">' + num(t.hours_per_month, 1) + '</a><div class="label">hours per month</div></div>' +
      "</div>" +
      "</header>" +
      '<section id="ranked">' +
      "<h2>The repeated tasks, biggest first</h2>" +
      '<div class="table-wrap"><table class="ranked"><thead><tr>' +
      '<th class="rank">#</th><th>Task</th><th class="num times">Times a month</th><th class="num">Per month</th><th class="num">Running total</th>' +
      "</tr></thead><tbody>" + rows + "</tbody></table></div>" +
      "</section>" +
      footer();
  }

  function viewOpportunity(id) {
    var o = opportunityById(id);
    if (!o) return notFound("task", id);
    var p = processById(o.process_id) || {};
    var matches = Number(p.match_count || 0);
    var active = Number(p.active_months);
    if (!isFinite(active) || active < 1) active = 1;
    var minutes = Number(o.minutes_saved_per_instance || 0);
    var inst = Number(o.instances_per_month || 0);
    var hours = Number(o.hours_per_month || 0);
    var dollars = Number(o.dollars_per_month || 0);
    var instSpan = corpusInstances(p, o);
    var hoursSpan = o.hours_per_month_corpus_span != null ? Number(o.hours_per_month_corpus_span) : instSpan * minutes / 60;
    var dollarsSpan = o.dollars_per_month_corpus_span != null ? Number(o.dollars_per_month_corpus_span) : hoursSpan * rate();
    var matched = o.matched_message_ids || p.matched_message_ids || [];
    var first = monthYear(p.first_match), last = monthYear(p.last_match);
    var when = first && last ? (first === last ? " in " + first : " from " + first + " to " + last) : "";

    return backLink("#/", "All tasks") +
      '<p class="eyebrow">Task ' + (rankOf(id) || "") + " of " + (DATA.opportunities || []).length + "</p>" +
      "<h1>" + esc(o.title) + "</h1>" +
      '<p class="lead">' + esc(firstSentence(p.description)) + "</p>" +

      "<h2>What it costs</h2>" +
      '<p class="cost">Happens about <a href="#matched" data-anchor="matched">' + num(inst, 1) + " times a month</a>, takes about " +
      num(minutes, 0) + " minutes each time, so about " + num(hours, 1) + " hours and <strong>" + money(dollars) + " a month</strong>.</p>" +
      '<p class="quiet">Based on <a href="#matched" data-anchor="matched">' + int(matches) + " matching emails</a>" + esc(when) + ".</p>" +

      "<h2>What to do about it</h2>" +
      "<p>" + esc(o.automation || "") + "</p>" +

      "<h2>The proof</h2>" +
      '<p class="quiet">Word for word from the emails. Click one to open it with the passage highlighted.</p>' +
      proof(o.evidence) +

      (o.artifact_markdown
        ? '<h2 id="artifact">Ready-to-use document</h2><div class="artifact">' + markdown(o.artifact_markdown) + "</div>"
        : "") +

      '<details class="calc" id="calc"><summary>How this was calculated</summary>' +
      '<div class="calc-body">' +
      '<div class="equation">' +
      eqRow(int(matches) + " matching emails, " + windowText(p), num(active, 1) + " active months") +
      eqRow(int(matches) + " / " + num(active, 1) + " months", num(inst, 2) + " a month") +
      eqRow(num(inst, 2) + " a month x " + num(minutes, 0) + " minutes / 60", num(hours, 2) + " hours a month") +
      eqRow(num(hours, 2) + " hours x " + money(rate()) + " per hour", money(dollars) + " a month", true) +
      "</div>" +
      '<p class="quiet">Averaged over the full ' + num(DATA.span_months, 1) + " month archive instead: " + num(instSpan, 2) + " a month, " +
      num(hoursSpan, 2) + " hours, " + money(dollarsSpan) + " a month.</p>" +
      '<p class="quiet">The minutes per time (' + num(minutes, 0) + ") is an estimate. Everything else is counted by code.</p>" +
      "<h3>Which emails count</h3><p>" + esc(ruleText(p.match_rule)) + "</p>" +
      '<p class="quiet">Part of the process <a href="' + procHref(o.process_id) + '">' + esc(p.name || o.process_id) + "</a>.</p>" +
      '<h3 id="matched">The ' + int(matches) + " matching emails</h3>" +
      messageList(matched, matches) +
      "</div></details>" +
      footer();
  }

  function eqRow(lhs, rhs, total) {
    return '<div class="row' + (total ? " total" : "") + '"><span class="lhs">' + lhs + '</span><span class="rhs">' + rhs + "</span></div>";
  }

  function viewProcess(id) {
    var p = processById(id);
    if (!p) return notFound("process", id);
    var opps = rankedOpportunities().filter(function (o) { return o.process_id === id; });
    var actors = p.actors || [];
    var first = monthYear(p.first_match), last = monthYear(p.last_match);
    var when = first && last ? (first === last ? " in " + first : " from " + first + " to " + last) : "";

    return backLink("#/", "All tasks") +
      '<p class="eyebrow">Process</p>' +
      "<h1>" + esc(p.name) + "</h1>" +
      '<p class="lead">' + esc(p.description || "") + "</p>" +
      '<p class="quiet"><a href="#matched" data-anchor="matched">' + int(p.match_count) + " matching emails</a>" + esc(when) +
      ", about " + num(p.instances_per_month, 1) + " a month.</p>" +
      (p.stall ? "<h2>Where it gets stuck</h2><p>" + esc(p.stall) + "</p>" : "") +
      (actors.length ? "<h2>Who does it</h2><p>" + esc(actors.slice(0, 5).join(", ")) + (actors.length > 5 ? " and " + (actors.length - 5) + " others" : "") + "</p>" : "") +
      (opps.length
        ? "<h2>What to do about it</h2><ul class=\"plain\">" + opps.map(function (o) {
            return '<li><a href="' + oppHref(o.opportunity_id) + '">' + esc(o.title) + '</a> <span class="quiet-inline">' + moneyDown(o.dollars_per_month) + " a month</span></li>";
          }).join("") + "</ul>"
        : "") +
      "<h2>The proof</h2>" + proof(p.evidence) +
      '<details class="calc" id="calc"><summary>How this was matched</summary><div class="calc-body">' +
      "<p>" + esc(ruleText(p.match_rule)) + "</p>" +
      '<p class="quiet">Active window ' + windowText(p) + ", " + num(Math.max(1, Number(p.active_months) || 1), 1) + " months. " +
      num(corpusInstances(p, null), 2) + " a month if averaged over the full " + num(DATA.span_months, 1) + " month archive.</p>" +
      '<h3 id="matched">The ' + int(p.match_count) + " matching emails</h3>" +
      messageList(p.matched_message_ids, p.match_count) +
      "</div></details>" +
      footer();
  }

  function viewMessage(id, quote) {
    var m = meta(id);
    var head = backLink(recallBack(), "Back") +
      '<p class="eyebrow">Source email</p>' +
      '<h1 class="msg-subject">' + esc(m.subject) + "</h1>" +
      '<dl class="msg-meta">' +
      "<dt>From</dt><dd>" + esc(m.from) + "</dd>" +
      "<dt>Date</dt><dd>" + esc(m.date || "undated") + "</dd>" +
      (m.mailbox ? "<dt>Mailbox</dt><dd>" + esc(m.mailbox) + (m.folder ? " / " + esc(m.folder) : "") + "</dd>" : "") +
      '<dt>Id</dt><dd>' + esc(id) + ' <a href="messages/' + encodeURIComponent(id) + '.txt" target="_blank" rel="noopener">raw file</a></dd>' +
      "</dl>";
    var body = '<div id="msg-body"><p class="loading">Loading message.</p></div>';
    setTimeout(function () { loadMessage(id, quote); }, 0);
    return head + body;
  }

  function loadMessage(id, quote) {
    var box = document.getElementById("msg-body");
    if (!box) return;
    fetch("messages/" + encodeURIComponent(id) + ".txt", { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error(r.status + " " + r.statusText); return r.text(); })
      .then(function (text) {
        var result = highlight(text, quote);
        var hint = "";
        if (quote) {
          hint = result.found
            ? '<p class="msg-hint">The highlighted passage is the quote this claim rests on.</p>'
            : '<p class="msg-hint miss">The quote was not found verbatim in this raw file. Quote: ' + esc(quote) + "</p>";
        }
        box.innerHTML = hint + '<pre class="raw">' + result.html + "</pre>";
        var mark = box.querySelector("mark");
        if (mark && mark.scrollIntoView) mark.scrollIntoView({ block: "center" });
      })
      .catch(function (err) {
        box.innerHTML = '<p class="msg-hint miss">Could not load messages/' + esc(id) + ".txt (" + esc(err.message) + "). The raw file was not copied at build time.</p>";
      });
  }

  // Find the quote in the raw text allowing any whitespace run to match any other.
  function highlight(text, quote) {
    if (!quote) return { html: esc(text), found: false };
    var tokens = quote.trim().split(/\s+/).filter(Boolean);
    if (!tokens.length) return { html: esc(text), found: false };
    var pattern = tokens.map(function (t) { return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }).join("\\s+");
    var re;
    try { re = new RegExp(pattern); } catch (e) { return { html: esc(text), found: false }; }
    var m = re.exec(text);
    if (!m) {
      // Retry case-insensitively, then on the first 40 characters, so a slightly
      // trimmed quote still lands near the right place.
      try { re = new RegExp(pattern, "i"); m = re.exec(text); } catch (e) { m = null; }
      if (!m && tokens.length > 6) {
        var shortPattern = tokens.slice(0, 6).map(function (t) { return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }).join("\\s+");
        try { re = new RegExp(shortPattern, "i"); m = re.exec(text); } catch (e) { m = null; }
      }
      if (!m) return { html: esc(text), found: false };
    }
    var start = m.index, end = m.index + m[0].length;
    return {
      html: esc(text.slice(0, start)) + "<mark>" + esc(text.slice(start, end)) + "</mark>" + esc(text.slice(end)),
      found: true
    };
  }

  function notFound(kind, id) {
    return backLink("#/", "All tasks") + "<h1>Not found</h1><p>No " + esc(kind) + " with id " + esc(id) + ".</p>";
  }

  // ---------------------------------------------------------------- routing

  function rememberBack() {
    try { sessionStorage.setItem("back", location.hash || "#/"); } catch (e) { /* ignore */ }
  }
  function recallBack() {
    try { return sessionStorage.getItem("back") || "#/"; } catch (e) { return "#/"; }
  }

  function parseHash() {
    var h = location.hash || "#/";
    if (h.charAt(0) === "#") h = h.slice(1);
    var anchor = "";
    var ai = h.indexOf("#");
    if (ai >= 0) { anchor = h.slice(ai + 1); h = h.slice(0, ai); }
    var q = "";
    var qi = h.indexOf("?");
    if (qi >= 0) { q = h.slice(qi + 1); h = h.slice(0, qi); }
    var parts = h.split("/").filter(Boolean);
    var params = {};
    q.split("&").forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf("=");
      var k = i >= 0 ? kv.slice(0, i) : kv;
      var v = i >= 0 ? kv.slice(i + 1) : "";
      try { params[decodeURIComponent(k)] = decodeURIComponent(v.replace(/\+/g, " ")); } catch (e) { params[k] = v; }
    });
    return { parts: parts, params: params, anchor: anchor };
  }

  // Scroll to an element, opening any collapsed details around it first.
  function reveal(anchorId) {
    var el = document.getElementById(anchorId);
    if (!el) return false;
    var d = el.closest ? el.closest("details") : null;
    if (d) d.open = true;
    el.scrollIntoView({ block: "start" });
    return true;
  }

  function render() {
    if (!DATA) return;
    var r = parseHash();
    var kind = r.parts[0] || "";
    var id = r.parts[1] ? safeDecode(r.parts[1]) : "";
    var html;
    if (kind === "opportunity" && id) html = viewOpportunity(id);
    else if (kind === "process" && id) html = viewProcess(id);
    else if (kind === "message" && id) {
      var quote = r.params.q || recallQuote(id);
      html = viewMessage(id, quote);
    } else html = viewHome();
    app.innerHTML = html;
    app.className = "app" + (kind === "message" ? " wide" : "");
    if (kind !== "message") rememberBack();
    if (!(r.anchor && reveal(r.anchor)) && kind !== "message") window.scrollTo(0, 0);
    document.title = titleFor(kind, id);
  }

  function safeDecode(s) { try { return decodeURIComponent(s); } catch (e) { return s; } }

  function titleFor(kind, id) {
    var base = "Where Enron loses time";
    if (kind === "opportunity") { var o = opportunityById(id); return o ? o.title + " | " + base : base; }
    if (kind === "process") { var p = processById(id); return p ? p.name + " | " + base : base; }
    if (kind === "message") return "Email " + id + " | " + base;
    return base;
  }

  document.addEventListener("click", function (ev) {
    if (!ev.target.closest) return;
    // In-page anchors inside a routed page: open the details and scroll, keep the route.
    var local = ev.target.closest("a[data-anchor]");
    if (local) {
      ev.preventDefault();
      reveal(local.getAttribute("data-anchor"));
      return;
    }
    // Store the quote on click so the message view has it even if the hash is edited.
    var a = ev.target.closest("a[data-quote-id]");
    if (!a) return;
    var href = a.getAttribute("href") || "";
    var qi = href.indexOf("?q=");
    if (qi >= 0) rememberQuote(a.getAttribute("data-quote-id"), safeDecode(href.slice(qi + 3)));
  });

  window.addEventListener("hashchange", render);

  fetch("data.json", { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw new Error(r.status + " " + r.statusText); return r.json(); })
    .then(function (d) { DATA = d; render(); })
    .catch(function (err) {
      app.innerHTML = '<p class="loading">Could not load data.json (' + esc(err.message) + "). Run `uv run python -m pipeline.build` and serve run/dashboard.</p>";
    });
})();
