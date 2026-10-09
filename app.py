from __future__ import annotations

import os
import base64
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

PROJECT_DIR = Path(__file__).resolve().parent
ASSET_DIR = PROJECT_DIR / "assets"
STYLES_PATH = ASSET_DIR / "styles.css"
IMAGE_STEMS = (
    "navicare_logo_mark",
    "navicare_hero",
    "navicare_scheme",
    "navicare_conversation",
)
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".svg")
# Skip a file above this size so an oversized photo cannot stall the page.
MAX_RASTER_BYTES = 1_500_000

PAGES = [
    "Home",
    "Understand my scheme",
    "Care conversation",
    "Ask NaviCare",
    "About Us",
    "Methodology",
]
HOME_DESTINATIONS = {
    "coverage": "Understand my scheme",
    "care": "Care conversation",
}

# -----------------------------------------------------------------------------
# Official sources and safety language
# -----------------------------------------------------------------------------
CARESHIELD_URL = "https://www.cpf.gov.sg/member/healthcare-financing/careshield-life"
ELDERSHIELD_URL = "https://www.cpf.gov.sg/member/healthcare-financing/eldershield"
MOH_SUPPLEMENTS_URL = "https://www.moh.gov.sg/managing-expenses/schemes-and-subsidies/careshield-life/careshield-life-and-eldershield-supplements/"
AIC_CARESHIELD_URL = "https://www.aic.sg/Financial-Assistance/CareShield-Life"
CPF_MEMBER_URL = "https://www.cpf.gov.sg/member"
MOH_CARESHIELD_URL = "https://www.moh.gov.sg/managing-expenses/schemes-and-subsidies/careshield-life/careshield-life/"

OFFICIAL_SOURCES: list[dict[str, str]] = [
    {
        "key": "careshield",
        "label": "CPF Board — CareShield Life",
        "short": "CPF CareShield Life",
        "url": CARESHIELD_URL,
    },
    {
        "key": "eldershield",
        "label": "CPF Board — ElderShield",
        "short": "CPF ElderShield",
        "url": ELDERSHIELD_URL,
    },
    {
        "key": "moh",
        "label": "MOH — CareShield Life",
        "short": "MOH CareShield Life",
        "url": MOH_CARESHIELD_URL,
    },
    {
        "key": "supplements",
        "label": "MOH — Supplements",
        "short": "MOH supplements",
        "url": MOH_SUPPLEMENTS_URL,
    },
    {
        "key": "aic",
        "label": "AIC — CareShield Life",
        "short": "AIC application help",
        "url": AIC_CARESHIELD_URL,
    },
    {
        "key": "cpf-member",
        "label": "CPF member services",
        "short": "CPF member home",
        "url": CPF_MEMBER_URL,
    },
]

DISCLAIMER = (
    "IMPORTANT NOTICE: This web application is a prototype developed for educational "
    "purposes only. The information provided here is NOT intended for real-world usage "
    "and should not be relied upon for making any decisions, especially those related "
    "to financial, legal, or healthcare matters.\n\n"
    "Furthermore, please be aware that the LLM may generate inaccurate or incorrect "
    "information. You assume full responsibility for how you use any generated output.\n\n"
    "Always consult with qualified professionals for accurate and personalised advice."
)

SOURCE_CONTEXT = f"""
You are an educational explainer about Singapore long-term-care protection. Use only the following official-source context for factual claims, and do not invent current rules, amounts, dates, or eligibility outcomes.

CPF Board — CareShield Life: {CARESHIELD_URL}
CPF Board describes CareShield Life as a long-term-care insurance scheme that provides financial support and monthly cash payouts if an insured person develops severe disability. Its public page discusses joining context by birth year, lifelong coverage, subsidies and premium support, MediSave payment, claims, the six activities of daily living, and official premium-check and application services. CPF Board states that all Singapore Citizens and Permanent Residents are eligible to join, but timing depends on birth year; it describes automatic coverage at age 30 for those born in 1980 or after, and optional participation for those born in 1979 or earlier, subject to the detailed rules on its page.

CPF Board — ElderShield: {ELDERSHIELD_URL}
CPF Board describes ElderShield as a closed long-term-care insurance scheme targeted at severe disability. It explains that plan benefits depend on the historical scheme joined and provides a secure route to check coverage through CPF member services. It also explains claims in relation to inability to perform three of six activities of daily living.

AIC — CareShield Life: {AIC_CARESHIELD_URL}
AIC provides public guidance on how to qualify, how the scheme works, how to apply, documents needed, eFASS, MOH-accredited severe-disability assessors, and applying on behalf of someone who lacks mental capacity.

MOH — CareShield Life and ElderShield Supplements: {MOH_SUPPLEMENTS_URL}
MOH explains that supplements add coverage on top of basic CareShield Life or ElderShield plans and publishes comparison materials. Supplement plans differ, so users should contact an insurer for product-specific information rather than rely on a generic assistant.
"""

