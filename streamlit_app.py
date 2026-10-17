import os
import html
import streamlit as st

st.set_page_config(page_title="Scam Shield", page_icon="🛡️")

# copy hosting secrets into environment variables before the agent is imported
for _k in ("GEMINI_API_KEY", "GEMINI_MODEL"):
    try:
        if _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
    except Exception:
        pass

from agent.core import analyze

COLORS = {"Safe": "#1b8a3b", "Suspicious": "#d98a00", "Dangerous": "#c62828"}

UI = {
    "English": {
        "risk": {"Safe": "Safe", "Suspicious": "Suspicious", "Dangerous": "Dangerous"},
        "confidence": "Confidence", "flags": "Red flags found", "why": "Why",
        "todo": "What to do next", "learn": "Learn more", "none": "None found",
        "tools": "Checks used",
        "disclaimer": "This is an assistant, not a replacement for reporting to the authorities. Always verify through the official channel.",
        "privacy": "Your messages are not stored by this app. They are sent to Google's Gemini API for analysis.",
    },
    "Urdu": {
        "risk": {"Safe": "محفوظ", "Suspicious": "مشکوک", "Dangerous": "خطرناک"},
        "confidence": "اعتماد", "flags": "خطرے کی نشانیاں", "why": "وجہ",
        "todo": "اب کیا کریں", "learn": "مزید جانیں", "none": "کوئی نہیں ملی",
        "tools": "استعمال شدہ جانچ",
        "disclaimer": "یہ ایک معاون ٹول ہے، متعلقہ اداروں کو رپورٹ کرنے کا متبادل نہیں۔ ہمیشہ سرکاری ذریعے سے تصدیق کریں۔",
        "privacy": "یہ ایپ آپ کے پیغامات محفوظ نہیں کرتی۔ تجزیے کے لیے وہ گوگل کے Gemini API کو بھیجے جاتے ہیں۔",
    },
}

EXAMPLES = [
    "Congratulations! You have won Rs. 500,000 in the JazzCash Lucky Draw. Claim now: http://jazzcash-prize-claim.xyz/win",
    "Your OTP for the transaction is 482913. Do not share this code with anyone. - Meezan Bank",
    "Your TCS parcel is on hold. Pay Rs. 150 customs fee at bit.ly/3xYzAbc to release it.",
]


def render(res, lang):
    t, e = UI[lang], html.escape
    color = COLORS[res["risk"]]
    flags = "".join(f"<li>{e(f)}</li>" for f in res["flags"]) or f"<li>{e(t['none'])}</li>"
    advice = "".join(f"<li>{e(a)}</li>" for a in res["advice"])
    direction = "rtl" if lang == "Urdu" else "ltr"
    return (
        f'<div dir="{direction}" style="line-height:1.7">'
        f'<div style="background:{color};color:white;padding:12px 16px;border-radius:10px;font-size:1.3em">'
        f"<b>{t['risk'][res['risk']]}</b> &nbsp;·&nbsp; {t['confidence']}: {int(res['confidence'])}%</div>"
        f"<h4>{t['flags']}</h4><ul>{flags}</ul>"
        f"<h4>{t['why']}</h4><p>{e(res['explanation'])}</p>"
        f"<h4>{t['todo']}</h4><ul>{advice}</ul>"
        f"<h4>{t['learn']}</h4><p>{e(res['learn_more'])}</p>"
        f"<p style='opacity:.7;font-size:.85em'>{t['tools']}: {e(', '.join(res.get('tools_used', [])) or '-')}</p>"
        f"<p style='opacity:.7;font-size:.85em'>{t['disclaimer']}</p>"
        f"</div>"
    )


st.title("🛡️ Scam Shield")
st.write("Paste a suspicious SMS, WhatsApp message or link to check if it is a scam.")

if "text" not in st.session_state:
    st.session_state.text = ""

st.caption("Try an example:")
cols = st.columns(len(EXAMPLES))
for i, col in enumerate(cols):
    if col.button(f"Example {i + 1}", key=f"ex{i}"):
        st.session_state.text = EXAMPLES[i]

text = st.text_area("Message or link", key="text", height=160)
lang = st.radio("Language", ["English", "Urdu"], horizontal=True,
                format_func=lambda x: "English" if x == "English" else "اردو")

if st.button("Check", type="primary"):
    if not text.strip():
        st.warning("Please paste a message or link.")
    else:
        try:
            with st.spinner("Checking..."):
                res = analyze(text, lang)
            st.markdown(render(res, lang), unsafe_allow_html=True)
        except Exception as ex:
            msg = str(ex)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                st.error("The service is busy right now (free usage limit reached). Please try again in a few minutes.")
            else:
                st.error(f"Something went wrong. Please try again. ({type(ex).__name__})")

st.markdown(f"<small>{UI['English']['privacy']}<br>{UI['Urdu']['privacy']}</small>", unsafe_allow_html=True)
