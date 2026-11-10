import base64, csv, io, os, re, tempfile, urllib.parse
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, Response, jsonify, render_template, request
from num2words import num2words
import ledger, nlu, shop, stt, tts

app = Flask(__name__)
ledger.init()
shop.init()
SHOP_INTENTS = {"bill", "restock", "stock", "stock_low", "report"}

MSG = {
    "hi": dict(unit=" रुपये",
        credit="{n} को {a} उधार लिखा। कुल बाकी {b} है।",
        credit_clear="{n} को {a} उधार लिखा। अब कोई बाकी नहीं है।",
        paid="{n} से {a} मिले। अब बाकी {b} है।",
        clear="{n} से {a} मिले। अब कोई बाकी नहीं है।",
        bal="{n} का कुल बाकी {b} है।", none="{n} का कोई हिसाब नहीं मिला।",
        today="आज {g} उधार दिया और {r} मिले। कुल बाकी {t} है।",
        undo="आख़िरी एंट्री रद्द की: {n}, {a}।", undo_none="रद्द करने के लिए कोई एंट्री नहीं है।",
        remind="{n} के लिए संदेश तैयार: {msg}", remind_none="{n} का कुछ बाकी नहीं है।",
        remind_msg="नमस्ते {n} जी, आपके {b} बाकी हैं। सुविधा से दे दीजिए। धन्यवाद।",
        thanks_msg="नमस्ते {n} जी, आपका सारा हिसाब चुकता हो गया है। धन्यवाद!",
        bill_ok="बिल #{id} बना। कुल {t}।", bill_ok_s="बिल बन गया। कुल {t}।",
        bill_part="बिल #{id} बना। कुल {t}, दिए {p}, बाकी {b}।", bill_part_s="बिल बन गया। कुल {t}, दिए {p}, बाकी {b}।",
        bill_noname="नाम बोलें तो बाकी खाते में चढ़ेगा।",
        low_warn="चेतावनी: {items} का स्टॉक कम है।", restock_ok="स्टॉक अपडेट: {items}।",
        stock_is="स्टॉक में है: {items}।", stock_low="स्टॉक कम: {items}।", stock_ok="सभी सामान का स्टॉक ठीक है।",
        per_day="आज", per_week="पिछले 7 दिन में", per_month="पिछले 30 दिन में",
        rep_ok="{p} {c} बिल, कुल बिक्री {r}। मिले {cash}, बाकी {cr}।", rep_top=" सबसे ज़्यादा बिका: {items}।",
        rep_none="{p} कोई बिक्री नहीं।", rep_prod="{n}: {p} {q} {u} बिके, {r}।", rep_none_p="{n}: {p} बिक्री नहीं।",
        stk="{n}: अभी {s} {u} है।", stk_sold=" पिछले 30 दिन में {m} {u} बिका।", stk_days=" इस रफ़्तार से करीब {d} दिन चलेगा।",
        stk_order=" {when} {x} {u} मंगाइए।", now="आज ही", tomorrow="कल", in_days="{k} दिन में",
        unknown="समझ नहीं आया, दोबारा बोलिए।", empty="आवाज़ साफ़ नहीं आई, दोबारा बोलिए।"),
    "bn": dict(unit=" টাকা",
        credit="{n}কে {a} ধার লেখা হলো। মোট বাকি {b}।",
        credit_clear="{n}কে {a} ধার লেখা হলো। এখন কোনো বাকি নেই।",
        paid="{n}-এর কাছ থেকে {a} পাওয়া গেল। এখন বাকি {b}।",
        clear="{n}-এর কাছ থেকে {a} পাওয়া গেল। আর কোনো বাকি নেই।",
        bal="{n}-এর মোট বাকি {b}।", none="{n}-এর কোনো হিসাব পাওয়া যায়নি।",
        today="আজ {g} ধার দিয়েছেন আর {r} পেয়েছেন। মোট বাকি {t}।",
        undo="শেষ এন্ট্রি বাতিল হলো: {n}, {a}।", undo_none="বাতিল করার মতো কোনো এন্ট্রি নেই।",
        remind="{n}-এর জন্য মেসেজ তৈরি: {msg}", remind_none="{n}-এর কোনো বাকি নেই।",
        remind_msg="নমস্কার {n}, আপনার {b} বাকি আছে। সুবিধামতো দিয়ে দেবেন। ধন্যবাদ।",
        thanks_msg="নমস্কার {n}, আপনার সব বাকি মিটে গেছে। ধন্যবাদ!",
        bill_ok="বিল #{id} তৈরি। মোট {t}।", bill_ok_s="বিল তৈরি হয়েছে। মোট {t}।",
        bill_part="বিল #{id} তৈরি। মোট {t}, দিয়েছেন {p}, বাকি {b}।", bill_part_s="বিল তৈরি হয়েছে। মোট {t}, দিয়েছেন {p}, বাকি {b}।",
        bill_noname="নাম বললে বাকি খাতায় উঠবে।",
        low_warn="সতর্কতা: {items}-এর স্টক কম।", restock_ok="স্টক আপডেট: {items}।",
        stock_is="স্টকে আছে: {items}।", stock_low="স্টক কম: {items}।", stock_ok="সব জিনিসের স্টক ঠিক আছে।",
        per_day="আজ", per_week="গত ৭ দিনে", per_month="গত ৩০ দিনে",
        rep_ok="{p} {c}টি বিল, মোট বিক্রি {r}। পেয়েছেন {cash}, বাকি {cr}।", rep_top=" সবচেয়ে বেশি বিক্রি: {items}।",
        rep_none="{p} কোনো বিক্রি নেই।", rep_prod="{n}: {p} {q} {u} বিক্রি, {r}।", rep_none_p="{n}: {p} বিক্রি নেই।",
        stk="{n}: এখন {s} {u} আছে।", stk_sold=" গত ৩০ দিনে {m} {u} বিক্রি হয়েছে।", stk_days=" এই হারে প্রায় {d} দিন চলবে।",
        stk_order=" {when} {x} {u} অর্ডার করুন।", now="আজই", tomorrow="কাল", in_days="{k} দিনের মধ্যে",
        unknown="বুঝতে পারিনি, আবার বলুন।", empty="আওয়াজ পরিষ্কার আসেনি, আবার বলুন।"),
}

