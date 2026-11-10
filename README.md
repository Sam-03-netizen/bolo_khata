# Bolo Khata (বলো খাতা \| बोलो खाता)

### A voice-first smart shop assistant for India's small retailers.

**Speak. Record. Manage your shop.**

Bolo Khata is a bilingual, voice-first shop management application
designed to help small retailers manage customer credit (Baki), billing,
inventory and sales records using natural spoken commands in **Bengali
and Hindi**.

Instead of navigating multiple screens or manually maintaining separate
notebooks, shopkeepers can speak a transaction and let the application
process the corresponding updates.

Built for the **Great Indian AI Internship Challenge**, using Gnani AI's
Prisma Speech-to-Text and Timbre Text-to-Speech models.

------------------------------------------------------------------------

## Demo

🎥 **Project Demo:** https://drive.google.com/file/d/13ZguTU3lj5aJykT5ASC7MoqsWi9JShdr/view?usp=sharing

💻 **Source Code:** https://github.com/Sam-03-netizen/bolo_khata

------------------------------------------------------------------------

## The Problem

Many small retailers in India manage their daily operations through
handwritten notebooks, calculators and memory.

This creates several challenges:

-   Customer credit and repayment records can become difficult to track.
-   Manual billing takes time during busy hours.
-   Inventory records are not always updated immediately after a sale.
-   Payment reminders require additional effort.
-   Shopkeepers may not have access to accessible, language-friendly
    digital tools.

Typing every transaction into a conventional application can also
interrupt their workflow.

## The Solution

Bolo Khata brings these everyday operations together through a
voice-first interface.

A shopkeeper can speak in Bengali or Hindi to record credit, receive
payments, generate bills, update stock, check sales and prepare customer
messages.

### The central workflow

Consider this Bengali command:

> রমেশকে ৩টা সাবানের ৫০০ টাকার বিল বানাও, ৩০০ টাকা দিয়েছে।

Meaning: Create a ₹500 bill for Ramesh for three soaps; he has paid
₹300.

The application processes the transaction:

  Operation                   Result
  --------------------- ------------
  Bill generated                ₹500
  Payment received              ₹300
  Outstanding balance           ₹200
  Soap inventory             40 → 37
  Customer khata          ₹200 added

The unpaid amount is recorded in the customer's credit ledger, and a
formatted WhatsApp bill is prepared for review and sending.

**One spoken transaction updates multiple parts of the shop's records.**

------------------------------------------------------------------------

## Key Features

### 1. Voice-first interaction

-   Speech-to-text integration using Gnani AI Prisma v3.0.
-   Spoken responses using Gnani AI Timbre v2.5.
-   Bengali and Hindi language support.
-   Hands-free listening mode.
-   Typed command input as an alternative to voice.

### 2. Customer Khata (Baki Management)

-   Record customer credit and repayments.
-   View outstanding customer balances.
-   Track daily credit and repayment totals.
-   Undo and redo individual khata entries.
-   Archive and restore khata records.
-   Save customer phone numbers.
-   Prepare WhatsApp payment reminders and payment confirmations.

### 3. Billing and Inventory Management

-   Maintain a product catalogue with prices and stock levels.
-   Generate bills through voice commands.
-   Support partial payments.
-   Automatically reduce inventory after billing.
-   Record outstanding bill amounts in customer khata.
-   Add stock through purchases or manual stock adjustments.
-   Display low-stock warnings.
-   Prepare itemised WhatsApp bills.

### 4. Sales and Purchase Records

-   Daily, weekly and monthly sales reports.
-   Track received payments and outstanding sales amounts.
-   View frequently sold products.
-   Maintain purchase and stock-change records.
-   Export sales, purchases, stock logs and khata records as CSV files
    compatible with spreadsheet applications.

### 5. Demand Forecasting

Bolo Khata includes a basic statistical demand forecasting module.

It uses: - Historical sales from the previous 30 days. -
Recency-weighted sales estimates. - Weekday sales patterns. - Current
inventory levels. - Configurable supplier lead time.

It estimates upcoming seven-day demand and provides stock coverage and
reorder suggestions.

**Important:** This is a statistical forecasting approach, not a trained
machine-learning model. Its reliability depends on the availability and
quality of historical sales data.

A clearly labelled demo-data feature is available to demonstrate the
forecasting functionality.

------------------------------------------------------------------------

## Technology Stack

  Component              Technology
  ---------------------- ------------------------
  Backend                Python, Flask
  Frontend               HTML, CSS, JavaScript
  Database               SQLite
  Speech-to-Text         Gnani AI Prisma v3.0
  Text-to-Speech         Gnani AI Timbre v2.5
  Data Export            Python CSV
  External Integration   WhatsApp click-to-chat

### Architecture

1.  The user speaks through the browser microphone.
2.  Audio is sent to the Flask backend.
3.  Gnani Prisma converts speech into text.
4.  The command parser identifies the intended operation.
5.  Flask processes the transaction using the ledger and shop modules.
6.  SQLite stores the corresponding records.
7.  The backend prepares a response and requests speech generation from
    Gnani Timbre.
