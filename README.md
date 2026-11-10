# Bolo Khata (বলো খাতা / बोलो खाता)

A **voice-first smart-shop assistant** for small shopkeepers, in **Hindi and Bengali**. Billing, customer credit (Baki), stock, WhatsApp messages and a simple demand forecast all work together, and you run them by speaking.

Built for the **Great Indian AI Internship Challenge** with Gnani AI's **Prisma** (speech to text) and **Timbre** (text to speech).

## One sentence, everything updates

> "রমেশকে ৩টা সাবানের ৫০০ টাকার বিল বানাও, ৩০০ টাকা দিয়েছে"

1. The soap stock goes from 10 to 7.
2. A bill for ₹500 is saved, with ₹300 paid.
3. The unpaid ₹200 goes into Ramesh's khata (Baki).
4. A WhatsApp message is ready: total ₹500, paid ₹300, balance ₹200.
5. The app speaks the result back.

## Two tabs

**Khata (Baki)**: who owes what, repayments, undo / redo / archive and restore, WhatsApp payment reminders (or a thank-you when everything is paid), and a saved phone number per customer so WhatsApp opens the right chat.

**Shop (stock and bills)**:
- Product list with prices (edit a price by tapping it) and stock levels
- Voice billing, with partial payment and a spoken bill total ("৫০০ টাকার বিল")
- Stock goes down on every bill and up on every purchase (voice or the ＋ button, with optional cost)
- Low-stock warnings on screen and spoken after a bill
- Sales reports for today, the last 7 days and the last 30 days, with a 14-day bar chart
- Purchase, sales, stock-change and khata records, downloadable as Excel-ready CSV
- Demand forecast per product and per category (see below)

## Things you can say

| Say | Result |
|---|---|
| "রমেশকে পাঁচশো টাকা ধার দিলাম" | Adds udhaar |
| "রমেশ ২০০ টাকা ফেরত দিয়েছে" | Records a repayment |
| "রমেশকে ২ কেজি চাল আর ১ লিটার তেলের বিল বানাও" | Bill, stock down, WhatsApp bill |
| "…ধারে বিল বানাও" | Whole bill goes to the khata |
| "চাল ৫০ কেজি এসেছে ২০০০ টাকায়" | Purchase record, stock up |
| "সাবানের স্টক কত" | Stock, last-30-day sales, days left, what to order and when |
| "এই মাসের বিক্রি কত" | Sales report |
| "মীরাকে মেসেজ পাঠাও" | Reminder or thank-you, ready for WhatsApp |
| "ভুল হয়েছে, মুছে দাও" | Undo the last khata entry |

The same works in Hindi ("रमेश को 2 किलो चावल का बिल बनाओ", "साबुन का स्टॉक कितना है"). Choose the language with the toggle at the top.

**Hands-free mode** (🎧) keeps listening: press once and keep talking. It learns the background noise, so steady shop noise is ignored.

## About the forecast

The forecast is a **statistical estimate**, not a neural network and not a guarantee. For each product it uses the last 30 days of your bills: recent days count more, and weekday patterns (for example busier weekends) are applied. From that it shows the expected sales for the next 7 days, how many days the current stock will last, and what to reorder and when (two weeks of cover, minus a supplier lead time of `LEAD_DAYS`).

A new shop has no history, so the forecast fills in as bills are saved. The **demo sales data** button adds 30 days of *made-up* sales (clearly marked, removable) so the feature can be shown.

## Built with

Gnani Prisma v3.0 (`/stt/v3`) and Timbre v2.5, Python, Flask, SQLite, and plain HTML, CSS and JavaScript.

## Run it

You need Python 3.10+ and a Gnani API key from [app.gnani.ai](https://app.gnani.ai).

```bash
git clone <this-repo-url>
cd bolo-khata
python -m venv venv
# Windows: venv\Scripts\activate     Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and paste your key. Then:

```bash
python app.py
```

Open <http://localhost:5000> in Chrome and allow the microphone.

## Files

```
app.py        server, replies, routes          shop.py     products, bills, stock, reports, forecast
nlu.py        understands khata sentences      ledger.py   khata database (nothing is ever really deleted)
stt.py        Prisma speech to text            tts.py      Timbre text to speech
templates/index.html   the page (tabs, tables, hands-free, charts)
```

## Known limitations

- Names are matched by spelling within one script: "রমেশ" and "रमेश" are different people. Use one language per session.
- Typed input expects digits ("500"); voice input returns digits automatically.
- Sentences are understood by keyword rules. Say the customer's name first, then the items and amounts. Products you add yourself are matched by their exact name.
- A spoken bill total replaces the catalogue prices; the WhatsApp bill shows the difference as an "adjustment" line.
- WhatsApp opens with the message ready; **you tap Send**. Sending silently needs the paid WhatsApp Business API.
- Selling more than the stock shows does not block the bill; stock goes to zero and a warning appears.
- No login and a single local database: this is a demo, not a production system.
- Noisy-shop accuracy has not been formally measured.

## Security

Never commit `.env` or your API key. `.gitignore` already excludes `.env`, `venv/` and `khata.db`. If a key is ever exposed, revoke it in the Gnani dashboard and make a new one.

Built by **Samriddhi Bhowmik** · `#GnaniAI` `#GreatIndianAIInternshipChallenge`
