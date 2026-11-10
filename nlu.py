"""Turns a sentence (Hindi, Bengali or Hinglish) into {intent, name, amount}."""
import difflib, re

DIGITS = str.maketrans("०१२३४५६७८९০১২৩৪৫৬৭৮৯", "0123456789" * 2)
# Words that sit right after the person's name.
MARKERS = {"को", "ko", "ने", "ne", "का", "ka", "की", "ki", "से", "se", "के", "ke",
           "কে", "থেকে", "এর", "er"}
PAID_MARKERS = {"ने", "ne", "से", "se", "থেকে"}  # "Sunita ne ..." = she paid us
SUFFIXES = ("কে", "ের")  # Bengali glues these to the name: রমেশকে, রমেশের
SKIP = {"आज", "aaj", "कल", "kal", "फिर", "phir", "अभी", "abhi", "एक", "ek",
        "আজ", "কাল", "আবার", "এখন", "কাছ", "আজকের",
        # "me / us / you" are never the customer's name
        "मुझे", "मुझको", "मुझसे", "मैंने", "मैं", "मेरे", "मेरा", "हमें", "हमने", "हम", "आपको", "तुम्हें", "आमा",
        "আমাকে", "আমায়", "আমি", "আমার", "আমাদের", "আমরা", "তোমাকে", "আপনাকে",
        "mujhe", "mujhko", "maine", "main", "mai", "hamein", "amake", "amak", "amaka", "amay", "amra"}
PAY = ("वापस", "wapas", "wapis", "जमा", "jama", "चुका", "chuka", "लौटा", "paid",
       "ফেরত", "জমা", "দিয়েছে", "শোধ", "ferot", "ferat", "diyeche")
CREDIT = ("उधार", "udhaar", "udhar", "credit", "ধার", "বাকি", "dhar", "dhaar",
          "देगी", "देगा", "देंगे", "देवे", "দেবে", "দেবেন", "debe", "dibe", "dega", "degi")  # "will give" = owes us
QUERY = ("हिसाब", "hisab", "hisaab", "बकाया", "बाकी", "baaki", "kitna", "कितना", "total",
         "बताओ", "batao", "बताइए", "হিসাব", "কত", "মোট", "বলো", "বলুন", "koto", "baki")

UNDO = ("undo", "cancel", "रद्द", "हटा", "गलत", "বাতিল", "মুছে", "ভুল", "batil")
REMIND = ("रिमाइंड", "रिमाइन्ड", "याद दिला", "reminder", "remind", "রিমাইন্ড", "রিমাইণ্ড", "মনে করিয়ে", "মনে করাও", "তাগাদা",
          # "send her a WhatsApp message" counts too
          "message", "whatsapp", "মেসেজ", "ম্যাসেজ", "হোয়াটস", "পাঠাও", "পাঠান",
          "मैसेज", "मेसेज", "संदेश", "व्हाट्स", "वॉट्स", "भेजो", "भेज दो", "भेजिए")

NUM = re.compile(r"\d+(?:\.\d+)?")

def _clean(text):
    t = text.translate(DIGITS).replace("₹", " ")
    return re.sub(r"(?<=\d),(?=\d)", "", t)

def match_name(name, known):
    low = {k.casefold(): k for k in known}
    if name.casefold() in low:
        return low[name.casefold()]
    close = difflib.get_close_matches(name.casefold(), list(low), n=1, cutoff=0.78)
    return low[close[0]] if close else name

def _mixed_script(w):
    """True for garbled words that mix Bengali and Devanagari letters: not a real name."""
    return bool(re.search("[\u0980-\u09FF]", w) and re.search("[\u0900-\u097F]", w))

def _names_before(tokens):
    return [x for x in tokens if x and x.lower() not in SKIP and not NUM.fullmatch(x) and not _mixed_script(x)]

def find_name(toks):
    for i, w in enumerate(toks):
        if w.lower() in MARKERS:
            before = _names_before(toks[:i])
            if before:
                return " ".join(before[-1:]), w.lower()
        for suf in SUFFIXES:
            if w.endswith(suf) and len(w) > len(suf) + 1 and w not in SKIP:
                before = _names_before(toks[:i] + [w[:-len(suf)]])
                return " ".join(before[-1:]), suf
    for i, w in enumerate(toks):  # no marker: the name is whatever comes before the amount
        if NUM.fullmatch(w):
            before = _names_before(toks[:i])
            if before:
                return before[0], None  # no marker: the name comes first ("Meera ... 70 ...")
    return None, None

def parse(text, known=()):
    t = _clean(text)
    low = t.lower()
    m = NUM.search(t)
    amount = float(m.group()) if m else None
    toks = [w.strip(".,?!।") for w in t.split()]

    name, marker = find_name(toks)
    if name:
        name = match_name(name, known)

    has = lambda words: any(w in low for w in words)
    if not amount and has(UNDO):
        intent = "undo"
    elif name and not amount and has(REMIND):
        intent = "remind"
    elif amount and name:
        if has(PAY) or (not has(CREDIT) and marker in PAID_MARKERS):
            intent = "payment"
        else:
            intent = "credit"
    elif has(QUERY):
        intent = "query"
    else:
        intent = "unknown"
    return {"intent": intent, "name": name, "amount": amount}
