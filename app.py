import os
import re
import time
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def _cfg(key: str, default: str = "") -> str:
    """Read from st.secrets (Streamlit Cloud) then fall back to env vars."""
    try:
        val = st.secrets.get(key)
        if val is not None:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)

OPENAI_API_KEY   = _cfg("OPENAI_API_KEY")
SMTP_HOST        = _cfg("SMTP_HOST")
SMTP_PORT        = int(_cfg("SMTP_PORT") or 587)
SMTP_USER        = _cfg("SMTP_USER")
SMTP_PASSWORD    = _cfg("SMTP_PASSWORD")
ALERT_EMAIL_TO   = _cfg("ALERT_EMAIL_TO")
ALERT_EMAIL_FROM = _cfg("ALERT_EMAIL_FROM")

# ─────────────────────────────────────────────────────────────────────────────
# FAQ Knowledge Base
# ─────────────────────────────────────────────────────────────────────────────

FAQ = [
    {
        "id": "online_course_access",
        "keywords": ["online course", "access online", "online class", "online training",
                     "course access", "online blended", "online portion", "online part",
                     "access course", "access my course", "how access"],
        "question": "How do I access my online course?",
        "answer": (
            "After enrolling, you will receive a confirmation email with a link to access your online course. "
            "Log in with the email address you used during registration. "
            "Complete the online portion before attending your hands-on skills session."
        ),
    },
    {
        "id": "login_issues",
        "keywords": ["login", "log in", "can't login", "password", "forgot password",
                     "reset password", "sign in", "account", "username", "cant log"],
        "question": "I'm having trouble logging in. What should I do?",
        "answer": (
            "If you cannot log in, try resetting your password using the 'Forgot Password' link on the login page. "
            "Make sure you are using the same email address you registered with. "
            "Clear your browser cache and cookies, then try again. "
            "If the problem persists, contact our support team."
        ),
    },
    {
        "id": "browser_troubleshooting",
        "keywords": ["browser", "not loading", "video not playing", "page won't load",
                     "technical issue", "chrome", "firefox", "safari", "edge", "compatible",
                     "not working", "page not", "site not"],
        "question": "The course isn't loading properly in my browser. What can I do?",
        "answer": (
            "We recommend using Google Chrome or Mozilla Firefox for the best experience. "
            "Make sure your browser is up to date. "
            "Disable browser extensions/ad blockers temporarily. "
            "Clear your cache and cookies. "
            "If videos won't play, check that JavaScript is enabled and your internet connection is stable."
        ),
    },
    {
        "id": "cpr_vs_bls",
        "keywords": ["cpr vs bls", "difference between cpr and bls", "cpr or bls", "bls vs cpr",
                     "what is bls", "what is cpr", "bls different", "cpr bls difference",
                     "difference cpr bls", "bls vs cpr"],
        "question": "What is the difference between CPR and BLS?",
        "answer": (
            "CPR (Cardiopulmonary Resuscitation) is a life-saving technique for cardiac arrest. "
            "BLS (Basic Life Support) is a higher-level certification that includes CPR plus additional "
            "skills like using an AED and relieving choking — designed for healthcare providers and first responders. "
            "If you are a healthcare professional, you likely need BLS. CPR courses are suitable for the general public."
        ),
    },
    {
        "id": "arc_vs_aha",
        "keywords": ["arc vs aha", "american red cross", "american heart association",
                     "red cross or heart association", "which certification", "arc or aha",
                     "aha or arc", "red cross aha", "arc aha difference"],
        "question": "What is the difference between ARC and AHA certifications?",
        "answer": (
            "ARC (American Red Cross) and AHA (American Heart Association) are both nationally recognized "
            "organizations that offer CPR/BLS certifications. "
            "Both follow similar guidelines and are widely accepted by employers. "
            "We offer courses certified by both organizations — check the course listing to see which "
            "certification it provides."
        ),
    },
    {
        "id": "same_day_enrollment",
        "keywords": ["same day", "enroll today", "sign up today", "last minute", "register today",
                     "same-day", "today class", "enroll now", "sign up now", "join today"],
        "question": "Can I enroll on the same day as the class?",
        "answer": (
            "Yes! Same-day enrollment is available as long as seats remain open. "
            "However, for blended learning courses, you must complete the online portion before the "
            "in-person skills session. "
            "We strongly recommend enrolling at least 24 hours in advance to ensure you have time to "
            "finish the online content."
        ),
    },
    {
        "id": "what_to_bring",
        "keywords": ["bring to class", "what to bring", "what should i bring", "bring with me",
                     "class requirements", "what do i need", "wear to class", "need to bring",
                     "bring class", "class items"],
        "question": "What should I bring to class?",
        "answer": (
            "Please bring a valid photo ID and your online course completion certificate (if applicable). "
            "Wear comfortable clothing you can move in, as you will practice skills on the floor. "
            "Arrive a few minutes early and bring any required paperwork or payment if not already "
            "completed online."
        ),
    },
    {
        "id": "email_requirement",
        "keywords": ["email required", "need email", "email address", "why email", "valid email",
                     "email for registration", "need an email", "require email"],
        "question": "Why do I need an email address to register?",
        "answer": (
            "A valid email address is required to create your account, receive your course confirmation, "
            "access your online materials, and receive your digital certification card. "
            "Please use an email address you check regularly."
        ),
    },
    {
        "id": "rescheduling",
        "keywords": ["reschedule", "change my class", "move my class", "different date",
                     "change date", "new date", "change class date", "switch class",
                     "change my appointment", "different time"],
        "question": "How do I reschedule my class?",
        "answer": (
            "To reschedule, log into your account and navigate to 'My Courses.' "
            "Select the class you wish to reschedule and choose an available date. "
            "Rescheduling is available up to 24 hours before your scheduled session. "
            "Contact support if you need to reschedule with less than 24 hours' notice."
        ),
    },
    {
        "id": "cancellation_refunds",
        "keywords": ["cancel", "refund", "cancellation", "money back", "return",
                     "get a refund", "canceled class", "cancel class", "refund policy",
                     "cancel my registration", "want refund"],
        "question": "What is the cancellation and refund policy?",
        "answer": (
            "Cancellations made more than 48 hours before the class start time are eligible for a full refund. "
            "Cancellations within 48 hours may receive a credit toward a future class. "
            "No-shows are not eligible for refunds. "
            "Contact our support team to initiate a cancellation."
        ),
    },
    {
        "id": "certification_timing",
        "keywords": ["how long", "when will i get", "certification time", "receive card",
                     "how soon", "card timing", "get my card", "receive certification",
                     "when get certificate", "card when", "cert when", "how long certificate"],
        "question": "How long does it take to receive my certification?",
        "answer": (
            "Digital certification cards are typically issued within 24 hours of successfully completing "
            "your course. "
            "Physical cards, if requested, may take 7–14 business days to arrive by mail."
        ),
    },
    {
        "id": "certificate_retrieval",
        "keywords": ["lost certificate", "retrieve certificate", "find my certificate",
                     "download certificate", "reprint", "reissue card", "lost card",
                     "missing certificate", "lost my card", "cant find certificate",
                     "where is my certificate", "retrieve my card"],
        "question": "I lost my certificate. How do I retrieve it?",
        "answer": (
            "Log into your account and go to 'My Certifications' to download or print your digital card "
            "at any time. "
            "If you cannot find it, contact support with your full name and date of class and we can "
            "re-send it."
        ),
    },
    {
        "id": "expedited_certification",
        "keywords": ["expedited", "urgent certificate", "need certificate fast", "same day certificate",
                     "rush certificate", "need it today", "asap certificate", "fast card",
                     "certificate urgently"],
        "question": "Can I get an expedited certification?",
        "answer": (
            "Digital cards are usually available within 24 hours and cannot be expedited further. "
            "If you have an urgent employer or hospital deadline, please contact our support team "
            "directly so we can prioritize your request."
        ),
    },
    {
        "id": "ceus",
        "keywords": ["ceu", "continuing education", "continuing education units", "credit hours",
                     "nursing ceu", "professional credits", "ce credits", "cme", "credit"],
        "question": "Do your courses offer CEUs (Continuing Education Units)?",
        "answer": (
            "Some of our courses offer CEUs for healthcare professionals. "
            "Please check the individual course description for CEU information. "
            "If you need specific documentation for your employer or licensing board, contact us "
            "and we will assist you."
        ),
    },
    {
        "id": "group_onsite_training",
        "keywords": ["group training", "onsite training", "on-site", "corporate training",
                     "team training", "train my staff", "group rate", "organization training",
                     "train my team", "company training", "business training", "bulk training"],
        "question": "Do you offer group or on-site training?",
        "answer": (
            "Yes! We offer group and on-site training for businesses, hospitals, schools, and organizations. "
            "Contact us to discuss scheduling, pricing, and minimum group sizes. "
            "We can bring certified instructors directly to your location."
        ),
    },
    {
        "id": "locations",
        "keywords": ["location", "where are you", "address", "near me", "city", "state",
                     "where can i take", "class near", "find a class", "training center",
                     "classes near", "near my area", "close to me"],
        "question": "Where are your class locations?",
        "answer": (
            "We have multiple training locations across the US. "
            "Visit our website and use the 'Find a Class' search to locate sessions near you by zip code or city. "
            "We also offer on-site training at your facility."
        ),
    },
    {
        "id": "hands_on_experience",
        "keywords": ["hands-on", "hands on", "practice", "mannequin", "skills session",
                     "in person", "in-person", "physical class", "practice skills",
                     "skill practice", "practice cpr"],
        "question": "Will I get hands-on practice?",
        "answer": (
            "Yes. Our blended learning courses include an in-person skills session where you practice on "
            "mannequins with a certified instructor. "
            "You must pass a skills evaluation to receive your certification."
        ),
    },
    {
        "id": "accreditation",
        "keywords": ["accredited", "accreditation", "recognized", "accepted", "hospital accepted",
                     "employer accepted", "valid certification", "nationally recognized",
                     "is it accepted", "certification valid", "legitimate"],
        "question": "Are your certifications accredited and accepted by employers?",
        "answer": (
            "Yes. Our certifications are issued through the American Heart Association (AHA) and/or the "
            "American Red Cross (ARC), which are nationally recognized and accepted by hospitals, clinics, "
            "schools, and most employers."
        ),
    },
    {
        "id": "first_time_renewals",
        "keywords": ["first time", "new student", "renewal", "renew", "expired card",
                     "how often renew", "renew certification", "re-certify", "first class",
                     "first cpr", "never taken", "beginner", "expired certification"],
        "question": "Can first-time students and renewals take the same course?",
        "answer": (
            "Yes. Our courses welcome both first-time students and those renewing their certification. "
            "Certifications are typically valid for 2 years. "
            "If your card is expired, you can still take the standard course — no special renewal course "
            "is needed."
        ),
    },
    {
        "id": "receipts",
        "keywords": ["receipt", "invoice", "proof of payment", "billing", "payment confirmation",
                     "paid", "tax receipt", "show payment", "payment proof", "billing record"],
        "question": "How do I get a receipt for my payment?",
        "answer": (
            "A payment confirmation email is sent automatically after purchase. "
            "You can also log into your account and go to 'Purchase History' to download a receipt at "
            "any time."
        ),
    },
    {
        "id": "feedback",
        "keywords": ["feedback", "review", "complaint", "suggestion", "rate", "rating",
                     "comment", "experience", "leave review", "give feedback", "survey"],
        "question": "How can I leave feedback about my course?",
        "answer": (
            "We appreciate your feedback! After completing your course, you will receive a follow-up "
            "email with a link to our survey. "
            "You can also contact us directly via email or phone to share your experience."
        ),
    },
    {
        "id": "contact_information",
        "keywords": ["contact", "phone number", "email address", "reach you", "customer service",
                     "support", "talk to someone", "speak with", "call you", "get in touch",
                     "contact support", "help desk", "reach support"],
        "question": "How do I contact customer support?",
        "answer": (
            "You can reach our customer support team at info@allcpr.org or by phone at 408-443-3055. "
            "We are available Monday–Friday, 9 AM–5 PM."
        ),
    },
]

