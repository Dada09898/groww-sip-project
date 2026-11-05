// Anonymous feedback from the MVP page: option taps and thumbs up/down.
// No message text and no personal data. Each event is one JSON line in Vercel Runtime Logs.
export default function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const b = req.body || {};
  const KINDS = ["option", "rating", "failed_demo_shown"];
  if (!KINDS.includes(b.kind)) return res.status(400).json({ error: "unknown kind" });
  console.log(JSON.stringify({
    event: "feedback",
    kind: b.kind,
    value: String(b.value ?? "").slice(0, 30),
    intent: String(b.intent ?? "").slice(0, 30),
    gated: typeof b.gated === "boolean" ? b.gated : undefined,
  }));
  return res.json({ ok: true });
}
