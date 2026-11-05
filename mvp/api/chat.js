import { COMPANION_PROMPT, CHECKER_PROMPT, FALLBACK } from "../lib/prompts.js";
import { checkGuard } from "../lib/guard.js";
import { llmJson } from "../lib/llm.js";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const { message = "", sip = {}, entry = "chat" } = req.body || {};
  if (!String(message).trim()) return res.status(400).json({ error: "Type what's on your mind." });

  const facts = `SIP FACTS (only use these): ${JSON.stringify(sip)}\nENTRY POINT: ${entry}\nUSER: ${String(message).slice(0, 1000)}`;
  const checks = { guard: null, checker: null };
  try {
    const draft = await llmJson(COMPANION_PROMPT, facts);
    const ALLOWED = ["returns_doubt","cash_crunch","payment_issue","trust","controls_confusion","wants_advice","other"];
    if (!ALLOWED.includes(draft.intent)) draft.intent = "other";   // eval found invented labels (e.g. returns_dump)
    const allText = [draft.reply, ...(draft.options || []).map(o => `${o.label}. ${o.meaning}`)].join("\n");

    const g = checkGuard(allText);
    checks.guard = g;
    if (!g.pass) return res.json({ ...FALLBACK, gated: true, gate_reason: "guard", draft_intent: draft.intent, checks });

    const verdict = await llmJson(CHECKER_PROMPT, `${facts}\n\nASSISTANT REPLY:\n${JSON.stringify(draft)}`, 300);
    checks.checker = verdict;
    if (!verdict.pass) return res.json({ ...FALLBACK, gated: true, gate_reason: "checker", draft_intent: draft.intent, checks });

    return res.json({ ...draft, gated: false, checks });
  } catch (e) {
    console.error(e);
    return res.json({ ...FALLBACK, gated: true, gate_reason: "error", checks: { error: String(e.message).slice(0, 200) } });
  }
}
