import io
import re
from datetime import date, timedelta
from html import escape
from pathlib import Path

import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)

from agents.travel_agent import travel_agent
import textwrap


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
        .stApp {
            background-color: #f4f7fb;
        }

        .main .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            background-color: #edf3fa;
            border-right: 1px solid #dce5ef;
        }

        .hero {
            background: linear-gradient(120deg, #193b63, #347eb3);
            padding: 42px 35px;
            border-radius: 18px;
            color: white;
            margin-bottom: 28px;
        }

        .hero-label {
            color: #b9dcff;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 2px;
            margin-bottom: 15px;
        }

        .hero h1 {
            color: white !important;
            font-size: 36px;
            font-weight: 750;
            margin-bottom: 14px;
        }

        .hero p {
            color: #f0f6ff !important;
            font-size: 16px;
            line-height: 1.7;
            margin-bottom: 0;
        }

        .feature-card {
            background-color: white;
            padding: 22px 20px;
            border: 1px solid #dfe8f2;
            border-radius: 15px;
            min-height: 140px;
            margin-bottom: 12px;
        }

        .feature-card h3 {
            color: #193b63;
            font-size: 19px;
            margin-bottom: 18px;
        }

        .feature-card p {
            color: #64748b;
            font-size: 14px;
            line-height: 1.6;
        }

        .section-label {
            color: #347eb3;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 2px;
            margin-top: 5px;
            margin-bottom: 8px;
        }

        .footer {
            text-align: center;
            color: #718096;
            padding: 25px 0 10px 0;
            font-size: 14px;
        }

        .result-heading {
            color: #193b63;
            font-size: 29px;
            font-weight: 700;
            margin-bottom: 20px;
        }

        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] button {
            background-color: #245e91 !important;
            color: white !important;
            border: none !important;
            border-radius: 9px !important;
            padding: 12px !important;
            font-weight: 600 !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] button:hover {
            background-color: #193b63 !important;
            color: white !important;
            border: none !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background-color: #193b63;
            color: white;
            border: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# RESPONSE TEXT EXTRACTION
# ============================================================

def extract_report_text(response):
    """Extract only readable text from the final LangChain message."""

    messages = response.get("messages", [])

    if not messages:
        return ""

    content = messages[-1].content

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, dict):
        if content.get("type") == "text":
            return str(content.get("text", "")).strip()
        if "text" in content:
            return str(content["text"]).strip()
        return ""

    if isinstance(content, list):
        text_parts = []

        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    text_parts.append(str(block.get("text", "")))
                elif isinstance(block.get("text"), str):
                    text_parts.append(block["text"])

        return "\n".join(part for part in text_parts if part).strip()

    return str(content).strip()


# ============================================================
# PDF FONT SETUP
# ============================================================

