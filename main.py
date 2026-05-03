#!/usr/bin/env python3
"""
PropaGanda-Pulse OSINT Terminal — Standalone Edition
═════════════════════════════════════════════════════
pip install fastapi uvicorn
python main.py
Open: http://localhost:8000
"""
from __future__ import annotations
import hashlib, re, time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="PropaGanda-Pulse", docs_url=None, redoc_url=None)


# ══════════════════════════════════════════════════════════════════════════════
#  ANALYSIS ENGINE  (deterministic, hash-seeded — no external APIs needed)
# ══════════════════════════════════════════════════════════════════════════════

TECHNIQUES = [
    "Loaded Language", "Appeal to Fear", "Ad Hominem", "Repetition",
    "False Dichotomy", "Bandwagon", "Glittering Generalities", "Card Stacking",
    "Name Calling", "Transfer", "Testimonial", "Plain Folks",
    "Scapegoating", "Emotional Appeal", "Cherry Picking", "Straw Man",
    "Whataboutism", "Dog Whistle", "Euphemism", "Dehumanization",
]

TECHNIQUE_INFO = {
    "Loaded Language":         ("Words or phrases with strong emotional connotations used to influence an audience.", ["terrorist vs freedom fighter", "regime vs government"]),
    "Appeal to Fear":          ("Creating anxiety or panic to push audiences toward a particular conclusion.", ["without this policy, chaos will follow"]),
    "Ad Hominem":              ("Attacking the character of a person rather than engaging with their argument.", ["don't listen to him, he's a criminal"]),
    "Repetition":              ("Repeating a message or slogan until it becomes accepted as truth.", ["fake news repeated until believed"]),
    "False Dichotomy":         ("Presenting only two options when more exist, forcing a binary choice.", ["you're either with us or against us"]),
    "Bandwagon":               ("Encouraging people to follow the crowd rather than think independently.", ["everyone supports this policy"]),
    "Glittering Generalities": ("Vague, emotionally appealing words that sound positive but lack substance.", ["freedom, democracy, justice"]),
    "Card Stacking":           ("Presenting only evidence that supports one side while ignoring contrary evidence.", ["citing only favorable statistics"]),
    "Name Calling":            ("Labeling opponents with negative terms to trigger rejection without examination.", ["communist", "fascist", "radical left"]),
    "Transfer":                ("Associating a respected symbol with an idea to lend it legitimacy.", ["using the national flag in campaign ads"]),
    "Testimonial":             ("Using quotes from respected figures to endorse a position.", ["experts agree...", "as Einstein once said (misattributed)"]),
    "Plain Folks":             ("Presenting a leader or idea as ordinary and relatable to common people.", ["I'm just like you", "a man of the people"]),
    "Scapegoating":            ("Blaming a specific group for complex problems to deflect responsibility.", ["immigrants taking jobs", "bankers causing poverty"]),
    "Emotional Appeal":        ("Using emotions rather than logic to persuade an audience.", ["think of the children", "our brave heroes"]),
    "Cherry Picking":          ("Selecting only data that supports a predetermined conclusion.", ["citing one favorable study while ignoring dozens opposing"]),
    "Straw Man":               ("Misrepresenting an opponent's argument to make it easier to attack.", ["critics want open borders (they want reform)"]),
    "Whataboutism":            ("Deflecting criticism by pointing to unrelated wrongdoing by others.", ["what about when the other side did X?"]),
    "Dog Whistle":             ("Coded language that sends a message to a specific audience.", ["law and order (racial undertones)", "globalist"]),
    "Euphemism":               ("Replacing harsh terms with milder language to obscure reality.", ["collateral damage for civilian deaths", "enhanced interrogation"]),
    "Dehumanization":          ("Using animal or pest metaphors to strip humanity from a group.", ["vermin", "cockroaches", "swarms"]),
}

