from .url_tools import extract_urls, analyze_url
from .patterns import scan
from .llm import judge


def analyze(text, language="English", use_tools=True):
    text = (text or "").strip()
    evidence, tools_used = {}, []

    if use_tools:
        urls = extract_urls(text)
        if urls:                                   # no link means no URL check
            evidence["links"] = [analyze_url(u) for u in urls[:3]]
            tools_used.append("url_analyzer")
        evidence["patterns"] = scan(text)
        tools_used.append("pattern_matcher")

    verdict = judge(text, evidence, language)
    out = verdict.model_dump()
    out["confidence"] = min(int(out["confidence"]), 99)  # never claim certainty
    out["tools_used"] = tools_used
    out["evidence"] = evidence
    return out


def analyze_image(image, language="English", use_tools=True, mime_type=None):
    """image: raw bytes, or a file path. Returns the same dict as analyze() plus 'extracted_text'."""
    import mimetypes
    from .llm import extract_text
    if isinstance(image, str):
        mime_type = mime_type or mimetypes.guess_type(image)[0] or "image/png"
        with open(image, "rb") as f:
            image = f.read()
    mime_type = mime_type or "image/png"
    text = extract_text(image, mime_type)
    if not text or text.strip().upper() == "NO_TEXT":
        raise ValueError("No readable text found in the image")
    out = analyze(text, language, use_tools=use_tools)
    out["extracted_text"] = text
    return out