def money(n, spoken, lang):
    if not spoken:
        return "₹" + f"{n:,.2f}".rstrip("0").rstrip(".")
    n = int(n + 0.5)
    try:
        return num2words(n, lang=lang) + MSG[lang]["unit"]  # TTS reads number words best
    except Exception:
        return f"{n}{MSG[lang]['unit']}"

def qty_str(x, spoken, lang):
    if spoken and float(x).is_integer():
        try:
            return num2words(int(x), lang=lang)
        except Exception:
            pass
    return f"{x:g}"

def state():
    return {"people": ledger.people(), "today": ledger.today(), "archived": ledger.archived(),
            "undone": ledger.undone(), "shop": shop.overview()}

# ---------- shop commands: bills, stock, reports ----------
def act_shop(sd):
    k = sd["intent"]
    r = {"intent": k, "name": sd.get("customer"), "amount": None, "total": 0, "today": ledger.today()}
    if k == "bill":
        b = shop.make_bill(sd["items"], sd.get("customer"), sd.get("total"), sd.get("paid"))
        if b["customer"]:
            if b["balance"] > 0:
                ledger.add(b["customer"], "credit", b["balance"])  # the unpaid part goes into the khata
            b["overall"] = ledger.balance(b["customer"])
        r["bill"], r["low"] = b, shop.low_among([p for p, _ in sd["items"]])
    elif k == "restock":
        r["after"] = shop.restock(sd["items"], sd.get("cost"))
    elif k == "stock":
        r["after"] = [(p, 0) for p in shop.fresh(sd["items"])]
        r["fc"] = {x["id"]: x for x in shop.forecast()["products"]}
    elif k == "report":
        r["rep"], r["period"], r["items"] = shop.report(sd["period"]), sd["period"], sd["items"]
    else:
        r["low"] = shop.low_stock()
    return r