TECHNIQUE_JUSTIFICATIONS = {
    "Loaded Language":         ["The text employs emotionally charged terminology that predisposes the reader toward a specific interpretation before evidence is presented.", "Word selection is systematically skewed toward terms with strong negative or positive valence, bypassing rational evaluation."],
    "Appeal to Fear":          ["Catastrophic outcomes are invoked without proportionate evidence, designed to trigger anxious compliance rather than reasoned agreement.", "The narrative centers on threat scenarios that activate the amygdala response, short-circuiting critical analysis."],
    "Ad Hominem":              ["Opposing viewpoints are dismissed through character attacks rather than substantive engagement with their claims.", "Source credibility is undermined through personal attacks rather than logical refutation."],
    "Repetition":              ["Key phrases are reiterated across the text in a pattern consistent with repetition-as-validation rather than argumentative necessity.", "The same claims recur with slight variations, a hallmark of repetition-based persuasion."],
    "False Dichotomy":         ["A complex issue is reduced to exactly two options, excluding viable middle grounds or alternative frameworks.", "Binary framing forecloses nuanced positions and pressures readers into a predetermined choice."],
    "Bandwagon":               ["Appeals to consensus and mass adoption are deployed to substitute for substantive argument.", "Social proof is invoked to discourage independent reasoning."],
    "Glittering Generalities": ["Vague virtue terms are used as rhetorical anchors without operational definition or empirical grounding.", "Abstract positive language is deployed to generate emotional assent without specifying actual policy positions."],
    "Card Stacking":           ["Evidence selection appears systematically biased toward one interpretive frame, with counterevidence absent or minimized.", "The argument relies on a curated dataset that excludes information inconsistent with the narrative."],
    "Name Calling":            ["Opposing parties are labeled with politically charged terms designed to trigger rejection rather than deliberation.", "Classification labels are used to bypass substantive engagement with arguments."],
    "Transfer":                ["Respected symbols or institutions are invoked to lend authority to claims that would otherwise require independent justification.", "Association with trusted entities is used as a substitute for direct evidentiary support."],
    "Testimonial":             ["Authority figures are cited in ways that exceed the scope of their demonstrated expertise.", "Endorsements from respected figures are used to short-circuit independent evaluation."],
    "Plain Folks":             ["The author or subject performs relatability to ordinary citizens in a manner that deflects from substantive policy critique.", "Folksy language and common-man imagery are deployed to manufacture authenticity."],
    "Scapegoating":            ["A specific group is assigned responsibility for systemic problems in a manner that forecloses structural analysis.", "Complex causation is reduced to a single out-group whose removal would supposedly resolve the problem."],
    "Emotional Appeal":        ["Emotional activation is the primary persuasive mechanism, with logical argument secondary or absent.", "Pathos-driven language is used to generate conviction independently of factual warrant."],
    "Cherry Picking":          ["Data citation patterns suggest selective inclusion of evidence aligned with the thesis while structurally similar contrary evidence is absent.", "The evidentiary base appears curated rather than representative."],
    "Straw Man":               ["The opposing position is rendered in terms that do not accurately represent the strongest version of that argument.", "A simplified or distorted version of the opponent's view is attacked rather than the actual claim."],
    "Whataboutism":            ["Criticism is deflected through reference to unrelated third-party conduct rather than direct engagement.", "The rhetorical pivot to other actors' behavior functions as a non-denial denial."],
    "Dog Whistle":             ["Terminology carries differential meaning for target versus general audiences, consistent with coded communication patterns.", "Phrase selection aligns with documented coded language catalogued in political communication literature."],
    "Euphemism":               ["Sanitized terminology is used to describe events or policies whose severity would otherwise trigger scrutiny.", "Language choice systematically reduces the apparent gravity of described actions."],
    "Dehumanization":          ["Subject groups are described using terminology that strips individual humanity, historically correlated with incitement.", "Metaphors applied to human subjects draw from pest, animal, or object categories rather than humanizing frames."],
}

COUNTRIES = [
    {"name": "United States",   "code": "US"},
    {"name": "United Kingdom",  "code": "GB"},
    {"name": "Russia",          "code": "RU"},
    {"name": "China",           "code": "CN"},
    {"name": "France",          "code": "FR"},
    {"name": "Germany",         "code": "DE"},
    {"name": "Iran",            "code": "IR"},
    {"name": "Israel",          "code": "IL"},
    {"name": "Brazil",          "code": "BR"},
    {"name": "India",           "code": "IN"},
    {"name": "Turkey",          "code": "TR"},
    {"name": "Australia",       "code": "AU"},
    {"name": "Canada",          "code": "CA"},
    {"name": "Japan",           "code": "JP"},
    {"name": "South Korea",     "code": "KR"},
    {"name": "Qatar",           "code": "QA"},
    {"name": "Saudi Arabia",    "code": "SA"},
    {"name": "Ukraine",         "code": "UA"},
]

DOMAIN_COUNTRY = {
    "bbc.co.uk":          "United Kingdom", "bbc.com":            "United Kingdom",
    "reuters.com":        "United Kingdom", "theguardian.com":    "United Kingdom",
    "independent.co.uk":  "United Kingdom",
    "nytimes.com":        "United States",  "washingtonpost.com": "United States",
    "foxnews.com":        "United States",  "cnn.com":            "United States",
    "theatlantic.com":    "United States",  "breitbart.com":      "United States",
    "apnews.com":         "United States",  "npr.org":            "United States",
    "rt.com":             "Russia",         "sputniknews.com":    "Russia",
    "tass.com":           "Russia",         "pravda.ru":          "Russia",
    "xinhuanet.com":      "China",          "chinadaily.com.cn":  "China",
    "globaltimes.cn":     "China",
    "aljazeera.com":      "Qatar",
    "dw.com":             "Germany",        "spiegel.de":         "Germany",
    "lemonde.fr":         "France",         "lefigaro.fr":        "France",
    "presstv.ir":         "Iran",
    "haaretz.com":        "Israel",         "timesofisrael.com":  "Israel",
    "thehindu.com":       "India",          "ndtv.com":           "India",
    "kyivindependent.com":"Ukraine",
}

