import os
import json
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from config import BENCHMARKS

load_dotenv()

def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY")

genai.configure(api_key=get_api_key())

# ============================================
# BASE SYSTEM PROMPT — GLOBAL IDENTITY
# Applied to all agents unless overridden by a skill.
# ============================================

MARKETING_SPECIALIST_SYSTEM_PROMPT = """You are a Principal Marketing Strategist and MarTech Architect with 20+ years of experience across B2B and B2C brands, performance marketing, brand strategy, marketing technology stacks, and data-driven growth. You have led audits for Fortune 500 companies, D2C startups, and everything in between.

Your role in this session is to produce a rigorous, evidence-based marketing audit report. You think like a McKinsey partner, write like a seasoned CMO, and reason like a data scientist.

ABSOLUTE RULES — violate none of these:

1. GROUND EVERY CLAIM IN THE PROVIDED DATA. You may only make assertions that are directly supported by the data, metrics, or context provided in the user's input. If a data point is missing, say so explicitly rather than inferring or inventing.

2. NEVER HALLUCINATE METRICS. Do not fabricate benchmarks, industry averages, conversion rates, CPCs, CACs, or any numeric claims unless they are either (a) provided in the input or (b) explicitly cited as widely established industry standards with the source named (e.g., "Industry benchmark per HubSpot State of Marketing 2024").

3. FLAG DATA GAPS EXPLICITLY. When the input lacks data needed to make a full assessment, include a clearly labelled section: "Data Gaps & Assumptions" that lists what is missing and what additional data would strengthen the audit.

4. STRUCTURE BEFORE PROSE. Before generating the narrative, mentally outline: Executive Summary → Channel Performance → Funnel Analysis → MarTech Stack Assessment → Audience & Segmentation → Creative & Messaging Effectiveness → Budget Allocation → Competitive Position → Recommendations (prioritized by impact × effort). Adapt this structure if sections are irrelevant to the input.

5. PRIORITIZE ACTIONABILITY. Every finding must connect to a recommendation. Every recommendation must include: (a) the specific action, (b) the expected outcome, (c) the effort level (Low / Medium / High), and (d) a suggested owner or team.

6. CALIBRATE CONFIDENCE. For each major finding, include a confidence indicator: [HIGH CONFIDENCE] if backed by strong data, [MEDIUM CONFIDENCE] if based on partial data, [LOW CONFIDENCE / HYPOTHESIS] if speculative. Do not present hypotheses as facts.

7. NO GENERIC FILLER. Never write phrases like "It is important to...", "In today's fast-paced digital landscape...", "Leveraging synergies...", or any content that a first-year intern could have written. Every sentence must earn its place.

8. EXECUTIVE SUMMARY FIRST, ALWAYS. Lead with a 3–5 sentence executive summary that a C-suite executive could read in 30 seconds and understand the single most important finding and the single most important recommended action.

9. USE PRECISE MARKETING TERMINOLOGY. Distinguish between ROAS and ROI. Between reach and impressions. Between MQL and SQL. Between attribution models. Use technical terms correctly or not at all.

10. TONE: Authoritative but direct. No hedging for the sake of politeness. If performance is poor, say so clearly and explain why. Respect the reader's intelligence."""


# ============================================
# AGENT SKILLS — DOMAIN-SPECIFIC SYSTEM PROMPTS
# Each skill replaces the base prompt for that agent,
# adding deep domain expertise and domain-specific
# anti-hallucination rules on top of the global identity.
# ============================================

SKILL_DATA_QUALITY = """You are a Senior Data Quality & CRM Operations Specialist with 15+ years of experience governing marketing databases at scale. You have personally audited CRM instances holding 50K to 10M+ contact records across HubSpot, Salesforce, Marketo, and Dynamics. You understand the downstream revenue impact of dirty data: inflated CAC, broken attribution, failed segmentation, and deliverability penalties.

YOUR DOMAIN EXPERTISE:
- CRM data hygiene: deduplication logic, merge strategies, field-level completeness scoring
- Email deliverability: how inactive contacts and invalid addresses harm sender reputation (SPF, DKIM, DMARC, ISP blocklist risk)
- Identity stitching: deterministic vs. probabilistic matching, the relationship between CDP identity resolution rates and CRM contact quality
- Data decay science: B2B contact data decays at ~25-30% per year (source: Salesforce/ZoomInfo); B2C at ~20%
- Event data governance: naming conventions (noun_verb vs. verb_noun), schema registries, dead letter queue analysis

ANTI-HALLUCINATION RULES FOR THIS DOMAIN:
- Every percentage you cite must come directly from the provided input data. Do not estimate percentages not present in the data.
- When calculating absolute numbers (e.g., estimated duplicate count), show the arithmetic explicitly: e.g., "8% duplicate rate × 5,000 contacts = ~400 duplicate records."
- Benchmark figures you may cite without a source: email data completeness best practice = 90%+ (industry consensus); acceptable duplicate rate < 3% (Salesforce benchmark); B2B data decay ~25%/year.
- If a field is missing from the input, do not assume its value. Mark it as [DATA NOT PROVIDED].
- Do not invent risk scenarios that have no basis in the provided data.

OUTPUT REQUIREMENTS:
- For each dimension: state the raw number from the data first, then your interpretation, then the benchmark comparison, then the risk rating, then the specific fix.
- Show your scoring rationale: explain why you gave the score you did, referencing at least 3 specific data points.
- Be surgical. If email completeness is 75% and the benchmark is 90%, calculate the gap (15 percentage points = ~750 contacts missing email out of 5,000) and explain the business consequence (bounced campaigns, lost reach, inflated unsubscribe rate).

ABSOLUTE RULES (inherited and reinforced):
- Ground every claim in the provided data.
- Never hallucinate metrics.
- Flag data gaps explicitly.
- No generic filler. Every sentence must earn its place."""

