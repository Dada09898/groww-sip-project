// One LLM call for the MVP and the eval. Set in Vercel env vars / your shell:
//   LLM_PROVIDER=gemini   + GEMINI_API_KEY   (free tier, aistudio.google.com)
//   LLM_PROVIDER=anthropic + ANTHROPIC_API_KEY (paid)
// If LLM_PROVIDER is not set, whichever key exists is used (Anthropic first).
export function provider() {
  if (process.env.LLM_PROVIDER) return process.env.LLM_PROVIDER.toLowerCase();
  return process.env.ANTHROPIC_API_KEY ? "anthropic" : "gemini";
}

function parseJson(text) {
  const m = String(text).replace(/```json|```/g, "").match(/\{[\s\S]*\}/);
  if (!m) throw new Error("No JSON in model output");
  return JSON.parse(m[0]);
}

async function gemini(system, user, maxTokens, model) {
  const key = process.env.GEMINI_API_KEY;
  if (!key) throw new Error("GEMINI_API_KEY is not set");
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`;
  const body = {
    systemInstruction: { parts: [{ text: system }] },
    contents: [{ role: "user", parts: [{ text: user }] }],
    generationConfig: { maxOutputTokens: Math.max(maxTokens * 4, 2048), responseMimeType: "application/json" }
  };
  for (let attempt = 0; attempt < 3; attempt++) {
    const r = await fetch(url, { method: "POST",
      headers: { "content-type": "application/json", "x-goog-api-key": key }, body: JSON.stringify(body) });
    if (r.status === 429 || r.status >= 500) { await new Promise(s => setTimeout(s, 2000 * (attempt + 1))); continue; }
    if (!r.ok) throw new Error(`Gemini ${r.status}: ${(await r.text()).slice(0, 200)}`);
    const d = await r.json();
    const parts = d.candidates?.[0]?.content?.parts || [];
    return parts.filter(p => !p.thought).map(p => p.text || "").join("");
  }
  throw new Error("Gemini rate limit");
}

async function anthropic(system, user, maxTokens, model) {
  const r = await fetch("https://api.anthropic.com/v1/messages", { method: "POST",
    headers: { "content-type": "application/json", "x-api-key": process.env.ANTHROPIC_API_KEY,
               "anthropic-version": "2023-06-01" },
    body: JSON.stringify({ model, max_tokens: maxTokens, system, messages: [{ role: "user", content: user }] }) });
  if (!r.ok) throw new Error(`Anthropic ${r.status}: ${(await r.text()).slice(0, 200)}`);
  const d = await r.json();
  return d.content.filter(b => b.type === "text").map(b => b.text).join("");
}

// role: "main" (companion + checker) or "judge" (eval only)
export async function llmJson(system, user, maxTokens = 700, role = "main") {
  if (provider() === "gemini") {
    // GEMINI_MODEL may be a comma-separated list: if one model is busy (503) or out of quota (429),
    // the next one is tried. Free-tier availability changes during the day.
    const list = (role === "judge"
      ? (process.env.GEMINI_JUDGE_MODEL || "gemini-flash-latest")
      : (process.env.GEMINI_MODEL || "gemini-flash-latest")).split(",").map(m => m.trim()).filter(Boolean);
    let lastErr;
    for (const model of list) {
      try { return parseJson(await gemini(system, user, maxTokens, model)); }
      catch (e) { lastErr = e; if (!/rate limit/i.test(e.message)) throw e; }
    }
    throw lastErr;
  }
  const model = role === "judge"
    ? (process.env.JUDGE_MODEL || "claude-opus-5-5")
    : (process.env.ANTHROPIC_MODEL || "claude-sonnet-5-5");
  return parseJson(await anthropic(system, user, maxTokens, model));
}