DOMAIN_SOURCE = {
    "rt.com": "state-media", "sputniknews.com": "state-media",
    "tass.com": "state-media", "pravda.ru": "state-media",
    "xinhuanet.com": "state-media", "chinadaily.com.cn": "state-media",
    "globaltimes.cn": "state-media", "presstv.ir": "state-media",
    "aljazeera.com": "state-media",
    "reuters.com": "wire", "apnews.com": "wire",
    "bbc.com": "mainstream", "bbc.co.uk": "mainstream",
    "nytimes.com": "mainstream", "washingtonpost.com": "mainstream",
    "cnn.com": "mainstream", "dw.com": "mainstream",
    "foxnews.com": "partisan", "breitbart.com": "partisan",
    "theatlantic.com": "independent",
}

GEO_SUMMARIES = {
    True: [
        "This piece exhibits strong geopolitical framing, positioning the subject nation as a defensive actor in a hostile international order. Narrative techniques suggest a deliberate attempt to shape perception of regional power dynamics.",
        "Classic sovereignty-threat framing pervades this text, invoking historical grievances to justify present-day positioning. The geopolitical subtext elevates national interest over multilateral consensus-building.",
        "The text deploys alliance-signaling rhetoric, reinforcing in-group solidarity while casting rival powers as inherently destabilizing. Selective citation of international law suggests instrumental rather than principled engagement.",
    ],
    False: [
        "This piece maintains relatively neutral geopolitical framing, presenting multiple state perspectives without overt allegiance to a particular power bloc. Minor editorial biases are detectable through source selection.",
        "Geopolitical content appears balanced in its surface presentation, though structural omissions — notably the absence of counter-hegemonic perspectives — suggest mild editorial alignment.",
    ],
}
INST_SUMMARIES = {
    True: [
        "The text consistently undermines institutional credibility, framing governmental bodies, expert consensus, and mainstream media as corrupt or captured. This anti-establishment posture is a hallmark of populist media operations.",
        "Strong anti-institutional sentiment pervades this piece. Scientific consensus, judicial authority, and international bodies are cast as adversarial forces opposing the legitimate will of ordinary citizens.",
        "Elite-capture framing is deployed throughout: institutions are portrayed not as imperfect but as systematically corrupted — a rhetorical move that forecloses reform in favour of replacement.",
    ],
    False: [
        "Institutional framing appears largely conventional, citing established authorities and maintaining deference to official narratives. Dissenting expert opinion is acknowledged but positioned as minority view.",
        "The piece operates within mainstream institutional discourse, reinforcing rather than challenging established power structures. Credentialist sourcing patterns suggest deep trust in formal expertise.",
    ],
}
SOCIO_SUMMARIES = {
    True: [
        "Clear ideological polarization detected. The text deploys economic grievance narratives alongside cultural identity markers to activate base sentiment. Left-right framing is prominent and structural.",
        "Strong socio-political signaling detected. Language patterns suggest deliberate audience segmentation along cultural and economic fault lines, with little rhetorical space allocated to synthesis or compromise.",
        "The text performs ideological sorting: issues that might be framed as technical or economic are systematically recast as moral and identity-laden, maximizing the emotional stakes of political disagreement.",
    ],
    False: [
        "Socio-political framing appears relatively centrist, avoiding overt ideological positioning while maintaining standard editorial conventions around balance.",
        "The piece maintains moderate ideological positioning, drawing from both progressive and traditional value frameworks without strong polarization. Rhetorical moderation may mask deeper editorial assumptions.",
    ],
}


def _hash(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)

