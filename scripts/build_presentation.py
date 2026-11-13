"""Build the team PowerPoint for the NaviCare capstone demo."""

from __future__ import annotations

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

TEAL = RGBColor(0x15, 0x84, 0x77)
NAVY = RGBColor(0x10, 0x2A, 0x43)
INK = RGBColor(0x1C, 0x2B, 0x33)
MUTED = RGBColor(0x5C, 0x6B, 0x73)
CREAM = RGBColor(0xF6, 0xF3, 0xEE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def add_rect(slide, left, top, width, height, fill):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    return shape


def add_text(slide, text, left, top, width, height, size=18, bold=False, color=INK, align=PP_ALIGN.LEFT, font="Calibri"):
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True
    frame.auto_size = None
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def set_notes(slide, text):
    notes = slide.notes_slide.notes_text_frame
    notes.text = text


def chrome(slide, eyebrow, title, page, pages):
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, CREAM)
    add_rect(slide, 0, 0, Inches(0.16), SLIDE_H, TEAL)
    add_text(slide, eyebrow.upper(), Inches(0.55), Inches(0.28), Inches(10), Inches(0.32), size=12, bold=True, color=TEAL)
    add_text(slide, title, Inches(0.52), Inches(0.52), Inches(12.2), Inches(0.7), size=32, bold=True, color=NAVY)
    add_text(slide, f"{page}  /  {pages}", Inches(11.4), Inches(7.05), Inches(1.5), Inches(0.28), size=12, color=MUTED, align=PP_ALIGN.RIGHT)


def bullets(slide, items, left, top, width, height, size=18):
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = PP_ALIGN.LEFT
        paragraph.level = 0
        paragraph.space_after = Pt(10)
        run = paragraph.add_run()
        run.text = item
        run.font.name = "Calibri"
        run.font.size = Pt(size)
        run.font.color.rgb = INK
    return box


def card(slide, left, top, width, height, kicker, heading, body):
    shape = add_rect(slide, left, top, width, height, WHITE)
    shape.shadow.inherit = False
    add_rect(slide, left, top, Inches(0.08), height, TEAL)
    add_text(slide, kicker.upper(), left + Inches(0.28), top + Inches(0.16), width - Inches(0.4), Inches(0.28), size=11, bold=True, color=TEAL)
    add_text(slide, heading, left + Inches(0.28), top + Inches(0.42), width - Inches(0.4), Inches(0.55), size=18, bold=True, color=NAVY)
    add_text(slide, body, left + Inches(0.28), top + Inches(1.0), width - Inches(0.45), height - Inches(1.15), size=14, color=INK)