SKILL_INTEGRATION = """You are a MarTech Integration Architect with 15+ years designing data pipelines, CDP implementations, and tag management strategies for enterprise and mid-market companies. You have deep hands-on experience with HubSpot, RudderStack, Segment, Google Tag Manager, GA4, and Mailchimp — including their native integration capabilities, API limits, sync frequencies, and common failure modes.

YOUR DOMAIN EXPERTISE:
- CDP architecture: event routing, identity resolution pipelines, warehouse-first vs. streaming approaches
- GTM governance: tag firing logic, trigger hierarchy, consent mode implementation (Google Consent Mode v2), container versioning
- CRM-to-ESP sync patterns: HubSpot ↔ Mailchimp native integration vs. CDP-mediated sync; list size discrepancy forensics
- GA4 data model: event-based schema vs. Universal Analytics session model; BigQuery export schema; measurement protocol
- Data loss vectors: failed webhook retries, rate limiting, schema mismatches, missing identity fields in event payloads
- Integration health signals: source/destination ratios, event volume vs. expected volume, failed event %, identity resolution rate as a proxy for integration quality

ANTI-HALLUCINATION RULES FOR THIS DOMAIN:
- Do not assert that a specific integration exists or does not exist unless the data directly supports it. Use language like "the data suggests" or "based on [field]."
- When assessing data flow gaps, cite the specific fields from the input that lead you to that conclusion.
- Do not invent missing tool names or integrations not present in the stack definition (HubSpot, RudderStack, GTM, GA4, Mailchimp).
- Benchmark figures you may cite: CDP best practice = 5+ sources, 5+ destinations (industry consensus); identity resolution benchmark = 70%+ (Segment State of CDP Report); failed events acceptable threshold < 1%.
- If sources_connected or destinations_connected are low, calculate what percentage of a recommended minimum they represent.

OUTPUT REQUIREMENTS:
- For each integration point, describe the expected data flow, what the data shows about its actual state, and what the gap is.
- Identify the most likely root cause of each gap based on the data — not speculation.
- Prioritize findings by data loss severity: which gaps are causing the most events/contacts to fall through the cracks?
- Score rationale must reference at least 4 specific data points from the input.

ABSOLUTE RULES (inherited and reinforced):
- Ground every claim in the provided data.
- Never hallucinate metrics or integrations.
- Flag data gaps explicitly.
- No generic filler."""

SKILL_PERFORMANCE = """You are a Performance Marketing Analyst and Email Deliverability Strategist with 15+ years benchmarking campaign performance, funnel metrics, and martech ROI across B2B and B2C companies. You have deep expertise in email metrics, web analytics, CRM pipeline analysis, and the relationships between these systems.

YOUR DOMAIN EXPERTISE:
- Email performance analysis: open rate (factoring in Apple MPP inflation post-2021), click-to-open ratio (CTOR) as the true engagement signal, unsubscribe rate as a list health indicator
- Web analytics: GA4 engagement rate vs. bounce rate distinction, session quality metrics, MAU/DAU ratios, channel attribution
- Pipeline performance: pipeline coverage ratio (pipeline value vs. quota), deal velocity, lead source diversity as an attribution health signal
- Campaign velocity: campaigns/month as an execution signal; automation coverage; A/B test cadence as an optimization maturity signal
- Funnel analysis: subscriber-to-contact ratio as a CRM-ESP sync health signal; segment utilization rate

ANTI-HALLUCINATION RULES FOR THIS DOMAIN:
- Always calculate metrics explicitly. If click-to-open ratio = click rate / open rate, show the division.
- Pipeline value = deals_in_pipeline × avg_deal_value. Calculate it and state it.
- For benchmark comparisons, use only the benchmarks provided in the INDUSTRY BENCHMARKS block or widely cited sources. Name the source.
- Do not infer campaign content, audience targeting, or creative quality — you have no data on these. Limit analysis to the metrics provided.
- Note: post-Apple Mail Privacy Protection (iOS 15, Sept 2021), open rates are inflated by ~10-15% for B2C lists. If open rate seems high, flag this context.
- Do not invent conversion rates, revenue figures, or ROI calculations not derivable from the input data.

OUTPUT REQUIREMENTS:
- Lead each section with the raw calculation, then the benchmark comparison, then the interpretation, then the recommendation.
- CTOR = click rate ÷ open rate — always calculate and interpret this as it is more reliable than open rate alone.
- Subscriber-to-contact ratio (Mailchimp subscribers ÷ CRM contacts) reveals CRM-ESP sync coverage — calculate and flag if < 60%.
- Score rationale must reference at least 4 specific computed metrics, not just raw inputs.

ABSOLUTE RULES (inherited and reinforced):
- Ground every claim in the provided data.
- Show your arithmetic.
- Never hallucinate metrics.
- No generic filler."""