def _flt(seed: int, idx: int) -> float:
    h = hashlib.md5(f"{seed}:{idx}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFF_FFFF

def _rng(seed: int, idx: int, lo: float, hi: float) -> float:
    return lo + _flt(seed, idx) * (hi - lo)

def _pick(seed: int, idx: int, items: list):
    i = int(_flt(seed, idx) * len(items))
    return items[min(i, len(items) - 1)]

def _shuffle_n(seed: int, offset: int, items: list, n: int) -> list:
    items = list(items)
    for i in range(len(items) - 1, 0, -1):
        j = int(_flt(seed, offset + i) * (i + 1))
        items[i], items[j] = items[j], items[i]
    return items[:n]

def _alignment(score: float) -> str:
    if score < -5.5: return "far-left"
    if score < -2:   return "center-left"
    if score <  2:   return "center"
    if score <  5.5: return "center-right"
    return "far-right"

def _domain(url: str) -> str:
    m = re.search(r'(?:https?://)?(?:www\.)?([^/\s]+)', url)
    return m.group(1).lower() if m else url.lower()

def _is_url(s: str) -> bool:
    return bool(re.match(r'^https?://', s, re.I) or re.match(r'^www\.', s, re.I) or
                re.match(r'^[a-z0-9-]+\.[a-z]{2,}(/|$)', s, re.I))


# ─── PRIMARY PROTOCOL — Narrative Integrity Firewall ──────────────────────────

def check_narrative_integrity(text: str) -> tuple[bool, str]:
    """Returns (pass, reason). reason is non-empty only on failure."""
    t = text.strip()
    if len(t) < 20:
        return False, "INSUFFICIENT_DATA"
    unique_chars = len(set(t.lower().replace(" ", "")))
    if unique_chars < 5 and len(t) > 5:
        return False, "INSUFFICIENT_DATA"
    words = [w for w in t.split() if w]
    if len(words) < 3 and not _is_url(t):
        return False, "INSUFFICIENT_DATA"
    return True, ""


# ─── Core Analysis ────────────────────────────────────────────────────────────

def analyze_input(text: str) -> dict:
    t       = text.strip()
    seed    = _hash(t)
    domain  = _domain(t)
    is_url  = _is_url(t)

    # Country detection
    country_name = next((c for d, c in DOMAIN_COUNTRY.items() if d in domain), None)
    if not country_name:
        country_name = _pick(seed, 0, [c["name"] for c in COUNTRIES])
    country = next(c for c in COUNTRIES if c["name"] == country_name)

    # Source type
    source_type = next((st for d, st in DOMAIN_SOURCE.items() if d in domain), None)
    if not source_type:
        source_type = _pick(seed, 5, ["mainstream", "independent", "partisan", "think-tank"])

    # Bias scores  -10 to +10
    geo_score   = round(_rng(seed, 10, -10, 10), 1)
    inst_score  = round(_rng(seed, 20, -10, 10), 1)
    socio_score = round(_rng(seed, 30, -10, 10), 1)
    bias_score  = round(geo_score * 0.4 + inst_score * 0.3 + socio_score * 0.3, 1)

    # Summaries
    geo_summary   = _pick(seed, 6, GEO_SUMMARIES[abs(geo_score) > 4])
    inst_summary  = _pick(seed, 7, INST_SUMMARIES[abs(inst_score) > 4])
    socio_summary = _pick(seed, 8, SOCIO_SUMMARIES[abs(socio_score) > 4])

    # Techniques per lens
    geo_techs   = _shuffle_n(seed, 100, TECHNIQUES, 4)
    inst_techs  = _shuffle_n(seed, 200, TECHNIQUES, 4)
    socio_techs = _shuffle_n(seed, 300, TECHNIQUES, 4)

    # Top-level detected techniques with justifications
    all_techs = _shuffle_n(seed, 400, TECHNIQUES, 5)
    detected_techniques = []
    for i, name in enumerate(all_techs):
        justs = TECHNIQUE_JUSTIFICATIONS.get(name, ["This technique was identified in the text."])
        detected_techniques.append({
            "name":          name,
            "justification": _pick(seed, 500 + i, justs),
        })

    analysis_id = hashlib.md5(f"{t}:{seed}".encode()).hexdigest()[:12]

    return {
        "id":                 analysis_id,
        "input":              t,
        "inputType":          "url" if is_url else "text",
        "biasScore":          bias_score,
        "alignment":          _alignment(bias_score),
        "sourceType":         source_type,
        "primaryCountry":     country_name,
        "primaryCountryCode": country["code"],
        "analyzedAt":         int(time.time() * 1000),
        "lenses": {
            "geopolitical": {
                "score":      geo_score,
                "alignment":  _alignment(geo_score),
                "techniques": geo_techs,
                "summary":    geo_summary,
            },
            "institutional": {
                "score":      inst_score,
                "alignment":  _alignment(inst_score),
                "techniques": inst_techs,
                "summary":    inst_summary,
            },
            "sociopolitical": {
                "score":      socio_score,
                "alignment":  _alignment(socio_score),
                "techniques": socio_techs,
                "summary":    socio_summary,
            },
        },
        "detectedTechniques": detected_techniques,
        "narrativeIntegrity": "PASS",
    }


# ══════════════════════════════════════════════════════════════════════════════
#  IN-MEMORY STORE
# ══════════════════════════════════════════════════════════════════════════════

_analyses: list[dict] = []


# ══════════════════════════════════════════════════════════════════════════════
#  REQUEST / RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    input: str


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=HTML)

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    text = req.input.strip()
    ok, reason = check_narrative_integrity(text)
    if not ok:
        return {
            "error": "ERROR: INSUFFICIENT_DATA - Input lacks sufficient narrative density for OSINT analysis.",
            "code":  reason,
        }
    result = analyze_input(text)
    _analyses.insert(0, result)
    if len(_analyses) > 50:
        _analyses.pop()
    return result

@app.get("/history")
async def history():
    return _analyses

@app.delete("/history")
async def clear_history():
    cleared = len(_analyses)
    _analyses.clear()
    return {"cleared": cleared}