def say_shop(r, spoken, lang):
    m, M, k = MSG[lang], (lambda n: money(n, spoken, lang)), r["intent"]
    nm, un, q = (lambda p: shop.pname(p, lang)), (lambda p: shop.unit(p, lang)), (lambda x: qty_str(x, spoken, lang))
    stock = lambda ps: ", ".join(f"{nm(p)} {q(p['stock'])} {un(p)}" for p in ps)
    when = lambda d: m["now"] if d == 0 else m["tomorrow"] if d == 1 else m["in_days"].format(k=q(d))
    if k == "bill":
        b = r["bill"]
        key = ("bill_part" if b["balance"] > 0 else "bill_ok") + ("_s" if spoken else "")
        head = m[key].format(id=b["id"], t=M(b["total"]), p=M(b["paid"]), b=M(b["balance"]))
        note = m["bill_noname"] if b["balance"] > 0 and not b["customer"] else ""
        warn = m["low_warn"].format(items=", ".join(nm(p) for p in r["low"])) if r["low"] else ""
        lines = [] if spoken else [f"• {nm(p)} {q(x)} {un(p)} = {M(p['price'] * x)}" for p, x in b["items"]]
        return (" " if spoken else "\n").join(filter(None, [head, *lines, note, warn]))
    if k == "restock":
        return m["restock_ok"].format(items=stock([p for p, _ in r["after"]]))
    if k == "stock":
        out = []
        for p, _ in r["after"]:
            f = r["fc"].get(p["id"], {})
            s = m["stk"].format(n=nm(p), s=q(p["stock"]), u=un(p))
            if f.get("sold30"):
                s += m["stk_sold"].format(m=q(round(f["sold30"], 1)), u=un(p))
            if f.get("days_left") is not None:
                s += m["stk_days"].format(d=q(max(1, round(f["days_left"]))))
                if f.get("suggest") and f["days_left"] < 14:
                    s += m["stk_order"].format(when=when(f["order_in"]), x=q(f["suggest"]), u=un(p))
            out.append(s)
        return " ".join(out)
    if k == "report":
        rp, per, pm = r["rep"], m["per_" + r["period"]], {p["id"]: p for p in shop.products()}
        if r["items"]:
            return " ".join(
                m["rep_prod"].format(n=nm(p), p=per, q=q(rp["all"][p["id"]]["qty"]), u=un(p), r=M(rp["all"][p["id"]]["revenue"]))
                if p["id"] in rp["all"] else m["rep_none_p"].format(n=nm(p), p=per) for p in r["items"])
        if not rp["bills"]:
            return m["rep_none"].format(p=per)
        s = m["rep_ok"].format(p=per, c=q(rp["bills"]), r=M(rp["revenue"]), cash=M(rp["cash"]), cr=M(rp["credit"]))
        return s + (m["rep_top"].format(items=", ".join(nm(pm[x["id"]]) for x in rp["top"])) if rp["top"] else "")
    return m["stock_low"].format(items=stock(r["low"])) if r["low"] else m["stock_ok"]

# ---------- khata commands ----------
def act(text):
    """Parse the sentence and update the books. Runs once per command."""
    sd = shop.detect(text)
    if sd:
        return act_shop(sd)
    r = nlu.parse(text, ledger.names())
    if r["intent"] in ("credit", "payment"):
        ledger.add(r["name"], r["intent"], r["amount"])
    if r["intent"] == "undo":
        r["undone"] = ledger.undo()
    if r["name"]:
        r["balance"] = ledger.balance(r["name"])
    r["total"] = sum(p["balance"] for p in ledger.people() if p["balance"] > 0)
    r["today"] = ledger.today()
    return r

def say(r, spoken, lang):
    m, M = MSG[lang], (lambda n: money(n, spoken, lang))
    k, name, amt, bal = r["intent"], r["name"], r["amount"], r.get("balance")
    if k in SHOP_INTENTS:
        return say_shop(r, spoken, lang)
    if k == "credit":
        return m["credit" if bal > 0 else "credit_clear"].format(n=name, a=M(amt), b=M(bal))
    if k == "payment":
        return (m["clear"] if bal <= 0 else m["paid"]).format(n=name, a=M(amt), b=M(bal))
    if k == "undo":
        u = r.get("undone")
        return m["undo"].format(n=u[0], a=M(u[2])) if u else m["undo_none"]
    if k == "remind":
        if bal is None:
            return m["none"].format(n=name)
        key = "remind_msg" if bal > 0 else "thanks_msg"  # owes money: reminder; all paid: thank-you
        return m["remind"].format(n=name, msg=m[key].format(n=name, b=M(max(bal, 0))))
    if k == "query" and name:
        if bal is None:
            return m["none"].format(n=name)
        return m["bal"].format(n=name, b=M(max(bal, 0)))
    if k == "query":
        t = r["today"]
        return m["today"].format(g=M(t["given"]), r=M(t["received"]), t=M(r["total"]))
    return m["unknown"]

def finish(text, lang="hi"):
    lang = lang if lang in MSG else "hi"
    r, wa, direct = None, None, False
    if not text:
        shown = spoken = MSG[lang]["empty"]
    else:
        r = act(text)
        shown, spoken = say(r, False, lang), say(r, True, lang)
        if r["intent"] == "remind" and r.get("balance") is not None:  # opens WhatsApp with the message ready
            key = "remind_msg" if r["balance"] > 0 else "thanks_msg"
            msg = MSG[lang][key].format(n=r["name"], b=money(max(r["balance"], 0), False, lang))
            phone = ledger.get_phone(r["name"])  # with a saved number WhatsApp opens that chat directly
            direct = bool(phone)
            wa = f"https://wa.me/{phone or ''}?text=" + urllib.parse.quote(msg)
        if r["intent"] == "bill":  # the itemised bill, ready to send on WhatsApp
            b = r["bill"]
            phone = ledger.get_phone(b["customer"]) if b["customer"] else None
            direct = bool(phone)
            wa = f"https://wa.me/{phone or ''}?text=" + urllib.parse.quote(shop.bill_text(b, lang))
    audio = None
    try:
        audio = base64.b64encode(tts.speak(spoken, lang)).decode()
    except Exception as e:  # the app still works without a voice reply
        print("TTS error:", e)
    return {"transcript": text, "reply": shown, "audio": audio, "lang": lang, "wa": wa, "wa_direct": direct,
            "intent": r["intent"] if r else None, **state()}

