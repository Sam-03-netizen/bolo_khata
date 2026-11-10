# Bolo Khata: solution pitch

**A voice-first smart-shop assistant for small shopkeepers, in Hindi and Bengali.**
By Samriddhi Bhowmik · Great Indian AI Internship Challenge · built on Gnani AI's Prisma and Timbre

## The problem
Small shopkeepers juggle three things while serving customers: **bills, udhaar (credit) and stock**. Most keep them in paper notebooks and in memory. Entries get missed, balances get disputed, awkward payment reminders get delayed, and nobody notices an item is running out until it is gone. Typing into an app is slow with busy hands, and most apps assume English.

## The solution
Bolo Khata lets the shopkeeper simply *say* what happened. One spoken sentence updates billing, credit, stock and the customer's WhatsApp message together:

> "রমেশকে ৩টা সাবানের ৫০০ টাকার বিল বানাও, ৩০০ টাকা দিয়েছে"

Soap stock goes from 10 to 7, a ₹500 bill is saved, the unpaid ₹200 is recorded as Ramesh's Baki, a WhatsApp bill (total ₹500, paid ₹300, balance ₹200) is ready to send, and the result is spoken back.

## How it uses Gnani's models
- **Prisma (speech to text):** understands Hindi and Bengali speech. Customer and product names are sent as hints, so names are misheard less often.
- **Timbre (text to speech):** answers in the shopkeeper's language, with a Hindi voice and a Bengali voice.

## What it does
- **Khata (Baki):** credit, repayments, undo / redo / restore, WhatsApp reminders, and a saved number per customer.
- **Shop:** products and prices, stock that updates on every bill and purchase, and low-stock warnings.
- **Records:** sales reports for today, 7 days and 30 days; purchase, sales and stock records downloadable as CSV.
- **Ask the shop:** "How much soap is left?" gives stock, last-30-day sales, days of stock left, and what to order and when.
- **Demand forecast:** next-7-day sales per product and category, from recent trend plus weekday pattern. It is a statistical estimate, not a neural network.
- **Hands-free mode** that learns background noise.

## Impact
Fewer forgotten udhaar entries, faster and clearer billing, polite reminders sent in seconds, and earlier restocking, all in the shopkeeper's own language and without typing.

## Honest limits
Sentences are understood by keyword rules (say the customer's name first). Names are matched within one script. The forecast needs sales history, so a clearly labelled sample-data mode is provided for demos. WhatsApp opens with the message ready and the shopkeeper taps Send. Accuracy in a noisy shop has not been formally measured. This is a single-shop local demo without login.

## Next steps
Login and a cloud database, the WhatsApp Business API, supplier orders from the forecast, and more languages.

**Stack:** Python, Flask, SQLite, plain JavaScript. **Code and setup:** see [README.md](README.md).