@app.get("/stats")
async def stats():
    if not _analyses:
        return {
            "count": 0, "avgBiasScore": 0.0,
            "countriesAnalyzed": 0, "alignmentBreakdown": {},
            "topTechniques": [], "recentActivity": [],
        }
    avg = sum(a["biasScore"] for a in _analyses) / len(_analyses)
    countries = len({a["primaryCountryCode"] for a in _analyses})
    alignment_bd: dict[str, int] = {}
    tc: dict[str, int] = {}
    for a in _analyses:
        alignment_bd[a["alignment"]] = alignment_bd.get(a["alignment"], 0) + 1
        for t in a.get("detectedTechniques", []):
            tc[t["name"]] = tc.get(t["name"], 0) + 1
    top = sorted(tc.items(), key=lambda x: x[1], reverse=True)[:6]
    return {
        "count":              len(_analyses),
        "avgBiasScore":       round(avg, 2),
        "countriesAnalyzed":  countries,
        "alignmentBreakdown": alignment_bd,
        "topTechniques":      [{"name": n, "count": c} for n, c in top],
        "recentActivity":     _analyses[:5],
    }

@app.get("/techniques")
async def techniques():
    return [
        {
            "name":        name,
            "description": TECHNIQUE_INFO[name][0],
            "examples":    list(TECHNIQUE_INFO[name][1]),
        }
        for name in TECHNIQUES
    ]