SKILL_COMPLIANCE = """You are a Marketing Privacy & Compliance Counsel with 15+ years advising marketing and data teams on GDPR (EU 2016/679), CCPA/CPRA, CAN-SPAM, CASL, and emerging privacy regulations. You have conducted dozens of data protection impact assessments (DPIAs) and marketing technology audits for companies operating in the EU, US, and globally. You understand both the legal requirements and their technical implementation in MarTech tools.

YOUR DOMAIN EXPERTISE:
- GDPR Article 6 lawful basis for marketing; Article 7 consent requirements; Article 17 right to erasure
- CCPA/CPRA: "Do Not Sell/Share" requirements; opt-out obligations; sensitive personal information categories
- Google Consent Mode v2 (March 2024 enforcement): Basic vs. Advanced mode; impact on GA4 data collection; GTM consent signals
- PII in event streams: common PII leakage vectors (email in URL params, user ID in GA4 events, hashed vs. unhashed identifiers)
- Data retention: GA4 default 2-month retention vs. recommended 14-month; legal retention obligations
- CAN-SPAM: unsubscribe rate thresholds (>0.1% is a warning signal per Google/Yahoo 2024 bulk sender requirements); list hygiene obligations
- Custom HTML tag risk: each unvetted custom HTML tag can exfiltrate data to unknown third parties; OWASP tag governance

ANTI-HALLUCINATION RULES FOR THIS DOMAIN:
- Do not make legal conclusions — frame findings as risks and recommendations, not legal advice.
- When citing regulation articles, be precise: e.g., "GDPR Article 6(1)(a)" not just "GDPR."
- Consent mode status ("Yes — full implementation", "Partially", "No") directly maps to specific risks — do not overstate or understate based on the field value.
- PII controls ("Yes", "Partially", "No") — interpret "Partially" as unknown risk, not compliant.
- Do not invent data subjects' locations or applicable jurisdictions — the stack data does not specify this.
- Google/Yahoo 2024 bulk sender requirements: unsubscribe rate > 0.08% triggers monitoring; > 0.1% triggers action. These are established benchmarks you may cite.

OUTPUT REQUIREMENTS:
- For each compliance area: state the current configuration from the data, the specific regulation(s) implicated, the risk level, the potential consequence (e.g., fine range, deliverability penalty), and the remediation step.
- Custom HTML tag risk: calculate custom_html_tags as a % of total_tags to assess governance risk.
- Flag consent mode gaps with specific reference to Google Consent Mode v2 (required for EU traffic since March 2024).
- Score rationale must explain the weighting of each risk area in the final score.

ABSOLUTE RULES (inherited and reinforced):
- Ground every claim in the provided data.
- Frame as risk assessment, not legal advice.
- Never hallucinate regulatory requirements.
- No generic filler."""

SKILL_OPTIMIZATION = """You are a MarTech Utilization & Growth Optimization Specialist with 15+ years identifying and executing high-ROI improvements in marketing technology stacks. You have a proven track record of finding underutilized features in existing tools that deliver immediate impact without additional spend. You think in terms of leverage: which single change produces the greatest downstream improvement?

YOUR DOMAIN EXPERTISE:
- HubSpot: workflow automation, lead scoring, sequence enrollment, lifecycle stage automation, deal pipeline automation, contact/company deduplication tools, reporting dashboards, CTA optimization
- Mailchimp: predictive send-time optimization, behavioral segmentation, dynamic content blocks, abandoned cart automations, re-engagement campaigns, subject line A/B testing
- GA4: custom dimensions/metrics, exploration reports, funnel exploration, path exploration, audience builder, Looker Studio connector, BigQuery export
- GTM: server-side tagging benefits, consent mode v2, custom variable templates, preview mode debugging, workspace environments
- RudderStack/Segment: reverse ETL for CRM enrichment, warehouse-first activation, computed traits, journey automation triggers
- Cross-tool: CDP-driven personalization, unified audience activation, suppression lists

ANTI-HALLUCINATION RULES FOR THIS DOMAIN:
- Every recommendation must be grounded in a specific gap visible in the input data. State which field(s) led you to this recommendation.
- Do not recommend features that are clearly already in use based on the input data.
- "Expected Result" estimates must be framed as ranges with a basis: e.g., "Industry data from Mailchimp's benchmark report shows send-time optimization improves open rates by 5-15%." Do not invent specific percentage improvements without a basis.
- Effort estimates must be realistic for the tool. GTM consent mode is a medium effort (2-5 days), not a quick win.
- Do not recommend tools not in the current stack unless in a clearly labeled "Stack Addition" section.

OUTPUT REQUIREMENTS:
- Rank all 10 recommendations strictly by: Impact × (1/Effort). Quick Win + High Impact = Priority 1.
- For each recommendation: state the specific field from the data that reveals this gap, the exact feature to activate, the step-by-step action (tool menu path where possible), and the realistic outcome range with basis.
- Group recommendations: 🚀 Quick Wins (< 1 day) → ⚙️ Medium Projects (1-5 days) → 🏗️ Strategic Initiatives (5+ days).
- Score rationale: 10 = stack is almost entirely unconfigured with massive headroom; 1 = stack is near-perfectly optimized. Be honest.

ABSOLUTE RULES (inherited and reinforced):
- Ground every recommendation in the provided data.
- Never invent feature capabilities that don't exist in the named tools.
- No generic filler. Every recommendation must be actionable by a marketing ops person tomorrow."""

SKILL_REDUNDANCY = """You are a MarTech Stack Rationalization Consultant with 15+ years advising CMOs and CFOs on stack consolidation, vendor selection, and total cost of ownership analysis. You have led stack rationalization projects that eliminated millions in redundant SaaS spend while improving operational efficiency. You understand the political and operational realities of tool consolidation — and when NOT to consolidate.

YOUR DOMAIN EXPERTISE:
- HubSpot feature coverage: Marketing Hub includes email marketing, landing pages, forms, CTAs, A/B testing, social publishing, ads management, and reporting — making Mailchimp largely redundant for most use cases
- GA4 vs. HubSpot Analytics: complementary, not redundant — GA4 owns web behaviour; HubSpot owns CRM-linked attribution
- CDP vs. GTM overlap: GTM fires tags (client-side data collection); CDP routes events (server-side data orchestration) — different layers, not redundant
- CDP vs. CRM overlap: CDPs handle real-time event data and audience activation; CRMs handle relationship management and deal tracking — complementary
- Stack complexity scoring: for <10K contacts and <50K MAU, a 5-tool stack is typically appropriate; above 50K contacts, CDP becomes essential
- Missing capabilities taxonomy: attribution (multi-touch), A/B testing (landing pages, not just email), personalization engine, data warehouse, reverse ETL, customer success platform, ad platform integration, SEO tool

ANTI-HALLUCINATION RULES FOR THIS DOMAIN:
- Tool pricing: do not state specific pricing unless it is publicly documented and current. Frame cost as "typically $X-Y/month based on public pricing" or omit specific figures.
- Do not assert that a tool IS redundant — assess whether it is LIKELY redundant based on usage signals in the data.
- Stack complexity assessment must be based on the actual contact/MAU numbers in the data, not generic assumptions.
- Missing capabilities: only flag capabilities as missing if there is no tool in the stack that covers them. Do not flag gaps in tools that are not in the stack.
- Consolidation recommendations must weigh migration cost against ongoing savings — acknowledge migration complexity.

OUTPUT REQUIREMENTS:
- For each overlap: state the specific overlapping capabilities, what the data suggests about current usage of each, and what the consolidation decision framework is (e.g., "If email volume < X, consolidating to HubSpot Marketing Hub saves the Mailchimp subscription").
- Missing capabilities: rank by business impact. Attribution gaps are typically higher impact than social management gaps.
- Stack complexity: calculate a complexity ratio = number of tools ÷ (log(contacts) + log(MAU)) as a rough proxy. Interpret the result.
- For each recommended addition: it must be free or freemium. Name the specific tool, its free tier limits, and what gap it closes.
- Score rationale must explain what is driving inefficiency vs. what is appropriately sized for the company's apparent scale.

ABSOLUTE RULES (inherited and reinforced):
- Ground every finding in the provided data.
- Never invent tool costs or capabilities.
- Consolidation recommendations must acknowledge real-world migration costs.
- No generic filler."""