EMERGENCY_KEYWORDS = [
    "how do i do cpr", "how to do cpr", "cpr steps", "perform cpr",
    "choking", "heimlich", "someone is choking", "what if someone is choking",
    "not breathing", "unconscious", "heart attack symptoms", "stroke symptoms",
    "emergency procedure", "first aid steps", "how to save someone",
    "aed steps", "use an aed", "how to use aed",
    "rescue breathing", "chest compressions how",
]

# ─────────────────────────────────────────────────────────────────────────────
# Matching Logic
# ─────────────────────────────────────────────────────────────────────────────

STOP_WORDS = {
    'i', 'a', 'an', 'the', 'is', 'it', 'my', 'me', 'how', 'do', 'can',
    'what', 'when', 'where', 'why', 'who', 'will', 'to', 'for', 'of',
    'in', 'on', 'at', 'be', 'are', 'was', 'were', 'have', 'has', 'had',
    'get', 'got', 'did', 'if', 'or', 'and', 'but', 'not', 'no', 'so',
    'up', 'out', 'about', 'with', 'from', 'by', 'this', 'that', 'there',
    'they', 'we', 'us', 'our', 'you', 'your', 'him', 'her', 'his', 'its',
    'would', 'should', 'could', 'please', 'need', 'want', 'like', 'just',
    'also', 'any', 'some', 'more', 'does', 'am', 'into', 'than', 'then',
    'hey', 'hi', 'hello', 'ok', 'okay', 'yeah', 'yes',
}


