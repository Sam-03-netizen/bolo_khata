"""Products, stock, bills, purchases, sales reports and a demand forecast. Same khata.db as the ledger."""
import math, os, random, re, sqlite3
from datetime import datetime, timedelta
import ledger, nlu

LEAD = int(os.getenv("LEAD_DAYS", 3))  # days a supplier needs to deliver
UNITS = {"kg": ("কেজি", "किलो"), "litre": ("লিটার", "लीटर"), "packet": ("প্যাকেট", "पैकेट"), "piece": ("পিস", "पीस")}
UNIT_WORDS = {"kg", "kilo", "কেজি", "কিলো", "किलो", "केजी", "litre", "liter", "লিটার", "लीटर", "packet", "প্যাকেট", "पैकेट",
              "piece", "pcs", "পিস", "पीस", "gram", "gm", "গ্রাম", "ग्राम", "dozen"}
GRAM = {"gram", "gm", "গ্রাম", "ग्राम"}
QTY_WORDS = {"আধা": .5, "আধ": .5, "आधा": .5, "half": .5, "দেড়": 1.5, "डेढ़": 1.5, "डेढ": 1.5}
DIG = str.maketrans("०१२३४५६७८९০১২৩৪৫৬৭৮৯", "0123456789" * 2)
SUF = ("", "র", "এর", "ের", "য়ের", "কে", "ক", "ও", "তে", "का", "के", "की", "को", "s", "es")
SUF_SHORT = ("", "য়ের", "য়", "কে")  # short names like চা must not match চার / চাও
BILL = ("বিল", "bill", "बिल")
STOCK = ("স্টক", "stock", "स्टॉक", "स्टोक")
ADD = ("এসেছে", "এলো", "আনলাম", "add", "restock", "आया", "आए", "आई", "मंगाया", "मँगाया", "নতুন")
CREDIT = ("ধার", "উধার", "उधार", "udhaar", "udhar", "dhar")
HOW_MUCH = ("কত আছে", "কতটা", "कितना", "कितने", "how much", "koto")
SALES = ("বিক্রি", "বিক্রয়", "sales", "sale", "बिक्री", "बेचा", "बिका")
WEEK = ("সপ্তাহ", "week", "हफ्त", "हफ़्त", "सप्ताह")
MONTH = ("মাস", "month", "महीन")
CUR = ("টাকা", "taka", "tk", "rs", "rupee", "rupaye", "रुपये", "रुपए", "रुपया", "रू")
PAID_W = {"দিয়েছে", "দিয়েছেন", "দিল", "দিলেন", "জমা", "নগদ", "পেমেন্ট", "दिए", "दिये", "जमा", "नकद", "भुगतान", "पेमेंट",
          "paid", "cash", "payment", "jama", "diyeche"}

SEED = [  # name_bn, name_hi, aliases, unit, price, stock, low-stock level, category
    ("চাল", "चावल", "চাল|चावल|chal|chawal|rice", "kg", 50, 100, 20, "staples"),
    ("আটা", "आटा", "আটা|आटा|ata|atta", "kg", 40, 60, 15, "staples"),
    ("ডাল", "दाल", "ডাল|दाल|dal", "kg", 120, 40, 10, "staples"),
    ("চিনি", "चीनी", "চিনি|चीनी|chini|sugar", "kg", 45, 50, 10, "staples"),
    ("তেল", "तेल", "তেল|तेल|tel|oil", "litre", 150, 30, 8, "staples"),
    ("নুন", "नमक", "নুন|লবণ|नमक|nun|namak|salt", "kg", 20, 40, 10, "staples"),
    ("দুধ", "दूध", "দুধ|दूध|dudh|doodh|milk", "litre", 60, 30, 10, "dairy"),
    ("ডিম", "अंडा", "ডিম|अंडा|अंडे|dim|anda|egg", "piece", 7, 120, 30, "dairy"),
    ("চা", "चाय", "চা|चाय|chai|tea", "packet", 80, 25, 8, "snacks"),
    ("বিস্কুট", "बिस्कुट", "বিস্কুট|बिस्कुट|biscuit", "packet", 10, 80, 20, "snacks"),
    ("সাবান", "साबुन", "সাবান|साबुन|saban|sabun|soap", "piece", 35, 40, 10, "care"),
]