8.  The frontend displays the result and plays the spoken response when
    audio is available.
9.  If applicable, a WhatsApp message is prepared for the user to review
    and send.

------------------------------------------------------------------------

## Project Structure

``` text
bolo-khata/
│
├── app.py                  # Flask application and API routes
├── ledger.py               # Customer credit ledger
├── nlu.py                  # Command parsing for khata operations
├── shop.py                 # Billing, inventory, reports and forecasting
├── stt.py                  # Gnani Prisma integration
├── tts.py                  # Gnani Timbre integration
│
├── templates/
│   └── index.html          # Frontend interface
│
├── .env.example            # Environment variable template
├── .gitignore
├── requirements.txt
├── README.md
└── PITCH.md
```

------------------------------------------------------------------------

## Getting Started

### Prerequisites

-   Python 3.10 or later.
-   A Gnani AI API key.
-   A modern browser with microphone support.

### 1. Clone the repository

``` bash
git clone https://github.com/Sam-03-netizen/bolo_khata.git
cd bolo_khata
```

### 2. Create a virtual environment

Windows:

``` bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

``` bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and add your Gnani API key.

``` env
GNANI_API_KEY=your_gnani_api_key

SHOP_NAME=My Shop
LEAD_DAYS=3
```

Keep your API key private. Never commit your `.env` file.

### 5. Run the application

``` bash
python app.py
```

Open:

``` text
http://localhost:5000
```

Allow microphone access when prompted.

For deployed use, microphone access requires a secure HTTPS origin.

------------------------------------------------------------------------

## Example Commands

  Language   Example command                Operation
  ---------- ------------------------------ -------------------
  Bengali    রমেশকে পাঁচশো টাকা ধার দিলাম    Record credit
  Bengali    রমেশ ২০০ টাকা ফেরত দিয়েছে      Record repayment
  Bengali    রমেশকে ৩টা সাবানের বিল বানাও   Generate bill
  Bengali    সাবানের স্টক কত                 Check inventory
  Bengali    এই মাসের বিক্রি কত              View sales report
  Hindi      रमेश को पाँच सौ रुपये उधार दिया    Record credit
  Hindi      साबुन का स्टॉक कितना है           Check inventory
  Hindi      इस महीने की बिक्री कितनी है       View sales report

Command understanding currently uses keyword-based rules and supported
sentence patterns. Results may vary with phrasing, pronunciation and
customer-name recognition.

------------------------------------------------------------------------

## Limitations

Bolo Khata is a functional prototype, not a production-ready retail
management system.

The current implementation has the following limitations:

1.  **Command understanding:** Uses rule-based parsing rather than a
    general-purpose conversational language model. Commands should
    follow supported patterns.
2.  **Name recognition:** Bengali and Devanagari names are not
    automatically treated as identical identities. Names may need to be
    entered consistently in one script.
3.  **Forecasting:** Predictions depend on historical sales. New shops
    may not have sufficient data for meaningful estimates.
4.  **WhatsApp:** Messages are prepared using WhatsApp click-to-chat.
    The shopkeeper must review and manually send them. Automated sending
    is not implemented.
5.  **Data storage:** Uses a local SQLite database and does not
    currently provide multi-user cloud synchronisation.
6.  **Authentication:** Shop-owner login, role-based permissions and
    multi-shop account management are not implemented.
7.  **Speech recognition:** Performance in noisy real-world retail
    environments has not been formally benchmarked.
8.  **Transaction recovery:** Undo and redo functionality currently
    applies to khata entries, not as a universal rollback mechanism for
    all billing and inventory operations.
9.  **Security:** The prototype has not undergone a formal production
    security audit and should not be used as the sole source of business
    records.

------------------------------------------------------------------------

## Future Improvements

The next development phase could focus on:

-   More robust multilingual natural-language understanding.
-   Improved customer-name recognition and transliteration.
-   Secure authentication and multiple shop-owner accounts.
-   Cloud database integration, synchronisation and automated backups.
-   WhatsApp Business API integration for supported automated messaging.
-   More comprehensive transaction history and rollback mechanisms.
-   Better forecasting using larger real-world datasets and evaluation.
-   Supplier management and purchase-order generation.
-   Additional Indian languages.
-   Field testing with actual small retailers to evaluate usability and
    speech recognition accuracy.

------------------------------------------------------------------------

## Built With Purpose

Bolo Khata explores how voice interfaces and multilingual AI can make
everyday digital tools more accessible to small businesses.

The goal is simple: reduce the effort of maintaining everyday shop
records without forcing shopkeepers to change the way they naturally
communicate.

**Built by Samriddhi Bhowmik**

Great Indian AI Internship Challenge

**Powered by Gnani AI Prisma and Timbre.**

------------------------------------------------------------------------

## Acknowledgements

Thanks to Gnani AI for providing the speech technologies used in this
project.

If you find the project interesting, consider starring the repository or
sharing your feedback.

**Repository:** https://github.com/Sam-03-netizen/bolo_khata