def register_pdf_fonts():
    """
    Register a Unicode font when available so the rupee symbol and
    other common characters render correctly in the downloaded PDF.
    """

    font_candidates = [
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
        (
            Path("C:/Windows/Fonts/segoeui.ttf"),
            Path("C:/Windows/Fonts/seguisb.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]

    for regular_path, bold_path in font_candidates:
        if regular_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("TravelFont", str(regular_path)))

                if bold_path.exists():
                    pdfmetrics.registerFont(
                        TTFont("TravelFont-Bold", str(bold_path))
                    )
                else:
                    pdfmetrics.registerFontFamily(
                        "TravelFont",
                        normal="TravelFont",
                        bold="TravelFont",
                        italic="TravelFont",
                        boldItalic="TravelFont",
                    )

                return "TravelFont", (
                    "TravelFont-Bold" if bold_path.exists() else "TravelFont"
                )
            except Exception:
                continue

    # Standard PDF fonts do not reliably contain the ₹ glyph.
    # The PDF formatter converts ₹ to INR when no Unicode font is found.
    return "Helvetica", "Helvetica-Bold"


# ============================================================
# PDF GENERATOR
# ============================================================

def create_pdf(report_text):
    """Create a formatted PDF from the clean travel-plan text."""

    if not isinstance(report_text, str):
        if isinstance(report_text, dict):
            report_text = report_text.get("text", "")
        elif isinstance(report_text, list):
            report_text = "\n".join(
                str(item.get("text", ""))
                if isinstance(item, dict)
                else str(item)
                for item in report_text
            )
        else:
            report_text = str(report_text)

    report_text = report_text.strip()

    if not report_text:
        raise ValueError("There is no travel-plan text available to create a PDF.")

    regular_font, bold_font = register_pdf_fonts()
    has_unicode_font = regular_font != "Helvetica"

    buffer = io.BytesIO()

    navy = colors.HexColor("#193B63")
    blue = colors.HexColor("#2875AD")
    grey = colors.HexColor("#64748B")
    light_grey = colors.HexColor("#DCE5EF")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        title="AI Travel Plan",
        author="AI Travel Planning Assistant",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=25,
        leading=31,
        textColor=navy,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName=regular_font,
        fontSize=10,
        leading=15,
        textColor=grey,
        alignment=TA_CENTER,
        spaceAfter=18,
    )

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName=bold_font,
        fontSize=12.5,
        leading=17,
        textColor=blue,
        spaceBefore=13,
        spaceAfter=7,
        keepWithNext=True,
    )

    subsection_style = ParagraphStyle(
        "SubsectionHeading",
        parent=styles["Heading3"],
        fontName=bold_font,
        fontSize=10.5,
        leading=14,
        textColor=navy,
        spaceBefore=8,
        spaceAfter=5,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#263445"),
        spaceAfter=5,
    )

    bullet_style = ParagraphStyle(
        "ReportBullet",
        parent=body_style,
        leftIndent=13,
        firstLineIndent=-9,
        spaceAfter=5,
    )

    subbullet_style = ParagraphStyle(
        "ReportSubBullet",
        parent=body_style,
        leftIndent=27,
        firstLineIndent=-9,
        spaceAfter=4,
    )

    story = [
        Spacer(1, 8 * mm),
        Paragraph("YOUR TRAVEL PLAN", title_style),
        Paragraph("AI-Powered Travel Planning Assistant", subtitle_style),
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=blue,
            spaceAfter=14,
        ),
    ]

    def clean_markdown(text):
        """Remove Markdown emphasis markers without creating HTML tags."""
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"__(.*?)__", r"\1", text)
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)

        if not has_unicode_font:
            text = text.replace("₹", "INR ")

        return escape(text)

    for raw_line in report_text.splitlines():
        indentation = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()

        if not line:
            story.append(Spacer(1, 3))
            continue

        if line in ("---", "***", "___"):
            story.append(Spacer(1, 6))
            continue

        # Ignore a duplicate report title if the agent includes one.
        if line.lower().replace("#", "").strip() == "your travel plan":
            continue

        heading_level = 0

        if line.startswith("### "):
            heading_level = 3
            line = line[4:]
        elif line.startswith("## "):
            heading_level = 2
            line = line[3:]
        elif line.startswith("# "):
            heading_level = 1
            line = line[2:]

        # Remove Markdown bullet markers before escaping text.
        bullet_marker = None
        if re.match(r"^[-*•]\s+", line):
            bullet_marker = re.match(r"^[-*•]\s+", line).group(0)
            line = line[len(bullet_marker):]

        formatted_line = clean_markdown(line)

        # Numbered all-caps section headings such as "1. TRIP SUMMARY".
        plain_heading = re.sub(r"<[^>]+>", "", formatted_line)
        is_numbered_section = bool(
            re.match(r"^\d+\.\s+[A-Z][A-Z0-9\s&/-]+$", plain_heading)
        )

        if is_numbered_section or heading_level in (1, 2):
            story.append(Paragraph(formatted_line, section_style))
            continue

        if heading_level == 3:
            story.append(Paragraph(formatted_line, subsection_style))
            continue

        if bullet_marker:
            if indentation >= 2:
                story.append(
                    Paragraph("– " + formatted_line, subbullet_style)
                )
            else:
                story.append(
                    Paragraph("• " + formatted_line, bullet_style)
                )
            continue

        story.append(Paragraph(formatted_line, body_style))

    def add_page_number(canvas, document):
        canvas.saveState()

        page_width, _ = A4

        canvas.setStrokeColor(light_grey)
        canvas.line(
            20 * mm,
            16 * mm,
            page_width - 20 * mm,
            16 * mm,
        )

        canvas.setFont(regular_font, 8)
        canvas.setFillColor(grey)

        canvas.drawString(
            20 * mm,
            10 * mm,
            "AI Travel Planning Assistant",
        )

        canvas.drawRightString(
            page_width - 20 * mm,
            10 * mm,
            f"Page {document.page}",
        )

        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## ✈️ AI Travel Planner")
    st.caption("Your intelligent travel companion")
    st.divider()

    st.markdown("### About the Project")
    st.write(
        "An Agentic AI-powered travel assistant that "
        "creates personalized travel plans using "
        "LangChain, Google Gemini and travel data."
    )

    st.divider()

    st.markdown("### What You Can Do")
    st.markdown(
        """
        - Search available flights
        - Find hotels within budget
        - Discover tourist attractions
        - Generate day-wise itineraries
        - Check weather forecasts
        - Estimate complete trip costs
        """
    )

    st.divider()

    st.caption("Technology Stack")
    st.markdown(
        """
        - Python
        - LangChain
        - Google Gemini
        - Streamlit
        - Open-Meteo API
        - JSON datasets
        """
    )

    st.divider()
    st.caption("Developed as an Agentic AI project.")


# ============================================================
# HERO SECTION
# ============================================================

st.html("""
<div class="hero">
    <div class="hero-label">
        YOUR NEXT ADVENTURE STARTS HERE
    </div>

    <h1>Plan smarter. Travel better.</h1>

    <p>
        Tell us where you want to go. Your AI travel assistant
        will organize flights, hotels, attractions, weather
        and your estimated budget.
    </p>
</div>
""")
# ============================================================
# FEATURE CARDS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="feature-card">
            <h3>✈️ Flight Search</h3>
            <p>
                Find matching flight options from the sample dataset.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="feature-card">
            <h3>🏨 Hotel Discovery</h3>
            <p>
                Explore accommodation options within your budget.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="feature-card">
            <h3>💰 Smart Budget</h3>
            <p>
                Estimate your travel expenses with an AI-powered plan.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.divider()


