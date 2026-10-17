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
    out["tools_used"] = tools_used
    out["evidence"] = evidence
    return out