def _words(text: str) -> set:
    return {w for w in re.sub(r"[^\w\s]", "", text.lower()).split()
            if w not in STOP_WORDS and len(w) > 1}


def is_emergency_question(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in EMERGENCY_KEYWORDS)


def find_faq_answer(user_question: str) -> dict | None:
    lower = re.sub(r"[^\w\s]", "", user_question.lower())
    user_words = _words(user_question)

    best_match = None
    best_score = 0.0

    for entry in FAQ:
        score = 0.0
        for kw in entry["keywords"]:
            kw_clean = re.sub(r"[^\w\s]", "", kw.lower())
            kw_words = _words(kw)

            if kw_clean in lower:
                score += 3.0
            elif kw_words and kw_words.issubset(set(lower.split())):
                score += 2.0
            else:
                overlap = len(kw_words & user_words)
                if overlap:
                    score += overlap * 0.8

        if score > best_score:
            best_score = score
            best_match = entry

    return best_match if best_score >= 0.8 else None


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI + Email helpers
# ─────────────────────────────────────────────────────────────────────────────

def polish_answer_with_openai(question: str, raw_answer: str) -> str:
    if not OPENAI_API_KEY:
        return raw_answer
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": (
                "You are a friendly customer service agent for AllCPR / BLS training. "
                "Rewrite the following answer in a warm, professional, concise tone. "
                "Do NOT add any information not already in the answer. Keep it under 5 sentences.\n\n"
                f"Customer question: {question}\n\nDraft answer: {raw_answer}\n\nPolished answer:"
            )}],
            max_tokens=300, temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return raw_answer