def build(path: str) -> None:
    presentation = Presentation()
    presentation.slide_width = SLIDE_W
    presentation.slide_height = SLIDE_H
    presentation.core_properties.title = "NaviCare team presentation"
    presentation.core_properties.subject = "CareShield Life and ElderShield information navigator"
    blank = presentation.slide_layouts[6]
    total = 12

    slide = presentation.slides.add_slide(blank)
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, NAVY)
    add_rect(slide, 0, 0, Inches(0.22), SLIDE_H, TEAL)
    add_text(slide, "AI CHAMPIONS BOOTCAMP  ·  TEAM OF 3", Inches(0.7), Inches(1.35), Inches(11), Inches(0.35), size=14, bold=True, color=TEAL)
    add_text(slide, "NaviCare", Inches(0.7), Inches(1.85), Inches(11), Inches(1.0), size=60, bold=True, color=WHITE)
    add_text(
        slide,
        "A CareShield Life and ElderShield\ninformation navigator",
        Inches(0.7),
        Inches(3.0),
        Inches(10),
        Inches(1.3),
        size=28,
        color=RGBColor(0xD7, 0xE8, 0xE4),
    )
    add_text(
        slide,
        "Educational prototype  ·  Replace these names before you present\nMember 1    ·    Member 2    ·    Member 3",
        Inches(0.7),
        Inches(5.55),
        Inches(10),
        Inches(0.8),
        size=18,
        color=WHITE,
    )
    set_notes(
        slide,
        "Open by saying the project name in full. Tell the room this is a learning prototype and not a coverage checker. Introduce the three speakers.",
    )

    slide = presentation.slides.add_slide(blank)
    chrome(slide, "Agenda", "Five parts to this presentation", 2, total)
    items = [
        ("01", "Background", "Where CareShield Life and ElderShield information lives today."),
        ("02", "Motivation", "Why a navigator is useful, and the limits we will not cross."),
        ("03", "Audience", "Who the app is for, and what each role can open."),
        ("04", "Technology stack", "Streamlit, the FAISS note index, and the optional model."),
        ("05", "Product demo", "The live path from the open pages to a retrieved answer."),
    ]
    for index, (number, heading, body) in enumerate(items):
        top = Inches(1.5) + Inches(index * 1.02)
        add_rect(slide, Inches(0.55), top, Inches(12.2), Inches(0.9), WHITE)
        add_text(slide, number, Inches(0.75), top + Inches(0.18), Inches(0.8), Inches(0.5), size=20, bold=True, color=TEAL)
        add_text(slide, heading, Inches(1.7), top + Inches(0.1), Inches(4.2), Inches(0.4), size=20, bold=True, color=NAVY)
        add_text(slide, body, Inches(5.8), top + Inches(0.18), Inches(6.6), Inches(0.5), size=16, color=INK)
    set_notes(slide, "Say the five headings only. Do not start the demo yet. Member 1 takes background and motivation. Member 2 takes audience and stack. Member 3 runs the demo.")

    slide = presentation.slides.add_slide(blank)
    chrome(slide, "Background", "The information is public, and it is split across three agencies", 3, total)
    card(
        slide,
        Inches(0.5),
        Inches(1.6),
        Inches(4.0),
        Inches(4.7),
        "CPF Board",
        "Two different schemes",
        "CareShield Life is the current long-term-care scheme. ElderShield is the closed historical scheme. Joining depends on birth year. A real coverage result belongs in CPF member services.",
    )
    card(
        slide,
        Inches(4.7),
        Inches(1.6),
        Inches(4.0),
        Inches(4.7),
        "MOH",
        "Claims and supplements",
        "Severe disability is explained through six activities of daily living, and an accredited assessor. Supplements sit on top of a basic plan and differ by insurer.",
    )
    card(
        slide,
        Inches(8.9),
        Inches(1.6),
        Inches(3.9),
        Inches(4.7),
        "AIC",
        "How to apply",
        "AIC publishes the application route, the documents, eFASS, and what changes when someone applies for a person who lacks mental capacity.",
    )
    set_notes(
        slide,
        "Background, not a policy lecture. One sentence per card. Stress that the agencies already publish this. The problem is knowing which page to open first.",
    )

    slide = presentation.slides.add_slide(blank)
    chrome(slide, "Motivation", "Help someone prepare, then send them to the official service", 4, total)
    bullets(
        slide,
        [
            "A family member can face three websites before they know whether the question is about joining, a claim, or an application.",
            "NaviCare turns that into two journeys and a follow-up question, using only broad choices such as a birth-year band.",
            "The app must not decide coverage, read a medical report, or estimate a payout.",
            "Home carries the required educational disclaimer. The prototype is not for real financial, legal, or healthcare decisions, and it is not for the general public.",
        ],
        Inches(0.6),
        Inches(1.6),
        Inches(12.1),
        Inches(4.8),
        size=22,
    )
    set_notes(
        slide,
        "Read the disclaimer line aloud. If a marker asks whether this gives advice, the answer is no. The next step is always CPF Board, MOH, or AIC.",
    )

    slide = presentation.slides.add_slide(blank)
    chrome(slide, "Audience", "Citizens and caregivers first. Markers use the same sign-in.", 5, total)
    card(
        slide,
        Inches(0.5),
        Inches(1.6),
        Inches(6.0),
        Inches(2.3),
        "Primary audience",
        "People learning the schemes",
        "A citizen or permanent resident who wants the difference between CareShield Life, ElderShield, and supplements before opening CPF.",
    )
    card(
        slide,
        Inches(6.75),
        Inches(1.6),
        Inches(6.0),
        Inches(2.3),
        "Second audience",
        "A family member preparing a call",
        "Someone who needs questions, documents to confirm, and the right agency. They are not asking NaviCare to file the claim.",
    )
    card(
        slide,
        Inches(0.5),
        Inches(4.1),
        Inches(12.25),
        Inches(2.3),
        "Out of scope",
        "Not an assessor, an insurer, or a member-services login",
        "Do not enter an NRIC, a diagnosis, a medical record, an account number, or an exact balance. The app has no account database and does not keep those details.",
    )
    set_notes(slide, "Point at the out-of-scope card last. It answers the sensitive-data rule in the submission guidelines.")

    slide = presentation.slides.add_slide(blank)
    chrome(slide, "Audience", "What each person can open", 6, total)
    headers = ["Who", "Sign-in", "Pages"]
    rows = [
        ["Anyone", "None", "Home, About Us, Methodology"],
        ["User", "user  /  aibootcamp", "Those pages, both journeys, and Ask NaviCare"],
        ["Admin", "admin  /  aibootcamp", "Every page, plus Admin: session counts and document notes"],
    ]
    add_rect(slide, Inches(0.55), Inches(1.7), Inches(12.2), Inches(0.7), NAVY)
    xs = [Inches(0.7), Inches(3.3), Inches(6.4)]
    widths = [Inches(2.4), Inches(2.9), Inches(6.0)]
    for text, left, width in zip(headers, xs, widths):
        add_text(slide, text, left, Inches(1.84), width, Inches(0.4), size=16, bold=True, color=WHITE)
    for index, row in enumerate(rows):
        top = Inches(2.5) + Inches(index * 1.15)
        add_rect(slide, Inches(0.55), top, Inches(12.2), Inches(1.05), WHITE)
        for text, left, width in zip(row, xs, widths):
            add_text(slide, text, left, top + Inches(0.28), width, Inches(0.5), size=18, bold=(left == xs[0]), color=NAVY if left == xs[0] else INK)
    set_notes(
        slide,
        "Show this before the demo so the room knows why you sign in halfway through. Home, About Us, and Methodology stay open on purpose.",
    )

    slide = presentation.slides.add_slide(blank)
    chrome(slide, "Technology stack", "A Streamlit app, a local vector index, and an optional model", 7, total)
    stack = [
        ("Python", "UI, journey rules, and retrieval live in the project folder. There is no separate user database."),
        ("Streamlit", "Multipage experience in one app: forms, tables, visual guides, and the chat."),
        ("FAISS", "Sample notes and admin uploads are split into passages and stored as normalised term vectors."),
        ("OpenAI, optional", "gpt-4o-mini is used only when OPENAI_API_KEY is set. Answers still work from the notes with no key."),
        ("Hosting", "Streamlit Community Cloud, from the GitHub repository, main file app.py."),
    ]
    for index, (heading, body) in enumerate(stack):
        top = Inches(1.5) + Inches(index * 1.02)
        add_rect(slide, Inches(0.55), top, Inches(12.2), Inches(0.92), WHITE)
        add_text(slide, heading, Inches(0.75), top + Inches(0.16), Inches(2.6), Inches(0.55), size=18, bold=True, color=TEAL)
        add_text(slide, body, Inches(3.4), top + Inches(0.16), Inches(9.1), Inches(0.62), size=16, color=INK)
    set_notes(
        slide,
        "If asked about the vector store, say FAISS, IndexFlatIP, built in rag.py from the markdown notes in data/samples. Retrieval does not call an API. The chat model does, and only when a key exists.",
    )

    slide = presentation.slides.add_slide(blank)
    chrome(slide, "Technology stack", "What happens when someone asks a question", 8, total)
    steps = [
        ("1", "Question", "A general question, with no personal data."),
        ("2", "Retrieve", "FAISS returns the closest passages from the sample set or an admin upload."),
        ("3", "Answer", "The built-in explainer, or the model if a key is configured."),
        ("4", "Check", "The screen names the passages and tells the reader to verify."),
    ]
    for index, (number, heading, body) in enumerate(steps):
        left = Inches(0.5) + Inches(index * 3.2)
        add_rect(slide, left, Inches(2.15), Inches(3.0), Inches(3.2), WHITE)
        add_text(slide, number, left + Inches(0.2), Inches(2.35), Inches(2.5), Inches(0.6), size=28, bold=True, color=TEAL)
        add_text(slide, heading, left + Inches(0.2), Inches(3.1), Inches(2.6), Inches(0.5), size=22, bold=True, color=NAVY)
        add_text(slide, body, left + Inches(0.2), Inches(3.7), Inches(2.6), Inches(1.3), size=16, color=INK)
    set_notes(slide, "Use this as the bridge into the demo. The live app should show the retrieved passage names after the answer.")

    slide = presentation.slides.add_slide(blank)
    chrome(slide, "Product demo", "Run it in this order", 9, total)
    demo = [
        "1   Home. Open the disclaimer. Do not sign in yet.",
        "2   About Us and Methodology. Both are open. Show one flowchart per use case.",
        "3   Click Explore scheme coverage. Sign in as user, password aibootcamp.",
        "4   Build a learning pathway. Show the comparison table and the six activities.",
        "5   Care conversation. Build a checklist for an AIC application.",
        "6   Ask NaviCare: “Where can a caregiver read about eFASS?” Show the retrieved passage and download the answer.",
        "7   Sign out. Sign in as admin. Show the session counts, then upload a short .txt note.",
        "8   Ask the same question again only if the new note should appear. End on the official CPF link.",
    ]
    bullets(slide, demo, Inches(0.6), Inches(1.5), Inches(12.2), Inches(5.2), size=18)
    set_notes(
        slide,
        "Member 3 drives. Keep the app already loaded. If the network stalls, use the local run. Do not type an NRIC or a medical story into the chat. The password on this slide is the demo password for the marking form.",
    )

    slide = presentation.slides.add_slide(blank)
    chrome(slide, "Product demo", "Group-of-3 sample, and where it appears in the demo", 10, total)
    mapping = [
        ("Roles", "User asks questions. Admin uploads a document and sees every page."),
        ("Features", "Scheme journey, care checklist, retrieval query, and answer download."),
        ("Vector store", "FAISS over data/samples, plus any note added on the Admin page."),
        ("Backend", "Streamlit. No user database. Uploaded notes are plain text files."),
        ("Deploy", "Streamlit Community Cloud. Put the URL and password aibootcamp in LaunchPad."),
        ("Pages", "About Us and Methodology are in the app and are open without a password."),
    ]
    for index, (heading, body) in enumerate(mapping):
        column = index % 2
        row = index // 2
        left = Inches(0.5) + Inches(column * 6.4)
        top = Inches(1.55) + Inches(row * 1.7)
        add_rect(slide, left, top, Inches(6.15), Inches(1.55), WHITE)
        add_text(slide, heading, left + Inches(0.25), top + Inches(0.15), Inches(5.7), Inches(0.4), size=18, bold=True, color=TEAL)
        add_text(slide, body, left + Inches(0.25), top + Inches(0.6), Inches(5.7), Inches(0.75), size=15, color=INK)
    set_notes(
        slide,
        "This slide answers the group-of-3 sample guideline. If a marker asks for the sample document set, open data/samples in the repository: five short notes on CareShield Life, ElderShield, daily activities, AIC, and supplements.",
    )

    slide = presentation.slides.add_slide(blank)
    chrome(slide, "Team of 3", "Suggested split. Replace the labels with your names.", 11, total)
    card(slide, Inches(0.5), Inches(1.7), Inches(4.0), Inches(4.5), "Member 1", "Background and motivation", "Official sources, why the journeys exist, and the disclaimer. Hands over after the motivation slide.")
    card(slide, Inches(4.7), Inches(1.7), Inches(4.0), Inches(4.5), "Member 2", "Audience and stack", "Who signs in, FAISS retrieval, and when the optional model is used. Hands over at the demo path.")
    card(slide, Inches(8.9), Inches(1.7), Inches(3.9), Inches(4.5), "Member 3", "Live demo", "Drives the eight demo steps. Ends by opening the CPF Board CareShield Life page.")
    set_notes(slide, "Edit the three names on the title slide and on this slide before the presentation. Keep each speaking part under two minutes so the demo has room.")

    slide = presentation.slides.add_slide(blank)
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, NAVY)
    add_rect(slide, 0, 0, Inches(0.22), SLIDE_H, TEAL)
    add_text(slide, "BEFORE YOU CLOSE", Inches(0.7), Inches(1.5), Inches(11), Inches(0.4), size=14, bold=True, color=TEAL)
    add_text(slide, "Verify with the\nofficial page.", Inches(0.7), Inches(2.05), Inches(11), Inches(1.6), size=44, bold=True, color=WHITE)
    add_text(
        slide,
        "NaviCare explains CareShield Life and ElderShield.\nIt does not decide cover, a claim, or a payout.\n\nuser or admin    ·    password aibootcamp",
        Inches(0.7),
        Inches(4.2),
        Inches(11),
        Inches(1.5),
        size=20,
        color=RGBColor(0xD7, 0xE8, 0xE4),
    )
    set_notes(slide, "Stop on this slide. Repeat the password only if the marker asks how to sign in. Thank the room.")

    presentation.save(path)


if __name__ == "__main__":
    build("NaviCare_presentation.pptx")
