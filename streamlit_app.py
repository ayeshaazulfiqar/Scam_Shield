import os
import html
import streamlit as st

st.set_page_config(page_title="Scam Shield", page_icon="🛡️", layout="centered")

# copy hosting secrets into environment variables before the agent is imported
for _k in ("GEMINI_API_KEY", "GEMINI_MODEL"):
    try:
        if _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
    except Exception:
        pass

from agent.core import analyze

try:  # screenshot input is shown only when the backend provides it
    from agent.core import analyze_image
except Exception:
    analyze_image = None

# ------------------------------------------------------------------ styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;600&display=swap');
#MainMenu, footer {visibility: hidden;}
.block-container {max-width: 820px; padding-top: 2.2rem; padding-bottom: 3rem;}
.stApp {
  background:
    radial-gradient(900px 420px at 12% -8%, rgba(124,92,255,.22), transparent 60%),
    radial-gradient(800px 380px at 105% 0%, rgba(34,211,238,.14), transparent 55%),
    #0b1020;
}
.hero {
  text-align: center; padding: 30px 22px 26px; border-radius: 22px;
  background: linear-gradient(135deg, rgba(124,92,255,.22), rgba(34,211,238,.10));
  border: 1px solid rgba(255,255,255,.10); margin-bottom: 22px;
}
.hero .logo {font-size: 3rem; line-height: 1;}
.hero h1 {margin: 8px 0 6px; font-size: 2.5rem; letter-spacing: -.5px; color: #fff; padding: 0;}
.hero p {margin: 0 auto; max-width: 560px; color: #b8c1e0; font-size: 1.05rem;}
.pills {margin-top: 14px;}
.pill {
  display: inline-block; margin: 3px 4px; padding: 4px 12px; border-radius: 999px;
  font-size: .8rem; color: #cfd6f3; background: rgba(255,255,255,.07);
  border: 1px solid rgba(255,255,255,.10);
}
.stTextArea textarea {
  border-radius: 14px !important; background: #10162d !important;
  border: 1px solid rgba(255,255,255,.12) !important; font-size: 1rem !important;
}
.stTextArea textarea:focus {border-color: #7c5cff !important; box-shadow: 0 0 0 2px rgba(124,92,255,.35) !important;}
.stButton > button {
  border-radius: 12px; border: 1px solid rgba(255,255,255,.14);
  background: rgba(255,255,255,.04); color: #dfe5fb; transition: all .15s ease;
}
.stButton > button:hover {border-color: #7c5cff; color: #fff; background: rgba(124,92,255,.14);}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #7c5cff, #22d3ee); color: #fff; border: 0;
  font-weight: 600; padding: .55rem 1.6rem;
}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
  filter: brightness(1.1); box-shadow: 0 6px 22px rgba(124,92,255,.45); color: #fff;
}
.stTabs [data-baseweb="tab"] {font-size: 1rem;}
.card {
  margin-top: 18px; padding: 22px 24px; border-radius: 20px;
  background: #121935; border: 1px solid rgba(255,255,255,.09);
  box-shadow: 0 10px 40px rgba(0,0,0,.35); line-height: 1.75;
}
.badge {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
  gap: 10px; padding: 16px 20px; border-radius: 16px; color: #fff;
}
.badge .verdict {font-size: 1.7rem; font-weight: 700;}
.badge .conf {font-size: 1rem; opacity: .95;}
.bar {height: 8px; border-radius: 999px; background: rgba(255,255,255,.12); margin: 14px 0 4px; overflow: hidden;}
.bar > div {height: 100%; border-radius: 999px;}
.meta {margin: 10px 0 2px;}
.tag {
  display: inline-block; margin: 3px 6px 3px 0; padding: 3px 12px; border-radius: 999px;
  font-size: .82rem; color: #d9defa; background: rgba(124,92,255,.18); border: 1px solid rgba(124,92,255,.35);
}
.card h4 {margin: 20px 0 6px; font-size: 1.05rem; color: #fff; padding: 0;}
.flag {
  display: block; margin: 6px 0; padding: 8px 14px; border-radius: 12px; color: #ffd9d9;
  background: rgba(239,68,68,.12); border: 1px solid rgba(239,68,68,.30);
}
.ok {display: block; margin: 6px 0; padding: 8px 14px; border-radius: 12px; color: #c9f5d8;
  background: rgba(34,197,94,.12); border: 1px solid rgba(34,197,94,.30);}
.step {display: block; margin: 6px 0; padding: 8px 14px; border-radius: 12px; background: rgba(255,255,255,.05);}
.card p {margin: 6px 0; color: #d5dbf5;}
.small {font-size: .82rem; opacity: .7;}
.extracted {
  margin-top: 14px; padding: 10px 14px; border-radius: 12px; font-size: .9rem; color: #b8c1e0;
  background: rgba(255,255,255,.04); border: 1px dashed rgba(255,255,255,.18); white-space: pre-wrap;
}
.rtl {direction: rtl; text-align: right; font-family: 'Noto Naskh Arabic', 'Segoe UI', serif; line-height: 2.1;}
.foot {margin-top: 26px; text-align: center; color: #8f99bf; font-size: .82rem;}
.foot .rtl {text-align: center; margin-top: 4px;}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ text
COLORS = {"Safe": "#16a34a", "Suspicious": "#d97706", "Dangerous": "#dc2626"}
ICONS = {"Safe": "✅", "Suspicious": "⚠️", "Dangerous": "🚨"}

UI = {
    "English": {
        "risk": {"Safe": "Safe", "Suspicious": "Suspicious", "Dangerous": "Dangerous"},
        "confidence": "Confidence", "flags": "Red flags found", "why": "Why",
        "todo": "What to do next", "learn": "Learn more", "none": "No red flags found",
        "type": "Scam type", "tactics": "Tactics used", "tools": "Checks used",
        "extracted": "Text read from your screenshot",
        "disclaimer": "This is an assistant, not a replacement for reporting to the authorities. Always verify through the official channel.",
        "privacy": "Your messages are not stored by this app. They are sent to Google's Gemini API for analysis.",
    },
    "Urdu": {
        "risk": {"Safe": "محفوظ", "Suspicious": "مشکوک", "Dangerous": "خطرناک"},
        "confidence": "اعتماد", "flags": "خطرے کی نشانیاں", "why": "وجہ",
        "todo": "اب کیا کریں", "learn": "مزید جانیں", "none": "کوئی خطرے کی نشانی نہیں ملی",
        "type": "فراڈ کی قسم", "tactics": "استعمال شدہ حربے", "tools": "استعمال شدہ جانچ",
        "extracted": "اسکرین شاٹ سے پڑھا گیا متن",
        "disclaimer": "یہ ایک معاون ٹول ہے، متعلقہ اداروں کو رپورٹ کرنے کا متبادل نہیں۔ ہمیشہ سرکاری ذریعے سے تصدیق کریں۔",
        "privacy": "یہ ایپ آپ کے پیغامات محفوظ نہیں کرتی۔ تجزیے کے لیے وہ گوگل کے Gemini API کو بھیجے جاتے ہیں۔",
    },
}

EXAMPLES = [
    ("🎁 Prize scam", "Congratulations! You have won Rs. 500,000 in the JazzCash Lucky Draw. Claim now: http://jazzcash-prize-claim.xyz/win"),
    ("🔐 Genuine OTP", "Your OTP for the transaction is 482913. Do not share this code with anyone. - Meezan Bank"),
    ("📦 Courier fee", "Your TCS parcel is on hold. Pay Rs. 150 customs fee at bit.ly/3xYzAbc to release it."),
]


def render(res, lang, extracted=None):
    t, e = UI[lang], html.escape
    risk = res["risk"]
    color = COLORS.get(risk, "#6b7280")
    try:
        conf = max(0, min(100, int(res["confidence"])))
    except Exception:
        conf = 0
    cls = "rtl" if lang == "Urdu" else ""

    if res["flags"]:
        flags = "".join(f'<span class="flag">🚩 {e(f)}</span>' for f in res["flags"])
    else:
        flags = f'<span class="ok">✅ {e(t["none"])}</span>'
    advice = "".join(f'<span class="step">✔️ {e(a)}</span>' for a in res["advice"])

    meta = ""
    scam_type = str(res.get("scam_type", "")).strip()
    if scam_type and scam_type.lower() != "none":
        meta += f'<span class="tag">{e(t["type"])}: {e(scam_type)}</span>'
    tactics = [x for x in res.get("tactics", []) if str(x).lower() != "none"]
    if tactics:
        meta += "".join(f'<span class="tag">{e(str(x))}</span>' for x in tactics)
    meta_html = f'<div class="meta">{meta}</div>' if meta else ""

    extracted_html = ""
    if extracted:
        extracted_html = f'<div class="extracted"><b>{e(t["extracted"])}</b><br>{e(extracted)}</div>'

    tools = e(", ".join(res.get("tools_used", [])) or "-")
    return (
        f'<div class="card {cls}">'
        f'<div class="badge" style="background:{color}">'
        f'<span class="verdict">{ICONS.get(risk, "")} {e(t["risk"].get(risk, risk))}</span>'
        f'<span class="conf">{e(t["confidence"])}: {conf}%</span></div>'
        f'<div class="bar"><div style="width:{conf}%;background:{color}"></div></div>'
        f'{meta_html}'
        f'<h4>{e(t["flags"])}</h4>{flags}'
        f'<h4>{e(t["why"])}</h4><p>{e(res["explanation"])}</p>'
        f'<h4>{e(t["todo"])}</h4>{advice}'
        f'<h4>{e(t["learn"])}</h4><p>{e(res["learn_more"])}</p>'
        f'{extracted_html}'
        f'<p class="small">{e(t["tools"])}: {tools}</p>'
        f'<p class="small">{e(t["disclaimer"])}</p>'
        f'</div>'
    )


def run_check(fn, lang):
    st.session_state.pop("result", None)
    st.session_state.pop("error", None)
    try:
        with st.spinner("Checking..."):
            res = fn()
        st.session_state.result = (res, lang)
    except Exception as ex:
        msg = str(ex)
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            st.session_state.error = "The service is busy right now (free usage limit reached). Please try again in a few minutes."
        elif "No readable text" in msg:
            st.session_state.error = "We could not find readable text in that image. Try a clearer screenshot."
        else:
            st.session_state.error = f"Something went wrong. Please try again. ({type(ex).__name__})"


# ------------------------------------------------------------------ page
st.markdown("""
<div class="hero">
  <div class="logo">🛡️</div>
  <h1>Scam Shield</h1>
  <p>Paste a suspicious SMS, WhatsApp message or link. Get a clear verdict and simple advice in Urdu or English.</p>
  <div class="pills">
    <span class="pill">🤖 AI agent</span><span class="pill">🔗 Link checks</span>
    <span class="pill">🗣️ Urdu &amp; English</span><span class="pill">🔒 Nothing stored</span>
  </div>
</div>
""", unsafe_allow_html=True)

lang = st.radio("Language", ["English", "Urdu"], horizontal=True,
                format_func=lambda x: "English" if x == "English" else "اردو")

if "text" not in st.session_state:
    st.session_state.text = ""

if analyze_image is not None:
    tab_text, tab_img = st.tabs(["✍️  Paste text", "📷  Upload screenshot"])
else:
    tab_text, tab_img = st.container(), None

with tab_text:
    st.caption("Try an example")
    cols = st.columns(len(EXAMPLES))
    for i, col in enumerate(cols):
        label, sample = EXAMPLES[i]
        if col.button(label, key=f"ex{i}", use_container_width=True):
            st.session_state.text = sample
    text = st.text_area("Message or link", key="text", height=150,
                        placeholder="Paste the message or link here...")
    if st.button("Check message", type="primary", key="check_text"):
        if not text.strip():
            st.warning("Please paste a message or link.")
        else:
            run_check(lambda: analyze(text, lang), lang)

if tab_img is not None:
    with tab_img:
        up = st.file_uploader("Upload a screenshot of the message", type=["png", "jpg", "jpeg"])
        if up is not None:
            st.image(up, width=300)
        if st.button("Check screenshot", type="primary", key="check_img"):
            if up is None:
                st.warning("Please upload a screenshot first.")
            else:
                run_check(lambda: analyze_image(up.getvalue(), lang, mime_type=up.type), lang)

if st.session_state.get("error"):
    st.error(st.session_state.error)
if st.session_state.get("result"):
    res, rlang = st.session_state.result
    st.markdown(render(res, rlang, res.get("extracted_text")), unsafe_allow_html=True)

with st.expander("How does Scam Shield work?"):
    st.markdown(
        "1. **Link checks:** looks for lookalike domains, shortened links, risky endings and brand-new domains.\n"
        "2. **Pattern checks:** looks for known scam wording such as fake prizes, OTP requests and urgent threats.\n"
        "3. **AI reasoning:** Gemini weighs the message and these findings and explains its verdict.\n\n"
        "It is an assistant, not a guarantee. Always verify through the official channel."
    )

st.markdown(
    f'<div class="foot">{html.escape(UI["English"]["privacy"])}'
    f'<div class="rtl">{html.escape(UI["Urdu"]["privacy"])}</div></div>',
    unsafe_allow_html=True,
)
