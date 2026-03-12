
# ============================================
# MarTech Stack Auditor — Data Configuration
# ============================================

STACK_DEFINITION = {
    "crm": {
        "name": "CRM (HubSpot)",
        "icon": "🏢",
        "fields": {
            "total_contacts": {
                "label": "Total Contacts",
                "type": "number",
                "default": 5000,
                "help": "Total contact records in HubSpot"
            },
            "contacts_with_email": {
                "label": "Contacts with Email (%)",
                "type": "slider",
                "min": 0, "max": 100, "default": 75,
                "help": "Percentage of contacts that have an email address"
            },
            "contacts_with_phone": {
                "label": "Contacts with Phone (%)",
                "type": "slider",
                "min": 0, "max": 100, "default": 40,
                "help": "Percentage of contacts that have a phone number"
            },
            "contacts_with_company": {
                "label": "Contacts with Company (%)",
                "type": "slider",
                "min": 0, "max": 100, "default": 60,
                "help": "Percentage of contacts linked to a company"
            },
            "duplicate_rate": {
                "label": "Estimated Duplicate Rate (%)",
                "type": "slider",
                "min": 0, "max": 50, "default": 8,
                "help": "Estimated % of duplicate contact records"
            },
            "lifecycle_stages_used": {
                "label": "Lifecycle Stages Actively Used",
                "type": "number",
                "default": 4,
                "help": "How many lifecycle stages have contacts in them (subscriber, lead, MQL, SQL, customer, etc.)"
            },
            "deals_in_pipeline": {
                "label": "Active Deals in Pipeline",
                "type": "number",
                "default": 120,
                "help": "Number of open deals"
            },
            "avg_deal_value": {
                "label": "Average Deal Value ($)",
                "type": "number",
                "default": 2500,
                "help": "Average dollar value of deals"
            },
            "lead_sources_tracked": {
                "label": "Lead Sources Being Tracked",
                "type": "number",
                "default": 5,
                "help": "Number of distinct lead sources (organic, paid, referral, etc.)"
            },
            "inactive_contacts_pct": {
                "label": "Inactive Contacts — No Activity 90+ Days (%)",
                "type": "slider",
                "min": 0, "max": 100, "default": 35,
                "help": "% of contacts with no activity in the last 90 days"
            },
            "custom_properties_count": {
                "label": "Custom Properties Created",
                "type": "number",
                "default": 15,
                "help": "Number of custom contact/deal properties"
            }
        }
    },
    "cdp": {
        "name": "CDP (RudderStack / Segment)",
        "icon": "🔀",
        "fields": {
            "sources_connected": {
                "label": "Sources Connected",
                "type": "number",
                "default": 3,
                "help": "Number of data sources (website, app, server, etc.)"
            },
            "destinations_connected": {
                "label": "Destinations Connected",
                "type": "number",
                "default": 4,
                "help": "Number of downstream tools receiving data"
            },
            "events_tracked": {
                "label": "Unique Events Tracked",
                "type": "number",
                "default": 25,
                "help": "Number of distinct event types (page view, sign up, purchase, etc.)"
            },
            "monthly_event_volume": {
                "label": "Monthly Event Volume",
                "type": "number",
                "default": 500000,
                "help": "Total events per month across all sources"
            },
            "identity_resolution_rate": {
                "label": "Identity Resolution Rate (%)",
                "type": "slider",
                "min": 0, "max": 100, "default": 55,
                "help": "% of events that can be tied to a known user"
            },
            "failed_events_pct": {
                "label": "Failed/Dropped Events (%)",
                "type": "slider",
                "min": 0, "max": 30, "default": 3,
                "help": "% of events that fail delivery to destinations"
            },
            "user_traits_captured": {
                "label": "User Traits Captured",
                "type": "number",
                "default": 12,
                "help": "Number of identify traits (name, email, plan, etc.)"
            },
            "event_naming_convention": {
                "label": "Consistent Event Naming Convention?",
                "type": "select",
                "options": ["Yes — strict schema", "Partially — some inconsistency", "No — ad hoc naming"],
                "default": "Partially — some inconsistency",
                "help": "Is there a documented naming convention for events?"
            },
            "pii_controls": {
                "label": "PII Filtering Configured?",
                "type": "select",
                "options": ["Yes", "Partially", "No"],
                "default": "Partially",
                "help": "Are PII fields being filtered/hashed before sending to destinations?"
            }
        }
    },
    "tag_manager": {
        "name": "Tag Manager (GTM)",
        "icon": "🏷️",
        "fields": {
            "total_tags": {
                "label": "Total Tags",
                "type": "number",
                "default": 18,
                "help": "Total number of tags in the container"
            },
            "analytics_tags": {
                "label": "Analytics Tags",
                "type": "number",
                "default": 5,
                "help": "Tags for analytics (GA4, Hotjar, etc.)"
            },
            "marketing_tags": {
                "label": "Marketing/Ad Tags",
                "type": "number",
                "default": 8,
                "help": "Tags for ad platforms (Meta Pixel, Google Ads, etc.)"
            },
            "custom_html_tags": {
                "label": "Custom HTML Tags",
                "type": "number",
                "default": 4,
                "help": "Number of custom HTML/JS tags (higher = more risk)"
            },
            "triggers_count": {
                "label": "Total Triggers",
                "type": "number",
                "default": 12,
                "help": "Number of trigger configurations"
            },
            "consent_mode_enabled": {
                "label": "Consent Mode Configured?",
                "type": "select",
                "options": ["Yes — full implementation", "Partially", "No"],
                "default": "Partially",
                "help": "Is Google Consent Mode or equivalent set up?"
            },
            "tag_firing_rules": {
                "label": "Tags with Specific Firing Rules (%)",
                "type": "slider",
                "min": 0, "max": 100, "default": 60,
                "help": "% of tags that fire on specific triggers vs 'All Pages'"
            },
            "version_published_recently": {
                "label": "Container Published in Last 30 Days?",
                "type": "select",
                "options": ["Yes", "No"],
                "default": "Yes",
                "help": "Has the GTM container been updated recently?"
            },
            "environments_configured": {
                "label": "Environments Configured (Dev/Staging/Prod)?",
                "type": "select",
                "options": ["Yes", "No"],
                "default": "No",
                "help": "Are GTM environments being used for safe testing?"
            }
        }
    },
    "analytics": {
        "name": "Analytics (GA4)",
        "icon": "📊",
        "fields": {
            "monthly_active_users": {
                "label": "Monthly Active Users",
                "type": "number",
                "default": 25000,
                "help": "MAU from GA4"
            },
            "bounce_rate": {
                "label": "Bounce Rate (%)",
                "type": "slider",
                "min": 0, "max": 100, "default": 55,
                "help": "Site-wide bounce rate"
            },
            "avg_session_duration_sec": {
                "label": "Avg Session Duration (seconds)",
                "type": "number",
                "default": 120,
                "help": "Average session duration in seconds"
            },
            "conversion_events_configured": {
                "label": "Conversion Events Configured",
                "type": "number",
                "default": 3,
                "help": "Number of events marked as conversions in GA4"
            },
            "custom_dimensions": {
                "label": "Custom Dimensions Created",
                "type": "number",
                "default": 4,
                "help": "Number of custom dimensions configured"
            },
            "data_retention_setting": {
                "label": "Data Retention Period",
                "type": "select",
                "options": ["2 months (default)", "14 months", "Custom"],
                "default": "2 months (default)",
                "help": "GA4 data retention setting"
            },
            "cross_domain_tracking": {
                "label": "Cross-Domain Tracking Configured?",
                "type": "select",
                "options": ["Yes", "No", "Not needed"],
                "default": "No",
                "help": "Is cross-domain tracking set up if you have multiple domains?"
            },
            "google_signals_enabled": {
                "label": "Google Signals Enabled?",
                "type": "select",
                "options": ["Yes", "No"],
                "default": "No",
                "help": "Is Google Signals turned on for demographics/cross-device?"
            },
            "bigquery_linked": {
                "label": "BigQuery Export Linked?",
                "type": "select",
                "options": ["Yes", "No"],
                "default": "No",
                "help": "Is the free BigQuery export enabled?"
            },
            "top_channel_breakdown": {
                "label": "Top Traffic Channel",
                "type": "select",
                "options": ["Organic Search", "Direct", "Paid Search", "Social", "Referral", "Email"],
                "default": "Organic Search",
                "help": "Primary traffic source"
            }
        }
    },
    "campaigns": {
        "name": "Campaign Management (Mailchimp)",
        "icon": "📧",
        "fields": {
            "total_subscribers": {
                "label": "Total Subscribers",
                "type": "number",
                "default": 3000,
                "help": "Total email subscribers"
            },
            "list_count": {
                "label": "Number of Lists/Audiences",
                "type": "number",
                "default": 3,
                "help": "Number of separate audience lists"
            },
            "avg_open_rate": {
                "label": "Average Open Rate (%)",
                "type": "slider",
                "min": 0, "max": 80, "default": 22,
                "help": "Average email open rate"
            },
            "avg_click_rate": {
                "label": "Average Click Rate (%)",
                "type": "slider",
                "min": 0, "max": 30, "default": 3,
                "help": "Average email click-through rate"
            },
            "unsubscribe_rate": {
                "label": "Unsubscribe Rate (%)",
                "type": "slider",
                "min": 0.0, "max": 5.0, "default": 0.5,
                "help": "Average unsubscribe rate per campaign"
            },
            "campaigns_last_30_days": {
                "label": "Campaigns Sent (Last 30 Days)",
                "type": "number",
                "default": 6,
                "help": "Number of campaigns sent in the past month"
            },
            "segments_used": {
                "label": "Active Segments",
                "type": "number",
                "default": 4,
                "help": "Number of audience segments being used"
            },
            "automations_active": {
                "label": "Active Automations/Journeys",
                "type": "number",
                "default": 2,
                "help": "Number of active email automations"
            },
            "ab_tests_run_last_90_days": {
                "label": "A/B Tests Run (Last 90 Days)",
                "type": "number",
                "default": 1,
                "help": "Number of A/B tests conducted"
            },
            "personalization_used": {
                "label": "Personalization Used?",
                "type": "select",
                "options": ["Yes — dynamic content", "Basic — name merge tags only", "No"],
                "default": "Basic — name merge tags only",
                "help": "Level of email personalization"
            }
        }
    }
}

# ============ INDUSTRY BENCHMARKS ============

BENCHMARKS = {
    "email_open_rate": {"good": 25, "average": 20, "poor": 15},
    "email_click_rate": {"good": 4, "average": 2.5, "poor": 1.5},
    "bounce_rate": {"good": 40, "average": 55, "poor": 70},
    "identity_resolution": {"good": 70, "average": 50, "poor": 30},
    "data_completeness_email": {"good": 90, "average": 75, "poor": 60},
    "duplicate_rate": {"good": 3, "average": 8, "poor": 15},
    "inactive_contacts": {"good": 20, "average": 35, "poor": 50}
}

def get_all_field_keys():
    """Returns a flat dict of all field values for agent context."""
    result = {}
    for tool_key, tool_data in STACK_DEFINITION.items():
        for field_key, field_config in tool_data["fields"].items():
            result[f"{tool_key}__{field_key}"] = field_config
    return result