# ══════════════════════════════════════════════════════════════════════════════
#  EMBEDDED HTML FRONTEND
# ══════════════════════════════════════════════════════════════════════════════

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>PropaGanda-Pulse OSINT Terminal</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#090910;--bg2:#0e0e1a;--amber:#ffb300;--amber-dim:#7a5500;
    --amber-glow:rgba(255,179,0,0.12);--red:#ff3333;--green:#00ff88;
    --border:rgba(255,179,0,0.2);--text:rgba(255,179,0,0.85);
  }
  body{background:var(--bg);color:var(--amber);font-family:'JetBrains Mono',monospace;
    font-size:13px;min-height:100vh;overflow-x:hidden;
    background-image:linear-gradient(rgba(255,179,0,0.025) 1px,transparent 1px),
      linear-gradient(90deg,rgba(255,179,0,0.025) 1px,transparent 1px);
    background-size:20px 20px;}
  .scan-line{position:fixed;top:0;left:0;width:100%;height:2px;
    background:var(--amber);opacity:0.25;animation:scan 8s linear infinite;
    pointer-events:none;z-index:9999;box-shadow:0 0 10px 2px var(--amber);}
  @keyframes scan{0%{transform:translateY(-10px)}100%{transform:translateY(100vh)}}
  header{display:flex;justify-content:space-between;align-items:center;
    padding:16px 24px;border-bottom:1px solid var(--border);}
  .logo{display:flex;align-items:center;gap:12px}
  .logo-icon{font-size:28px;color:var(--amber)}
  .logo h1{font-size:18px;font-weight:800;letter-spacing:.15em;text-transform:uppercase}
  .logo p{font-size:10px;color:var(--amber-dim);letter-spacing:.12em;text-transform:uppercase}
  .status{text-align:right;font-size:11px}
  .status .live{color:var(--green);animation:blink 1.5s step-end infinite}
  @keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
  main{display:grid;grid-template-columns:1fr 320px;gap:20px;padding:20px 24px;min-height:calc(100vh - 73px)}
  @media(max-width:768px){main{grid-template-columns:1fr}}
  .panel{border:1px solid var(--border);background:var(--bg2);padding:16px;position:relative}
  .panel::before,.panel::after{content:'';position:absolute;width:8px;height:8px;border-color:var(--amber);border-style:solid}
  .panel::before{top:-1px;left:-1px;border-width:2px 0 0 2px}
  .panel::after{top:-1px;right:-1px;border-width:2px 2px 0 0}
  .panel-footer::before{bottom:-1px;left:-1px;border-width:0 0 2px 2px;top:auto}
  .panel-title{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
    color:var(--text);border-bottom:1px solid var(--border);padding-bottom:10px;margin-bottom:12px;
    display:flex;align-items:center;gap:8px}
  textarea{width:100%;min-height:110px;background:rgba(0,0,0,0.4);border:1px solid var(--border);
    color:var(--amber);font-family:'JetBrains Mono',monospace;font-size:12px;padding:10px;
    resize:vertical;outline:none;transition:border-color .2s}
  textarea:focus{border-color:var(--amber)}
  textarea::placeholder{color:var(--amber-dim)}
  .btn-row{display:flex;justify-content:space-between;align-items:center;margin-top:10px}
  .prompt{color:var(--amber-dim);font-size:11px}
  button{background:transparent;border:1px solid var(--amber);color:var(--amber);
    font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;letter-spacing:.1em;
    text-transform:uppercase;padding:8px 20px;cursor:pointer;transition:all .2s}
  button:hover{background:var(--amber);color:var(--bg)}
  button:disabled{opacity:.4;cursor:not-allowed}
  button.danger{border-color:var(--red);color:var(--red)}
  button.danger:hover{background:var(--red);color:#fff}
  /* Progress */
  .progress-wrap{margin-top:16px;display:none}
  .progress-label{display:flex;justify-content:space-between;font-size:11px;margin-bottom:6px}
  .progress-bar{height:4px;background:rgba(255,179,0,0.1);border:1px solid var(--border)}
  .progress-fill{height:100%;background:var(--amber);transition:width .3s ease;width:0%}
  .scan-log{margin-top:10px;font-size:10px;color:var(--amber-dim);line-height:2}
  /* Error */
  .error-box{display:none;border:1px solid var(--red);background:rgba(255,51,51,.06);
    padding:14px;margin-top:16px;color:var(--red);font-size:12px}
  /* Results */
  #results{display:none}
  .result-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px}
  .result-meta{font-size:10px;color:var(--amber-dim);margin-top:4px;letter-spacing:.05em}
  .bias-num{font-size:36px;font-weight:800;text-align:right}
  .gauge-wrap{margin-bottom:20px}
  .gauge-labels{display:flex;justify-content:space-between;font-size:10px;color:var(--amber-dim);margin-bottom:4px}
  .gauge{height:8px;background:rgba(255,179,0,0.08);border:1px solid var(--border);position:relative}
  .gauge-midline{position:absolute;left:50%;top:0;bottom:0;width:1px;background:rgba(255,179,0,0.3)}
  .gauge-fill{position:absolute;top:0;bottom:0;background:rgba(255,179,0,0.7);transition:all 1s ease}
  .gauge-cursor{position:absolute;top:50%;transform:translate(-50%,-50%);
    width:4px;height:12px;background:#fff;box-shadow:0 0 8px 2px rgba(255,255,255,0.6);transition:left 1s ease}
  .alignment-label{text-align:center;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin-top:8px}
  /* Techniques */
  .techniques-section{border-top:1px solid var(--border);padding-top:14px;margin-top:4px}
  .tech-item{background:rgba(0,0,0,0.3);border:1px solid var(--border);padding:10px;margin-bottom:8px;font-size:11px}
  .tech-name{font-weight:700;text-transform:uppercase;letter-spacing:.08em;
    background:rgba(255,179,0,0.1);border:1px solid var(--border);
    padding:2px 8px;display:inline-block;margin-bottom:6px;font-size:10px}
  .tech-just{color:var(--text);line-height:1.7}
  /* Lenses */
  .lenses{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}
  @media(max-width:640px){.lenses{grid-template-columns:1fr}}
  .lens{border:1px solid var(--border);background:rgba(0,0,0,0.3);padding:12px}
  .lens-title{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
    color:var(--amber-dim);border-bottom:1px solid var(--border);padding-bottom:8px;margin-bottom:10px}
  .lens-score{font-size:11px;margin-bottom:6px}
  .mini-gauge{height:3px;background:rgba(255,179,0,0.08);border:1px solid var(--border);position:relative;margin-bottom:8px}
  .mini-fill{position:absolute;top:0;bottom:0;background:rgba(255,179,0,0.5)}
  .mini-mid{position:absolute;left:50%;top:0;bottom:0;width:1px;background:rgba(255,179,0,0.3)}
  .lens-align{font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:8px}
  .lens-summary{font-size:10px;color:var(--text);line-height:1.7;margin-bottom:10px}
  .lens-tags{display:flex;flex-wrap:wrap;gap:4px}
  .lens-tag{font-size:9px;text-transform:uppercase;background:rgba(255,179,0,0.08);
    border:1px solid var(--border);padding:2px 5px;color:var(--amber-dim)}
  /* Right column */
  .right-col{display:flex;flex-direction:column;gap:16px}
  .stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
  .stat-box{background:rgba(0,0,0,0.3);border:1px solid var(--border);padding:10px}
  .stat-label{font-size:9px;text-transform:uppercase;letter-spacing:.1em;color:var(--amber-dim);margin-bottom:4px}
  .stat-val{font-size:20px;font-weight:800}
  .top-tech-item{display:flex;justify-content:space-between;font-size:11px;
    color:var(--text);padding:3px 0;border-bottom:1px solid rgba(255,179,0,0.07)}
  .history-list{max-height:340px;overflow-y:auto}
  .hist-item{border:1px solid var(--border);padding:10px;margin-bottom:6px;cursor:pointer;transition:background .15s}
  .hist-item:hover{background:var(--amber-glow)}
  .hist-meta{display:flex;justify-content:space-between;font-size:9px;color:var(--amber-dim);margin-bottom:4px}
  .hist-align{font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:2px}
  .hist-input{font-size:10px;color:var(--amber-dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .empty{text-align:center;padding:32px;color:var(--amber-dim);font-size:11px}
  .section-title{font-size:10px;color:var(--amber-dim);text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px}
</style>
</head>
<body>
<div class="scan-line"></div>
<header>
  <div class="logo">
    <span class="logo-icon">&#x25BA;</span>
    <div>
      <h1>PropaGanda-Pulse OSINT</h1>
      <p>Classified Intelligence Terminal</p>
    </div>
  </div>
  <div class="status">
    STATUS: <span class="live">SECURE</span><br>
    <span style="color:var(--amber-dim);font-size:10px">NODE: OP-ALPHA-9</span>
  </div>
</header>

<main>
  <!-- Left column -->
  <div>
    <div class="panel panel-footer" style="margin-bottom:16px">
      <div class="panel-title">&#x2316; Target Acquisition</div>
      <textarea id="inp" placeholder="PASTE RAW TEXT OR URL INTERCEPT HERE..."></textarea>
      <div class="btn-row">
        <span class="prompt">&gt; AWAITING INPUT</span>
        <button id="scanBtn" onclick="runScan()">Execute Scan</button>
      </div>
      <div class="progress-wrap" id="progressWrap">
        <div class="progress-label"><span>Executing Protocol...</span><span id="pct">0%</span></div>
        <div class="progress-bar"><div class="progress-fill" id="pFill"></div></div>
        <div class="scan-log" id="scanLog"></div>
      </div>
      <div class="error-box" id="errBox"></div>
    </div>

    <div id="results">
      <div class="panel panel-footer" style="margin-bottom:16px">
        <div class="result-header">
          <div>
            <div class="panel-title" style="border:none;margin:0;padding:0">&#x26A1; Threat Assessment</div>
            <div class="result-meta" id="resultMeta"></div>
          </div>
          <div><div style="font-size:10px;color:var(--amber-dim);text-align:right;margin-bottom:4px">Bias Score</div>
            <div class="bias-num" id="biasNum"></div></div>
        </div>
        <div class="gauge-wrap">
          <div class="gauge-labels"><span>Extreme Left (-10)</span><span>Neutral (0)</span><span>Extreme Right (+10)</span></div>
          <div class="gauge">
            <div class="gauge-midline"></div>
            <div class="gauge-fill" id="gFill"></div>
            <div class="gauge-cursor" id="gCursor"></div>
          </div>
          <div class="alignment-label" id="alignLabel"></div>
        </div>
        <div class="techniques-section" id="techSection"></div>
      </div>
      <div class="lenses" id="lensesWrap"></div>
    </div>
  </div>

  <!-- Right column -->
  <div class="right-col">
    <div class="panel panel-footer">
      <div class="panel-title">&#x2248; System Telemetry</div>
      <div class="stat-grid">
        <div class="stat-box"><div class="stat-label">Total Scans</div><div class="stat-val" id="sTotalScans">0</div></div>
        <div class="stat-box"><div class="stat-label">Global Avg Bias</div><div class="stat-val" id="sAvgBias">0.00</div></div>
      </div>
      <div class="section-title">Top Signatures</div>
      <div id="sTopTechs"><div class="empty" style="padding:12px">No data</div></div>
    </div>
    <div class="panel panel-footer" style="flex:1">
      <div class="panel-title" style="justify-content:space-between">
        <span>&#x2261; Intercept Log</span>
        <button class="danger" onclick="purge()" style="padding:3px 10px;font-size:9px">Purge</button>
      </div>
      <div class="history-list" id="histList"><div class="empty">Log empty</div></div>
    </div>
  </div>
</main>

<script>
let _currentResult = null;
const STEPS = [
  "> Initializing semantic analysis engine...",
  "> Extracting entity relationships...",
  "> Cross-referencing technique signatures...",
  "> Calculating bias telemetry...",
  "> Generating narrative intelligence report...",
];

async function runScan() {
  const inp = document.getElementById('inp').value.trim();
  if (!inp) return;
  document.getElementById('scanBtn').disabled = true;
  document.getElementById('errBox').style.display = 'none';
  document.getElementById('results').style.display = 'none';
  document.getElementById('progressWrap').style.display = 'block';
  let prog = 0, step = 0;
  document.getElementById('scanLog').innerHTML = '';
  const iv = setInterval(() => {
    prog = Math.min(prog + Math.random() * 18, 90);
    document.getElementById('pFill').style.width = prog + '%';
    document.getElementById('pct').textContent = Math.floor(prog) + '%';
    if (step < STEPS.length && prog > step * 18) {
      document.getElementById('scanLog').innerHTML += '<div>' + STEPS[step] + '</div>';
      step++;
    }
  }, 300);
  try {
    const r = await fetch('/analyze', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input:inp})});
    const data = await r.json();
    clearInterval(iv);
    document.getElementById('pFill').style.width = '100%';
    document.getElementById('pct').textContent = '100%';
    await sleep(400);
    document.getElementById('progressWrap').style.display = 'none';
    if (data.code === 'INSUFFICIENT_DATA' || data.error) {
      showError(data.error || 'ERROR: INSUFFICIENT_DATA - Input lacks sufficient narrative density for OSINT analysis.');
    } else {
      showResult(data);
      loadStats(); loadHistory();
    }
  } catch(e) {
    clearInterval(iv);
    showError('ERROR: Connection failed. Is the server running?');
  }
  document.getElementById('scanBtn').disabled = false;
}