# ---------- web routes ----------
@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/ledger")
def get_ledger():
    return jsonify(state())

@app.post("/api/voice")
def voice():
    f = request.files.get("audio")
    if not f:
        return jsonify(error="No audio received"), 400
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as t:
        f.save(t)
        path = t.name
    try:
        lang = request.form.get("lang", "hi")
        text = stt.transcribe(path, ledger.names() + shop.product_names(lang), lang)
    except Exception as e:
        return jsonify(error=str(e)), 502
    finally:
        os.remove(path)
    return jsonify(finish(text, lang))

@app.post("/api/text")  # typed test, no speech-to-text credits used
def text():
    d = request.get_json(silent=True) or {}
    return jsonify(finish(d.get("text", "").strip(), d.get("lang", "hi")))

def norm_phone(s):
    d = re.sub(r"\D", "", s or "")
    if not d:
        return ""
    if len(d) == 11 and d.startswith("0"):
        d = d[1:]
    if len(d) == 10:
        d = "91" + d  # India
    if not 11 <= len(d) <= 15:
        raise ValueError
    return d

@app.post("/api/phone")
def phone():
    d = request.get_json(silent=True) or {}
    try:
        ledger.set_phone(d.get("name", ""), norm_phone(d.get("phone", "")))
    except ValueError:
        return jsonify(error="bad number"), 400
    return jsonify(state())

@app.post("/api/product")
def product_add():
    d = request.get_json(silent=True) or {}
    try:
        shop.add_product(str(d.get("name", "")).strip(), d.get("unit", "piece"), float(d["price"]),
                         float(d.get("stock") or 0), float(d.get("low") or 0))
    except (KeyError, ValueError):
        return jsonify(error="bad product"), 400
    return jsonify(state())

@app.post("/api/stock")
def stock_add():
    d = request.get_json(silent=True) or {}
    try:
        pid, delta = int(d["id"]), float(d["delta"])
        if delta > 0:  # stock coming in is a purchase record (cost is optional)
            shop.purchase(pid, delta, float(d["cost"]) if d.get("cost") else None)
        else:
            shop.adjust_stock(pid, delta, "correction")
    except (KeyError, ValueError):
        return jsonify(error="bad stock"), 400
    return jsonify(state())

@app.post("/api/price")
def price_set():
    d = request.get_json(silent=True) or {}
    try:
        shop.set_price(int(d["id"]), float(d["price"]))
    except (KeyError, ValueError):
        return jsonify(error="bad price"), 400
    return jsonify(state())

@app.post("/api/demo")
def demo():
    (shop.demo_on if (request.get_json(silent=True) or {}).get("on") else shop.demo_off)()
    return jsonify(state())

@app.get("/api/bill/<int:bid>")
def bill_again(bid):
    b = shop.get_bill(bid)
    if not b:
        return jsonify(error="no such bill"), 404
    lang = request.args.get("lang", "hi")
    phone = ledger.get_phone(b["customer"]) if b["customer"] else None
    return jsonify(wa=f"https://wa.me/{phone or ''}?text=" + urllib.parse.quote(shop.bill_text(b, lang)), direct=bool(phone))

@app.get("/api/export/<kind>")
def export(kind):
    try:
        head, rows = shop.export_rows(kind)
    except KeyError:
        return jsonify(error="unknown"), 404
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(head)
    w.writerows(rows)
    return Response("\ufeff" + buf.getvalue(), mimetype="text/csv",  # BOM so Excel shows Bengali and Hindi correctly
                    headers={"Content-Disposition": f"attachment; filename=bolo-khata-{kind}.csv"})

@app.post("/api/undo")
def undo():
    ledger.undo()
    return jsonify(state())

@app.post("/api/redo")
def redo():
    ledger.redo()
    return jsonify(state())

@app.post("/api/reset")  # archives the khata; /api/restore brings it back
def reset():
    ledger.clear()
    return jsonify(state())

@app.post("/api/restore")
def restore():
    ledger.restore()
    return jsonify(state())

if __name__ == "__main__":
    app.run(debug=True, port=5000)