def summarize_question(question: str) -> str:
    if OPENAI_API_KEY:
        try:
            import openai
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": (
                    "Summarize the following customer question in one concise sentence "
                    "for an internal support ticket. Do not answer it.\n\nQuestion: " + question
                )}],
                max_tokens=80, temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass
    return f"Customer asked: {question[:200]}"


def send_alert_email(user_question: str, summary: str, reason: str) -> bool:
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO, ALERT_EMAIL_FROM]):
        return False
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[AllCPR Agent] Unanswered Question — {timestamp}"
        msg["From"] = ALERT_EMAIL_FROM
        msg["To"] = ALERT_EMAIL_TO
        body = (
            f"AllCPR Smart Customer Service Agent — Escalation\n"
            f"{'='*52}\n"
            f"Timestamp : {timestamp}\n"
            f"Reason    : {reason}\n\n"
            f"Customer Question:\n{user_question}\n\n"
            f"AI Summary:\n{summary}\n\n"
            f"Please follow up with the customer."
        )
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo(); server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL_TO, msg.as_string())
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Streamlit UI
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AllCPR Smart Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    background: #f4f4f4 !important;
    font-family: 'Inter', sans-serif !important;
    color: #1a1a1a !important;
    margin: 0; padding: 0;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* ── AllCPR Top Contact Bar ── */