# ============================================================
# TRAVEL FORM
# ============================================================

st.markdown(
    '<div class="section-label">START PLANNING</div>',
    unsafe_allow_html=True,
)

st.markdown("## 🌍 Plan Your Trip")

st.write(
    "Enter your travel details below to generate a personalized itinerary."
)

with st.form("travel_form"):
    col1, col2 = st.columns(2)

    with col1:
        source_city = st.text_input(
            "📍 Source City",
            placeholder="e.g. Bangalore",
        )

    with col2:
        destination_city = st.text_input(
            "🌴 Destination City",
            placeholder="e.g. Goa",
        )

    col3, col4 = st.columns(2)

    with col3:
        number_of_days = st.number_input(
            "🗓️ Number of Days",
            min_value=3,
            max_value=7,
            value=4,
            step=1,
        )

    with col4:
        number_of_travellers = st.number_input(
            "👥 Number of Travellers",
            min_value=1,
            max_value=10,
            value=2,
            step=1,
        )

    col5, col6 = st.columns(2)

    with col5:
        travel_date = st.date_input(
            "Travel Start Date",
            value=date.today(),
            min_value=date.today(),
        )

    with col6:
        hotel_budget = st.number_input(
            "🏨 Hotel Budget per Night (₹)",
            min_value=500,
            max_value=50000,
            value=3000,
            step=500,
        )

    submitted = st.form_submit_button(
        "✨ Generate My Travel Plan",
        use_container_width=True,
    )


# ============================================================
# GENERATE TRAVEL PLAN
# ============================================================

if submitted:
    if not source_city.strip() or not destination_city.strip():
        st.error("Please enter both source city and destination city.")

    elif source_city.strip().lower() == destination_city.strip().lower():
        st.error("Source city and destination city cannot be the same.")

    else:
        end_date = travel_date + timedelta(days=int(number_of_days) - 1)
        nights = int(number_of_days) - 1

        user_request = f"""
Create a complete travel plan using your available tools.

TRAVEL DETAILS:

Source city: {source_city.strip()}
Destination city: {destination_city.strip()}

Travel start date: {travel_date.strftime("%Y-%m-%d")}
Travel end date: {end_date.strftime("%Y-%m-%d")}

Number of days: {int(number_of_days)}
Number of nights: {nights}

Number of travellers: {int(number_of_travellers)}

Maximum hotel budget per night: ₹{int(hotel_budget)}

REQUIREMENTS:

1. Search for matching flights using the flight dataset.
2. Find suitable hotels within the given nightly budget.
3. Discover available tourist attractions.
4. Generate a day-wise itinerary for the requested duration.
5. Retrieve weather information for the requested trip dates.
6. Estimate the complete trip budget using the budget tool.

IMPORTANT:

- Use the exact travel dates.
- Do not invent flight, hotel or attraction information.
- Do not invent unavailable weather information.
- Clearly disclose missing data.
- Include flight and hotel prices when available.
- Include the complete budget breakdown.
- Explain the assumptions behind the budget.
- Make sure the itinerary follows the requested dates.
- Do not claim that any booking has been made.

FORMAT YOUR RESPONSE USING THESE SECTIONS:

1. TRIP SUMMARY
2. FLIGHT DETAILS
3. HOTEL RECOMMENDATION
4. DAY-WISE ITINERARY
5. WEATHER FORECAST
6. BUDGET BREAKDOWN
7. IMPORTANT NOTES
"""

        st.divider()

        st.markdown(
            '<div class="result-heading">🧳 Your Travel Plan</div>',
            unsafe_allow_html=True,
        )

        with st.spinner(
            "🤖 Your AI travel agent is planning your trip..."
        ):
            try:
                response = travel_agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": user_request,
                            }
                        ]
                    }
                )

                report_text = extract_report_text(response)

                if not report_text:
                    st.error(
                        "The AI agent did not return readable text. "
                        "Please try again."
                    )
                else:
                    st.session_state["travel_report"] = report_text

                    st.success(
                        "Your travel plan has been generated successfully!"
                    )

                    st.markdown(report_text)

            except Exception as e:
                st.error(
                    "Something went wrong while generating your travel plan."
                )
                st.exception(e)


# ============================================================
# DOWNLOAD PDF
# ============================================================

if st.session_state.get("travel_report"):
    st.divider()
    st.markdown("## 📥 Download Your Travel Plan")

    try:
        pdf_file = create_pdf(st.session_state["travel_report"])

        st.download_button(
            label="📄 Download Travel Plan as PDF",
            data=pdf_file,
            file_name="AI_Travel_Plan.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as e:
        st.error(
            "Unable to generate the PDF. Please check the error below."
        )
        st.exception(e)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        <b>AI Travel Planning Assistant</b><br>
        Powered by LangChain · Google Gemini · Open-Meteo
    </div>
    """,
    unsafe_allow_html=True,
)
