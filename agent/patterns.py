import re

RULES = {
    "prize_lottery": [
        r"\bcongratulations?\b", r"\byou (have )?(won|been selected)\b",
        r"\blucky (draw|winner)\b", r"\b(prize|jackpot|lottery)\b",
        r"\b(inaam|inam|mubarak ho|jeet)\b", r"(مبارک|انعام|لکی ڈرا)",
    ],
    "wallet_bank_impersonation": [
        r"\b(jazz ?cash|easy ?paisa|sadapay|nayapay|hbl|ubl|meezan|mcb|alfalah|askari|faysal)\b.{0,80}\b(verify|update|suspend|blocked|kyc|locked|limit)\b",
        r"\b(kyc|biometric)\b.{0,40}\b(expire|pending|update|verify|verification)\b",
    ],
    "account_threat": [
        r"\b(account|sim|card|wallet|cnic)\b.{0,50}\b(block(ed)?|suspend(ed)?|clos(e|ed)|deactivat\w*|expire[sd]?)\b",
        r"\bband ho\b", r"(اکاؤنٹ|سم).{0,30}(بند|بلاک)",
    ],
    "urgency": [
        r"\b(urgent|immediately|last chance|act now|final (warning|notice))\b",
        r"\bwithin \d+ ?(hours?|hrs?|minutes?|mins?)\b", r"\bexpires? (today|soon|in)\b",
        r"\b(foran|abhi|24 ghant)\w*", r"(فوری|فوراً)",
    ],
    "otp_request": [
        r"(?<!not )(?<!n't )(?<!never )\b(send|share|give|forward|provide)\b.{0,30}\b(code|otp|pin|cvv|password)\b",
        r"\b(otp|pin|cnic)\b.{0,20}\b(bhej|batao|share kar|dein)\w*",
    ],
    "government_scheme": [
        r"\b(bisp|ehsaas|benazir|nadra|fbr|income support|kafalat|8171)\b", r"\btax refund\b",
    ],
    "courier_fee": [
        r"\b(parcel|package|courier|delivery|shipment)\b.{0,60}\b(fee|charges?|pay|customs|held|on hold|address)\b",
    ],
    "job_scam": [
        r"\b(job offer|hiring|work from home|part[- ]time|no experience)\b",
        r"\bearn\b.{0,20}\d+", r"\b(registration|processing|security) (fee|deposit)\b",
    ],
}

LEGIT_SIGNALS = [
    r"do not share (this|the|your)? ?(code|otp|pin)",
    r"\bnever share\b", r"\bdon'?t share\b",
    r"if (you|this) (did not|didn'?t|wasn'?t) (request|make|initiate|you)",
    r"kisi se share na",
]


def scan(text):
    found = {}
    for scam_type, pats in RULES.items():
        hits = []
        for p in pats:
            for m in re.finditer(p, text, flags=re.I | re.DOTALL):
                hits.append(m.group(0)[:60])
        if hits:
            found[scam_type] = hits[:5]
    legit = []
    for p in LEGIT_SIGNALS:
        for m in re.finditer(p, text, flags=re.I):
            legit.append(m.group(0)[:60])
    return {
        "scam_pattern_matches": found,
        "legit_signals": legit[:3],
        "pattern_types_matched": len(found),
    }