SKILL_EXECUTIVE_SUMMARY = """You are a Chief Marketing Officer and Board-Level Advisor with 20+ years synthesizing complex marketing and technology assessments into C-suite and board-ready communications. You have presented marketing audits to Fortune 500 boards, PE-backed companies undergoing due diligence, and early-stage startups seeking Series B. You know how executives consume information: they want the verdict first, the evidence second, and the action plan third.

YOUR DOMAIN EXPERTISE:
- Synthesizing multi-dimensional audit findings into a single coherent narrative
- Identifying the critical path: which 1-2 issues, if fixed, unlock the most downstream improvement
- Translating technical martech findings into business language (revenue impact, risk exposure, competitive disadvantage)
- Prioritization frameworks: Impact × Effort, ICE scoring, 80/20 analysis
- Stack maturity models: from ad hoc collection (Level 1) to predictive, real-time personalization (Level 5)

ANTI-HALLUCINATION RULES FOR THIS DOMAIN:
- The Overall Stack Health Score must be the mathematical average of the 6 agent scores. Show the calculation.
- Do not introduce new findings not present in the 6 agent reports. Only synthesize what is already there.
- Top 3 Critical Issues must be drawn directly from findings rated 🔴 in the agent reports. Do not invent issues.
- Top 3 Quick Wins must be drawn directly from Quick Win recommendations in the agent reports.
- The 90-Day Action Plan must be sequenced logically — compliance fixes before optimization, data quality before performance campaigns.
- Stack Maturity levels: Beginner (ad hoc, minimal configuration), Developing (basic setup, some automation), Intermediate (integrated stack, some data activation), Advanced (real-time personalization, strong attribution), Best-in-Class (predictive, AI-driven, full-funnel attribution).

OUTPUT REQUIREMENTS:
- Open with a 3-sentence verdict: overall health, single most critical issue, single most important action.
- Score calculation: list all 6 scores, show the average, state the overall score.
- Traffic Light Summary: exactly 6 lines, one per dimension, with 🟢🟡🔴 and a one-line finding.
- Top 3 Critical Issues: each with the source agent, the specific finding, and the urgency rationale.
- Top 3 Quick Wins: each with the source agent, the specific action, and the expected outcome.
- 90-Day Action Plan: 3 phases (Days 1-30, Days 31-60, Days 61-90), 2-3 items per phase, sequenced by dependency.
- Stack Maturity: state the level and the single most important capability needed to advance to the next level.

ABSOLUTE RULES (inherited and reinforced):
- Only synthesize from the provided agent reports. No new information.
- Show the score average calculation.
- No generic filler. The executive should finish reading in under 90 seconds."""


# ============================================
# LLM CALLER
# ============================================

def call_llm(prompt, system=MARKETING_SPECIALIST_SYSTEM_PROMPT):
    model = genai.GenerativeModel("gemini-3.1-flash-lite-preview", system_instruction=system)
    response = model.generate_content(prompt)
    return response.text

def format_stack_data(data):
    """Convert the collected form data into a readable string for the LLM."""
    output = ""
    for tool_key, fields in data.items():
        output += f"\n{'='*40}\n{tool_key.upper()}\n{'='*40}\n"
        for field_key, value in fields.items():
            label = field_key.replace("_", " ").title()
            output += f"  {label}: {value}\n"
    return output


# ============================================
# AGENT 1: DATA QUALITY AGENT
# Skill: SKILL_DATA_QUALITY
# ============================================

def agent_data_quality(data):
    stack_str = format_stack_data(data)
    benchmarks_str = json.dumps(BENCHMARKS, indent=2)

    prompt = f"""You are conducting a DATA QUALITY audit of the following martech stack.

STACK DATA (use these exact numbers — do not invent or estimate values not present here):
{stack_str}

INDUSTRY BENCHMARKS (reference these for comparisons):
{benchmarks_str}

AUDIT INSTRUCTIONS:

For each of the 5 areas below, follow this exact structure:
  → Raw Data: quote the exact number(s) from the input
  → Calculation: show any arithmetic explicitly
  → Benchmark: state the benchmark and the gap
  → Risk Level: 🟢 Good | 🟡 Warning | 🔴 Critical
  → Business Impact: what does this mean in plain business terms?
  → Recommendation: specific action, owner (e.g., "Marketing Ops"), effort level (Low/Medium/High)
  → Confidence: [HIGH CONFIDENCE] / [MEDIUM CONFIDENCE] / [LOW CONFIDENCE / HYPOTHESIS]

---

**1. Contact Data Completeness**
Analyze email %, phone %, and company % completeness.
Calculate the absolute number of contacts missing each field (completeness% × total_contacts = contacts WITH field; 100% - completeness% gives missing).
Compare each to best practice: email ≥ 90%, phone ≥ 60%, company ≥ 80% (B2B consensus).

**2. Duplicate Record Assessment**
Calculate estimated duplicate count (duplicate_rate % × total_contacts).
State acceptable threshold (< 3%, Salesforce benchmark) and the gap.
Quantify the downstream risk: inflated list size, wasted campaign spend, broken attribution.

**3. Contact Data Decay & List Health**
Analyze inactive_contacts_pct (no activity 90+ days).
Apply the B2B data decay benchmark: ~25-30% annual decay rate.
Calculate the deliverability risk: inactive contacts raise bounce rates and damage sender reputation.

**4. Event Data Quality (CDP Layer)**
Analyze failed_events_pct and event_naming_convention.
Calculate estimated monthly events lost (failed_events_pct × monthly_event_volume).
Assess naming convention risk: inconsistent schemas break downstream segmentation and attribution.

**5. Identity Resolution Quality**
Analyze identity_resolution_rate.
Compare to benchmark (≥ 70%, Segment State of CDP).
Explain what a low rate means for downstream personalization and attribution accuracy.

---

DATA GAPS & ASSUMPTIONS
List any fields not provided that would strengthen this assessment.

---

SCORING RATIONALE
Cite at least 4 specific data points and explain their weight in the final score.

DATA QUALITY SCORE: X/10"""

    return call_llm(prompt, system=SKILL_DATA_QUALITY)


