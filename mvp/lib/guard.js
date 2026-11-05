// Deterministic first line of defence. Runs on every draft before the LLM checker.
// Works sentence by sentence so a correct refusal ("I can't say which fund is better")
// or a reported claim ("a video said the market will crash") is not blocked by mistake.

// Sentences with these words are refusals, negations or reported speech.
const EXEMPT = /\b(can'?t|cannot|can not|unable|not able|won'?t|don'?t|do not|isn'?t|not|no one|nobody|never|said|says|saying|claims?|heard|whether)\b/i;

const RULES = [
  // Always blocked, even inside a refusal: the reply must never name these.
  { name: "names_amc_or_fund", always: true,
    rx: /\b(parag parikh|ppfas|nippon|quant|mirae|motilal|bandhan|uti|dsp|edelweiss|canara robeco|franklin|invesco|sundaram|aditya birla|navi|groww mutual fund)\b/i },
  { name: "names_bank_amc_fund", always: true,
    rx: /\b(hdfc|sbi|icici|axis|kotak|tata|idfc|baroda|lic)\b[\w\s]{0,20}\b(mutual fund|mf|fund|scheme|amc|bluechip|flexi ?cap|small ?cap|mid ?cap|large ?cap)\b/i },
  { name: "urgency_or_fomo", always: true,
    rx: /\b(miss out|act now|hurry|last chance|don'?t miss|you will regret|before it'?s too late|limited time|right now or)\b/i },
  // Blocked unless the sentence is a refusal / negation / reported speech.
  { name: "recommendation",
    rx: /\b(i|we) (would )?(recommend|suggest|advise)\b|\b(best|better|top|good) (funds?|schemes?|amcs?|category|categories)\b|\b(switch|move) (to|into) (a |an )?(different |another |better )?(fund|scheme|category)\b/i },
  { name: "directive",
    rx: /\byou (should|must|need to|have to) (stop|cancel|continue|invest|buy|sell|switch|redeem|keep|pause|skip)\b/i },
  { name: "prediction",
    rx: /\b(will|is going to|are going to|bound to) (definitely |surely |certainly |soon )?(recover|go up|rise|bounce back|give (good |better )?returns|crash|fall|double)\b|\bguarantee(d|s)?\b/i },
];

export function checkGuard(text = "") {
  const sentences = String(text).split(/(?<=[.!?।])\s+|\n+/).filter(Boolean);
  const hits = [];
  for (const s of sentences) {
    for (const r of RULES) {
      if (!r.rx.test(s)) continue;
      if (!r.always && EXEMPT.test(s)) continue;
      hits.push({ rule: r.name, sentence: s.slice(0, 160) });
    }
  }
  return { pass: hits.length === 0, hits };
}
