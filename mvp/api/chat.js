import { COMPANION_PROMPT, CHECKER_PROMPT, FALLBACK, ADVICE_REPLY } from "../lib/prompts.js";

// Clear requests for fund picks or a yes/no decision get a fixed answer (no AI call).
const ADVICE_PATTERNS = [
  /\b(which|kaun ?sa|konsa|kon sa|best|better|top|suggest|recommend)\b[^.?!\n]{0,40}\b(funds?|schemes?|stocks?|mf|small ?cap|mid ?cap|large ?cap|index)\b/i,
  /\bfund (ka )?naam\b/i,
  /\b(should i|kya mujhe|kya main)\b[^.?!\n]{0,30}\b(switch|shift)\b/i,
  /\b(yes or no|haan ya na|ha ya na|just tell me (to|whether))\b/i,
];
const HINGLISH = /\b(hai|kya|mujhe|karu|karun|bata|batao|kaunsa|konsa|nahi|paisa|paise|mera|meri|sakta|chahiye)\b/i;

// Same question + same SIP numbers -> reuse the checked answer for a few hours (saves free-tier quota).
const CACHE = new Map();
const CACHE_MS = 6 * 60 * 60 * 1000;
// Light limit per visitor so one tester can't use up the whole free quota.
const HITS = new Map();
const LIMIT = 20, WINDOW_MS = 10 * 60 * 1000;
import { checkGuard } from "../lib/guard.js";
import { llmJson } from "../lib/llm.js";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const { message = "", sip = {}, entry = "chat", history = [] } = req.body || {};
  const t0 = Date.now();
  const ip = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim() || "unknown";
  const now = Date.now();
  const hits = (HITS.get(ip) || []).filter(t => now - t < WINDOW_MS);
  if (hits.length >= LIMIT) return res.status(429).json({ error: "You've asked a lot in a short time. Please try again in a few minutes." });
  hits.push(now); HITS.set(ip, hits);
  if (HITS.size > 5000) HITS.clear();
  if (!String(message).trim()) return res.status(400).json({ error: "Type what's on your mind." });

  // last few turns, so a follow-up like "aur pause kitne mahine?" makes sense
  const past = (Array.isArray(history) ? history : []).slice(-4)
    .filter(h => h && (h.role === "user" || h.role === "assistant"))
    .map(h => `${h.role === "user" ? "USER" : "YOU"}: ${String(h.text || "").slice(0, 300)}`).join("\n");
  const facts = `SIP FACTS (only use these): ${JSON.stringify(sip)}\nENTRY POINT: ${String(entry).slice(0, 40)}\n` +
    (past ? `EARLIER IN THIS CONVERSATION (context only, do not repeat it):\n${past}\n` : "") +
    `USER: ${String(message).slice(0, 1000)}`;
  // one anonymous log line per answer (no message text), visible in Vercel Runtime Logs
  const log = (intent, gated, gate_reason) => console.log(JSON.stringify({ event: "chat", entry: String(entry).slice(0, 40), intent, gated, gate_reason, ms: Date.now() - t0, turns: past ? past.split("\n").length : 0 }));
  const checks = { guard: null, checker: null };

  if (ADVICE_PATTERNS.some(r => r.test(String(message)))) {
    log("wants_advice", false, "advice_rule");
    return res.json({ intent: "wants_advice", reply: HINGLISH.test(String(message)) ? ADVICE_REPLY.hi : ADVICE_REPLY.en,
      options: FALLBACK.options, sources: FALLBACK.sources, confidence: 1, gated: false, checks: { route: "advice_rule" } });
  }

  const key = past ? null : JSON.stringify([String(message).trim().toLowerCase(), sip, String(entry)]);
  const hit = key && CACHE.get(key);
  if (hit && now - hit.at < CACHE_MS) { log(hit.body.intent, hit.body.gated, "cached"); return res.json({ ...hit.body, cached: true }); }
  const remember = body => { if (key && !body.gated) { if (CACHE.size > 300) CACHE.clear(); CACHE.set(key, { at: now, body }); } return body; };

  try {
    const draft = await llmJson(COMPANION_PROMPT, facts);
    const ALLOWED = ["returns_doubt","cash_crunch","payment_issue","trust","controls_confusion","wants_advice","other"];
    if (!ALLOWED.includes(draft.intent)) draft.intent = "other";   // eval found invented labels (e.g. returns_dump)
    const allText = [draft.reply, ...(draft.options || []).map(o => `${o.label}. ${o.meaning}`)].join("\n");

    const g = checkGuard(allText);
    checks.guard = g;
    if (!g.pass) { log(draft.intent, true, "guard"); return res.json({ ...FALLBACK, gated: true, gate_reason: "guard", draft_intent: draft.intent, checks }); }

    const verdict = await llmJson(CHECKER_PROMPT, `${facts}\n\nASSISTANT REPLY:\n${JSON.stringify(draft)}`, 300);
    checks.checker = verdict;
    if (!verdict.pass) { log(draft.intent, true, "checker"); return res.json({ ...FALLBACK, gated: true, gate_reason: "checker", draft_intent: draft.intent, checks }); }

    log(draft.intent, false, "");
    return res.json(remember({ ...draft, gated: false, checks }));
  } catch (e) {
    console.error(e);
    log("fallback", true, "error");
    return res.json({ ...FALLBACK, gated: true, gate_reason: "error", checks: { error: String(e.message).slice(0, 200) } });
  }
}
