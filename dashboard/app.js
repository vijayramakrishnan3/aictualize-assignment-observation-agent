/* Observation dashboard. Plain JS, hash routing, no dependencies.
 *
 * Routes
 *   #/                          ranked opportunities
 *   #/opportunity/<id>          the math, rule, matched messages, evidence, artifact
 *   #/process/<id>              description, actors, stall, evidence, matched messages
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
  function int(v) { return num(v, 0); }
  function dateOnly(iso) {
    if (!iso) return "undated";
    return String(iso).slice(0, 10);
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
      if ((m = /^(#{1,6})\s+(.*)$/.exec(line))) {
        flushPara(); closeList();
        var lvl = m[1].length;
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
        // continuation of a list item
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

  function crumbs(parts) {
    var out = ['<a href="#/">Report</a>'];
    for (var i = 0; i < parts.length; i++) {
      out.push('<span class="sep">/</span>');
      out.push(parts[i].href ? '<a href="' + parts[i].href + '">' + esc(parts[i].text) + "</a>" : esc(parts[i].text));
    }
    return '<div class="crumbs">' + out.join("") + "</div>";
  }

  function ruleBlock(rule) {
    if (!rule) return '<p class="empty">No match rule recorded.</p>';
    var plain = [];
    if (rule.subject_regex) plain.push("subject matches /" + rule.subject_regex + "/");
    if (rule.body_any && rule.body_any.length) plain.push("body contains any of " + rule.body_any.map(function (k) { return '"' + k + '"'; }).join(", "));
    if (rule.from_any && rule.from_any.length) plain.push("sender is one of " + rule.from_any.join(", "));
    return '<pre class="rule">' + esc(JSON.stringify(rule, null, 2)) + "</pre>" +
      '<p class="rule-plain">' + (plain.length ? esc(plain.join("; ")) + ". Non-duplicate messages only. Code counts the matches." : "Empty rule, matches nothing.") + "</p>";
  }

  function evidenceList(evidence) {
    if (!evidence || !evidence.length) return '<p class="empty">No evidence survived validation.</p>';
    return evidence.map(function (ev) {
      var id = ev.message_id;
      var m = meta(id);
      var from = ev.from || m.from;
      var date = ev.date || m.date;
      var subject = ev.subject || m.subject;
      var href = msgHref(id, ev.quote);
      return '<blockquote class="evidence">' +
        '<p class="quote"><a href="' + href + '" data-quote-id="' + esc(id) + '">' + esc(ev.quote) + "</a></p>" +
        '<p class="cite"><a href="' + href + '" data-quote-id="' + esc(id) + '">' + esc(from) + ", " + esc(dateOnly(date)) + ", " + esc(subject) + "</a> " +
        "<code>" + esc(id) + "</code></p>" +
        "</blockquote>";
    }).join("");
  }

  function messageList(ids, total) {
    ids = ids || [];
    if (!ids.length) return '<p class="empty">No messages matched.</p>';
    var shown = ids.slice(0, MSG_LIMIT);
    var items = shown.map(function (id) {
      var m = meta(id);
      return "<li>" +
        '<span class="date">' + esc(dateOnly(m.date)) + "</span>" +
        '<span class="subject"><a href="' + msgHref(id) + '">' + esc(m.subject) + "</a></span>" +
        '<span class="from">' + esc(m.from) + "</span>" +
        '<span class="id"><a href="' + msgHref(id) + '">' + esc(id) + "</a></span>" +
        "</li>";
    }).join("");
    var note = "";
    var t = Number(total);
    if (isFinite(t) && t > shown.length) note = '<p class="small faint">Showing the first ' + int(shown.length) + " of " + int(t) + " matched messages.</p>";
    else if (ids.length > shown.length) note = '<p class="small faint">Showing the first ' + int(shown.length) + " of " + int(ids.length) + ".</p>";
    return '<ul class="msg-list">' + items + "</ul>" + note;
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
      var art = o.artifact_markdown
        ? '<a class="tag" href="' + href + '#artifact">' + esc(o.artifact_type || "artifact") + "</a>"
        : '<span class="tag none">none</span>';
      return "<tr>" +
        '<td class="rank">' + (i + 1) + "</td>" +
        '<td class="title"><a href="' + href + '">' + esc(o.title) + "</a></td>" +
        '<td class="proc"><a href="' + procHref(o.process_id) + '">' + esc(p.name || o.process_id) + "</a></td>" +
        '<td class="num"><a class="num" href="' + href + '">' + num(o.instances_per_month, 1) + "</a></td>" +
        '<td class="num"><a class="num" href="' + href + '">' + num(o.hours_per_month, 1) + "</a></td>" +
        '<td class="num"><a class="num" href="' + href + '">' + money(o.dollars_per_month) + "</a></td>" +
        '<td class="num running">' + money(running) + "</td>" +
        "<td>" + art + "</td>" +
        "</tr>";
    }).join("");

    var top = opps.length ? opps[0] : null;
    var hoursHref = top ? oppHref(top.opportunity_id) : "#/";

    return "" +
      '<header class="masthead">' +
      '<p class="kicker">Observation report</p>' +
      "<h1>" + esc(DATA.company || "Enron, four mailboxes") + "</h1>" +
      '<p class="sub">' + int(t.messages) + " messages read, " + int(t.unique) + " unique, over " + num(DATA.span_months, 1) + " months. " +
      "Every figure below links to the messages it came from.</p>" +
      '<div class="figures">' +
      figure("Hours per month", '<a href="' + hoursHref + '">' + num(t.hours_per_month, 0) + "</a>", "across " + opps.length + " opportunities") +
      figure("Dollars per month", '<a href="' + hoursHref + '">' + money(t.dollars_per_month) + "</a>", "at " + money(rate()) + " per hour, blended") +
      figure("Corpus span", num(DATA.span_months, 1), "months, first to last dated message") +
      figure("Artifact threshold", money(threshold()), "per month, drafted above this line") +
      "</div>" +
      '<div class="stats">' +
      "<span>Messages <b>" + int(t.messages) + "</b></span>" +
      "<span>Unique <b>" + int(t.unique) + "</b></span>" +
      "<span>Duplicates <b>" + int(t.duplicates) + "</b></span>" +
      "<span>Undated <b>" + int(t.undated) + "</b></span>" +
      "<span>Processes <b>" + (DATA.processes || []).length + "</b></span>" +
      "<span>Rate <b>" + money(rate()) + "/hr</b></span>" +
      (DATA.generated_at ? "<span>Computed <b>" + esc(String(DATA.generated_at).slice(0, 16).replace("T", " ")) + "</b></span>" : "") +
      "</div>" +
      "</header>" +
      "<h2>Opportunities, ranked by dollars per month</h2>" +
      "<table><thead><tr>" +
      "<th>#</th><th>Opportunity</th><th>Process</th>" +
      '<th class="num">Instances / mo</th><th class="num">Hours / mo</th><th class="num">Dollars / mo</th><th class="num">Running total</th><th>Artifact</th>' +
      "</tr></thead><tbody>" + rows + "</tbody>" +
      "<tfoot><tr><td colspan=\"4\" class=\"label\">Total</td>" +
      '<td class="num">' + num(t.hours_per_month, 1) + "</td>" +
      '<td class="num">' + money(t.dollars_per_month) + "</td>" +
      '<td class="num">' + money(running) + "</td><td></td></tr></tfoot>" +
      "</table>" +
      "<h2>Processes</h2>" +
      processTable() +
      '<p class="small muted" style="margin-top:32px">Method. Code parsed and deduplicated every message. A model proposed processes and quotes. ' +
      "Every quote was verified as an exact substring of its message. For each process the model proposed a match rule and code counted the messages that match it. " +
      "Instances per month = matches / span. Hours = instances x minutes saved / 60. Dollars = hours x " + money(rate()) + ". " +
      "Minutes saved per instance is a judgment, not a measurement.</p>";
  }

  function figure(label, value, note) {
    return '<div class="figure"><div class="label">' + esc(label) + '</div><div class="value">' + value + '</div><div class="note">' + esc(note) + "</div></div>";
  }

  function processTable() {
    var ps = DATA.processes || [];
    if (!ps.length) return '<p class="empty">No processes.</p>';
    var rows = ps.map(function (p) {
      var href = procHref(p.process_id);
      var opps = (DATA.opportunities || []).filter(function (o) { return o.process_id === p.process_id; });
      var dollars = opps.reduce(function (s, o) { return s + Number(o.dollars_per_month || 0); }, 0);
      return "<tr>" +
        '<td class="title"><a href="' + href + '">' + esc(p.name) + "</a></td>" +
        "<td>" + esc((p.actors || []).slice(0, 3).join(", ")) + ((p.actors || []).length > 3 ? " and " + ((p.actors || []).length - 3) + " more" : "") + "</td>" +
        '<td class="num"><a class="num" href="' + href + '">' + int(p.match_count) + "</a></td>" +
        '<td class="num"><a class="num" href="' + href + '">' + num(p.instances_per_month, 1) + "</a></td>" +
        '<td class="num">' + opps.length + "</td>" +
        '<td class="num">' + money(dollars) + "</td>" +
        "</tr>";
    }).join("");
    return "<table><thead><tr><th>Process</th><th>Actors</th>" +
      '<th class="num">Matched</th><th class="num">Instances / mo</th><th class="num">Opportunities</th><th class="num">Dollars / mo</th>' +
      "</tr></thead><tbody>" + rows + "</tbody></table>";
  }

  function viewOpportunity(id) {
    var o = opportunityById(id);
    if (!o) return notFound("opportunity", id);
    var p = processById(o.process_id) || {};
    var matches = Number(p.match_count || 0);
    var span = Number(DATA.span_months || 1);
    var minutes = Number(o.minutes_saved_per_instance || 0);
    var inst = Number(o.instances_per_month || 0);
    var hours = Number(o.hours_per_month || 0);
    var dollars = Number(o.dollars_per_month || 0);
    var r = rankOf(id);
    var above = dollars >= threshold();
    var matched = o.matched_message_ids || p.matched_message_ids || [];

    return crumbs([{ text: "Opportunity " + (r || "") }]) +
      '<p class="lede">' + esc(o.title) + "</p>" +
      '<p class="lede-sub">Rank ' + (r || "?") + " of " + (DATA.opportunities || []).length + ". Process " +
      '<a href="' + procHref(o.process_id) + '">' + esc(p.name || o.process_id) + "</a>. " +
      (o.artifact_type && o.artifact_type !== "none" ? "Artifact type " + esc(o.artifact_type) + ". " : "") +
      (above ? "Above" : "Below") + " the " + money(threshold()) + " threshold.</p>" +

      '<div class="two-col">' +
      "<div>" +
      "<h2>The math</h2>" +
      '<div class="equation">' +
      eqRow('<a href="' + procHref(o.process_id) + '#matched">' + int(matches) + " matched messages</a> / " + num(span, 2) + " months", num(inst, 2) + " per month") +
      eqRow(num(inst, 2) + " per month x " + num(minutes, 0) + " min saved / 60", num(hours, 2) + " hours per month") +
      eqRow(num(hours, 2) + " hours x " + money(rate()) + " per hour", money(dollars) + " per month", true) +
      "</div>" +
      '<p class="small muted" style="margin-top:10px">Matches are counted by code against the rule below. Minutes saved per instance (' + num(minutes, 0) + ") is the model's estimate and the one figure here with no ground truth.</p>" +
      "<h2>Match rule</h2>" + ruleBlock(p.match_rule) +
      "</div>" +
      "<div>" +
      "<h2>What to build</h2>" +
      "<p>" + esc(o.automation || "") + "</p>" +
      (o.rationale ? "<h3>Rationale</h3><p>" + esc(o.rationale) + "</p>" : "") +
      (p.stall ? "<h3>Where it stalls today</h3><p>" + esc(p.stall) + "</p>" : "") +
      "</div>" +
      "</div>" +

      "<h2>Evidence</h2>" +
      '<p class="small muted">Each quote is verbatim from the message it links to. Click one to open the raw message with the quote highlighted.</p>' +
      evidenceList(o.evidence) +

      (o.artifact_markdown
        ? '<h2 id="artifact">Artifact, ' + esc(o.artifact_type || "drafted") + "</h2>" +
          '<p class="small muted">Drafted from the evidence above. Meant to be usable the next morning without editing.</p>' +
          '<div class="artifact">' + markdown(o.artifact_markdown) + "</div>"
        : '<h2 id="artifact">Artifact</h2><p class="empty">None drafted. ' + (above ? "The drafter did not produce one." : "This opportunity is below the " + money(threshold()) + " per month threshold.") + "</p>") +

      '<h2 id="matched">Matched messages</h2>' +
      '<p class="small muted">Every non-duplicate message the rule matched. This is the frequency count, open to inspection.</p>' +
      messageList(matched, matches);
  }

  function eqRow(lhs, rhs, total) {
    return '<div class="row' + (total ? " total" : "") + '"><span class="lhs">' + lhs + '</span><span class="rhs">' + rhs + "</span></div>";
  }

  function viewProcess(id) {
    var p = processById(id);
    if (!p) return notFound("process", id);
    var opps = rankedOpportunities().filter(function (o) { return o.process_id === id; });
    var oppRows = opps.map(function (o) {
      return "<tr>" +
        '<td class="rank">' + rankOf(o.opportunity_id) + "</td>" +
        '<td class="title"><a href="' + oppHref(o.opportunity_id) + '">' + esc(o.title) + "</a></td>" +
        '<td class="num"><a class="num" href="' + oppHref(o.opportunity_id) + '">' + num(o.hours_per_month, 1) + "</a></td>" +
        '<td class="num"><a class="num" href="' + oppHref(o.opportunity_id) + '">' + money(o.dollars_per_month) + "</a></td>" +
        "</tr>";
    }).join("");

    return crumbs([{ text: "Process" }]) +
      '<p class="lede">' + esc(p.name) + "</p>" +
      '<p class="lede-sub">' + int(p.match_count) + " matched messages, " + num(p.instances_per_month, 1) + " per month over " + num(DATA.span_months, 1) + " months.</p>" +
      '<div class="two-col">' +
      "<div>" +
      "<h2>What happens</h2><p>" + esc(p.description || "") + "</p>" +
      (p.stall ? "<h3>Where it stalls</h3><p>" + esc(p.stall) + "</p>" : "") +
      "<h3>Who touches it</h3>" +
      ((p.actors || []).length ? '<div class="actors">' + p.actors.map(function (a) { return "<span>" + esc(a) + "</span>"; }).join("") + "</div>" : '<p class="empty">No actors listed.</p>') +
      "</div>" +
      "<div>" +
      "<h2>Match rule</h2>" + ruleBlock(p.match_rule) +
      "<h2>Opportunities</h2>" +
      (opps.length
        ? '<table><thead><tr><th>#</th><th>Opportunity</th><th class="num">Hours / mo</th><th class="num">Dollars / mo</th></tr></thead><tbody>' + oppRows + "</tbody></table>"
        : '<p class="empty">No opportunities attached to this process.</p>') +
      "</div>" +
      "</div>" +
      "<h2>Evidence</h2>" + evidenceList(p.evidence) +
      '<h2 id="matched">Matched messages</h2>' +
      messageList(p.matched_message_ids, p.match_count);
  }

  function viewMessage(id, quote) {
    var m = meta(id);
    var backHref = recallBack();
    var head = crumbs([{ text: "Message " + id }]) +
      '<a class="back" href="' + backHref + '">Back</a>' +
      '<p class="lede">' + esc(m.subject) + "</p>" +
      '<div class="msg-meta">' +
      '<div class="row">From <b>' + esc(m.from) + "</b></div>" +
      '<div class="row">Date <b>' + esc(m.date || "undated") + "</b></div>" +
      (m.mailbox ? '<div class="row">Mailbox <b>' + esc(m.mailbox) + (m.folder ? " / " + esc(m.folder) : "") + "</b></div>" : "") +
      '<div class="row">Id <b>' + esc(id) + '</b> <a class="small" href="messages/' + encodeURIComponent(id) + '.txt" target="_blank" rel="noopener">raw file</a></div>' +
      "</div>";
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
            ? '<p class="msg-hint">Highlighted the quote this claim rests on.</p>'
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
    return crumbs([{ text: "Not found" }]) + '<p class="lede">No ' + esc(kind) + " with id " + esc(id) + "</p>" + '<p><a href="#/">Back to the report</a></p>';
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
    if (kind !== "message") rememberBack();
    if (r.anchor) {
      var el = document.getElementById(r.anchor);
      if (el) el.scrollIntoView({ block: "start" });
    } else if (kind !== "message") {
      window.scrollTo(0, 0);
    }
    document.title = titleFor(kind, id);
  }

  function safeDecode(s) { try { return decodeURIComponent(s); } catch (e) { return s; } }

  function titleFor(kind, id) {
    var base = "Observation report";
    if (kind === "opportunity") { var o = opportunityById(id); return o ? o.title + " | " + base : base; }
    if (kind === "process") { var p = processById(id); return p ? p.name + " | " + base : base; }
    if (kind === "message") return "Message " + id + " | " + base;
    return base + " | " + (DATA.company || "");
  }

  // Store the quote on click so the message view has it even if the hash is edited.
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest ? ev.target.closest("a[data-quote-id]") : null;
    if (!a) return;
    var href = a.getAttribute("href") || "";
    var qi = href.indexOf("?q=");
    if (qi >= 0) rememberQuote(a.getAttribute("data-quote-id"), safeDecode(href.slice(qi + 3)));
  });

  window.addEventListener("hashchange", function () {
    // Anchor-only changes on the same route still re-render; cheap, and keeps state simple.
    render();
  });

  fetch("data.json", { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw new Error(r.status + " " + r.statusText); return r.json(); })
    .then(function (d) { DATA = d; render(); })
    .catch(function (err) {
      app.innerHTML = '<p class="loading">Could not load data.json (' + esc(err.message) + "). Run `uv run python -m pipeline.build` and serve run/dashboard.</p>";
    });
})();
