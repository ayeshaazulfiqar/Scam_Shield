import html
import os
import gradio as gr
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


def render(res, lang):
    t, e = UI[lang], html.escape
    color = COLORS[res["risk"]]
    flags = "".join(f"<li>{e(f)}</li>" for f in res["flags"]) or f"<li>{e(t['none'])}</li>"
    advice = "".join(f"<li>{e(a)}</li>" for a in res["advice"])
    direction = "rtl" if lang == "Urdu" else "ltr"
    return f"""
<div dir="{direction}" style="line-height:1.7">
  <div style="background:{color};color:white;padding:12px 16px;border-radius:10px;font-size:1.3em">
    <b>{t['risk'][res['risk']]}</b> &nbsp;·&nbsp; {t['confidence']}: {int(res['confidence'])}%
  </div>
  <h4>{t['flags']}</h4><ul>{flags}</ul>
  <h4>{t['why']}</h4><p>{e(res['explanation'])}</p>
  <h4>{t['todo']}</h4><ul>{advice}</ul>
  <h4>{t['learn']}</h4><p>{e(res['learn_more'])}</p>
  <p style="opacity:.7;font-size:.85em">{t['tools']}: {e(', '.join(res.get('tools_used', [])) or '-')}</p>
  <p style="opacity:.7;font-size:.85em">{t['disclaimer']}</p>
</div>"""


def run(text, lang):
    if not text or not text.strip():
        return "<p>Please paste a message or link.</p>"
    try:
        return render(analyze(text, lang), lang)
    except Exception as ex:
        return f"<p>Something went wrong. Please try again. ({html.escape(type(ex).__name__)})</p>"


EXAMPLES = [
    ["Congratulations! You have won Rs. 500,000 in the JazzCash Lucky Draw. Claim now: http://jazzcash-prize-claim.xyz/win"],
    ["Your OTP for the transaction is 482913. Do not share this code with anyone. - Meezan Bank"],
    ["Your TCS parcel is on hold. Pay Rs. 150 customs fee at bit.ly/3xYzAbc to release it."],
]

with gr.Blocks(title="Scam Shield") as demo:
    gr.Markdown("# 🛡️ Scam Shield\nPaste a suspicious SMS, WhatsApp message or link to check if it is a scam.")
    text = gr.Textbox(lines=6, label="Message or link")
    lang = gr.Radio([("English", "English"), ("اردو", "Urdu")], value="English", label="Language")
    btn = gr.Button("Check", variant="primary")
    out = gr.HTML()
    gr.Examples(examples=EXAMPLES, inputs=[text])
    btn.click(run, [text, lang], out)
    gr.Markdown(f"<small>{UI['English']['privacy']}</small><div dir='rtl' style='text-align:right'><small>{UI['Urdu']['privacy']}</small></div>")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
