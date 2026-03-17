# MarTech Stack Auditor — v1.0 Documentation

**Version:** 1.0
**Last Updated:** March 2026
**Repository:** github.com/di14mehdi8/martech-stack-auditor
**Deployment:** Streamlit Cloud
**LLM Provider:** Google Gemini (gemini-3.1-flash-lite-preview)

---

## 1. Overview

MarTech Stack Auditor is an AI-powered web application that analyzes a company's marketing technology stack across 6 critical dimensions and produces a structured, evidence-based audit report. Users manually enter metrics from their martech tools; 6 specialist AI agents analyze the data in parallel and a 7th agent synthesizes the findings into an executive summary. The output includes scored findings, visualizations, and a downloadable PDF report.

**Who it's for:** Marketing Operations teams, CMOs, and MarTech consultants auditing HubSpot + RudderStack + GTM + GA4 + Mailchimp stacks.

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   BROWSER (User)                    │
│              localhost:8501 / Streamlit Cloud       │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────┐
│              STREAMLIT APPLICATION                  │
│                    app.py                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Input Forms │  │ Report View  │  │ PDF Export│ │
│  │  (5 tool     │  │ (charts,     │  │ (ReportLab│ │
│  │   tabs)      │  │  scores,     │  │  + kaleido│ │
│  └──────┬───────┘  │  findings)   │  └───────────┘ │
│         │          └──────────────┘                │
└─────────┼───────────────────────────────────────────┘
          │ run_full_audit(data)
┌─────────▼───────────────────────────────────────────┐
│              AGENT ORCHESTRATOR                     │
│                   agents.py                         │
│                                                     │
│  ┌──────────┐ ┌───────────┐ ┌──────────────────┐   │
│  │ Agent 1  │ │ Agent 2   │ │ Agent 3          │   │
│  │ Data     │ │ Integration│ │ Performance      │   │
│  │ Quality  │ │ Health    │ │                  │   │
│  └──────────┘ └───────────┘ └──────────────────┘   │
│  ┌──────────┐ ┌───────────┐ ┌──────────────────┐   │
│  │ Agent 4  │ │ Agent 5   │ │ Agent 6          │   │
│  │Compliance│ │Optimization│ │ Redundancy       │   │
│  └──────────┘ └───────────┘ └──────────────────┘   │
│                      │                              │
│              ┌───────▼────────┐                     │
│              │   Agent 7      │                     │
│              │ Executive      │                     │
│              │ Summary        │                     │
│              └───────┬────────┘                     │
└──────────────────────┼──────────────────────────────┘
                       │ call_llm(prompt, system=SKILL_*)
┌──────────────────────▼──────────────────────────────┐
│           GOOGLE GEMINI API                         │
│       gemini-3.1-flash-lite-preview                 │
│    (free tier — 1,500 req/day, ~32K context)        │
└─────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
User fills 5 tool forms
        │
        ▼
collected_data dict (49 data points)
        │
        ▼
run_full_audit(collected_data)
        │
        ├──► agent_data_quality()   ──► SKILL_DATA_QUALITY system prompt
        ├──► agent_integration()    ──► SKILL_INTEGRATION system prompt
        ├──► agent_performance()    ──► SKILL_PERFORMANCE system prompt
        ├──► agent_compliance()     ──► SKILL_COMPLIANCE system prompt
        ├──► agent_optimization()   ──► SKILL_OPTIMIZATION system prompt
        ├──► agent_redundancy()     ──► SKILL_REDUNDANCY system prompt
        │
        ▼
All 6 outputs concatenated
        │
        ▼
executive_summary agent  ──► SKILL_EXECUTIVE_SUMMARY system prompt
        │
        ▼
results dict stored in st.session_state
        │
        ├──► Report UI (charts, score cards, findings tabs)
        └──► PDF generation (ReportLab + kaleido)
```

---

## 3. File Structure

```
martech-auditor/
│
├── app.py                  # Main Streamlit application (UI + PDF generation)
├── agents.py               # All AI agents, skills, and LLM caller
├── charts.py               # Plotly chart generators (radar, gauge, bar)
├── config.py               # Stack field definitions + industry benchmarks
├── requirements.txt        # Python dependencies
├── .env                    # Local environment variables (not committed)
└── martech-auditor-v1.md   # This document
```

---

## 4. Source Files — Detailed Reference

### 4.1 `app.py` — Application Layer

**Responsibilities:**
- Page configuration, global CSS, layout
- Session state management
- Input form rendering (5 tool tabs, 49 fields)
- Audit launch orchestration + progress display
- Report rendering (score cards, charts, tabs, findings)
- Generation timer display
- PDF report generation and download

**Key Functions:**

| Function | Purpose |
|---|---|
| `format_elapsed(seconds)` | Formats generation time as "X.Xs" or "Xm Xs" |
| `strip_markdown(text)` | Removes markdown syntax before PDF rendering |
| `PageNumCanvas` | ReportLab canvas subclass for "Page X of Y" footers |
| `generate_pdf_report(...)` | Builds full PDF into BytesIO — cover, metrics, charts, findings |
| `extract_score(text)` | Regex parser to extract numeric score from agent output |
| `score_color_class(score)` | Maps score to CSS color class (green/yellow/red) |
| `render_input_field(...)` | Renders the correct Streamlit widget for a field type |

**Session State Keys:**

| Key | Type | Purpose |
|---|---|---|
| `audit_results` | dict / None | Full results from `run_full_audit()` |
| `stack_data` | dict | Raw input data from the forms |
| `audit_running` | bool | Prevents concurrent audit runs |
| `generation_time` | float / None | Elapsed seconds for the audit run |
| `pdf_cache` | bytes / None | Cached PDF bytes to avoid regeneration |

---

### 4.2 `agents.py` — AI Agent Layer

**Responsibilities:**
- Google Gemini API client initialization
- Base system prompt (`MARKETING_SPECIALIST_SYSTEM_PROMPT`)
- 7 domain-specific skill constants (`SKILL_*`)
- 6 specialist agent functions + 1 orchestrator
- `call_llm()` wrapper
- `format_stack_data()` formatter

**LLM Call Pattern:**
```python
call_llm(prompt, system=SKILL_DATA_QUALITY)
# → GenerativeModel("gemini-3.1-flash-lite-preview", system_instruction=SKILL_*)
# → model.generate_content(prompt)
# → response.text
```

---

### 4.3 `charts.py` — Visualization Layer

| Function | Chart Type | Input | Output |
|---|---|---|---|
| `create_radar_chart(scores)` | Plotly Scatterpolar | score_map dict | Radar with benchmark overlay |
| `create_score_gauge(score, title)` | Plotly Indicator | float, str | Gauge 0-10 with color zones |
| `create_bar_comparison(data, benchmarks)` | Plotly Bar (horizontal) | two dicts | Grouped bar: actual vs. benchmark |

All charts use transparent backgrounds and are compatible with both Streamlit rendering and kaleido PNG export for PDF embedding.

---

### 4.4 `config.py` — Data Configuration Layer

**`STACK_DEFINITION`** — defines the 5 tools and their input fields:

| Tool Key | Tool Name | Field Count | Field Types |
|---|---|---|---|
| `crm` | HubSpot CRM | 11 | number, slider |
| `cdp` | RudderStack / Segment | 9 | number, slider, select |
| `tag_manager` | Google Tag Manager | 9 | number, slider, select |
| `analytics` | Google Analytics 4 | 10 | number, slider, select |
| `campaigns` | Mailchimp | 10 | number, slider, select |

**Total: 49 data points collected per audit.**

**`BENCHMARKS`** — industry benchmarks used by agents for comparison:

| Benchmark Key | Good | Average | Poor |
|---|---|---|---|
| `email_open_rate` | 25% | 20% | 15% |
| `email_click_rate` | 4% | 2.5% | 1.5% |
| `bounce_rate` | 40% | 55% | 70% |
| `identity_resolution` | 70% | 50% | 30% |
| `data_completeness_email` | 90% | 75% | 60% |
| `duplicate_rate` | 3% | 8% | 15% |
| `inactive_contacts` | 20% | 35% | 50% |

---

## 5. The Agent System

### 5.1 Architecture: Base Prompt + Skills

Every AI call in this system uses a two-layer prompt architecture:

```
Layer 1 — Base Identity (MARKETING_SPECIALIST_SYSTEM_PROMPT)
  Global persona, universal anti-hallucination rules, tone and terminology standards.
  Applied as fallback when no skill is specified.

Layer 2 — Domain Skill (SKILL_*)
  Deep domain expertise for a specific audit dimension.
  Replaces the base prompt for that agent's call.
  Adds domain-specific anti-hallucination rules and output structure requirements.
```

### 5.2 Agent Inventory

#### Agent 1 — Data Quality (`agent_data_quality`)
- **Skill:** `SKILL_DATA_QUALITY`
- **Domain:** CRM data hygiene, email deliverability, identity stitching, event governance
- **Analyzes:** Contact completeness, duplicate rate, data decay, event quality, identity resolution
- **Key Calculations:** Absolute missing contact counts, estimated duplicates, monthly events lost
- **Anti-hallucination:** Forces explicit arithmetic; limits benchmark citations to provided data or named industry sources
- **Output:** 5 scored sections + Data Gaps + Score rationale + DATA QUALITY SCORE /10

#### Agent 2 — Integration Health (`agent_integration`)
- **Skill:** `SKILL_INTEGRATION`
- **Domain:** MarTech integration architecture, CDP pipelines, GTM governance, GA4 data model
- **Analyzes:** CDP hub utilization, CRM↔ESP sync, GTM→GA4→CDP pipeline, BigQuery export, top 3 data gaps
- **Key Calculations:** Sync coverage ratio (subscribers ÷ contacts), CDP integration surface coverage, estimated data loss
- **Anti-hallucination:** Does not assert integrations exist unless data supports it; cites specific fields for every conclusion
- **Output:** 5 scored sections + Data Gaps + Score rationale + INTEGRATION HEALTH SCORE /10

#### Agent 3 — Performance (`agent_performance`)
- **Skill:** `SKILL_PERFORMANCE`
- **Domain:** Email performance, web analytics, pipeline metrics, campaign velocity, audience utilization
- **Analyzes:** CTOR, bounce rate, pipeline value, automation coverage, segment utilization
- **Key Calculations:** CTOR = click_rate ÷ open_rate; pipeline value = deals × avg_value; subscriber-to-contact ratio
- **Anti-hallucination:** Shows all arithmetic; flags Apple MPP open rate inflation; no revenue inference beyond provided data
- **Output:** 5 scored sections + Data Gaps + Score rationale + PERFORMANCE SCORE /10

#### Agent 4 — Compliance (`agent_compliance`)
- **Skill:** `SKILL_COMPLIANCE`
- **Domain:** GDPR, CCPA/CPRA, CAN-SPAM, Google Consent Mode v2, PII governance
- **Analyzes:** Consent management, PII controls, data retention, data minimization, tag risk, email compliance
- **Key Calculations:** Custom HTML tag % of total tags, unsubscribe rate vs. Google/Yahoo 2024 thresholds
- **Anti-hallucination:** Frames findings as risk assessments (not legal conclusions); cites specific regulation articles; does not infer jurisdiction
- **Output:** 6 scored sections + Data Gaps + Score rationale + COMPLIANCE SCORE /10

#### Agent 5 — Optimization (`agent_optimization`)
- **Skill:** `SKILL_OPTIMIZATION`
- **Domain:** MarTech feature utilization, growth levers, CRO, automation activation
- **Analyzes:** 10 ranked optimization opportunities grounded in specific data gaps
- **Key Structure:** Gap Signal → Title → Tool → Feature → Steps → Impact → Effort → Expected Outcome → Owner
- **Anti-hallucination:** Every recommendation traces back to a named field in the input data; outcome estimates require stated basis
- **Output:** 10 ranked recommendations grouped by effort + OPTIMIZATION OPPORTUNITY SCORE /10

#### Agent 6 — Redundancy & Gaps (`agent_redundancy`)
- **Skill:** `SKILL_REDUNDANCY`
- **Domain:** Stack rationalization, TCO analysis, capability gap mapping, consolidation strategy
- **Analyzes:** Tool overlaps (HubSpot vs. Mailchimp, GA4 vs. HubSpot Analytics, CDP vs. GA4), missing capabilities, stack complexity, consolidation opportunities, recommended additions
- **Anti-hallucination:** Does not state specific pricing without public documentation; frames redundancy as "Confirmed / Likely / Unlikely"; acknowledges migration complexity
- **Output:** 5 sections + Data Gaps + Score rationale + STACK EFFICIENCY SCORE /10

#### Agent 7 — Executive Summary (`run_full_audit` → `call_llm` with `SKILL_EXECUTIVE_SUMMARY`)
- **Skill:** `SKILL_EXECUTIVE_SUMMARY`
- **Domain:** C-suite communication, strategic synthesis, prioritization frameworks
- **Input:** Concatenated outputs from all 6 agents
- **Rule:** Only synthesizes — does not introduce new analysis
- **Output Structure:** Verdict (3 sentences) → Score Calculation → Traffic Light Summary → Top 3 Critical Issues → Top 3 Quick Wins → 90-Day Action Plan → Stack Maturity Level

---

## 6. Prompt Architecture

### 6.1 Skill Constant Map

| Constant | Lines | Agent |
|---|---|---|
| `MARKETING_SPECIALIST_SYSTEM_PROMPT` | ~45 | Default / fallback |
| `SKILL_DATA_QUALITY` | ~50 | Agent 1 |
| `SKILL_INTEGRATION` | ~50 | Agent 2 |
| `SKILL_PERFORMANCE` | ~55 | Agent 3 |
| `SKILL_COMPLIANCE` | ~60 | Agent 4 |
| `SKILL_OPTIMIZATION` | ~55 | Agent 5 |
| `SKILL_REDUNDANCY` | ~60 | Agent 6 |
| `SKILL_EXECUTIVE_SUMMARY` | ~50 | Agent 7 |

### 6.2 Anti-Hallucination Mechanisms

Every skill enforces:
1. **Data citation requirement** — every claim must reference a named field from the input
2. **Explicit arithmetic** — calculations are shown step by step (e.g., "8% × 5,000 = 400 duplicates")
3. **Benchmark sourcing** — benchmarks not in the input must be attributed to a named source
4. **Confidence tagging** — `[HIGH CONFIDENCE]` / `[MEDIUM CONFIDENCE]` / `[LOW CONFIDENCE / HYPOTHESIS]`
5. **Data gap flagging** — missing fields are listed explicitly, not silently assumed
6. **No invention rule** — if a data point is not present, it is marked `[DATA NOT PROVIDED]`

---

## 7. PDF Export System

### 7.1 Library Stack
- **`reportlab`** (v4.4.10) — PDF generation engine
- **`kaleido`** (v1.0.0rc0) — Plotly → PNG export for chart embedding

### 7.2 PDF Structure

| Section | Content |
|---|---|
| Cover Page | Title, subtitle, generation date, generation time, overall score |
| Executive Summary | Parsed and stripped AI output |
| Score Summary Table | All 6 dimension scores + overall, with alternating row shading |
| Radar Chart | Stack health radar exported as PNG via kaleido |
| Bar Chart | Key metrics vs. benchmarks exported as PNG via kaleido |
| Detailed Findings | All 6 agent outputs, markdown-stripped and styled |
| Footer (every page) | "Page X of Y" + timestamp via `PageNumCanvas` |

### 7.3 Key Design Decisions
- **BytesIO only** — no disk writes; PDF lives in memory
- **Cached in session state** — `st.session_state.pdf_cache` prevents regeneration on every render
- **Charts wrapped in try/except** — PDF generates successfully even if kaleido fails
- **`PageNumCanvas`** — custom canvas subclass that does a two-pass build to enable "Page X of Y"

---

## 8. Dependencies

```
google-generativeai    # Gemini API client
streamlit              # Web application framework
python-dotenv          # .env file loading
plotly                 # Interactive charts + kaleido PNG export
reportlab              # PDF generation
kaleido               # Plotly → PNG for PDF embedding
```

---

## 9. Environment & Configuration

### 9.1 Required Environment Variable

| Variable | Where to set | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | `.env` (local) or Streamlit Cloud Secrets | Gemini API authentication |

### 9.2 Streamlit Cloud Secrets Format
```toml
GEMINI_API_KEY = "AIza..."
```

### 9.3 Local Development
```bash
# Activate virtual environment (if using venv)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

---

## 10. Known Limitations & v2 Roadmap

### 10.1 v1 Limitations
- **Manual input only** — all 49 data points are entered by hand; no live API connections
- **Fixed stack** — hardcoded to HubSpot + RudderStack + GTM + GA4 + Mailchimp
- **Sequential agent execution** — agents run one at a time (Gemini free tier rate limits prevent parallelization)
- **No audit history** — results live in session state and are lost on page refresh
- **Single user** — no authentication, no multi-user support

### 10.2 v2 Roadmap (from sidebar)
| Feature | Description |
|---|---|
| HubSpot API | Auto-pull contact counts, deal data, property lists |
| GA4 Admin API | Auto-pull MAU, events, retention settings |
| GTM API | Auto-pull tag counts, trigger configurations |
| Mailchimp API | Auto-pull subscriber counts, campaign metrics |
| RudderStack API | Auto-pull sources, destinations, event volume |
| BigQuery Export | Direct data warehouse connectivity |
| Scheduled Audits | Weekly/monthly automated re-runs |
| Historical Trends | Score trending over time |

---

## 11. Scoring Reference

All agents score their dimension out of 10. The executive summary agent calculates the overall score as the arithmetic mean of all 6.

| Score Range | Status | CSS Class |
|---|---|---|
| 7.0 – 10.0 | 🟢 Healthy | `score-green` |
| 5.0 – 6.9 | 🟡 Needs Attention | `score-yellow` |
| 0.0 – 4.9 | 🔴 Critical | `score-red` |

---

## 12. Git History Summary

| Commit | Description |
|---|---|
| `c741b45` | MarTech Stack Auditor V1.0 — initial release |
| `7d4b8ca` | V1.0 ready |
| `807385b` | feat: add generation timer, PDF export, and marketing specialist system prompt |
| `bfa0009` | added skills to agents — 7 domain-specific skill constants with anti-hallucination enforcement |