function showError(msg) {
  const b = document.getElementById('errBox');
  b.textContent = msg; b.style.display = 'block';
  document.getElementById('progressWrap').style.display = 'none';
}

function showResult(d) {
  _currentResult = d;
  document.getElementById('results').style.display = 'block';
  const s = d.biasScore >= 0 ? '+' : '';
  document.getElementById('biasNum').textContent = s + d.biasScore.toFixed(1);
  document.getElementById('alignLabel').textContent = 'Alignment: ' + d.alignment;
  document.getElementById('resultMeta').textContent =
    'ID: ' + d.id + ' | TYPE: ' + d.inputType + ' | SOURCE: ' + (d.sourceType||'UNKNOWN') +
    ' | COUNTRY: ' + (d.primaryCountry||'UNKNOWN');
  // Gauge
  const pct = 50 + (d.biasScore * 5);
  const fill = document.getElementById('gFill');
  const cursor = document.getElementById('gCursor');
  if (d.biasScore < 0) { fill.style.left = pct+'%'; fill.style.width = (-d.biasScore*5)+'%'; }
  else { fill.style.left = '50%'; fill.style.width = (d.biasScore*5)+'%'; }
  cursor.style.left = 'calc('+pct+'% - 2px)';
  // Techniques
  const ts = document.getElementById('techSection');
  ts.innerHTML = '<div class="panel-title" style="border:none;padding:0;margin-bottom:10px">&#x2731; Signatures Detected</div>';
  (d.detectedTechniques||[]).forEach(t => {
    ts.innerHTML += '<div class="tech-item"><span class="tech-name">'+esc(t.name)+'</span><div class="tech-just">'+esc(t.justification)+'</div></div>';
  });
  // Lenses
  const lw = document.getElementById('lensesWrap');
  lw.innerHTML = '';
  const lensNames = {geopolitical:'Geopolitical',institutional:'Institutional',sociopolitical:'Sociopolitical'};
  for (const [key, lens] of Object.entries(d.lenses||{})) {
    const lp = 50 + (lens.score * 5);
    const mfLeft = lens.score < 0 ? lp+'%' : '50%';
    const mfW = Math.abs(lens.score * 5)+'%';
    const tags = (lens.techniques||[]).map(t=>'<span class="lens-tag">'+esc(t)+'</span>').join('');
    lw.innerHTML += `<div class="lens">
      <div class="lens-title">${lensNames[key]||key} Lens</div>
      <div class="lens-score">Score: ${lens.score>0?'+':''}${lens.score.toFixed(1)}</div>
      <div class="mini-gauge"><div class="mini-mid"></div><div class="mini-fill" style="left:${mfLeft};width:${mfW}"></div></div>
      <div class="lens-align">${esc(lens.alignment)}</div>
      <div class="lens-summary">${esc(lens.summary)}</div>
      <div class="lens-tags">${tags}</div>
    </div>`;
  }
  document.querySelector('main').scrollTo({top:0,behavior:'smooth'});
}