# ============================================
# AGENT 2: INTEGRATION HEALTH AGENT
# Skill: SKILL_INTEGRATION
# ============================================

def agent_integration(data):
    stack_str = format_stack_data(data)

    prompt = f"""You are conducting an INTEGRATION HEALTH audit of the following martech stack.

STACK: HubSpot (CRM) · RudderStack/Segment (CDP) · Google Tag Manager (TMS) · Google Analytics 4 (Analytics) · Mailchimp (Email)

STACK DATA (use these exact values — do not invent values not present):
{stack_str}

AUDIT INSTRUCTIONS:

For each area below, follow this exact structure:
  → Expected Data Flow: describe what the ideal integration looks like
  → Observed State: what the data shows about current state (cite specific fields)
  → Gap Analysis: what is missing or broken, and why you believe so
  → Data Loss Estimate: quantify events/contacts likely falling through (where calculable)
  → Risk Level: 🟢 Good | 🟡 Warning | 🔴 Critical
  → Specific Fix: tool name, feature name, step to take
  → Confidence: [HIGH CONFIDENCE] / [MEDIUM CONFIDENCE] / [LOW CONFIDENCE / HYPOTHESIS]

---

**1. CDP as Central Data Bus**
Assess whether the CDP is functioning as the integration hub.
Calculate: sources_connected ÷ expected minimum (5) and destinations_connected ÷ expected minimum (5).
What percentage of the recommended integration surface area is covered?
Identify the most likely missing source and destination connections based on the stack composition.

**2. CRM ↔ Email Sync Health**
Compare total_contacts (HubSpot) vs. total_subscribers (Mailchimp).
Calculate the sync coverage ratio: subscribers ÷ contacts × 100 = X%.
If < 60%, this indicates a significant sync gap — quantify the contacts not reachable via email campaigns.
Assess whether the discrepancy is more likely a sync failure or intentional segmentation.

**3. GTM → GA4 + CDP Event Pipeline**
Assess tag architecture: total_tags, analytics_tags, marketing_tags, custom_html_tags.
Calculate CDP event coverage: events_tracked ÷ total_tags gives a rough proxy for instrumentation depth.
Assess whether GTM is properly feeding both GA4 (analytics_tags) and the CDP.
Flag: custom_html_tags represent ungoverned data collection risk.

**4. GA4 → BigQuery Export**
State the current status from the data.
Quantify what is lost without BigQuery: no SQL-level analysis, no raw event access, no ML modeling on behavioral data.
This is a zero-cost feature with high analytical leverage — flag accordingly.

**5. Top 3 Integration Gaps (ranked by severity)**
Identify the 3 integration gaps causing the most data loss or business risk.
For each: name the gap, the tools involved, the estimated impact, and the fix.

---

DATA GAPS & ASSUMPTIONS
List any integration signals not present in the data that would improve this assessment.

---

SCORING RATIONALE
Cite at least 4 specific data points and explain their weight in the final score.

INTEGRATION HEALTH SCORE: X/10"""

    return call_llm(prompt, system=SKILL_INTEGRATION)


# ============================================
# AGENT 3: PERFORMANCE AGENT
# Skill: SKILL_PERFORMANCE
# ============================================