CARE_COMPARISON = pd.DataFrame(
    [
        [
            "CareShield Life",
            "Current long-term-care scheme",
            "Monthly cash payouts for life if claim criteria are met",
            "Check the current joining and claim rules on CPF Board",
        ],
        [
            "ElderShield",
            "Closed historical scheme",
            "Plan-dependent historical payouts and duration",
            "Check actual coverage through CPF member services",
        ],
        [
            "Supplements",
            "Additional private coverage",
            "Benefits differ by plan",
            "Read MOH comparison materials and contact the insurer",
        ],
    ],
    columns=[
        "Topic",
        "High-level description",
        "What the app can explain",
        "Official next step",
    ],
)

ADL_TABLE = pd.DataFrame(
    [
        [
            "Washing",
            "Washing in a bath or shower, including getting in and out, or washing by other means.",
        ],
        [
            "Dressing",
            "Putting on, taking off, securing, and unfastening garments and relevant appliances.",
        ],
        ["Feeding", "Feeding oneself after food has been prepared and made available."],
        [
            "Toileting",
            "Using the toilet or managing bowel and bladder function with appropriate aids.",
        ],
        [
            "Walking or moving around",
            "Moving indoors from room to room on level surfaces.",
        ],
        [
            "Transferring",
            "Moving from a bed to an upright chair or wheelchair, and vice versa.",
        ],
    ],
    columns=["Activity of daily living", "Plain-language description"],
)

CHAT_STARTERS = [
    (
        "Compare the schemes",
        "What is the high-level difference between CareShield Life and ElderShield?",
    ),
    ("Daily living activities", "What are the six activities of daily living?"),
    (
        "Applying as a caregiver",
        "Where can a caregiver learn about applying for CareShield Life?",
    ),
]


def resolve_nav(
    current: str | None, pending: str | None, query_page: str | None = None
) -> str:
    """Pick the visible page. A queued destination wins, then the current page, then a shared URL."""
    if pending in PAGES:
        return pending
    if current in PAGES:
        return current
    if query_page in PAGES:
        return query_page
    return "Home"


def inject_css() -> None:
    css = STYLES_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


def get_secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def gate_if_configured() -> None:
    password = get_secret("APP_PASSWORD")
    if not password:
        return
    if st.session_state.get("authenticated"):
        return
    st.markdown(
        '<div class="hero"><div class="eyebrow">Private educational prototype</div><h1>NaviCare</h1><p>Enter the access password configured by the project owner to continue.</p></div>',
        unsafe_allow_html=True,
    )
    entered = st.text_input("Access password", type="password")
    if st.button("Continue", type="primary"):
        if entered == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


def disclaimer() -> None:
    with st.expander("Important prototype notice", expanded=True):
        st.warning(DISCLAIMER)