def init():
    with ledger._c() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name_bn TEXT, name_hi TEXT, aliases TEXT,
            unit TEXT, price REAL, stock REAL, low REAL, cat TEXT);
        CREATE TABLE IF NOT EXISTS bills(id INTEGER PRIMARY KEY, ts TEXT DEFAULT (datetime('now','localtime')),
            customer TEXT, total REAL, paid REAL, demo INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS bill_items(bill_id INTEGER, product_id INTEGER, qty REAL, price REAL);
        CREATE TABLE IF NOT EXISTS purchases(id INTEGER PRIMARY KEY, ts TEXT DEFAULT (datetime('now','localtime')),
            product_id INTEGER, qty REAL, cost REAL);
        CREATE TABLE IF NOT EXISTS stock_log(id INTEGER PRIMARY KEY, ts TEXT DEFAULT (datetime('now','localtime')),
            product_id INTEGER, delta REAL, reason TEXT);""")
        try:  # databases made before partial payments existed
            c.execute("ALTER TABLE bills ADD COLUMN paid REAL")
        except sqlite3.OperationalError:
            pass
        if not c.execute("SELECT 1 FROM products").fetchone():
            c.executemany("INSERT INTO products(name_bn,name_hi,aliases,unit,price,stock,low,cat) VALUES (?,?,?,?,?,?,?,?)", SEED)

def products():
    with ledger._c() as c:
        rows = c.execute("SELECT id,name_bn,name_hi,aliases,unit,price,stock,low,cat FROM products ORDER BY cat, id").fetchall()
    return [dict(id=r[0], name_bn=r[1], name_hi=r[2], aliases=[a.lower() for a in r[3].split("|") if a],
                 unit=r[4], price=r[5], stock=r[6], low=r[7], cat=r[8]) for r in rows]

def pname(p, lang):
    return p["name_bn"] if lang == "bn" else p["name_hi"]

def unit(p, lang):
    return UNITS[p["unit"]][0 if lang == "bn" else 1]

def product_names(lang):
    return [pname(p, lang) for p in products()]

def add_product(name, unit_, price, stock, low):
    if not name or unit_ not in UNITS or price < 0 or stock < 0 or low < 0:
        raise ValueError
    with ledger._c() as c:
        c.execute("INSERT INTO products(name_bn,name_hi,aliases,unit,price,stock,low,cat) VALUES (?,?,?,?,?,?,?,?)",
                  (name, name, name.lower(), unit_, price, stock, low, "staples"))

def set_price(pid, price):
    with ledger._c() as c:
        c.execute("UPDATE products SET price=? WHERE id=?", (price, pid))

def purchase(pid, qty, cost=None):
    """Stock comes in: update stock and keep a purchase record (cost is the total paid, optional)."""
    with ledger._c() as c:
        c.execute("UPDATE products SET stock=stock+? WHERE id=?", (qty, pid))
        c.execute("INSERT INTO purchases(product_id,qty,cost) VALUES (?,?,?)", (pid, qty, cost))
        c.execute("INSERT INTO stock_log(product_id,delta,reason) VALUES (?,?,?)", (pid, qty, "purchase"))

def adjust_stock(pid, delta, reason):
    with ledger._c() as c:
        c.execute("UPDATE products SET stock=MAX(stock+?,0) WHERE id=?", (delta, pid))
        c.execute("INSERT INTO stock_log(product_id,delta,reason) VALUES (?,?,?)", (pid, delta, reason))

# ---------- understanding a spoken or typed shop sentence ----------
def _num(t):
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(?:টা|টি|ta|ti|pcs|pc)?", t)
    return float(m.group(1)) if m else None

def _is_money(toks, j):
    return j + 1 < len(toks) and any(toks[j + 1].lower().startswith(c) for c in CUR)

def match(text, prods):
    toks = [w.strip(".,?!।:;()") for w in text.translate(DIG).replace("₹", " ").split()]
    hits = []
    for i, t in enumerate(toks):
        tl, best = t.lower(), None
        for p in prods:
            for a in p["aliases"]:
                if tl.startswith(a) and tl[len(a):] in (SUF_SHORT if len(a) <= 2 else SUF) and (not best or len(a) > best[0]):
                    best = (len(a), p)
        if best:
            hits.append((i, best[1]))
    return toks, hits

def quantities(toks, hits):
    """'2 kg rice' or 'rice 2 kg': the number next to each product. Returns (items, used number positions)."""
    claimed, found = set(), {}
    for i, p in hits:
        q = None
        for rng in (range(i - 1, max(i - 4, -1), -1), range(i + 1, min(i + 4, len(toks)))):
            u = None
            for j in rng:
                tl = toks[j].lower()
                if tl in UNIT_WORDS:
                    u = tl
                    continue
                n = QTY_WORDS.get(tl, _num(tl))
                if n is not None and j not in claimed and not _is_money(toks, j):  # "500 টাকা" is money, not a quantity
                    claimed.add(j)
                    q = n / 1000 if u in GRAM else n
                break
            if q is not None:
                break
        slot = found.setdefault(p["id"], [p, 0])
        slot[1] += q if q is not None else 1
    return [tuple(v) for v in found.values()], claimed

def customer(toks, hits):
    skip = {i for i, _ in hits}
    keep = [t for i, t in enumerate(toks) if i not in skip and t.lower() not in UNIT_WORDS and _num(t) is None
            and t.lower() not in PAID_W and not any(t.lower().startswith(b) for b in BILL + CUR)]
    return nlu.find_name(keep)[0]

def detect(text):
    """Returns a shop command or None (then the khata parser takes over)."""
    toks, hits = match(text, products())
    low = text.lower()
    has = lambda ws: any(w in low for w in ws)
    period = "month" if has(MONTH) else "week" if has(WEEK) else "day"
    if not hits:
        if has(SALES):
            return {"intent": "report", "period": period, "items": []}
        return {"intent": "stock_low"} if has(STOCK) else None
    items, claimed = quantities(toks, hits)
    credit = has(CREDIT)
    nums = [(i, _num(t)) for i, t in enumerate(toks) if i not in claimed and _num(t) is not None]
    if has(BILL):
        paid_w = PAID_W | ({"दिया", "दी"} if not credit else set())
        paid_pos = [i for i, t in enumerate(toks) if t.lower() in paid_w]
        total = paid = None
        if nums and paid_pos:  # the number closest to a "paid" word is the payment
            near = min(nums, key=lambda n: min(abs(n[0] - p) for p in paid_pos))
            if min(abs(near[0] - p) for p in paid_pos) <= 3:
                paid, nums = near[1], [n for n in nums if n is not near]
        if nums:
            total = nums[0][1]  # a spoken bill total overrides the catalogue prices
        if credit and paid is None:
            paid = 0
        return {"intent": "bill", "items": items, "customer": customer(toks, hits), "total": total, "paid": paid}
    if has(ADD):
        return {"intent": "restock", "items": items, "cost": nums[0][1] if len(items) == 1 and nums else None}
    if has(SALES):
        return {"intent": "report", "period": period, "items": [p for p, _ in items]}
    if has(STOCK) or has(HOW_MUCH):
        return {"intent": "stock", "items": [p for p, _ in items]}
    return None

# ---------- bills and stock ----------
def make_bill(items, cust=None, total=None, paid=None):
    calc = sum(p["price"] * q for p, q in items)
    total = calc if total is None else float(total)
    paid = total if paid is None else min(max(float(paid), 0.0), total)
    with ledger._c() as c:
        bid = c.execute("INSERT INTO bills(customer,total,paid) VALUES (?,?,?)", (cust, total, paid)).lastrowid
        for p, q in items:
            c.execute("INSERT INTO bill_items VALUES (?,?,?,?)", (bid, p["id"], q, p["price"]))
            c.execute("UPDATE products SET stock=MAX(stock-?,0) WHERE id=?", (q, p["id"]))
            c.execute("INSERT INTO stock_log(product_id,delta,reason) VALUES (?,?,?)", (p["id"], -q, f"bill {bid}"))
    return {"id": bid, "customer": cust, "total": total, "paid": paid, "balance": total - paid, "sum": calc, "items": items}

def restock(items, cost=None):
    for p, q in items:
        purchase(p["id"], q, cost if len(items) == 1 else None)
    fr = {p["id"]: p for p in products()}
    return [(fr[p["id"]], q) for p, q in items]

def fresh(prods):
    pm = {p["id"]: p for p in products()}
    return [pm[p["id"]] for p in prods if p["id"] in pm]

def low_stock():
    return [p for p in products() if p["stock"] <= p["low"]]

def low_among(prods):
    return [p for p in fresh(prods) if p["stock"] <= p["low"]]

def fmt(x):
    return ("%.2f" % x).rstrip("0").rstrip(".")

def bill_text(b, lang):
    bn = lang == "bn"
    shop = os.getenv("SHOP_NAME", "আমার দোকান" if bn else "मेरी दुकान")
    lines = [f"• {pname(p, lang)} {fmt(q)} {unit(p, lang)} × ₹{fmt(p['price'])} = ₹{fmt(p['price'] * q)}" for p, q in b["items"]]
    if abs(b["total"] - b.get("sum", b["total"])) > 0.01:
        lines.append(f"• {'সমন্বয়' if bn else 'एडजस्टमेंट'}: ₹{fmt(b['total'] - b['sum'])}")
    out = [f"*{shop}* — {'বিল' if bn else 'बिल'} #{b['id']}", *lines, f"{'মোট' if bn else 'कुल'}: *₹{fmt(b['total'])}*"]
    if b.get("balance", 0) > 0:
        out += [f"{'দিয়েছেন' if bn else 'दिए'}: ₹{fmt(b['paid'])}", f"{'বাকি' if bn else 'बाकी'}: *₹{fmt(b['balance'])}*"]
        if (b.get("overall") or 0) > b["balance"] + 0.01:
            out.append(f"{'মোট বাকি (আগেরটা সহ)' if bn else 'कुल बाकी (पुराना मिलाकर)'}: ₹{fmt(b['overall'])}")
    else:
        out.append("✓ " + ("পরিশোধিত" if bn else "भुगतान पूरा"))
    out.append("ধন্যবাদ!" if bn else "धन्यवाद!")
    return "\n".join(out)

def get_bill(bid):
    with ledger._c() as c:
        b = c.execute("SELECT id, customer, total, COALESCE(paid,total) FROM bills WHERE id=?", (bid,)).fetchone()
        rows = c.execute("SELECT product_id, qty, price FROM bill_items WHERE bill_id=?", (bid,)).fetchall() if b else []
    if not b:
        return None
    pm = {p["id"]: p for p in products()}
    items = [(dict(pm[i], price=pr), q) for i, q, pr in rows if i in pm]
    return {"id": b[0], "customer": b[1], "total": b[2], "paid": b[3], "balance": b[2] - b[3], "items": items,
            "sum": sum(p["price"] * q for p, q in items), "overall": ledger.balance(b[1]) if b[1] else None}

def recent_bills(n=6):
    with ledger._c() as c:
        rows = c.execute("SELECT id, ts, customer, total, COALESCE(paid,total) FROM bills WHERE demo=0 ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    return [{"id": r[0], "ts": r[1], "customer": r[2], "total": r[3], "paid": r[4]} for r in rows]

def recent_purchases(n=8):
    with ledger._c() as c:
        rows = c.execute("SELECT ts, product_id, qty, cost FROM purchases ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    return [{"ts": r[0], "product_id": r[1], "qty": r[2], "cost": r[3]} for r in rows]

# ---------- sales reports ----------
def report(period, today=None):
    today = today or datetime.now().date()
    start = (today - timedelta(days={"day": 0, "week": 6, "month": 29}[period])).isoformat()
    with ledger._c() as c:
        n, rev, cash = c.execute("SELECT COUNT(*), COALESCE(SUM(total),0), COALESCE(SUM(COALESCE(paid,total)),0) FROM bills WHERE date(ts)>=?", (start,)).fetchone()
        rows = c.execute("""SELECT bi.product_id, SUM(bi.qty), SUM(bi.qty*bi.price) FROM bill_items bi JOIN bills b ON b.id=bi.bill_id
                            WHERE date(b.ts)>=? GROUP BY 1 ORDER BY 3 DESC""", (start,)).fetchall()
    top = [{"id": i, "qty": q, "revenue": r} for i, q, r in rows]
    return {"bills": n, "revenue": rev, "cash": cash, "credit": rev - cash, "top": top[:3], "all": {x["id"]: x for x in top}}

def daily(n=14):
    start = datetime.now().date() - timedelta(days=n - 1)
    with ledger._c() as c:
        got = dict(c.execute("SELECT date(ts), SUM(total) FROM bills WHERE date(ts)>=? GROUP BY 1", (start.isoformat(),)).fetchall())
    days = [(start + timedelta(days=i)).isoformat() for i in range(n)]
    return [{"date": d, "revenue": got.get(d, 0)} for d in days]

# ---------- demand forecast ----------
def forecast():
    """Next 7 days per product: recent-days-weighted average x weekday pattern over the last 30 days.
    A statistical estimate, not a guarantee."""
    today = datetime.now().date()
    days = [today - timedelta(days=29 - i) for i in range(30)]
    with ledger._c() as c:
        rows = c.execute("""SELECT bi.product_id, date(b.ts), SUM(bi.qty) FROM bill_items bi JOIN bills b ON b.id=bi.bill_id
                            WHERE date(b.ts)>=? GROUP BY 1,2""", (days[0].isoformat(),)).fetchall()
    sales = {}
    for pid, d, q in rows:
        sales.setdefault(pid, {})[d] = q
    out, cats = [], {}
    for p in products():
        s = [sales.get(p["id"], {}).get(d.isoformat(), 0) for d in days]
        if not sum(s):
            out.append({"id": p["id"], "week": 0, "trend": "flat", "days_left": None, "order_in": None, "sold30": 0,
                        "reorder": p["stock"] <= p["low"], "suggest": 0})
            continue
        rate = s[0]
        for x in s[1:]:
            rate = 0.85 * rate + 0.15 * x  # recent days count more
        mean, wf = sum(s) / 30, {}
        for wd in range(7):
            v = [x for d, x in zip(days, s) if d.weekday() == wd]
            wf[wd] = min(1.8, max(0.5, (sum(v) / len(v)) / mean))
        week = sum(rate * wf[(today + timedelta(days=k)).weekday()] for k in range(1, 8))
        last7, prev7 = sum(s[-7:]), sum(s[-14:-7])
        trend = "up" if prev7 and last7 > 1.15 * prev7 else "down" if prev7 and last7 < 0.85 * prev7 else "flat"
        left = p["stock"] / rate if rate > 0 else None
        out.append({"id": p["id"], "week": week, "trend": trend, "days_left": left, "sold30": sum(s),
                    "order_in": None if left is None else max(0, math.floor(left - LEAD)),
                    "reorder": (left is not None and left < 7) or p["stock"] <= p["low"],
                    "suggest": max(0, math.ceil(week * 2 - p["stock"]))})  # two weeks of cover
        c = cats.setdefault(p["cat"], [0, 0, 0])
        c[0] += week * p["price"]; c[1] += last7 * p["price"]; c[2] += prev7 * p["price"]
    tr = lambda a, b: "up" if b and a > 1.15 * b else "down" if b and a < 0.85 * b else "flat"
    return {"products": out, "cats": [{"cat": k, "value": v[0], "trend": tr(v[1], v[2])} for k, v in cats.items()]}

def demo_on():
    """30 days of made-up sales so the forecast and reports can be shown. Flagged as demo and removable."""
    demo_off()
    rnd, today = random.Random(7), datetime.now().date()
    base = {"চাল": 5, "আটা": 3, "ডাল": 2, "চিনি": 3, "তেল": 2.5, "নুন": 1, "দুধ": 8, "ডিম": 20, "চা": 3, "বিস্কুট": 8, "সাবান": 3}
    grow = {"দুধ": 0.02, "বিস্কুট": 0.015, "তেল": -0.012}
    prods = products()
    with ledger._c() as c:
        for k in range(30):
            d = today - timedelta(days=29 - k)
            wk, lines = (1.5 if d.weekday() >= 5 else 1.0), []
            for p in prods:
                if p["name_bn"] in base:
                    q = base[p["name_bn"]] * wk * (1 + grow.get(p["name_bn"], 0) * k) * rnd.uniform(0.75, 1.25)
                    lines.append((p, max(1, round(q)) if p["unit"] in ("piece", "packet") else round(q * 2) / 2))
            total = sum(p["price"] * q for p, q in lines)
            bid = c.execute("INSERT INTO bills(ts,customer,total,paid,demo) VALUES (?,?,?,?,1)",
                            (d.isoformat() + " 12:00:00", None, total, total)).lastrowid
            c.executemany("INSERT INTO bill_items VALUES (?,?,?,?)", [(bid, p["id"], q, p["price"]) for p, q in lines])

def demo_off():
    with ledger._c() as c:
        c.execute("DELETE FROM bill_items WHERE bill_id IN (SELECT id FROM bills WHERE demo=1)")
        c.execute("DELETE FROM bills WHERE demo=1")

def export_rows(kind):
    q = {
        "sales": ("bill,time,customer,product,qty,price,line_total,bill_total,paid,demo",
                  """SELECT b.id,b.ts,b.customer,p.name_bn,bi.qty,bi.price,bi.qty*bi.price,b.total,COALESCE(b.paid,b.total),b.demo
                     FROM bill_items bi JOIN bills b ON b.id=bi.bill_id JOIN products p ON p.id=bi.product_id ORDER BY b.id"""),
        "purchases": ("time,product,qty,total_cost", "SELECT pu.ts,p.name_bn,pu.qty,pu.cost FROM purchases pu JOIN products p ON p.id=pu.product_id ORDER BY pu.id"),
        "stock": ("time,product,change,reason", "SELECT s.ts,p.name_bn,s.delta,s.reason FROM stock_log s JOIN products p ON p.id=s.product_id ORDER BY s.id"),
        "khata": ("time,customer,type,amount,status",
                  "SELECT ts,name,kind,amount,CASE void WHEN 0 THEN 'active' WHEN 1 THEN 'undone' ELSE 'archived' END FROM txns ORDER BY id"),
    }[kind]
    with ledger._c() as c:
        return q[0].split(","), c.execute(q[1]).fetchall()

def overview():
    with ledger._c() as c:
        demo = bool(c.execute("SELECT 1 FROM bills WHERE demo=1 LIMIT 1").fetchone())
    reports = {k: {a: b for a, b in report(k).items() if a != "all"} for k in ("day", "week", "month")}
    reports["daily"] = daily()
    return {"products": [{k: v for k, v in p.items() if k != "aliases"} for p in products()], "bills": recent_bills(),
            "purchases": recent_purchases(), "reports": reports, "forecast": forecast(), "demo": demo}