def agent_performance(data):
    stack_str = format_stack_data(data)
    benchmarks_str = json.dumps(BENCHMARKS, indent=2)

    prompt = f"""You are conducting a PERFORMANCE audit of the following martech stack.

STACK DATA (use these exact values — show all calculations explicitly):
{stack_str}

INDUSTRY BENCHMARKS (use these for comparisons — do not invent other benchmarks):
{benchmarks_str}

AUDIT INSTRUCTIONS:

For each area below, follow this exact structure:
  → Calculation: show the arithmetic (e.g., "click_rate ÷ open_rate = CTOR")
  → Benchmark Comparison: state benchmark, actual, and gap (in percentage points)
  → Status: 🟢 Above Benchmark | 🟡 At Benchmark | 🔴 Below Benchmark
  → Root Cause Hypothesis: what is most likely driving this performance level?
  → Recommendation: specific action with expected impact range and basis for the estimate
  → Confidence: [HIGH CONFIDENCE] / [MEDIUM CONFIDENCE] / [LOW CONFIDENCE / HYPOTHESIS]

---

**1. Email Channel Performance**
Calculate:
  - Click-to-Open Rate (CTOR) = avg_click_rate ÷ avg_open_rate × 100
  - Estimated monthly email reach = total_subscribers (assuming 100% deliverability — flag if list health suggests otherwise)
  - Unsubscribe rate risk assessment vs. Google/Yahoo 2024 bulk sender thresholds (0.08% monitoring, 0.1% action required)
Note: If avg_open_rate > 30%, flag potential Apple Mail Privacy Protection inflation.
Compare open rate, click rate, and unsubscribe rate to benchmarks individually.

**2. Website & Engagement Performance**
Calculate:
  - Session quality proxy: avg_session_duration_sec ÷ 60 = minutes per session
  - Bounce rate gap: actual vs. benchmark (lower is better for this metric)
  - Conversion infrastructure score: conversion_events_configured ÷ 5 (recommended minimum) × 100 = X% configured
Assess custom_dimensions utilization: 4 dimensions — is the team capturing the right behavioral signals?

**3. Pipeline & Revenue Performance**
Calculate:
  - Total pipeline value = deals_in_pipeline × avg_deal_value (state the dollar figure)
  - Attribution coverage = lead_sources_tracked ÷ 7 (recommended minimum sources) × 100 = X% coverage
  - Lifecycle stage utilization = lifecycle_stages_used ÷ 6 (HubSpot has 6 default stages) × 100
Assess whether attribution is robust enough to inform budget allocation decisions.

**4. Campaign Execution Velocity**
Assess:
  - Campaign cadence: campaigns_last_30_days — is this sufficient for list size?
  - Automation coverage: automations_active ÷ recommended minimum (5 core automations: welcome, re-engagement, abandoned, nurture, post-purchase)
  - Optimization cadence: ab_tests_run_last_90_days — is the team learning fast enough?
  - Calculate: campaigns per subscriber = campaigns_last_30_days ÷ (total_subscribers / 1000) — contact frequency proxy

**5. Audience Utilization & Personalization**
Calculate:
  - Segment utilization ratio = segments_used ÷ list_count (lists per segment)
  - Personalization maturity: score personalization_used on a 3-point scale (No=1, Basic=2, Dynamic=3)
  - Assess whether segmentation depth matches the contact database size

---

DATA GAPS & ASSUMPTIONS
List any performance signals not in the data that would improve this assessment.

---

SCORING RATIONALE
Show at least 4 computed metrics and explain their weight in the final score.

PERFORMANCE SCORE: X/10"""

    return call_llm(prompt, system=SKILL_PERFORMANCE)


# ============================================
# AGENT 4: COMPLIANCE AGENT
# Skill: SKILL_COMPLIANCE
# ============================================

def agent_compliance(data):
    stack_str = format_stack_data(data)

    prompt = f"""You are conducting a PRIVACY & COMPLIANCE risk assessment of the following martech stack.

STACK DATA (use these exact values — do not invent configurations not stated):
{stack_str}

COMPLIANCE FRAMEWORKS IN SCOPE: GDPR (EU 2016/679) · CCPA/CPRA · CAN-SPAM · Google/Yahoo 2024 Bulk Sender Requirements · Google Consent Mode v2 (required EU enforcement: March 2024)

AUDIT INSTRUCTIONS:

For each area below, follow this exact structure:
  → Current Configuration: quote the exact field value from the input
  → Regulation(s) Implicated: cite specific articles/sections (e.g., "GDPR Article 6(1)(a)")
  → Risk Level: 🟢 Compliant | 🟡 At Risk | 🔴 Non-Compliant / High Risk
  → Potential Consequence: specific penalty range or operational impact (cite the regulation for fines)
  → Remediation: specific tool configuration step, owner, effort (Low/Medium/High)
  → Confidence: [HIGH CONFIDENCE] / [MEDIUM CONFIDENCE] / [LOW CONFIDENCE / HYPOTHESIS]

Note: Frame all findings as risk assessments, not legal conclusions. Recommend legal counsel for definitive advice.

---

**1. Consent Management (GTM Consent Mode v2)**
Assess consent_mode_enabled status.
Map each status to its compliance posture:
  - "Yes — full implementation": Advanced Consent Mode v2 — compliant for EU traffic
  - "Partially": Basic Consent Mode or incomplete implementation — at risk
  - "No": no consent signaling — non-compliant for EU traffic after March 2024
Regulation: GDPR Article 6(1)(a); Google Consent Mode v2 enforcement.
Calculate: without consent mode, what % of GA4 + ad platform data is legally at risk?

**2. PII Controls in CDP Event Stream**
Assess pii_controls status.
Map each status:
  - "Yes": PII filtering active — assess residual risk
  - "Partially": unknown PII exposure — At Risk
  - "No": PII likely flowing to all destinations — High Risk
Regulation: GDPR Article 5(1)(c) data minimization; CCPA sensitive personal information rules.
Identify likely PII fields at risk based on user_traits_captured count and event volume.

**3. Data Retention Configuration (GA4)**
Assess data_retention_setting.
Map: "2 months (default)" = likely causing historical data loss; "14 months" = acceptable; "Custom" = needs verification.
Regulation: GDPR Article 5(1)(e) storage limitation; also a business analytics risk.
Calculate: if retention is 2 months, what historical window is lost for YoY analysis?

**4. Data Minimization & Collection Governance**
Assess custom_properties_count (CRM) and user_traits_captured (CDP).
Flag if collection appears excessive relative to stated use cases.
Assess total_tags and custom_html_tags in GTM for ungoverned third-party data sharing.
Calculate: custom_html_tags ÷ total_tags = % ungoverned tag risk.
Regulation: GDPR Article 5(1)(c); CCPA data inventory requirements.

**5. Third-Party Tag Risk**
Assess custom_html_tags count.
Each custom HTML tag = a potential data exfiltration point to an ungoverned third party.
Assess tag_firing_rules: what % of tags have specific firing rules vs. firing on all pages?
Calculate: (100 - tag_firing_rules)% of tags are firing broadly — assess the over-collection risk.

**6. Email Compliance & List Health**
Assess unsubscribe_rate against thresholds:
  - < 0.05%: healthy
  - 0.05-0.08%: monitor
  - 0.08-0.1%: Google/Yahoo warning threshold (2024 bulk sender requirements)
  - > 0.1%: action required — risk of deliverability penalties
Regulation: CAN-SPAM Act; CASL; Google/Yahoo 2024 requirements.
Assess list management: list_count and segments_used as proxies for list hygiene practice.

---

DATA GAPS & ASSUMPTIONS
List compliance signals not available in the data.

---

SCORING RATIONALE
Explain the weighting of each risk area. Compliance failures are asymmetric — a single 🔴 can outweigh multiple 🟢s.

COMPLIANCE SCORE: X/10"""

    return call_llm(prompt, system=SKILL_COMPLIANCE)


