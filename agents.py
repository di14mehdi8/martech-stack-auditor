import os
import json
from dotenv import load_dotenv
from groq import Groq
from config import BENCHMARKS

load_dotenv()

def get_api_key():
    try:
	return st.secrets("GROQ_API_KEY")
    except:
	return os.getenv("GROQ_API_KEY")

import streamlit as st
client = Groq(api_key=get_api_key)

def call_llm(prompt, system="You are a senior martech consultant who has audited 200+ marketing technology stacks."):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )
    return response.choices[0].message.content

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
# ============================================

def agent_data_quality(data):
    stack_str = format_stack_data(data)
    benchmarks_str = json.dumps(BENCHMARKS, indent=2)

    prompt = f"""You are auditing the DATA QUALITY of this martech stack.

STACK DATA:
{stack_str}

INDUSTRY BENCHMARKS:
{benchmarks_str}

Analyze the following and be SPECIFIC with numbers:

1. **Contact Data Completeness** — What % of CRM contacts have email, phone, company? How does this compare to best practice (90%+ for email)?

2. **Duplicate Assessment** — The duplicate rate is reported. Is this acceptable? What's the estimated number of duplicate records?

3. **Data Decay** — What % of contacts are inactive 90+ days? What does this mean for deliverability and list health?

4. **Event Data Quality** — Look at CDP failed events %, event naming conventions. Are there data quality risks?

5. **Identity Resolution** — What's the identity resolution rate? How does this compare to the benchmark?

For each area give:
- Current state (use actual numbers from the data)
- Benchmark comparison
- Risk level: 🟢 Good, 🟡 Warning, 🔴 Critical
- Specific recommendation

End with a DATA QUALITY SCORE out of 10."""

    return call_llm(prompt)

# ============================================
# AGENT 2: INTEGRATION AGENT
# ============================================

def agent_integration(data):
    stack_str = format_stack_data(data)

    prompt = f"""You are auditing the INTEGRATION HEALTH of this martech stack.

The stack consists of:
- CRM: HubSpot
- CDP: RudderStack/Segment
- Tag Manager: Google Tag Manager
- Analytics: Google Analytics 4
- Campaign Management: Mailchimp

STACK DATA:
{stack_str}

Analyze:

1. **CDP as Integration Hub** — With {{sources_connected}} sources and {{destinations_connected}} destinations, is the CDP being used as the central data bus? What connections are likely missing?

2. **CRM ↔ Campaign Tool Sync** — Are HubSpot contacts likely syncing with Mailchimp? Look at contact counts vs subscriber counts for clues. Identify risks of data silos.

3. **Tag Manager ↔ Analytics ↔ CDP** — Is GTM properly feeding both GA4 and the CDP? Look at tag counts and event counts for clues.

4. **BigQuery Export** — Is GA4 connected to BigQuery? What are they missing by not having this?

5. **Data Flow Gaps** — Based on all the data, identify the TOP 3 integration gaps that are likely causing data loss or inconsistency.

For each area give:
- Current state assessment
- Risk level: 🟢 Good, 🟡 Warning, 🔴 Critical
- Specific fix with tool names

End with an INTEGRATION SCORE out of 10."""

    return call_llm(prompt)

# ============================================
# AGENT 3: PERFORMANCE AGENT
# ============================================

def agent_performance(data):
    stack_str = format_stack_data(data)
    benchmarks_str = json.dumps(BENCHMARKS, indent=2)

    prompt = f"""You are auditing the PERFORMANCE of this martech stack.

STACK DATA:
{stack_str}

INDUSTRY BENCHMARKS:
{benchmarks_str}

Analyze:

1. **Email Performance** — Open rate, click rate, unsubscribe rate vs benchmarks. Are they above or below average? Calculate click-to-open ratio.

2. **Website Performance** — Bounce rate, session duration, MAU. How healthy is the traffic? Is the bounce rate concerning?

3. **Pipeline Performance** — Deals in pipeline × avg deal value = pipeline value. How many lead sources are tracked? Is attribution likely working?

4. **Campaign Velocity** — Campaigns per month, automations active, A/B tests run. Is the team executing enough? Are they optimizing?

5. **Audience Utilization** — Segments used in campaigns vs total contacts. Is personalization being leveraged?

For each area:
- Calculate specific metrics from the data
- Compare to benchmarks with 🟢🟡🔴
- Give a specific improvement with expected impact

End with a PERFORMANCE SCORE out of 10."""

    return call_llm(prompt)

# ============================================
# AGENT 4: COMPLIANCE AGENT
# ============================================