.allcpr-contact-bar {
    background: #fff;
    border-bottom: 1px solid #e8e8e8;
    padding: 6px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8rem;
    color: #444;
}
.allcpr-contact-bar a { color: #444; text-decoration: none; margin-right: 18px; }
.allcpr-contact-bar a:hover { color: #c0272d; }
.social-icons { display: flex; gap: 12px; }
.social-icons a {
    width: 26px; height: 26px; border-radius: 50%;
    border: 1px solid #ddd;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; color: #555; text-decoration: none;
    transition: all 0.15s;
}
.social-icons a:hover { background: #c0272d; color: white; border-color: #c0272d; }

/* ── AllCPR Navbar ── */
.allcpr-nav {
    background: #fff;
    border-bottom: 3px solid #c0272d;
    padding: 10px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.allcpr-logo {
    display: flex; align-items: center; gap: 10px;
    text-decoration: none;
}
.allcpr-logo-circle {
    width: 48px; height: 48px; border-radius: 50%;
    border: 3px solid #c0272d;
    display: flex; align-items: center; justify-content: center;
    background: #fff;
}
.allcpr-logo-cross {
    font-size: 1.5rem; color: #c0272d; font-weight: 900; line-height: 1;
}
.allcpr-logo-text {
    font-size: 1.3rem; font-weight: 800;
    color: #c0272d; letter-spacing: -0.5px;
}
.allcpr-nav-links {
    display: flex; gap: 0; align-items: center;
}
.allcpr-nav-links a {
    padding: 8px 16px;
    font-size: 0.875rem; font-weight: 500;
    color: #333; text-decoration: none;
    border-radius: 4px;
    transition: color 0.15s;
    white-space: nowrap;
}
.allcpr-nav-links a:hover { color: #c0272d; }
.allcpr-nav-links a.active { color: #c0272d; font-weight: 600; }
.nav-btn {
    background: #c0272d !important;
    color: white !important;
    border-radius: 6px !important;
    padding: 8px 18px !important;
    font-weight: 600 !important;
    margin-left: 6px;
}
.nav-btn:hover { background: #a01e24 !important; }

/* ── Page hero banner ── */
.page-hero {
    background: linear-gradient(135deg, #c0272d 0%, #8b0000 100%);
    padding: 28px 40px;
    display: flex; align-items: center; gap: 18px;
}
.page-hero-icon {
    width: 52px; height: 52px; border-radius: 50%;
    background: rgba(255,255,255,0.2);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem;
    border: 2px solid rgba(255,255,255,0.35);
}
.page-hero-title {
    font-size: 1.3rem; font-weight: 700; color: #fff;
}
.page-hero-sub {
    font-size: 0.78rem; color: rgba(255,255,255,0.8);
    margin-top: 2px;
}
.hero-badge {
    margin-left: auto;
    display: flex; align-items: center; gap: 7px;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.75rem; color: rgba(255,255,255,0.9);
}
.live-dot {
    width: 7px; height: 7px; border-radius: 50%; background: #4ade80;
    animation: live 2s infinite;
}
@keyframes live {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(74,222,128,0.5); }
    50%       { opacity: 0.6; box-shadow: 0 0 0 5px rgba(74,222,128,0); }
}

/* ── Chat body layout ── */
.chat-body {
    display: flex;
    max-width: 1100px;
    margin: 30px auto;
    gap: 22px;
    padding: 0 24px 40px;
}

/* ── Chat window ── */
.chat-window {
    flex: 1;
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.08);
    overflow: hidden;
    border: 1px solid #e8e8e8;
}
.chat-window-header {
    background: #f9f9f9;
    border-bottom: 1px solid #e8e8e8;
    padding: 14px 20px;
    display: flex; align-items: center; gap: 10px;
}
.chat-win-avatar {
    width: 36px; height: 36px; border-radius: 50%;
    background: #c0272d;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; color: white; font-weight: 700;
}
.chat-win-name { font-size: 0.9rem; font-weight: 600; color: #1a1a1a; }
.chat-win-status {
    font-size: 0.7rem; color: #16a34a;
    display: flex; align-items: center; gap: 4px;
}
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #16a34a; }

/* ── Messages ── */
.messages { padding: 20px; min-height: 320px; width: 100%; box-sizing: border-box; }

.msg-row {
    display: flex; align-items: flex-end; gap: 8px;
    margin-bottom: 14px; width: 100%; min-width: 0;
}
.msg-row.user { flex-direction: row-reverse; }

.av {
    width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 700;
}
.av.agent { background: #c0272d; color: white; }
.av.user  { background: #e5e7eb; color: #555; }

/* msg-body: flex child that anchors bubble width */
.msg-body {
    display: flex; flex-direction: column;
    flex: 1 1 0; min-width: 0;
}
.msg-row.user .msg-body { align-items: flex-end; }
.msg-row:not(.user) .msg-body { align-items: flex-start; }

.bubble {
    display: inline-block;
    max-width: 78%;
    padding: 11px 15px;
    font-size: 0.875rem;
    line-height: 1.65;
    overflow-wrap: break-word;
    word-break: break-word;
    border-radius: 16px;
    box-sizing: border-box;
    min-width: 0;
}
.bubble.agent {
    background: #f3f4f6;
    border-bottom-left-radius: 4px;
    color: #1a1a1a;
}
.bubble.user {
    background: #c0272d;
    color: white;
    border-bottom-right-radius: 4px;
}
.msg-label { font-size: 0.62rem; color: #9ca3af; margin-top: 3px; padding: 0 4px; }

/* ── Typing indicator ── */
.typing-wrap {
    display: flex; align-items: flex-end; gap: 8px; margin-bottom: 14px;
}
.typing-bubble {
    background: #f3f4f6;
    border-radius: 16px 16px 16px 4px;
    padding: 14px 18px;
    display: flex; align-items: center; gap: 5px;
}
.typing-bubble span {
    width: 8px; height: 8px; border-radius: 50%;
    background: #c0272d; display: inline-block;
    animation: dot-bounce 1.3s infinite ease-in-out;
}
.typing-bubble span:nth-child(2) { animation-delay: 0.2s; }
.typing-bubble span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-bounce {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
    40%            { transform: translateY(-8px); opacity: 1; }
}

/* ── Quick chip buttons ── */
.chips-label {
    font-size: 0.68rem; color: #9ca3af; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    padding: 10px 20px 6px; border-top: 1px solid #f3f4f6;
}

/* All .stButton > button = chip style (expander buttons override via higher specificity) */
.stButton > button {
    background: #fff !important;
    border: 1.5px solid #e5e7eb !important;
    border-radius: 24px !important;
    color: #c0272d !important;
    font-size: 0.76rem !important;
    font-weight: 500 !important;
    padding: 5px 14px !important;
    box-shadow: none !important;
    transition: background 0.13s, border-color 0.13s !important;
    font-family: 'Inter', sans-serif !important;
    white-space: normal !important;
    line-height: 1.35 !important;
    min-height: 34px !important;
}
.stButton > button:hover {
    background: #fef2f2 !important;
    border-color: #c0272d !important;
    color: #c0272d !important;
    transform: none !important;
}
.stButton > button:focus { box-shadow: none !important; outline: none !important; }

/* ── Input row ── */
.input-row { padding: 14px 20px; border-top: 1px solid #e8e8e8; background: #fafafa; }

.stTextInput > div > div > input {
    background: #fff !important;
    border: 1.5px solid #e5e7eb !important;
    border-radius: 10px !important;
    color: #1a1a1a !important;
    padding: 11px 15px !important;
    font-size: 0.875rem !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #c0272d !important;
    box-shadow: 0 0 0 3px rgba(192,39,45,0.1) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #c4c4c4 !important; }

.stFormSubmitButton > button {
    background: #c0272d !important;
    border: none !important; border-radius: 10px !important;
    color: white !important; font-weight: 600 !important;
    font-size: 0.875rem !important; padding: 11px 16px !important;
    width: 100% !important; height: 46px !important;
    white-space: nowrap !important;
    min-width: 64px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 2px 6px rgba(192,39,45,0.3) !important;
    transition: background 0.15s !important;
}
.stFormSubmitButton > button:hover {
    background: #a01e24 !important;
}

.stForm, [data-testid="stForm"] { background: transparent !important; border: none !important; }

.input-hint {
    font-size: 0.65rem; color: #c4c4c4; text-align: center; margin-top: 8px;
}

/* ── Info sidebar card ── */
.info-box {
    background: #fff; border-radius: 12px;
    border: 1px solid #e8e8e8;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    overflow: hidden; margin-bottom: 14px;
}
.info-box-header {
    background: #c0272d; padding: 12px 16px;
    font-size: 0.8rem; font-weight: 600; color: white;
}
.info-box-body { padding: 14px 16px; }
.info-item {
    display: flex; align-items: flex-start; gap: 8px;
    font-size: 0.78rem; color: #444; margin-bottom: 10px; line-height: 1.5;
}
.info-item:last-child { margin-bottom: 0; }
.info-icon { font-size: 0.9rem; flex-shrink: 0; margin-top: 1px; }

/* ── Collapsible topics expander ── */
[data-testid="stExpander"] {
    background: #fff !important;
    border: 1px solid #e8e8e8 !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06) !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] > details > summary {
    background: #c0272d !important;
    color: white !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 12px 16px !important;
    border-radius: 0 !important;
    list-style: none !important;
}
[data-testid="stExpander"] > details > summary:hover {
    background: #a01e24 !important;
    color: white !important;
}
[data-testid="stExpander"] > details > summary svg {
    fill: white !important; stroke: white !important;
}
[data-testid="stExpander"] > details[open] > summary {
    border-bottom: 1px solid #e8e8e8 !important;
}
[data-testid="stExpander"] > details > div {
    padding: 4px 0 !important;
}

/* Topic buttons styled as list rows */
[data-testid="stExpander"] .stButton > button {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid #f5f5f5 !important;
    border-radius: 0 !important;
    padding: 8px 14px !important;
    text-align: left !important;
    color: #444 !important;
    font-size: 0.77rem !important;
    width: 100% !important;
    justify-content: flex-start !important;
    box-shadow: none !important;
    font-weight: 400 !important;
    line-height: 1.4 !important;
    transition: background 0.12s, color 0.12s, padding-left 0.12s !important;
}
[data-testid="stExpander"] .stButton > button:hover {
    background: #fef2f2 !important;
    color: #c0272d !important;
    padding-left: 20px !important;
    border-bottom-color: #f9d0d0 !important;
}
[data-testid="stExpander"] .stButton > button:focus,
[data-testid="stExpander"] .stButton > button:active {
    box-shadow: none !important;
    outline: none !important;
    color: #c0272d !important;
    background: #fef2f2 !important;
}

/* ── AllCPR Footer ── */
.allcpr-footer {
    background: #222;
    color: #aaa;
    text-align: center;
    padding: 20px 40px;
    font-size: 0.75rem;
    margin-top: 10px;
}
.allcpr-footer a { color: #c0272d; text-decoration: none; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #e0e0e0; border-radius: 4px; }

/* ── Responsive ── */
@media (max-width: 900px) {
    .allcpr-nav-links { display: none !important; }
    .allcpr-contact-bar { flex-direction: column; gap: 4px; text-align: center; }
    .allcpr-nav { padding: 10px 16px !important; }
    .page-hero { padding: 18px 16px !important; flex-wrap: wrap; gap: 10px; }
    .hero-badge { margin-left: 0 !important; }
}
@media (max-width: 768px) {
    /* Stack the two-column layout */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0 !important;
    }
    [data-testid="stHorizontalBlock"] > div {
        width: 100% !important;
        min-width: 100% !important;
        flex: none !important;
    }
    .bubble { max-width: 85% !important; }
    .messages { padding: 14px !important; }
    .input-row { padding: 10px 14px !important; }
    .chips-label { padding: 8px 14px 4px !important; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ── AllCPR Navbar ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="allcpr-contact-bar">
  <div>
    <a href="mailto:info@allcpr.org">✉ info@allcpr.org</a>
    <a href="tel:4084433055">📞 408-443-3055</a>
  </div>
  <div class="social-icons">
    <a href="https://facebook.com" target="_blank">f</a>
    <a href="https://twitter.com"  target="_blank">t</a>
    <a href="https://instagram.com" target="_blank">in</a>
  </div>
</div>

<div class="allcpr-nav">
  <a class="allcpr-logo" href="https://allcpr.org" target="_blank">
    <div class="allcpr-logo-circle">
      <div class="allcpr-logo-cross">+</div>
    </div>
    <span class="allcpr-logo-text">ALLCPR</span>
  </a>
  <div class="allcpr-nav-links">
    <a href="https://allcpr.org" target="_blank">Home</a>
    <a href="https://allcpr.org/courses" target="_blank">Courses</a>
    <a href="https://allcpr.org/locations" target="_blank">Locations</a>
    <a href="https://allcpr.org/faq" target="_blank">FAQ</a>
    <a href="https://allcpr.org/group-training" target="_blank">Group Training</a>
    <a href="https://allcpr.org/resources" target="_blank">Resources</a>
    <a href="https://allcpr.org/join" target="_blank" class="nav-btn">Join Us</a>
  </div>
</div>

<div class="page-hero">
  <div class="page-hero-icon" style="font-size:1.2rem;font-weight:700;">CS</div>
  <div>
    <div class="page-hero-title">Smart Customer Service Agent</div>
    <div class="page-hero-sub">Get instant answers about CPR, BLS, certification, scheduling &amp; more</div>
  </div>
  <div class="hero-badge"><div class="live-dot"></div> Agent Online</div>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "agent",
            "content": (
                "Hello! Welcome to AllCPR customer support. "
                "I can help you with online courses, certification, scheduling, refunds, locations, and more. "
                "How can I assist you today?"
            ),
        }
    ]
if "pending" not in st.session_state:
    st.session_state.pending = None

# ── Layout: chat + sidebar ────────────────────────────────────────────────────
TOPIC_ICONS = {
    "online_course_access": "🎓", "login_issues": "🔑",
    "browser_troubleshooting": "🌐", "cpr_vs_bls": "❤️",
    "arc_vs_aha": "🏅", "same_day_enrollment": "⚡",
    "what_to_bring": "🎒", "email_requirement": "📧",
    "rescheduling": "📅", "cancellation_refunds": "💳",
    "certification_timing": "⏱", "certificate_retrieval": "📄",
    "expedited_certification": "🚀", "ceus": "📚",
    "group_onsite_training": "🏢", "locations": "📍",
    "hands_on_experience": "🤝", "accreditation": "✅",
    "first_time_renewals": "🔄", "receipts": "🧾",
    "feedback": "💬", "contact_information": "📞",
}

left_col, right_col = st.columns([3, 1], gap="medium")

with left_col:
    # Chat window header
    st.markdown("""
    <div class="chat-window">
      <div class="chat-window-header">
        <div class="chat-win-avatar">+</div>
        <div>
          <div class="chat-win-name">AllCPR Support Agent</div>
          <div class="chat-win-status"><div class="status-dot"></div> Online — Typically replies instantly</div>
        </div>
      </div>
    """, unsafe_allow_html=True)

    # Messages
    msgs_html = '<div class="messages">'
    for msg in st.session_state.messages:
        content = msg["content"].replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        if msg["role"] == "user":
            msgs_html += f"""
            <div class="msg-row user">
              <div class="av user">Y</div>
              <div class="msg-body">
                <div class="bubble user">{content}</div>
                <div class="msg-label">You</div>
              </div>
            </div>"""
        else:
            msgs_html += f"""
            <div class="msg-row">
              <div class="av agent">+</div>
              <div class="msg-body">
                <div class="bubble agent">{content}</div>
                <div class="msg-label">AllCPR Agent</div>
              </div>
            </div>"""

    # Typing indicator placeholder (shown while pending)
    if st.session_state.pending:
        msgs_html += """
        <div class="typing-wrap">
          <div class="av agent">+</div>
          <div class="typing-bubble">
            <span></span><span></span><span></span>
          </div>
        </div>"""

    msgs_html += "</div>"
    st.markdown(msgs_html, unsafe_allow_html=True)

    # Quick chip buttons — clicking sends the question directly to the agent
    SUGGESTIONS = [
        "How do I access my course?",
        "CPR vs BLS difference?",
        "Can I enroll same day?",
        "How long for my certificate?",
        "What's the refund policy?",
        "Do you offer group training?",
    ]
    st.markdown('<div class="chips-label">Common questions</div>', unsafe_allow_html=True)
    for row in [SUGGESTIONS[:3], SUGGESTIONS[3:]]:
        cols = st.columns(len(row))
        for col, suggestion in zip(cols, row):
            with col:
                if st.button(suggestion, key=f"chip_{suggestion[:20]}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": suggestion})
                    st.session_state.pending = suggestion
                    st.rerun()

    # Input
    st.markdown('<div class="input-row">', unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True):
        c1, c2 = st.columns([6, 1])
        with c1:
            user_input = st.text_input(
                "msg", placeholder="Type your question here…",
                label_visibility="collapsed",
            )
        with c2:
            submitted = st.form_submit_button("Send")
    st.markdown(
        '<div class="input-hint">Answers sourced from the AllCPR FAQ only · '
        'Not a substitute for professional medical advice</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close chat-window

with right_col:
    # Contact card
    st.markdown("""
    <div class="info-box">
      <div class="info-box-header">Contact Us</div>
      <div class="info-box-body">
        <div class="info-item"><span class="info-icon">✉️</span> info@allcpr.org</div>
        <div class="info-item"><span class="info-icon">📞</span> 408-443-3055</div>
        <div class="info-item"><span class="info-icon">🕐</span> Mon–Fri, 9 AM – 5 PM</div>
        <div class="info-item"><span class="info-icon">📍</span> Nearly 100 locations nationwide</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Collapsible topics — collapsed by default, click any to send question
    with st.expander("Topics I can help with", expanded=False):
        for entry in FAQ:
            if st.button(entry["question"], key=f"topic_{entry['id']}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": entry["question"]})
                st.session_state.pending = entry["question"]
                st.rerun()

    # Contact support detail
    st.markdown("""
    <div class="info-box" style="margin-top:14px;">
      <div class="info-box-header">Need more help?</div>
      <div class="info-box-body" style="font-size:0.78rem;color:#444;line-height:1.7;">
        If the agent can't answer your question, our support team will follow up.<br><br>
        <strong>Email:</strong> <a href="mailto:info@allcpr.org" style="color:#c0272d;">info@allcpr.org</a><br>
        <strong>Phone:</strong> 408-443-3055<br>
        <strong>Hours:</strong> Mon–Fri, 9 AM – 5 PM<br><br>
        You can also type your question below and it will be automatically forwarded to the team.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="allcpr-footer">
  © 2024 AllCPR · <a href="https://allcpr.org" target="_blank">allcpr.org</a> ·
  American Red Cross Primary Licensed Training Provider ·
  Proud AHA Training Site
</div>
""", unsafe_allow_html=True)

# ── Message handling — typing animation via pending state ─────────────────────
if submitted and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input.strip()})
    st.session_state.pending = user_input.strip()
    st.rerun()

if st.session_state.pending:
    question = st.session_state.pending

    # Brief delay so typing dots are visible before the answer appears
    time.sleep(1.2)

    if is_emergency_question(question):
        agent_reply = (
            "I'm sorry, I can only answer based on the AllCPR FAQ. "
            "This question may require professional medical or emergency guidance, "
            "so I have forwarded it to our support team for review."
        )
        email_sent = send_alert_email(
            user_question=question,
            summary=summarize_question(question),
            reason="Emergency / medical procedure question",
        )
    else:
        match = find_faq_answer(question)
        if match:
            agent_reply = polish_answer_with_openai(question, match["answer"])
            email_sent = False
        else:
            agent_reply = (
                "Thank you for reaching out! I wasn't able to find a specific answer to your question "
                "in our FAQ. I've forwarded it to our support team and someone will follow up with you shortly. "
                "You can also contact us directly at info@allcpr.org or 408-443-3055."
            )
            email_sent = send_alert_email(
                user_question=question,
                summary=summarize_question(question),
                reason="Question not found in FAQ knowledge base",
            )

    if email_sent:
        agent_reply += "\n\n✉️ Your question has been sent to our support team."

    st.session_state.messages.append({"role": "agent", "content": agent_reply})
    st.session_state.pending = None
    st.rerun()