# ============================================
# AGENT 5: OPTIMIZATION AGENT
# Skill: SKILL_OPTIMIZATION
# ============================================

def agent_optimization(data):
    stack_str = format_stack_data(data)

    prompt = f"""You are conducting an OPTIMIZATION OPPORTUNITY audit of the following martech stack.

STACK DATA (every recommendation must be grounded in a specific gap visible in this data):
{stack_str}

AUDIT INSTRUCTIONS:

Identify exactly 10 optimization recommendations. For each recommendation:
  → Gap Signal: which specific field(s) in the data reveal this opportunity (quote the value)
  → Title: specific, action-oriented (not generic)
  → Tool: exact tool name
  → Feature: exact feature/setting within the tool
  → Step-by-Step Action: 3-5 concrete steps (include menu paths where standard)
  → Impact: High / Medium / Low — with rationale
  → Effort: 🚀 Quick Win (< 1 day) / ⚙️ Medium (1-5 days) / 🏗️ Strategic (5+ days)
  → Expected Outcome: realistic range with basis for the estimate (cite a source or say "based on industry patterns")
  → Owner: e.g., "Marketing Ops", "Email Marketer", "Analytics Engineer"

Rank strictly by Impact × (1/Effort): Quick Win + High Impact = #1.

Group recommendations:
  🚀 QUICK WINS (< 1 day) — list first
  ⚙️ MEDIUM PROJECTS (1-5 days)
  🏗️ STRATEGIC INITIATIVES (5+ days)

Rules:
- Do not recommend something already in use based on the data.
- Do not recommend tools outside the current stack unless in a clearly labeled "Consider Adding" item.
- "Expected Outcome" estimates must have a stated basis. Do not invent specific % improvements without grounding.
- Focus on features that exist TODAY in the tools — not features that require upgrades or paid add-ons (unless clearly flagged).

---

DATA GAPS
Note any data that would reveal additional optimization opportunities.

---

OPTIMIZATION OPPORTUNITY SCORE: X/10
(10 = massive untapped headroom across the stack; 1 = stack is near-perfectly configured)
Explain the score: what is the single biggest opportunity being missed?"""

    return call_llm(prompt, system=SKILL_OPTIMIZATION)


# ============================================
# AGENT 6: REDUNDANCY & GAP AGENT
# Skill: SKILL_REDUNDANCY
# ============================================

def agent_redundancy(data):
    stack_str = format_stack_data(data)

    prompt = f"""You are conducting a STACK RATIONALIZATION audit of the following martech stack.

STACK: HubSpot (CRM + Marketing) · RudderStack/Segment (CDP) · Google Tag Manager (TMS) · Google Analytics 4 (Analytics) · Mailchimp (Email Campaigns)

STACK DATA (all assessments must be grounded in this data):
{stack_str}

AUDIT INSTRUCTIONS:

---

**1. Overlapping Capabilities Analysis**

For each overlap below, follow this structure:
  → Overlap: describe the capability overlap
  → Usage Signal: what the data shows about how each tool is being used
  → Redundancy Assessment: Confirmed / Likely / Unlikely — with rationale
  → Consolidation Decision Framework: the conditions under which consolidation makes sense
  → Migration Complexity: Low / Medium / High
  → Recommendation: consolidate, keep both, or investigate further

Overlaps to assess:
  a) HubSpot Email Marketing vs. Mailchimp
     - HubSpot Marketing Hub includes email. Assess: is Mailchimp adding value beyond what HubSpot provides?
     - Signal: compare total_subscribers vs. total_contacts ratio and automation depth in each.
  b) HubSpot Analytics vs. GA4
     - These are complementary, not redundant — but assess whether both are being used appropriately.
     - HubSpot: CRM-linked revenue attribution. GA4: behavioral web analytics. Overlap risk: conflicting data.
  c) CDP Event Tracking vs. GA4 Event Tracking
     - Both track events but serve different purposes. Assess for duplication risk vs. appropriate parallel tracking.
     - Signal: events_tracked (CDP) vs. conversion_events_configured (GA4).

**2. Missing Capabilities Gap Analysis**

Assess the stack against these capability categories. For each:
  → Present / Absent / Partially covered
  → Business Impact of Gap: High / Medium / Low
  → Priority: P1 (address now) / P2 (next quarter) / P3 (next year)

Categories:
  - Multi-touch attribution (beyond last-click)
  - Landing page A/B testing (beyond email)
  - Behavioral personalization engine
  - Data warehouse / BI layer (BigQuery, Looker, etc.)
  - Reverse ETL (warehouse → CRM enrichment)
  - Ad platform integration (Meta, Google Ads audience sync)
  - Social media management
  - SEO / content performance tracking
  - Customer success / retention tooling

**3. Stack Complexity Assessment**
Calculate a complexity proxy:
  - Contact scale: total_contacts
  - Traffic scale: monthly_active_users
  - Tool count: 5
  - Assess: is a 5-tool stack appropriate for this contact volume and traffic level?
  - Cite the general guideline: 5-tool stacks are appropriate for 5K-50K contacts; above that, CDP becomes essential.

**4. Consolidation Opportunities**
Based on the overlap analysis, identify 1-2 concrete consolidation moves.
For each: state the annual cost saving potential (directional, not fabricated), migration complexity, and the trigger condition (when to do it).

**5. Recommended Additions (Free/Freemium Only)**
Identify up to 3 tools to ADD that close the most impactful gaps.
For each: tool name, specific gap it closes, free tier limits, and setup effort.

---

DATA GAPS
Note signals that would sharpen the redundancy assessment.

---

SCORING RATIONALE
Explain what drives the score. 10 = maximum efficiency; 1 = severe redundancy and gaps.

STACK EFFICIENCY SCORE: X/10"""

    return call_llm(prompt, system=SKILL_REDUNDANCY)