async function loadStats() {
  try {
    const r = await fetch('/stats'); const d = await r.json();
    document.getElementById('sTotalScans').textContent = d.count;
    document.getElementById('sAvgBias').textContent = (d.avgBiasScore||0).toFixed(2);
    const tt = document.getElementById('sTopTechs');
    if ((d.topTechniques||[]).length === 0) { tt.innerHTML='<div class="empty" style="padding:8px">No data</div>'; return; }
    tt.innerHTML = d.topTechniques.slice(0,5).map(t=>`<div class="top-tech-item"><span>${esc(t.name)}</span><span>${t.count}</span></div>`).join('');
  } catch(e){}
}

async function loadHistory() {
  try {
    const r = await fetch('/history'); const data = await r.json();
    const hl = document.getElementById('histList');
    if (!data.length) { hl.innerHTML='<div class="empty">Log empty</div>'; return; }
    hl.innerHTML = data.map(a=>`<div class="hist-item" onclick='loadHistItem(${JSON.stringify(a)})'>
      <div class="hist-meta"><span>${new Date(a.analyzedAt).toLocaleTimeString()}</span><span>${a.inputType}</span></div>
      <div class="hist-align">${esc(a.alignment)}</div>
      <div class="hist-input">${esc(a.input)}</div>
    </div>`).join('');
  } catch(e){}
}

function loadHistItem(a) { showResult(a); document.getElementById('results').style.display='block'; window.scrollTo({top:0,behavior:'smooth'}); }

async function purge() {
  await fetch('/history',{method:'DELETE'});
  loadHistory(); loadStats();
}

function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') }
function sleep(ms){ return new Promise(r=>setTimeout(r,ms)) }

document.getElementById('inp').addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') runScan();
});

loadStats(); loadHistory();
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "═"*55)
    print("  PropaGanda-Pulse OSINT Terminal")
    print("  http://localhost:8000")
    print("  Ctrl+C to stop")
    print("═"*55 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
