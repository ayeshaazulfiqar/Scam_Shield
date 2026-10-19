import re, os, ipaddress, difflib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import tldextract
import requests

_ext = tldextract.TLDExtract(suffix_list_urls=())  # bundled suffix list, no network call

URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:/[^\s<>\"']*)?",
    re.I,
)

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rb.gy",
              "shorturl.at", "ow.ly", "bit.do", "tiny.cc", "t.ly",
              "short.gy", "rebrand.ly", "buff.ly", "lnkd.in", "s.id"}
SUSPICIOUS_TLDS = {"xyz", "top", "click", "link", "icu", "buzz", "site", "online", "live",
                   "work", "support", "loan", "tk", "ml", "ga", "cf", "gq", "monster",
                   "cyou", "rest", "vip"}

# brand -> official registered domains (VERIFY these before the demo)
BRANDS = {
    "jazzcash": {"jazzcash.com.pk", "jazzcash.com"},
    "easypaisa": {"easypaisa.com.pk"},
    "sadapay": {"sadapay.pk"},
    "nayapay": {"nayapay.com"},
    "meezan": {"meezanbank.com"},
    "alfalah": {"bankalfalah.com"},
    "hbl": {"hbl.com", "hbl.com.pk"},
    "ubl": {"ubl.com.pk"},
    "mcb": {"mcb.com.pk"},
    "nadra": {"nadra.gov.pk"},
    "ehsaas": {"ehsaas.gov.pk"},
    "bisp": {"bisp.gov.pk"},
    "fbr": {"fbr.gov.pk"},
    "daraz": {"daraz.pk"},
    "tcs": {"tcsexpress.com"},
    "leopards": {"leopardscourier.com"},
    "pakpost": {"pakpost.gov.pk"},
}
LEET = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "$": "s"})


def _host(url):
    u = re.sub(r"^[a-z]+://", "", url, flags=re.I)
    u = u.split("/")[0].split("?")[0].split("#")[0]
    u = u.split("@")[-1]
    return u.split(":")[0].lower()


def _is_ip(host):
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def extract_urls(text):
    urls = []
    for m in URL_RE.findall(text or ""):
        u = m.rstrip(".,;:!?)]}'\"")
        host = _host(u)
        ext = _ext(host)
        if _is_ip(host) or (ext.suffix and ext.domain):
            if u not in urls:
                urls.append(u)
    return urls


def domain_age_days(domain, timeout=6):
    def _q():
        import whois
        d = whois.whois(domain).creation_date
        return d[0] if isinstance(d, list) else d
    ex = ThreadPoolExecutor(max_workers=1)
    try:
        d = ex.submit(_q).result(timeout=timeout)
        if d is None:
            return None
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - d).days
    except Exception:
        return None
    finally:
        ex.shutdown(wait=False)


def urlhaus_listed(url):
    """Optional blocklist. Needs a free abuse.ch key in env URLHAUS_KEY (check their docs)."""
    key = os.environ.get("URLHAUS_KEY")
    if not key:
        return None
    try:
        r = requests.post("https://urlhaus-api.abuse.ch/v1/url/",
                          data={"url": url}, headers={"Auth-Key": key}, timeout=5)
        return r.json().get("query_status") == "ok"
    except Exception:
        return None


def _brand_flags(host, ext, registered):
    out = []
    norm = host.translate(LEET)
    squashed = norm.replace("-", "").replace(".", "")
    tokens = [t for t in re.split(r"[.\-]", norm) if t]
    dom = ext.domain.translate(LEET)
    for brand, official in BRANDS.items():
        if registered in official:
            continue
        if len(brand) <= 4:
            hit = brand in tokens
        else:
            hit = brand in squashed or (
                len(brand) >= 6 and 0.8 <= difflib.SequenceMatcher(None, dom, brand).ratio() < 1.0)
        if hit:
            out.append((f"looks like '{brand}' but the domain is {registered}, not an official {brand} domain", 4))
    return out


def analyze_url(url):
    host = _host(url)
    authority = re.sub(r"^[a-z]+://", "", url, flags=re.I).split("/")[0]
    ext = _ext(host)
    ip = _is_ip(host)
    registered = host if ip else ".".join(p for p in [ext.domain, ext.suffix] if p)
    f = []

    if ip:
        f.append(("link uses a raw IP address instead of a domain name", 3))
    if registered in SHORTENERS:
        f.append(("URL shortener hides the real destination", 2))
    if url.lower().startswith("http://"):
        f.append(("link does not use HTTPS", 1))
    if "@" in authority:
        f.append(("link contains '@', which can hide the real destination", 3))
    if "xn--" in host:
        f.append(("domain uses punycode, which can imitate other letters", 3))
    if ext.suffix.split(".")[-1] in SUSPICIOUS_TLDS:
        f.append((f"domain ends in .{ext.suffix.split('.')[-1]}, often used in scams", 2))
    if len([s for s in ext.subdomain.split(".") if s]) >= 3:
        f.append(("too many subdomains", 2))
    if ext.domain.count("-") >= 2:
        f.append(("domain name has many hyphens", 1))
    if len(url) > 75:
        f.append(("unusually long link", 1))
    if not ip:
        f += _brand_flags(host, ext, registered)

    age = None
    if not ip and registered not in SHORTENERS:
        age = domain_age_days(registered)
        if age is not None and age < 30:
            f.append((f"domain was registered only {age} days ago", 3))
        elif age is not None and age < 90:
            f.append((f"domain is fairly new ({age} days old)", 2))

    listed = urlhaus_listed(url)
    if listed:
        f.append(("listed in the URLhaus malware/phishing blocklist", 5))

    return {
        "url": url,
        "registered_domain": registered,
        "domain_age_days": age,
        "blocklisted": listed,
        "red_flags": [m for m, _ in f],
        "heuristic_points": sum(p for _, p in f),
    }