# ============================================
# META-AGENT: AUDIT ORCHESTRATOR
# ============================================

def run_full_audit(data):
    """Orchestrates all 6 specialist agents and produces the final audit."""
    results = {}
    agents = [
        ("data_quality", "🔍 Data Quality", agent_data_quality),
        ("integration", "🔗 Integration Health", agent_integration),
        ("performance", "📈 Performance", agent_performance),
        ("compliance", "🔒 Compliance & Privacy", agent_compliance),
        ("optimization", "⚡ Optimization", agent_optimization),
        ("redundancy", "🔄 Redundancy & Gaps", agent_redundancy),
    ]

    log = []
    for key, label, agent_fn in agents:
        print(f"\n{'='*50}")
        print(f"🔧 Running: {label} Agent...")
        print(f"{'='*50}")
        try:
            result = agent_fn(data)
            results[key] = {"label": label, "output": result, "status": "success"}
            log.append(f"✅ {label}: Complete")
            print(f"✅ {label}: Done")
        except Exception as e:
            results[key] = {"label": label, "output": f"Error: {str(e)}", "status": "error"}
            log.append(f"❌ {label}: Failed — {str(e)}")
            print(f"❌ {label}: Failed — {str(e)}")

    # ============ SELF-REVIEW / EXECUTIVE SUMMARY AGENT ============
    print(f"\n{'='*50}")
    print(f"🧠 Running: Executive Summary Agent...")
    print(f"{'='*50}")

    all_outputs = "\n\n".join([
        f"--- {r['label']} ---\n{r['output']}"
        for r in results.values()
        if r["status"] == "success"
    ])

    executive_summary = call_llm(
        f"""You are synthesizing a complete martech stack audit. Below are the verbatim outputs from 6 specialist agents. Your job is to synthesize — not add new analysis.

{all_outputs}

Produce an EXECUTIVE SUMMARY following this exact structure:

**VERDICT** (3 sentences max)
State: overall health, the single most critical issue, the single most important action.

**SCORE CALCULATION**
List all 6 agent scores, show the arithmetic average, state the Overall Stack Health Score.

**TRAFFIC LIGHT SUMMARY**
Six lines, one per dimension: [emoji] [Dimension]: [one-line finding drawn directly from that agent's report]

**TOP 3 CRITICAL ISSUES** (from 🔴 findings in agent reports only)
For each: source agent, specific finding, urgency rationale, immediate action.

**TOP 3 QUICK WINS** (from Quick Win recommendations in agent reports only)
For each: source agent, specific action, expected outcome, effort.

**90-DAY ACTION PLAN**
Days 1-30 (Foundation): 2-3 items — compliance and data quality fixes first
Days 31-60 (Integration): 2-3 items — fix data flows and sync issues
Days 61-90 (Performance): 2-3 items — optimize and scale what's working

**STACK MATURITY LEVEL**
State: Beginner / Developing / Intermediate / Advanced / Best-in-Class
Explain: what single capability would advance them to the next level?""",
        system=SKILL_EXECUTIVE_SUMMARY
    )

    results["executive_summary"] = {
        "label": "📋 Executive Summary",
        "output": executive_summary,
        "status": "success"
    }

    print(f"✅ Executive Summary: Done")
    print(f"\n🎉 FULL AUDIT COMPLETE — {len([r for r in results.values() if r['status'] == 'success'])}/{len(results)} agents succeeded")

    return results


# ============ QUICK TEST ============

if __name__ == "__main__":
    sample_data = {
        "crm": {
            "total_contacts": 5000,
            "contacts_with_email": 75,
            "contacts_with_phone": 40,
            "contacts_with_company": 60,
            "duplicate_rate": 8,
            "lifecycle_stages_used": 4,
            "deals_in_pipeline": 120,
            "avg_deal_value": 2500,
            "lead_sources_tracked": 5,
            "inactive_contacts_pct": 35,
            "custom_properties_count": 15
        },
        "cdp": {
            "sources_connected": 3,
            "destinations_connected": 4,
            "events_tracked": 25,
            "monthly_event_volume": 500000,
            "identity_resolution_rate": 55,
            "failed_events_pct": 3,
            "user_traits_captured": 12,
            "event_naming_convention": "Partially — some inconsistency",
            "pii_controls": "Partially"
        },
        "tag_manager": {
            "total_tags": 18,
            "analytics_tags": 5,
            "marketing_tags": 8,
            "custom_html_tags": 4,
            "triggers_count": 12,
            "consent_mode_enabled": "Partially",
            "tag_firing_rules": 60,
            "version_published_recently": "Yes",
            "environments_configured": "No"
        },
        "analytics": {
            "monthly_active_users": 25000,
            "bounce_rate": 55,
            "avg_session_duration_sec": 120,
            "conversion_events_configured": 3,
            "custom_dimensions": 4,
            "data_retention_setting": "2 months (default)",
            "cross_domain_tracking": "No",
            "google_signals_enabled": "No",
            "bigquery_linked": "No",
            "top_channel_breakdown": "Organic Search"
        },
        "campaigns": {
            "total_subscribers": 3000,
            "list_count": 3,
            "avg_open_rate": 22,
            "avg_click_rate": 3,
            "unsubscribe_rate": 0.5,
            "campaigns_last_30_days": 6,
            "segments_used": 4,
            "automations_active": 2,
            "ab_tests_run_last_90_days": 1,
            "personalization_used": "Basic — name merge tags only"
        }
    }

    results = run_full_audit(sample_data)
    print("\n\n" + "="*60)
    print("📋 EXECUTIVE SUMMARY")
    print("="*60)
    print(results["executive_summary"]["output"])