def agent_compliance(data):
    stack_str = format_stack_data(data)

    prompt = f"""You are auditing the PRIVACY & COMPLIANCE posture of this martech stack.

STACK DATA:
{stack_str}

Analyze for GDPR, CCPA, and general privacy best practices:

1. **Consent Management** — Is GTM Consent Mode configured? What's the current state? What's the risk?

2. **PII Controls** — Is the CDP filtering PII before sending to destinations? What data is likely leaking?

3. **Data Retention** — GA4 retention setting. Is the default 2-month setting causing data loss? What should it be?

4. **Data Minimization** — Look at custom properties in CRM, traits in CDP. Is there evidence of collecting more data than needed?

5. **Third-Party Tag Risk** — How many custom HTML tags in GTM? Each one is a potential data leak. Assess the risk.

6. **Email Compliance** — Unsubscribe rate, list management. Are there signs of potential CAN-SPAM or GDPR issues?

For each area:
- Current state
- Risk level: 🟢 Compliant, 🟡 At Risk, 🔴 Non-Compliant
- Specific remediation step

End with a COMPLIANCE SCORE out of 10."""

    return call_llm(prompt)

# ============================================
# AGENT 5: OPTIMIZATION AGENT
# ============================================

def agent_optimization(data):
    stack_str = format_stack_data(data)

    prompt = f"""You are a martech optimization specialist. Based on this stack data, identify QUICK WINS.

STACK DATA:
{stack_str}

Provide exactly 10 optimization recommendations ranked by IMPACT and EFFORT:

For each recommendation provide:
- **Title**: Clear action item
- **Impact**: High / Medium / Low
- **Effort**: Quick Win (< 1 day) / Medium (1-5 days) / Large (5+ days)
- **Tool**: Which tool to configure
- **Details**: Step-by-step what to do (be specific, not generic)
- **Expected Result**: What metric will improve and by how much (estimate)

Focus on:
- Unused features in their current tools
- Easy configuration changes
- Low-hanging fruit in email, analytics, and CRM
- Things they're clearly NOT doing that they should be

Prioritize Quick Wins with High Impact first.

End with an OPTIMIZATION OPPORTUNITY SCORE out of 10 (10 = tons of easy improvements available, 1 = already optimized)."""

    return call_llm(prompt)

# ============================================
# AGENT 6: REDUNDANCY & GAP AGENT
# ============================================

def agent_redundancy(data):
    stack_str = format_stack_data(data)

    prompt = f"""You are auditing this martech stack for REDUNDANCIES and GAPS.

Stack: HubSpot (CRM) + RudderStack (CDP) + GTM (Tag Manager) + GA4 (Analytics) + Mailchimp (Campaigns)

STACK DATA:
{stack_str}

Analyze:

1. **Overlapping Capabilities**:
   - HubSpot has email marketing built-in AND they're using Mailchimp. Is this redundant? What should they consolidate?
   - HubSpot has analytics AND they're using GA4. Where should each be used?
   - CDP tracks events AND GA4 tracks events. Is there duplication?

2. **Missing Capabilities** — Based on this stack, what's MISSING?
   Consider: attribution, A/B testing beyond email, personalization engine, data warehouse, reverse ETL, landing page optimization, social management, ad platform integration.

3. **Stack Complexity Score** — Is this stack too complex for their apparent size (based on contact counts and traffic)?

4. **Consolidation Opportunities** — Could they eliminate a tool and save money/complexity?

5. **Recommended Additions** — Top 3 tools they should ADD (free/cheap options only).

For each finding:
- Specific assessment
- 💰 Cost impact (saving or investment needed)
- Priority: P1 (now) / P2 (next quarter) / P3 (later)

End with a STACK EFFICIENCY SCORE out of 10."""

    return call_llm(prompt)

# ============================================
# META-AGENT: AUDIT ORCHESTRATOR
# ============================================

def run_full_audit(data):
    """Orchestrates all 6 agents and produces the final audit."""
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

    # ============ SELF-REVIEW AGENT ============
    print(f"\n{'='*50}")
    print(f"🧠 Running: Self-Review Agent...")
    print(f"{'='*50}")

    all_outputs = "\n\n".join([
        f"--- {r['label']} ---\n{r['output']}"
        for r in results.values()
        if r["status"] == "success"
    ])

    executive_summary = call_llm(
        f"""You are reviewing a complete martech stack audit. Below are the outputs from 6 specialist agents.

{all_outputs}

Create an EXECUTIVE SUMMARY that includes:

1. **Overall Stack Health Score** — Average the 6 scores, give a single score out of 10
2. **Traffic Light Summary** — One line per area with 🟢🟡🔴
3. **Top 3 Critical Issues** — The most urgent problems to fix NOW
4. **Top 3 Quick Wins** — Easiest improvements with biggest impact
5. **90-Day Action Plan** — Prioritized list of what to do in the next 3 months
6. **Stack Maturity Level** — Rate as: Beginner / Developing / Intermediate / Advanced / Best-in-Class

Keep it concise and executive-friendly. Use bullet points. No fluff.""",
        system="You are a CMO-level martech advisor presenting to the C-suite."
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
    # Test with sample data
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