def page_header(eyebrow: str, title: str, intro: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(intro)


def source_strip(text: str, url: str, label: str = "Read the official source") -> None:
    st.markdown(
        f'<div class="source-strip">{text} <a href="{url}" target="_blank" rel="noopener noreferrer">{label} ↗</a></div>',
        unsafe_allow_html=True,
    )


def render_link_buttons(keys: list[str]) -> None:
    sources = [source for source in OFFICIAL_SOURCES if source["key"] in keys]
    if not sources:
        return
    columns = st.columns(len(sources))
    for column, source in zip(columns, sources):
        with column:
            st.link_button(source["short"], source["url"], width="stretch")


def render_flow(steps: list[str]) -> None:
    parts: list[str] = []
    for index, step in enumerate(steps, start=1):
        parts.append(
            f'<div class="flow-step"><span class="eyebrow">{index:02d}</span><br>{step}</div>'
        )
        if index != len(steps):
            parts.append('<div class="flow-arrow" aria-hidden="true">→</div>')
    st.markdown(f'<div class="flow">{"".join(parts)}</div>', unsafe_allow_html=True)


def image_file(stem: str) -> Path | None:
    """Return the first usable picture for a stem stored in assets/."""
    for suffix in IMAGE_SUFFIXES:
        path = ASSET_DIR / f"{stem}{suffix}"
        if path.is_file() and 0 < path.stat().st_size <= MAX_RASTER_BYTES:
            return path
    return None


def required_assets() -> list[Path]:
    files = [STYLES_PATH]
    for stem in IMAGE_STEMS:
        found = image_file(stem)
        if found is not None:
            files.append(found)
    return files


def show_image(stem: str, caption: str) -> None:
    path = image_file(stem)
    if path is None:
        st.info(f"Add assets/{stem}.png to show this illustration.")
        return
    st.image(str(path), width="stretch", caption=caption)


def render_brand_bar() -> None:
    logo = image_file("navicare_logo_mark")
    if logo is None or logo.stat().st_size > 120_000:
        mark = ""
    else:
        logo_uri = "data:image/png;base64," + base64.b64encode(
            logo.read_bytes()
        ).decode("ascii")
        mark = f'<img src="{logo_uri}" alt="NaviCare logo mark" width="44" height="44">'
    st.markdown(
        f'<div class="brand-bar">{mark}<div><div class="brand-name">NaviCare</div><div class="brand-subtitle">CareShield Life and ElderShield information navigator</div></div></div>',
        unsafe_allow_html=True,
    )


def queue_page(page: str) -> None:
    st.session_state["pending_page"] = page
    st.rerun()


def apply_pending_navigation() -> None:
    pending = st.session_state.pop("pending_page", None)
    query_page = None
    try:
        query_page = st.query_params.get("page")
    except Exception:
        query_page = None
    current = st.session_state.get("nav")
    st.session_state["nav"] = resolve_nav(
        current if isinstance(current, str) else None,
        pending if isinstance(pending, str) else None,
        query_page,
    )


def remember_page_in_url(page: str) -> None:
    try:
        if st.query_params.get("page") != page:
            st.query_params["page"] = page
    except Exception:
        return


def render_home() -> None:
    st.markdown(
        '<div class="hero"><div class="eyebrow">Long-term-care learning companion · educational prototype</div><h1>Understand protection before you need it.</h1><p>NaviCare brings CareShield Life, ElderShield, and caregiving support information into two practical, source-linked journeys.</p></div>',
        unsafe_allow_html=True,
    )
    show_image(
        "navicare_hero",
        "A calmer way to learn, prepare, and find the right official next step.",
    )
    disclaimer()
    st.write("")
    st.markdown(
        '<div class="eyebrow">Start with a scenario</div>', unsafe_allow_html=True
    )
    st.subheader("A clearer next step, without collecting sensitive data")
    st.markdown(
        "Choose a learning pathway. Your broad answers stay in this session and are used only to organise public information and questions for further reading."
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(
            '<div class="card teal-card"><div class="eyebrow">01 · Coverage</div><h3>Understand my scheme</h3><p>Learn the difference between CareShield Life, ElderShield, and supplements, then find the official route to check your own coverage.</p></div>',
            unsafe_allow_html=True,
        )
        if st.button("Explore scheme coverage", width="stretch", key="home_coverage"):
            queue_page(HOME_DESTINATIONS["coverage"])
    with right:
        st.markdown(
            '<div class="card accent-card"><div class="eyebrow">02 · Caregiving</div><h3>Prepare for a care conversation</h3><p>Build a general checklist for speaking with AIC, CPF Board, MOH, a healthcare provider, or an accredited assessor.</p></div>',
            unsafe_allow_html=True,
        )
        if st.button("Prepare a care conversation", width="stretch", key="home_care"):
            queue_page(HOME_DESTINATIONS["care"])
    st.write("")
    st.markdown('<div class="eyebrow">What is inside</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    with a:
        st.markdown(
            '<div class="card"><div class="metric-label">01</div><div class="metric-value">Explain</div><p>Compare schemes and explain the six activities of daily living in plain language.</p></div>',
            unsafe_allow_html=True,
        )
    with b:
        st.markdown(
            '<div class="card"><div class="metric-label">02</div><div class="metric-value">Prepare</div><p>Turn a broad situation into questions, documents to confirm, and official next steps.</p></div>',
            unsafe_allow_html=True,
        )
    with c:
        st.markdown(
            '<div class="card"><div class="metric-label">03</div><div class="metric-value">Ask</div><p>Use the optional chatbot for source-grounded concept questions, with verification reminders.</p></div>',
            unsafe_allow_html=True,
        )
    st.write("")
    source_strip(
        "Core content is based on public CPF Board, MOH, and AIC guidance.",
        CARESHIELD_URL,
    )
    st.write("")
    render_link_buttons(["careshield", "eldershield", "aic", "supplements"])


def coverage_output(birth_band: str, focus: str, role: str) -> dict[str, Any]:
    prompts = []
    if birth_band == "Born in 1980 or after":
        prompts.append(
            "CPF Board describes automatic CareShield Life coverage at age 30 for those born in 1980 or after, subject to the detailed official rules. Use the CPF Board page to verify the current position for a real person."
        )
    elif birth_band == "Born in 1979 or earlier":
        prompts.append(
            "CPF Board describes ElderShield as a closed scheme and CareShield Life participation as optional for many people born in 1979 or earlier, with detailed exceptions. Check the official pages rather than assuming coverage."
        )
    else:
        prompts.append(
            "Birth year is relevant to the CareShield Life and ElderShield context, but this prototype cannot determine which scheme covers a particular person."
        )
    if focus == "Claims and severe disability":
        prompts.append(
            "Read the official explanation of the six activities of daily living and the role of an MOH-accredited assessor. The app cannot assess disability or predict claim approval."
        )
    elif focus == "Premiums and support":
        prompts.append(
            "Explore official information on MediSave payment, subsidies, premium support, and the premium-check service. Do not enter an exact premium or account balance here."
        )
    elif focus == "Supplements":
        prompts.append(
            "MOH explains that supplements provide additional coverage, but benefits differ. Use official comparison materials and contact an insurer for product-specific questions."
        )
    else:
        prompts.append(
            "Start with the high-level scheme comparison, then use CPF Board’s secure member service to check actual coverage."
        )
    if role == "Family member or caregiver":
        prompts.append(
            "AIC provides public guidance for applying on behalf of someone who lacks mental capacity, including additional documents and support routes."
        )
    else:
        prompts.append(
            "For a personal coverage result, use CPF Board’s secure member services rather than entering personal details into this prototype."
        )
    return {"prompts": prompts}


def render_coverage() -> None:
    intro_col, visual_col = st.columns([1.18, 0.82], gap="large")
    with intro_col:
        page_header(
            "01 · Coverage explorer",
            "Understand my long-term-care scheme",
            "Use broad context to learn what to read next. This is an educational explainer, not a coverage or eligibility checker.",
        )
    with visual_col:
        show_image(
            "navicare_scheme",
            "A high-level map of protection concepts—not a personal coverage result.",
        )
    source_strip(
        "CPF Board provides the source-of-truth pages for CareShield Life and ElderShield coverage, benefits, premiums, and claims.",
        CARESHIELD_URL,
    )
    render_link_buttons(["careshield", "eldershield", "cpf-member"])
    st.write("")
    with st.form("coverage_form"):
        st.markdown("#### Choose the learning context")
        col1, col2 = st.columns(2)
        with col1:
            birth_band = st.selectbox(
                "Broad birth-year context",
                [
                    "Prefer not to say",
                    "Born in 1980 or after",
                    "Born in 1979 or earlier",
                ],
                key="coverage_birth",
            )
            role = st.selectbox(
                "Who is this learning pathway for?",
                ["Myself", "Family member or caregiver", "General learning"],
                key="coverage_role",
            )
        with col2:
            focus = st.selectbox(
                "What do you want to understand?",
                [
                    "General comparison",
                    "Claims and severe disability",
                    "Premiums and support",
                    "Supplements",
                ],
                key="coverage_focus",
            )
            st.caption(
                "Do not enter your name, exact age, NRIC number, health information, account details, or exact financial amounts."
            )
        submitted = st.form_submit_button(
            "Build my learning pathway", type="primary", width="stretch"
        )
    if submitted:
        st.session_state["coverage_result"] = coverage_output(birth_band, focus, role)
    if "coverage_result" in st.session_state:
        result = st.session_state["coverage_result"]
        st.write("")
        st.markdown('<div class="eyebrow">Your pathway</div>', unsafe_allow_html=True)
        st.subheader("Learn first, then verify through official services")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                '<div class="card"><div class="metric-label">Core topic</div><div class="metric-value">'
                + focus
                + "</div><p>A learning lens, not a personalised result.</p></div>",
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                '<div class="card"><div class="metric-label">Scheme context</div><div class="metric-value">Compare</div><p>CareShield Life and ElderShield have different joining and coverage histories.</p></div>',
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                '<div class="card"><div class="metric-label">Next step</div><div class="metric-value">Check</div><p>Use CPF Board’s secure member services for actual coverage.</p></div>',
                unsafe_allow_html=True,
            )
        st.write("")
        st.markdown("#### Your learning prompts")
        for index, item in enumerate(result["prompts"], start=1):
            st.markdown(
                f'<div class="step"><strong>Prompt {index:02d}</strong><br>{item}</div>',
                unsafe_allow_html=True,
            )
        st.write("")
        st.markdown("#### High-level comparison")
        st.dataframe(CARE_COMPARISON, width="stretch", hide_index=True)
        st.markdown("#### Six activities of daily living")
        with st.expander("Open the plain-language explainer"):
            st.dataframe(ADL_TABLE, width="stretch", hide_index=True)
        chart = pd.DataFrame(
            {
                "Scheme or topic": ["CareShield Life", "ElderShield", "Supplements"],
                "Public explanation scope": [5, 4, 3],
            }
        ).set_index("Scheme or topic")
        st.bar_chart(chart, color="#087f70", height=220)
        st.caption(
            "Relative breadth of the public explanation in this prototype; this is not a measure of coverage or value."
        )
        st.markdown(
            f"Continue with [CPF Board CareShield Life]({CARESHIELD_URL}), [CPF Board ElderShield]({ELDERSHIELD_URL}), or [CPF member services]({CPF_MEMBER_URL})."
        )
    st.info(
        "This page does not determine coverage, interpret medical information, or predict a claim."
    )


def care_output(audience: str, task: str, destination: str) -> dict[str, Any]:
    checklist = []
    if task == "Understand a possible claim":
        checklist.extend(
            [
                "Read the official claim criteria and the six activities of daily living.",
                "Ask which MOH-accredited assessor and application route applies.",
                "Confirm which documents AIC or the relevant agency requires.",
            ]
        )
    elif task == "Apply or find application support":
        checklist.extend(
            [
                "Open AIC’s CareShield Life application guidance and eFASS information.",
                "Prepare only the documents requested by the official service.",
                "If applying for someone who lacks mental capacity, check the additional-document guidance before starting.",
            ]
        )
    elif task == "Support an older family member":
        checklist.extend(
            [
                "Clarify whether the question concerns CareShield Life, ElderShield, or another support scheme.",
                "Write down questions for CPF Board, AIC, MOH, or the healthcare provider.",
                "Use official secure services for any coverage or account check.",
            ]
        )
    else:
        checklist.extend(
            [
                "Start with the official overview page for the selected destination.",
                "Separate general questions from personal account or health information.",
                "Keep a note of the official contact or e-service to use next.",
            ]
        )
    checklist.append(
        f"Your intended destination is {destination}; verify the correct route on the official website before sharing any information."
    )
    if audience == "Caregiver or family member":
        checklist.append(
            "Ask about consent, authority, and additional documents before acting on behalf of another person."
        )
    else:
        checklist.append(
            "Do not share medical records, NRIC details, account numbers, or exact financial details with this prototype."
        )
    return {"checklist": checklist}


def render_care() -> None:
    intro_col, visual_col = st.columns([1.18, 0.82], gap="large")
    with intro_col:
        page_header(
            "02 · Care conversation",
            "Prepare for a care or claim conversation",
            "Create a general checklist for the right public-service destination. The application cannot assess disability, interpret a medical report, or predict claim approval.",
        )
    with visual_col:
        show_image(
            "navicare_conversation",
            "Use this journey to prepare questions—not to interpret a medical assessment.",
        )
    source_strip(
        "AIC provides practical guidance on applications, documents, assessors, eFASS, and support for caregivers.",
        AIC_CARESHIELD_URL,
    )
    render_link_buttons(["aic", "careshield", "moh"])
    st.write("")
    with st.form("care_form"):
        st.markdown("#### Set the conversation context")
        col1, col2 = st.columns(2)
        with col1:
            audience = st.selectbox(
                "Who are you preparing for?",
                ["Myself", "Caregiver or family member", "General learning"],
                key="care_audience",
            )
            task = st.selectbox(
                "What are you trying to do?",
                [
                    "Understand a possible claim",
                    "Apply or find application support",
                    "Support an older family member",
                    "Learn the general process",
                ],
                key="care_task",
            )
        with col2:
            destination = st.selectbox(
                "Which destination are you preparing to contact?",
                ["CPF Board", "AIC", "MOH or healthcare provider", "Not sure yet"],
                key="care_destination",
            )
            st.caption(
                "Do not enter diagnoses, medical records, NRIC details, account numbers, addresses, or exact financial amounts."
            )
        submitted = st.form_submit_button(
            "Build my conversation checklist", type="primary", width="stretch"
        )
    if submitted:
        st.session_state["care_result"] = care_output(audience, task, destination)
    if "care_result" in st.session_state:
        result = st.session_state["care_result"]
        st.write("")
        st.markdown('<div class="eyebrow">Your checklist</div>', unsafe_allow_html=True)
        st.subheader("Questions and preparation prompts")
        left, right = st.columns([1.15, 0.85], gap="large")
        with left:
            for index, item in enumerate(result["checklist"], start=1):
                st.markdown(
                    f'<div class="step"><strong>Step {index:02d}</strong><br>{item}</div>',
                    unsafe_allow_html=True,
                )
        with right:
            st.markdown(
                '<div class="card"><div class="metric-label">Care pathway principle</div><div class="metric-value">Ask, verify, prepare</div><p>Use this checklist to organise a conversation. Only the relevant official agency, assessor, or professional can advise on a real situation.</p></div>',
                unsafe_allow_html=True,
            )
            st.write("")
            chart = pd.DataFrame(
                {
                    "Preparation area": [
                        "Official route",
                        "Documents",
                        "Assessor or provider",
                        "Authority / consent",
                        "Verification",
                    ],
                    "Checklist emphasis": [5, 5, 4, 4, 5],
                }
            ).set_index("Preparation area")
            st.bar_chart(chart, color="#ed765e", height=240)
            st.caption(
                "Relative emphasis in this generic checklist, not a score of the person or claim."
            )
        st.write("")
        st.markdown(
            f"Useful official destinations include [AIC CareShield Life guidance]({AIC_CARESHIELD_URL}), [CPF Board CareShield Life]({CARESHIELD_URL}), and [MOH CareShield Life information]({MOH_CARESHIELD_URL})."
        )
    st.info(
        "This page is a preparation guide only. It does not provide medical, legal, insurance, or financial advice."
    )


def assistant_reply(messages: list[dict[str, str]]) -> str:
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return "The optional chatbot is not connected yet. The guided tools remain available. Add OPENAI_API_KEY as a server-side environment variable or Streamlit secret to enable concept questions."
    base_url = get_secret("OPENAI_API_BASE") or None
    model = get_secret("CARE_LLM_MODEL") or get_secret("CPF_LLM_MODEL") or "gpt-4o-mini"
    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    system = {
        "role": "system",
        "content": (
            "You are NaviCare, a concise educational explainer for Singapore long-term-care protection. "
            "Use only the official source context below. Do not request or process medical records, diagnoses, NRIC numbers, account numbers, exact balances, addresses, or other personal data. "
            "Do not diagnose disability, interpret a medical assessment, decide coverage or eligibility, predict claim approval, calculate a personal payout, recommend a supplement, or rank private insurers. "
            "For personal or current questions, direct the user to CPF Board, MOH, or AIC official services. Include a short 'Verify with CPF Board, MOH, or AIC' reminder in every answer.\n\n"
            + SOURCE_CONTEXT
        ),
    }
    request_kwargs: dict[str, Any] = {
        "model": model,
        "messages": [system] + messages[-8:],
        "max_tokens": 700,
    }
    response = client.chat.completions.create(**request_kwargs)
    return (
        response.choices[0].message.content
        or "I could not produce an answer. Please verify the information with CPF Board, MOH, or AIC."
    )


def render_chatbot() -> None:
    page_header(
        "03 · Optional chatbot",
        "Ask NaviCare",
        "Ask about concepts, public processes, and where to read next. The chatbot is source-grounded but can still be wrong, so verify every answer with the official agency.",
    )
    st.markdown(
        '<div class="notice"><strong>Privacy boundary.</strong> Ask general questions only. Do not enter a diagnosis, medical record, NRIC number, account number, exact balance, address, or other identifying information.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    if not get_secret("OPENAI_API_KEY"):
        st.info(
            "The guided tools work without a key. Add OPENAI_API_KEY to server-side secrets to enable the optional chatbot."
        )
    st.markdown("**Try a safe starter question**")
    columns = st.columns(len(CHAT_STARTERS))
    for column, (label, prompt) in zip(columns, CHAT_STARTERS):
        with column:
            if st.button(label, key=f"chat_prompt_{label}", width="stretch"):
                st.session_state["pending_chat_prompt"] = prompt
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    for message in st.session_state["chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    typed = st.chat_input("Ask a general CareShield Life or ElderShield question…")
    prompt = typed or st.session_state.pop("pending_chat_prompt", None)
    if prompt:
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Checking the official-source context…"):
                try:
                    answer = assistant_reply(st.session_state["chat_messages"])
                except Exception:
                    answer = "The chatbot could not connect. Please use the guided tools and verify information with CPF Board, MOH, or AIC."
            st.markdown(answer)
        st.session_state["chat_messages"].append(
            {"role": "assistant", "content": answer}
        )
    st.write("")
    source_strip(
        "The chatbot is a starting point only. Verify current rules and personal details through official services.",
        CPF_MEMBER_URL,
        "Open CPF member services",
    )
    render_link_buttons(["cpf-member", "careshield", "aic"])


def render_about() -> None:
    page_header(
        "Documentation",
        "About NaviCare",
        "A capstone prototype that makes long-term-care protection information easier to explore without collecting sensitive data.",
    )
    st.markdown(
        "**Full project title:** NaviCare: A CareShield Life and ElderShield Information Navigator"
    )
    st.markdown("### Project scope")
    st.write(
        "NaviCare consolidates public information about CareShield Life, ElderShield, long-term-care claims, and caregiver support. It is designed for citizens and families who want to understand the topic and prepare questions before using official services."
    )
    st.markdown("### Objectives")
    objectives = pd.DataFrame(
        [
            [
                "Consolidate information",
                "Bring CPF Board, MOH, and AIC guidance into one source-linked experience.",
            ],
            [
                "Personalise safely",
                "Use broad, non-identifying context to shape a learning pathway or conversation checklist.",
            ],
            [
                "Enhance understanding",
                "Explain schemes, activities of daily living, claims concepts, and public-service routes in plain language.",
            ],
            [
                "Present information effectively",
                "Combine forms, tables, charts, flow diagrams, links, and a guarded chatbot.",
            ],
        ],
        columns=["Objective", "How the prototype addresses it"],
    )
    st.dataframe(objectives, width="stretch", hide_index=True)
    st.markdown("### Data sources")
    st.write(
        "The prototype uses public pages from CPF Board for CareShield Life and ElderShield, MOH for the scheme overview and supplements, and AIC for claim-support and application guidance. These official sources are the source of truth and should be checked for current information."
    )
    for source in OFFICIAL_SOURCES:
        st.markdown(f"- [{source['label']}]({source['url']})")
    st.markdown("### Features")
    features = pd.DataFrame(
        [
            [
                "Understand my scheme",
                "Broad birth-year and topic context produces source-linked learning prompts and a high-level comparison.",
            ],
            [
                "Care conversation",
                "Broad audience, task, and destination context produces a non-personalised preparation checklist.",
            ],
            [
                "Optional chatbot",
                "A source-grounded assistant answers concept questions and refuses unsafe personal-data or decision requests.",
            ],
            [
                "Documentation",
                "About Us and Methodology pages explain the scope, data flow, limitations, and use-case flow diagrams.",
            ],
        ],
        columns=["Feature", "Description"],
    )
    st.dataframe(features, width="stretch", hide_index=True)
    st.markdown("### Privacy and safety")
    st.write(
        "The guided tools do not require login, a database, or personal information. The chatbot reads only a server-side API key and receives the current conversation plus a fixed public-source context. Users must not submit sensitive information."
    )
    with st.expander("Required prototype disclaimer"):
        st.warning(DISCLAIMER)


def render_methodology() -> None:
    page_header(
        "Documentation",
        "Methodology",
        "The application uses a source-first flow: understand the context, surface concepts, provide safe preparation prompts, and point back to official services.",
    )
    st.markdown("### Overall data flow")
    render_flow(
        [
            "Choose a journey",
            "Broad, non-identifying inputs",
            "Educational rules",
            "Prompts or checklist",
            "Official CPF, MOH, and AIC links",
        ]
    )
    st.markdown("### Use case 1 — Understand my long-term-care scheme")
    render_flow(
        [
            "Birth-year band and role",
            "Question focus",
            "Scheme comparison",
            "Learning prompts",
            "Secure coverage-check link",
        ]
    )
    st.write(
        "This flow explains the public distinction between CareShield Life, ElderShield, and supplements. It does not determine actual coverage, eligibility, claim status, or payout."
    )
    st.markdown("### Use case 2 — Prepare for a care or claim conversation")
    render_flow(
        [
            "Audience and task",
            "Intended destination",
            "Questions and documents",
            "Conversation checklist",
            "CPF Board, AIC, or MOH",
        ]
    )
    st.write(
        "This flow helps users prepare for an official conversation. It does not diagnose disability, interpret medical assessments, or predict claim approval."
    )
    st.markdown("### Chatbot implementation")
    st.write(
        "The optional chatbot receives a fixed source context and the most recent conversation turns. It uses a server-side OPENAI_API_KEY and a configurable CARE_LLM_MODEL, defaulting to gpt-4o-mini for broad OpenAI-compatible support. The request uses standard chat-completion fields and deliberately omits provider-specific reasoning parameters. It is disabled gracefully when no key is configured."
    )
    st.markdown("### Limitations")
    limitations = pd.DataFrame(
        [
            [
                "Freshness",
                "The prototype is not a live mirror of CPF Board, MOH, or AIC. Verify current rules at the official source.",
            ],
            [
                "Medical and financial sensitivity",
                "No diagnosis, medical interpretation, personal claim decision, payout estimate, or insurance recommendation.",
            ],
            [
                "Personalisation",
                "Inputs are broad by design and produce educational prompts, not an eligibility assessment.",
            ],
            [
                "Language model",
                "Generated answers can be inaccurate. Users must verify with CPF Board, MOH, or AIC.",
            ],
            [
                "Privacy",
                "Do not submit medical records, NRIC details, account information, exact balances, or other identifiers.",
            ],
        ],
        columns=["Area", "Boundary"],
    )
    st.dataframe(limitations, width="stretch", hide_index=True)


def render_footer() -> None:
    st.divider()
    links = " ".join(
        f'<a href="{source["url"]}" target="_blank" rel="noopener noreferrer">{source["short"]}</a>'
        for source in OFFICIAL_SOURCES
    )
    st.markdown(f'<p class="footer-links">{links}</p>', unsafe_allow_html=True)
    st.caption(
        "NaviCare · Educational prototype · Verify current and personal information with CPF Board, MOH, or AIC."
    )


def render_sidebar() -> str:
    apply_pending_navigation()
    with st.sidebar:
        logo = image_file("navicare_logo_mark")
        if logo is not None:
            st.image(str(logo), width=64)
        st.markdown("## NaviCare")
        st.caption("Understand care protection. Verify always.")
        st.radio("Navigate", PAGES, key="nav", label_visibility="collapsed")
        st.divider()
        st.markdown("### Official sources")
        for source in OFFICIAL_SOURCES:
            st.markdown(
                f'<a href="{source["url"]}" target="_blank" rel="noopener noreferrer">{source["short"]}</a>',
                unsafe_allow_html=True,
            )
        st.divider()
        st.markdown("### Two journeys")
        st.markdown(
            "**Scheme coverage**  \nCareShield Life, ElderShield, and supplements"
        )
        st.markdown(
            "**Care conversation**  \nQuestions, documents, and official next steps"
        )
        st.divider()
        st.caption("No sensitive data needed. Do not enter health or account details.")
    return str(st.session_state["nav"])


def main() -> None:
    st.set_page_config(
        page_title="NaviCare: A CareShield Life and ElderShield Information Navigator",
        page_icon=str(image_file("navicare_logo_mark") or "🧭"),
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    render_brand_bar()
    gate_if_configured()
    page = render_sidebar()
    if page == "Home":
        render_home()
    elif page == "Understand my scheme":
        render_coverage()
    elif page == "Care conversation":
        render_care()
    elif page == "Ask NaviCare":
        render_chatbot()
    elif page == "About Us":
        render_about()
    elif page == "Methodology":
        render_methodology()
    else:
        st.session_state["nav"] = "Home"
        render_home()
    render_footer()
    remember_page_in_url(page if page in PAGES else "Home")


if __name__ == "__main__":
    main()
