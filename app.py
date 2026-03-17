import streamlit as st
import re
import time
import logging
from datetime import datetime
from io import BytesIO
from config import STACK_DEFINITION, BENCHMARKS
from agents import run_full_audit, format_stack_data
from charts import create_radar_chart, create_score_gauge, create_bar_comparison

# ReportLab — PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, ListFlowable, ListItem, PageBreak
)
from reportlab.platypus.flowables import Image as RLImage
from reportlab.pdfgen import canvas as pdf_canvas

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="MarTech Stack Auditor",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS — ENTERPRISE GRADE
# ============================================

st.markdown("""
<style>
    /* ===== FONTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ===== GLOBAL ===== */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* ===== HEADER ===== */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 2.5rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .main-header h1 {
        color: white;
        font-size: 1.85rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        margin: 0;
        line-height: 1.5;
    }
    .version-badge {
        display: inline-block;
        background: rgba(99,102,241,0.2);
        color: #a5b4fc;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 500;
        margin-left: 12px;
        vertical-align: middle;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: #fafbfc;
        border-right: 1px solid #e2e8f0;
    }

    .sidebar-section-title {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #94a3b8;
        margin: 1.5rem 0 0.8rem 0;
        padding: 0;
    }

    .connection-item {
        display: flex;
        align-items: center;
        padding: 10px 14px;
        margin: 4px 0;
        border-radius: 8px;
        background: white;
        border: 1px solid #e2e8f0;
        transition: all 0.15s ease;
    }
    .connection-item:hover {
        border-color: #cbd5e1;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .connection-item.future {
        background: #f8fafc;
        border: 1px dashed #e2e8f0;
        opacity: 0.55;
    }

    .conn-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 12px;
        flex-shrink: 0;
    }
    .conn-indicator.active {
        background: #22c55e;
        box-shadow: 0 0 6px rgba(34,197,94,0.4);
    }
    .conn-indicator.inactive {
        background: #cbd5e1;
    }

    .conn-text {
        flex: 1;
    }
    .conn-name {
        font-size: 0.82rem;
        font-weight: 500;
        color: #1e293b;
        line-height: 1.3;
    }
    .conn-method {
        font-size: 0.68rem;
        color: #94a3b8;
        font-weight: 400;
    }

    .conn-badge {
        font-size: 0.6rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .conn-badge.live {
        background: #dcfce7;
        color: #15803d;
    }
    .conn-badge.soon {
        background: #f1f5f9;
        color: #94a3b8;
    }

    /* ===== METRIC CARDS ===== */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.3rem 1rem;
        text-align: center;
        transition: all 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        border-color: #cbd5e1;
    }
    .metric-card .score {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.2rem 0;
        letter-spacing: -1px;
    }
    .metric-card .label {
        font-size: 0.72rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card .sublabel {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 2px;
    }
    .score-green { color: #16a34a; }
    .score-yellow { color: #d97706; }
    .score-red { color: #dc2626; }

    /* ===== SECTION HEADERS ===== */
    .section-header {
        border-left: 3px solid #6366f1;
        padding: 0.7rem 1.2rem;
        margin: 2rem 0 1rem 0;
        background: #f8fafc;
        border-radius: 0 8px 8px 0;
    }
    .section-header h3 {
        margin: 0;
        color: #0f172a;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: -0.2px;
    }

    /* ===== STATUS PILLS ===== */
    .pill {
        display: inline-block;
        padding: 3px 14px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .pill-green {
        background: #dcfce7;
        color: #15803d;
    }
    .pill-yellow {
        background: #fef3c7;
        color: #b45309;
    }
    .pill-red {
        background: #fee2e2;
        color: #b91c1c;
    }

    /* ===== TOOL INPUT SECTIONS ===== */
    .tool-hint {
        background: #f0f4ff;
        border: 1px solid #dbeafe;
        border-radius: 8px;
        padding: 0.7rem 1rem;
        font-size: 0.82rem;
        color: #3b82f6;
        margin-bottom: 1rem;
    }

    /* ===== TABS ===== */

.stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: F1F5F9_1;
        padding: 4px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 18px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 500;
        color: 334155_1 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: 0F172A_1 !important;
        background: ffffff;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: 1E293B_1 !important;
        background: E2E8F0_1;
    }

    /* ===== BUTTONS ===== */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
        border: none;
        border-radius: 10px;
        padding: 0.7rem 2rem;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.2px;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(99,102,241,0.35);
    }

    /* ===== FOOTER ===== */
    .app-footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.78rem;
        padding: 1.5rem 0;
        line-height: 1.8;
    }
    .app-footer strong {
        color: #64748b;
    }

    /* ===== HIDE STREAMLIT DEFAULTS ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================

if "audit_results" not in st.session_state:
    st.session_state.audit_results = None
if "audit_running" not in st.session_state:
    st.session_state.audit_running = False
if "stack_data" not in st.session_state:
    st.session_state.stack_data = {}
if "generation_time" not in st.session_state:
    st.session_state.generation_time = None
if "pdf_cache" not in st.session_state:
    st.session_state.pdf_cache = None

# ============================================
# HELPERS
# ============================================

def extract_score(text):
    patterns = [
        r'(?:overall|total|final)?[\s]*(?:score|rating)[\s]*(?::|is|=)[\s]*(\d+(?:\.\d+)?)\s*(?:/\s*10|out of 10)',
        r'(\d+(?:\.\d+)?)\s*(?:/\s*10|out of 10)',
        r'(?:score|rating)[\s]*(?::|is|=)[\s]*(\d+(?:\.\d+)?)',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            score = float(matches[-1])
            if 0 <= score <= 10:
                return score
    return 5.0

def score_color_class(score):
    if score >= 7: return "score-green"
    elif score >= 5: return "score-yellow"
    return "score-red"

def score_pill(score):
    if score >= 7: return '<span class="pill pill-green">Healthy</span>'
    elif score >= 5: return '<span class="pill pill-yellow">Needs Attention</span>'
    return '<span class="pill pill-red">Critical</span>'

def format_elapsed(seconds):
    if seconds >= 60:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}m {s}s"
    return f"{seconds:.1f}s"

def strip_markdown(text: str) -> str:
    """Remove markdown syntax, preserving plain text and emojis."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
    return text.strip()


# ============================================
# PDF GENERATION
# ============================================

class PageNumCanvas(pdf_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        pdf_canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(num_pages)
            pdf_canvas.Canvas.showPage(self)
        pdf_canvas.Canvas.save(self)

    def _draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#94a3b8"))
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(72, 52, letter[0] - 72, 52)
        self.drawString(72, 38, f"Page {self._pageNumber} of {page_count}")
        self.drawRightString(
            letter[0] - 72, 38,
            f"MarTech Stack Auditor — {datetime.now().strftime('%B %d, %Y')}"
        )
        self.restoreState()


def generate_pdf_report(results, score_map, overall_score, stack_data, generation_time_str):
    """Generate a complete PDF audit report. Returns a BytesIO buffer."""
    buffer = BytesIO()
    page_width = letter[0] - 144  # 6.5 inches usable

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=72,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CoverTitle', parent=styles['Title'],
        fontSize=28, textColor=colors.HexColor('#0f172a'),
        spaceAfter=12, fontName='Helvetica-Bold', alignment=1,
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle', parent=styles['Normal'],
        fontSize=14, textColor=colors.HexColor('#64748b'),
        spaceAfter=8, fontName='Helvetica', alignment=1,
    )
    meta_style = ParagraphStyle(
        'Meta', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#94a3b8'),
        spaceAfter=4, fontName='Helvetica', alignment=1,
    )
    h1_style = ParagraphStyle(
        'H1', parent=styles['Heading1'],
        fontSize=16, textColor=colors.HexColor('#0f172a'),
        spaceBefore=16, spaceAfter=8, fontName='Helvetica-Bold',
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=12, textColor=colors.HexColor('#1e293b'),
        spaceBefore=10, spaceAfter=5, fontName='Helvetica-Bold',
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#334155'),
        spaceAfter=5, leading=15, fontName='Helvetica',
    )
    caption_style = ParagraphStyle(
        'Caption', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#94a3b8'),
        spaceAfter=8, fontName='Helvetica', alignment=1,
    )

    story = []

    # ===== COVER PAGE =====
    story.append(Spacer(1, 1.8 * inch))
    story.append(Paragraph("Marketing Audit Report", title_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("MarTech Stack — Comprehensive Analysis", subtitle_style))
    story.append(Spacer(1, 0.4 * inch))
    story.append(HRFlowable(width=page_width, thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", meta_style))
    story.append(Paragraph(f"Generation time: {generation_time_str}", meta_style))
    story.append(Paragraph(f"Overall Stack Health Score: {overall_score}/10", meta_style))
    story.append(Spacer(1, 2.5 * inch))
    story.append(HRFlowable(width=page_width, thickness=0.5, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "Powered by MarTech Stack Auditor · AI-powered audit across 6 critical dimensions",
        meta_style
    ))
    story.append(PageBreak())

    # ===== EXECUTIVE SUMMARY =====
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(HRFlowable(width=page_width, thickness=0.5, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 0.15 * inch))
    if "executive_summary" in results and results["executive_summary"]["status"] == "success":
        for line in results["executive_summary"]["output"].split('\n'):
            line = line.strip()
            if line:
                story.append(Paragraph(strip_markdown(line), body_style))
    story.append(Spacer(1, 0.3 * inch))

    # ===== KEY METRICS TABLE =====
    story.append(Paragraph("Score Summary", h1_style))
    story.append(HRFlowable(width=page_width, thickness=0.5, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 0.15 * inch))

    table_data = [['Dimension', 'Score', 'Status']]
    table_data.append([
        'Overall Stack Health', f"{overall_score}/10",
        'Healthy' if overall_score >= 7 else ('Needs Attention' if overall_score >= 5 else 'Critical')
    ])
    for name, score in score_map.items():
        status = 'Healthy' if score >= 7 else ('Needs Attention' if score >= 5 else 'Critical')
        table_data.append([name, f"{score}/10", status])

    col_widths = [page_width * 0.5, page_width * 0.2, page_width * 0.3]
    metrics_table = Table(table_data, colWidths=col_widths)
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.3 * inch))

    # ===== CHARTS =====
    story.append(Paragraph("Visual Analysis", h1_style))
    story.append(HRFlowable(width=page_width, thickness=0.5, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 0.15 * inch))

    try:
        radar_fig = create_radar_chart(score_map)
        radar_bytes = radar_fig.to_image(format='png', width=800, height=500, scale=1.5)
        radar_buf = BytesIO(radar_bytes)
        chart_h = page_width * 500 / 800
        story.append(RLImage(radar_buf, width=page_width, height=chart_h))
        story.append(Paragraph("Stack Health Radar — Your scores vs. Industry Benchmark (7/10)", caption_style))
        story.append(Spacer(1, 0.2 * inch))
    except Exception:
        logging.exception("Radar chart export failed")

    if stack_data:
        try:
            comparison_data = {
                "Email Open Rate (%)": stack_data.get("campaigns", {}).get("avg_open_rate", 0),
                "Email Click Rate (%)": stack_data.get("campaigns", {}).get("avg_click_rate", 0),
                "Bounce Rate (%)": stack_data.get("analytics", {}).get("bounce_rate", 0),
                "Identity Resolution (%)": stack_data.get("cdp", {}).get("identity_resolution_rate", 0),
                "Data Completeness (%)": stack_data.get("crm", {}).get("contacts_with_email", 0),
            }
            comparison_benchmarks = {
                "Email Open Rate (%)": {"average": BENCHMARKS["email_open_rate"]["good"]},
                "Email Click Rate (%)": {"average": BENCHMARKS["email_click_rate"]["good"]},
                "Bounce Rate (%)": {"average": BENCHMARKS["bounce_rate"]["good"]},
                "Identity Resolution (%)": {"average": BENCHMARKS["identity_resolution"]["good"]},
                "Data Completeness (%)": {"average": BENCHMARKS["data_completeness_email"]["good"]},
            }
            bar_fig = create_bar_comparison(comparison_data, comparison_benchmarks)
            bar_bytes = bar_fig.to_image(format='png', width=700, height=350, scale=1.5)
            bar_buf = BytesIO(bar_bytes)
            bar_h = page_width * 350 / 700
            story.append(RLImage(bar_buf, width=page_width, height=bar_h))
            story.append(Paragraph("Key Metrics vs. Industry Benchmarks", caption_style))
            story.append(Spacer(1, 0.2 * inch))
        except Exception:
            logging.exception("Bar chart export failed")

    story.append(PageBreak())

    # ===== DETAILED FINDINGS =====
    story.append(Paragraph("Detailed Findings", h1_style))
    story.append(HRFlowable(width=page_width, thickness=0.5, color=colors.HexColor('#e2e8f0')))

    agent_keys_pdf = ["data_quality", "integration", "performance", "compliance", "optimization", "redundancy"]
    for key in agent_keys_pdf:
        if key not in results or results[key]["status"] != "success":
            continue
        agent_data = results[key]
        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph(strip_markdown(agent_data['label']), h2_style))

        bullet_items = []
        for line in agent_data["output"].split('\n'):
            line_stripped = line.strip()
            if not line_stripped:
                if bullet_items:
                    story.append(ListFlowable(
                        [ListItem(Paragraph(item, body_style), leftIndent=20) for item in bullet_items],
                        bulletType='bullet', bulletColor=colors.HexColor('#6366f1'),
                    ))
                    bullet_items = []
                story.append(Spacer(1, 0.04 * inch))
                continue

            if re.match(r'^[-*•]\s', line_stripped):
                bullet_items.append(strip_markdown(line_stripped[2:]))
            elif re.match(r'^\d+\.\s', line_stripped):
                bullet_items.append(strip_markdown(re.sub(r'^\d+\.\s*', '', line_stripped)))
            else:
                if bullet_items:
                    story.append(ListFlowable(
                        [ListItem(Paragraph(item, body_style), leftIndent=20) for item in bullet_items],
                        bulletType='bullet', bulletColor=colors.HexColor('#6366f1'),
                    ))
                    bullet_items = []
                clean = strip_markdown(line_stripped)
                if clean:
                    is_heading = re.match(r'^#{1,3}\s', line_stripped) or (
                        line_stripped.startswith('**') and line_stripped.endswith('**')
                    )
                    story.append(Paragraph(clean, h2_style if is_heading else body_style))

        if bullet_items:
            story.append(ListFlowable(
                [ListItem(Paragraph(item, body_style), leftIndent=20) for item in bullet_items],
                bulletType='bullet', bulletColor=colors.HexColor('#6366f1'),
            ))

    doc.build(story, canvasmaker=PageNumCanvas)
    buffer.seek(0)
    return buffer


def render_input_field(tool_key, field_key, field_config):
    unique_key = f"{tool_key}__{field_key}"
    label = field_config["label"]
    help_text = field_config.get("help", "")

    if field_config["type"] == "number":
        return st.number_input(label, value=field_config["default"], min_value=0, help=help_text, key=unique_key)
    elif field_config["type"] == "slider":
        return st.slider(
            label, min_value=field_config.get("min", 0), max_value=field_config.get("max", 100),
            value=field_config["default"], help=help_text, key=unique_key
        )
    elif field_config["type"] == "select":
        options = field_config["options"]
        default_idx = options.index(field_config["default"]) if field_config["default"] in options else 0
        return st.selectbox(label, options=options, index=default_idx, help=help_text, key=unique_key)
    return None

# ============================================
# HEADER
# ============================================

st.markdown("""
<div class="main-header">
    <h1>MarTech Stack Auditor <span class="version-badge">v1.0 Manual Input</span></h1>
    <p>AI-powered audit across 6 critical dimensions — data quality, integrations, performance,
    compliance, optimization, and stack efficiency. Powered by 6 specialist AI agents.</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:

    st.markdown('<div class="sidebar-section-title">Active Connections</div>', unsafe_allow_html=True)

    active_connections = [
        ("HubSpot CRM", "Manual Input"),
        ("RudderStack CDP", "Manual Input"),
        ("Google Tag Manager", "Manual Input"),
        ("Google Analytics 4", "Manual Input"),
        ("Mailchimp", "Manual Input"),
    ]

    for name, method in active_connections:
        st.markdown(f"""
        <div class="connection-item">
            <div class="conn-indicator active"></div>
            <div class="conn-text">
                <div class="conn-name">{name}</div>
                <div class="conn-method">{method}</div>
            </div>
            <span class="conn-badge live">Live</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">Roadmap — v2 Connectors</div>', unsafe_allow_html=True)

    future_connections = [
        "HubSpot API",
        "GA4 Admin API",
        "GTM API",
        "Mailchimp API",
        "RudderStack API",
        "BigQuery Export",
        "Scheduled Audits",
        "Historical Trends",
    ]

    for name in future_connections:
        st.markdown(f"""
        <div class="connection-item future">
            <div class="conn-indicator inactive"></div>
            <div class="conn-text">
                <div class="conn-name">{name}</div>
                <div class="conn-method">Coming soon</div>
            </div>
            <span class="conn-badge soon">v2</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">Audit Configuration</div>', unsafe_allow_html=True)

    audit_depth = st.selectbox(
        "Audit Depth",
        ["Standard — 6 agents", "Deep — 6 agents + follow-up"],
        index=0,
        label_visibility="collapsed"
    )

# ============================================
# MAIN CONTENT
# ============================================

if st.session_state.audit_results is None:

    # ============ DATA INPUT ============

    st.markdown("""
    <div class="section-header">
        <h3>Stack Data Input</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "Provide the metrics from your martech tools below. Approximate values work well — "
        "the AI agents are designed to work with estimates. Hover over the help icons for "
        "guidance on where to find each metric in your tools."
    )

    tool_tab_labels = [
        f"{tool['name']}" for tool in STACK_DEFINITION.values()
    ]
    tool_tabs = st.tabs(tool_tab_labels)

    collected_data = {}

    hints = {
        "crm": "Where to find this: HubSpot → Reports → Contact Analytics, Deals → Pipeline View",
        "cdp": "Where to find this: RudderStack Dashboard → Sources, Destinations, Live Events",
        "tag_manager": "Where to find this: GTM → Workspace overview, Tags list, Triggers list",
        "analytics": "Where to find this: GA4 → Reports → Acquisition, Engagement; Admin → Data Settings",
        "campaigns": "Where to find this: Mailchimp → Audience dashboard, Campaigns tab, Automations"
    }

    for idx, (tool_key, tool_config) in enumerate(STACK_DEFINITION.items()):
        with tool_tabs[idx]:
            st.markdown(f"#### {tool_config['name']}")

            st.markdown(
                f'<div class="tool-hint">{hints.get(tool_key, "")}</div>',
                unsafe_allow_html=True
            )

            tool_data = {}
            fields = list(tool_config["fields"].items())
            col1_fields = fields[:len(fields)//2 + len(fields)%2]
            col2_fields = fields[len(fields)//2 + len(fields)%2:]

            col1, col2 = st.columns(2)

            with col1:
                for field_key, field_config in col1_fields:
                    tool_data[field_key] = render_input_field(tool_key, field_key, field_config)

            with col2:
                for field_key, field_config in col2_fields:
                    tool_data[field_key] = render_input_field(tool_key, field_key, field_config)

            collected_data[tool_key] = tool_data

    # ============ LAUNCH ============

    st.markdown("---")

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown(
            "<div style='text-align:center; margin-bottom:0.5rem; color:#64748b; font-size:0.9rem;'>"
            "Ready to audit — analyzing <strong>49 data points</strong> across <strong>6 dimensions</strong>"
            "</div>",
            unsafe_allow_html=True
        )
        launch = st.button("Launch Full Stack Audit", use_container_width=True, type="primary")

    if launch:
        st.session_state.stack_data = collected_data
        st.session_state.pdf_cache = None

        st.markdown("---")
        progress_bar = st.progress(0)
        status_container = st.status("Initializing audit agents...", expanded=True)

        agent_steps = [
            ("Data Quality Agent", "Analyzing contact completeness, duplicates, and data decay"),
            ("Integration Agent", "Mapping data flows between your 5 tools"),
            ("Performance Agent", "Benchmarking metrics against industry standards"),
            ("Compliance Agent", "Checking GDPR, CCPA, and consent configurations"),
            ("Optimization Agent", "Identifying quick wins and growth opportunities"),
            ("Redundancy Agent", "Finding overlaps and gaps in your stack"),
            ("Executive Summary", "Synthesizing findings into actionable insights"),
        ]

        with status_container:
            for i, (label, desc) in enumerate(agent_steps):
                st.write(f"**{label}** — {desc}")
                progress_bar.progress(i / len(agent_steps))
                if i == 0:
                    _start = time.time()
                    results = run_full_audit(collected_data)
                    st.session_state.generation_time = time.time() - _start
                time.sleep(0.3)
            progress_bar.progress(1.0)

        status_container.update(label="Audit complete — all 7 agents finished", state="complete")
        st.session_state.audit_results = results
        st.rerun()

else:

    # ============ RESULTS ============

    results = st.session_state.audit_results

    # ===== GENERATION TIMER =====
    if st.session_state.generation_time is not None:
        gen_time_str = f"Generated in {format_elapsed(st.session_state.generation_time)}"
        st.markdown(
            f'<div style="text-align:right; color:#94a3b8; font-size:0.78rem; '
            f'margin-bottom:0.5rem; font-family:Inter,sans-serif;">⏱ {gen_time_str}</div>',
            unsafe_allow_html=True
        )

    score_map = {}
    agent_keys = ["data_quality", "integration", "performance", "compliance", "optimization", "redundancy"]
    display_names = {
        "data_quality": "Data Quality",
        "integration": "Integration",
        "performance": "Performance",
        "compliance": "Compliance",
        "optimization": "Optimization",
        "redundancy": "Stack Efficiency"
    }

    for key in agent_keys:
        if key in results and results[key]["status"] == "success":
            score_map[display_names[key]] = extract_score(results[key]["output"])

    overall_score = round(sum(score_map.values()) / len(score_map), 1) if score_map else 0

    # ===== SCORE CARDS =====

    st.markdown("""
    <div class="section-header">
        <h3>Audit Score Overview</h3>
    </div>
    """, unsafe_allow_html=True)

    score_cols = st.columns([1.5] + [1] * len(score_map))

    with score_cols[0]:
        color_class = score_color_class(overall_score)
        pill = score_pill(overall_score)
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="label">Overall Stack Health</div>'
            f'<div class="score {color_class}">{overall_score}</div>'
            f'<div class="sublabel">out of 10 &nbsp; {pill}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    for i, (name, score) in enumerate(score_map.items()):
        with score_cols[i + 1]:
            color_class = score_color_class(score)
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="label">{name}</div>'
                f'<div class="score {color_class}">{score}</div>'
                f'<div class="sublabel">/ 10</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # ===== CHARTS =====

    st.markdown("")
    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        st.markdown("#### Stack Health Radar")
        radar_fig = create_radar_chart(score_map)
        st.plotly_chart(radar_fig, use_container_width=True)

    with chart_col2:
        st.markdown("#### Key Metrics vs Benchmarks")
        data = st.session_state.stack_data
        if data:
            comparison_data = {
                "Email Open Rate (%)": data.get("campaigns", {}).get("avg_open_rate", 0),
                "Email Click Rate (%)": data.get("campaigns", {}).get("avg_click_rate", 0),
                "Bounce Rate (%)": data.get("analytics", {}).get("bounce_rate", 0),
                "Identity Resolution (%)": data.get("cdp", {}).get("identity_resolution_rate", 0),
                "Data Completeness (%)": data.get("crm", {}).get("contacts_with_email", 0),
            }
            comparison_benchmarks = {
                "Email Open Rate (%)": {"average": BENCHMARKS["email_open_rate"]["good"]},
                "Email Click Rate (%)": {"average": BENCHMARKS["email_click_rate"]["good"]},
                "Bounce Rate (%)": {"average": BENCHMARKS["bounce_rate"]["good"]},
                "Identity Resolution (%)": {"average": BENCHMARKS["identity_resolution"]["good"]},
                "Data Completeness (%)": {"average": BENCHMARKS["data_completeness_email"]["good"]},
            }
            bar_fig = create_bar_comparison(comparison_data, comparison_benchmarks)
            st.plotly_chart(bar_fig, use_container_width=True)

    # ===== EXECUTIVE SUMMARY =====

    st.markdown("""
    <div class="section-header">
        <h3>Executive Summary</h3>
    </div>
    """, unsafe_allow_html=True)

    if "executive_summary" in results and results["executive_summary"]["status"] == "success":
        st.markdown(results["executive_summary"]["output"])

    # ===== DETAILED TABS =====

    st.markdown("""
    <div class="section-header">
        <h3>Detailed Findings</h3>
    </div>
    """, unsafe_allow_html=True)

    detail_tabs = st.tabs([
        "Data Quality",
        "Integration",
        "Performance",
        "Compliance",
        "Optimization",
        "Redundancy & Gaps"
    ])

    for idx, key in enumerate(agent_keys):
        with detail_tabs[idx]:
            if key in results and results[key]["status"] == "success":
                agent_data = results[key]
                score = score_map.get(display_names[key], 5)

                gauge_col, content_col = st.columns([1, 3])
                with gauge_col:
                    gauge = create_score_gauge(score, display_names[key])
                    st.plotly_chart(gauge, use_container_width=True)

                with content_col:
                    st.markdown(f"### {agent_data['label']}")
                    st.markdown(score_pill(score), unsafe_allow_html=True)
                    st.markdown("---")

                st.markdown(agent_data["output"])
            else:
                st.error(f"Agent failed: {results.get(key, {}).get('output', 'Unknown error')}")

    # ===== EXPORT =====

    st.markdown("""
    <div class="section-header">
        <h3>Export Report</h3>
    </div>
    """, unsafe_allow_html=True)

    gen_time_str = (
        format_elapsed(st.session_state.generation_time)
        if st.session_state.generation_time else "N/A"
    )

    dl_col1, dl_col2, dl_col3 = st.columns([1, 2, 1])
    with dl_col2:
        try:
            if st.session_state.pdf_cache is None:
                with st.spinner("Building PDF…"):
                    pdf_buf = generate_pdf_report(
                        results, score_map, overall_score,
                        st.session_state.stack_data, gen_time_str
                    )
                    st.session_state.pdf_cache = pdf_buf.getvalue()
            st.download_button(
                label="⬇ Download PDF Report",
                data=st.session_state.pdf_cache,
                file_name="martech_audit_report.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
        except Exception:
            logging.exception("PDF generation failed")
            st.error("PDF generation failed. Please try again.")

    # ===== NEW AUDIT =====

    st.markdown("---")
    new_col1, new_col2, new_col3 = st.columns([1, 2, 1])
    with new_col2:
        if st.button("Run New Audit", use_container_width=True):
            st.session_state.audit_results = None
            st.session_state.stack_data = {}
            st.session_state.generation_time = None
            st.session_state.pdf_cache = None
            st.rerun()

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown("""
<div class="app-footer">
    <strong>MarTech Stack Auditor</strong> v1.0 &nbsp;&middot;&nbsp; Powered by 6 AI Agents
    &nbsp;&middot;&nbsp; Built for Marketing Operations Teams<br>
    v2 Roadmap: API connectors, scheduled audits, historical trending, team collaboration
</div>
""", unsafe_allow_html=True)
