import datetime
import sqlite3
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Use resend for email sending
# pip install resend
import resend

app = FastAPI(
    title="Python Code Exam App",
    description="Register candidate, show multiple questions with expected output panel, code editor, run code output, send result to HR",
    version="0.3"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "simple_exam_app1.db"

HR_EMAIL = "roopa.satish@timelineinvestments.in"

RESEND_API_KEY = "re_7RW6QVrT_FS96FnnKhHhVEdmQkNhqGHVd"

def get_db():
    c = sqlite3.connect(DB_NAME)
    c.row_factory = sqlite3.Row
    return c

def ensure_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS candidate1 (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        position_applied TEXT,
        dhan_client_id TEXT,
        dhan_access_token TEXT,
        reg_time TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attempt (
        attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_idx INTEGER,
        code TEXT,
        output TEXT,
        created TEXT
    )""")
    # Add table to record exam completion
    cur.execute("""
    CREATE TABLE IF NOT EXISTS exam_completion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        completed_at TEXT
    )""")
    conn.commit()
    conn.close()
ensure_db()

def get_exam_questions():
    return [
        # ... no change, keep as is ...
        {
            "question": (
                "TLI - Question 1: Trading Risk Summary — Dhan API (Python)\n\n"
                "Objective:\n"
                "Use the Dhan API ('dhanhq' library) to connect to a trading account, retrieve balance and open positions, and generate a position risk summary.\n\n"
                "Instructions:\n"
                "1. Import the DhanHQ client:\n"
                "   - `from dhanhq import dhanhq`\n"
                "   - Use sample/demo credentials for `client_id` and `access_token`.\n"
                "2. Create a DhanHQ connection:\n"
                "   - `dhan = dhanhq(client_id, access_token)`\n"
                "3. Fetch and print the available account balance using `dhan.get_fund_limits()`, extracting the appropriate available balance field from the response.\n"
                "4. Get all current open positions via `dhan.get_positions()`.\n"
                "5. For each position, extract (and print in summary table):\n"
                "   - Symbol (e.g. position['tradingSymbol'])\n"
                "   - Quantity (e.g. position['netQty'])\n"
                "   - Buy Average Price (e.g. position['buyAvg'])\n"
                "   - Security Id (position['securityId'])\n"
                "   - Last Traded Price (LTP): Use `dhan.intraday_minute_data(security_id, \"NSE_EQ\", \"EQUITY\", \"from_date\", \"to_date\")`, fetch the most recent closing price as LTP\n"
                "   - Calculate Unrealized PnL: (LTP - Buy Avg) * Quantity\n"
                "   - Calculate Percentage Change: ((LTP - Buy Avg) / Buy Avg) * 100\n"
                "6. Print a formatted summary line for each position as follows:\n"
                "   Position: <SYMBOL> | Quantity: <QTY> | Buy Avg: <BUY_AVG> | LTP: <LTP> | Unrealized PnL: <PNL> | % Change: <PERCENT>%\n"
                "7. Print totals:\n"
                "   - Print the available balance and the total cumulative Unrealized PnL across all positions.\n\n"
                "Notes:\n"
                "- If you do not have live API credentials, use placeholder strings for `client_id` and `access_token`.\n"
                "- The goal is to show usage of the API and correct calculations regardless of live connectivity.\n"
            ),
            "expected_output":
"""Sample Output:
Position: INFY-EQ | Quantity: 100 | Buy Avg: 1550.00 | LTP: 1570.00 | Unrealized PnL: +2000.0 | % Change: +1.29%

Position: RELIANCE-EQ | Quantity: 30 | Buy Avg: 2500.00 | LTP: 2490.00 | Unrealized PnL: -300.0 | % Change: -0.40%
-----------------------------------------------
Available Balance: ₹100000.00

"""
        },
        {
            "question": (
                "TLI - Question 2: Step-by-Step: Fetching Historical Data & Generating EMA Signal using Dhan API\n\n"
                "**Step 1: Authenticate & Setup**\n"
                "- Use the given `client_id` and `access_token` (provided as example values) to authorize requests to the Dhan API.\n"
                "    from dhanhq import dhanhq\n"
                "    `dhan = dhanhq(client_id, access_token)`\n\n"
                "**Step 2: Connect to Dhan and Fetch Historical Data**\n"
                "- Identify the IDEA security's `security_id`. (E.g., for IDEA, security_id = 12345, replace with actual value if needed.)\n"
                "- Use Dhan's historical-candles endpoint to fetch 5-minute candle data for the last 3 trading days for that security.\n"
                "- Required parameters typically include:\n"
                "    - security_id =\"14366\"\n"
                "    - from and to dates (calculate the date range for last 3 days)\n"
                "    - Add authentication headers with `access_token`.\n"
                "    from_date=3 days back date YYYY-MM-DD\n"
                "    to_date= current day date YYYY-MM-DD\n"
                "    securityID=\"\"\n"
                "      hist = dhan.intraday_minute_data(securityId, \"NSE_EQ\", \"EQUITY\", \"from_date\", \"to_date\")\n"
                "      returns dtaeOHLCV\n"
                "      take only \n\n"
                "**Step 3: Prepare Data**\n"
                "- Extract the 'close' prices from the historical candle data and store them in a list or pandas Series.\n\n"
                "# Step 4: Explanation\n"
                "# To calculate EMA (Exponential Moving Average) indicators for a time series of prices (such as stock closing prices),\n"
                "# you typically use a pandas DataFrame. For each row (which often represents a 5-minute candle/bar), you calculate:\n"
                "#  - EMA20: the moving average of the 'close' price using a span/window of 20 periods.\n"
                "#  - EMA50: the moving average of the 'close' price using a span/window of 50 periods.\n"
                "# In pandas, this can be done with the .ewm(span=...).mean() method on the 'close' column.\n"
                "# The EMA values help signal trends: when EMA20 crosses above EMA50, it often signals bullish momentum,\n"
                "# and when EMA20 crosses below EMA50, it can signal bearish momentum.\n"
                "- Using pandas or a simple EMA formula, calculate:\n"
                "    - EMA20 (Exponential Moving Average of last 20 closes)\n"
                "    - EMA50 (Exponential Moving Average of last 50 closes)\n\n"
                "**Step 5: Print Results**\n"
                "- Print the latest `close` price, EMA20, and EMA50 values with clear labels.\n\n"
                "**Step 6: Generate Trading Signal**\n"
                "- If EMA20 > EMA50, print \"Bullish\"\n"
                "- If EMA20 < EMA50, print \"Bearish\"\n"
            ),
            "expected_output": """A DataFrame should be printed similar to:

            open   high    low  .Volume..     timestamp      EMA20      EMA50
        0     11.20  11.22  11.11  ...  1.771818e+09  11.150000  11.150000
        1     11.16  11.19  11.10  ...  1.771818e+09  11.165750  11.165300
        2     11.19  11.21  11.16  ...  1.771818e+09  11.178326  11.177332
        3     11.18  11.20  11.17  ...  1.771818e+09  11.181696  11.180692
        4     11.18  11.18  11.16  ...  1.771819e+09  11.176448  11.176216
        ...     ...    ...    ...  ...           ...        ...        ...
        1120  10.73  10.75  10.72  ...  1.772013e+09  10.734637  10.740533
        1121  10.73  10.74  10.72  ...  1.772013e+09  10.735148  10.740512
        1122  10.73  10.74  10.73  ...  1.772013e+09  10.734658  10.740100
        1123  10.74  10.75  10.73  ...  1.772013e+09  10.736119  10.740488
        1124  10.75  10.76  10.73  ...  1.772014e+09  10.737441  10.740861

(Format: each row contains open, high, low, volume, timestamp, EMA20, and EMA50. Number of rows and values will depend on actual data returned.)


(Values will vary depending on price series in the code.)
"""
        },
        {
            "question": (
                "Q3: TLI-  Dataset → DB → PnL Question\n\n"
                "Objective:\n\n"
                "Candidate receives predefined trade dataset.\n\n"
                "They must:\n"
                "1. Insert into database\n"
                "2. Calculate realized PnL;\n"
                "3. Return output via API or script\n"
                "No external APIs.\n\n"
                "Problem Statement\n\n"
                "Given dataset:\n"
                "symbol,side,price,qty\n"
                "SBIN,BUY,500,10\n"
                "SBIN,SELL,520,10\n"
                "INFY,BUY,1500,5\n"
                "INFY,SELL,1480,5\n\n"
                "Tasks:\n"
                "• Create DB table using sqlite3\n"
                "• Insert records\n"
                "• Calculate realized PnL per symbol\n"
                "• Return final output\n"
                "Print the result of factorial(5)."
            ),
            "expected_output": """SBIN : +200
INFY : -100
TOTAL PnL : +100
"""
        },
        {
            "question": (
                "Q4: TLI - Question 4: Risk-Based Market Order Placement\n\n"
                "Objective:\n"
                "Develop a risk-controlled market order execution function using the Dhan API.\n\n"
                "Requirements:\n\n"
                "from dhanhq import dhanhq\n\n"
                "Create dhan object using access token and the client id given below:\n"
                "dhan = dhanhq(clientid, access_token)\n\n"
                "Fetch data using:\n"
                "data should have security_id=\"14366\", \"NSE_EQ\", \"EQUITY\", \"from_date\", \"to_date\"\n"
                "from_date and to_date should be today's date YYYY-MM-DD\n"
                "dhan.intraday_minute_data(data)\n\n"
                "1. Fetch the Last Traded Price (LTP) of the given security.\n"
                "2. Place a BUY market order using Dhan API.\n"
                "3. dhan.place_order(security_id,           \n"
                "    exchange_segment=dhan.NSE_EQ,\n"
                "    transaction_type=dhan.BUY,\n"
                "    quantity=1,\n"
                "    order_type=dhan.MARKET,\n"
                "    product_type=dhan.INTRA,\n"
                "    price=0)\n"
                "4. Implement retry logic: If the order fails, retry once (total 2 attempts).\n"
                "5. Print the details of the order placed (including symbol, LTP, quantity, and order status).\n\n"
                "Assume you have access to the Dhan API using proper authentication.\n\n"
                "Note: Use placeholder functions/mock the API if actual credentials are not available. Focus on correct structure and logic."
            ),
            "expected_output":
                "Order Placed:\n"
                "Symbol: <symbol>\n"
                "LTP: <last_traded_price>\n"
                "Quantity: 1\n"
                "Order Status: <order_status>\n"
        }
    ]

class RegisterModel1(BaseModel):
    name: str
    email: str
    phone: str
    position_applied: str
    dhan_client_id: str
    dhan_access_token: str

class AttemptModel(BaseModel):
    user_id: int
    code: str
    question_idx: int

def send_hr_email(user_id):
    """
    Compose a .txt report (UTF-8 safe, for Unicode characters like ₹)
    and email it to HR as an attachment using Resend.
    For unanswered questions, includes 'Not Attempted'.
    """
    import tempfile

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM candidate1 WHERE user_id=?", (user_id,))
    candidate = cur.fetchone()
    if not candidate:
        return
    cur.execute(
        "SELECT question_idx, code, output FROM attempt WHERE user_id=? ORDER BY question_idx", (user_id,)
    )
    attempts = cur.fetchall()
    questions = get_exam_questions()

    attempt_map = {a["question_idx"]: a for a in attempts}
    txt_lines = []
    txt_lines.append("=== Candidate Exam Submission Report ===\n")
    txt_lines.append(f"Name: {candidate['name']}")
    txt_lines.append(f"Email: {candidate['email']}")
    txt_lines.append(f"Phone: {candidate['phone']}")
    txt_lines.append(f"Position Applied: {candidate['position_applied']}")
    txt_lines.append(f"Dhan Client ID: {candidate['dhan_client_id']}")
    txt_lines.append(f"Dhan Access Token: {candidate['dhan_access_token']}")
    txt_lines.append(f"Submitted at: {candidate['reg_time']}\n")
    for idx in range(len(questions)):
        txt_lines.append(f"\n--- Question {idx+1} ---")
        txt_lines.append(f"Question: {questions[idx]['question']}")
        txt_lines.append(f"Expected Output:\n{questions[idx]['expected_output']}")
        if idx in attempt_map:
            attempt = attempt_map[idx]
            txt_lines.append("Candidate Code:\n" + (attempt["code"] or ""))
            txt_lines.append("Output:\n" + (attempt["output"] or ""))
        else:
            txt_lines.append("Candidate Code:\n[NOT ATTEMPTED]")
            txt_lines.append("Output:\n[NOT ATTEMPTED]")
        txt_lines.append("-" * 36)
    txt_content = "\n".join(txt_lines)

    # Save to a temporary file using UTF-8 encoding
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt", encoding="utf-8") as tf:
        tf.write(txt_content)
        tf.flush()
        temp_txt_path = tf.name

    try:
        resend.api_key = "re_hW5ToeJj_KzXHNfzwsgFVZMZ4f5EYy8NR"
        with open(temp_txt_path, "rb") as f:
            file_bytes = f.read()
        import base64
        file_bytes_b64 = base64.b64encode(file_bytes).decode("utf-8")
        file_payload = {
            "content": file_bytes_b64,
            "filename": f"{candidate['name'].replace(' ', '_')}_exam_report.txt",
            "type": "text/plain"
        }
        text_body = (
            f"Dear HR,\n\n"
            f"Please find attached the detailed submission report for candidate: {candidate['name']}.\n\n"
            "Regards,\nExam System"
        )
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": ["roopamugappa@gmail.com"],
            "subject": f"Python Exam Submission: {candidate['name']}",
            "text": text_body,
            "attachments": [file_payload]
        })
    except Exception as e:
        print(f"Error sending email via resend: {e}")
    finally:
        try:
            os.remove(temp_txt_path)
        except Exception:
            pass

@app.get("/", response_class=HTMLResponse)
def home():
    tl_words = [
        "TIME", "LINE", "INVESTMENT", "PRIVATE", "LIMITED"
    ]
    header_html = '<div style="text-align:center;margin-bottom:10px;margin-top:8px;font-family:sans-serif;"><span style="font-size:2.1em;font-weight:bold;">'
    for word in tl_words:
        header_html += f'<span style="color: red;">{word[0]}</span><span style="color: black;">{word[1:]}</span> '
    header_html += '</span></div>'
    sub_header_html = '<div style="text-align:center;margin-bottom:23px;"><span style="font-size:1.25em;color:#333;font-weight:500;letter-spacing:0.03em;">Candidate Selection Process</span></div>'

    return f"""
    <html style="height: 100%;">
      <head>
        <title>Register for Python Exam</title>
        <style>
          html, body {{
            height: 100%;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            width: 100vw;
          }}
          body {{
            font-family: sans-serif;
            width: 100vw;
            height: 100vh;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: #f9fbfd;
          }}
          .register-panel {{
            box-shadow: 0 1px 5px #e0e0e8;
            background: #fff;
            border-radius: 10px;
            padding: 36px 45px;
            min-width: 320px;
            max-width: 98vw;
            width: 420px;
            margin: 0;
          }}
          @media (max-width: 500px) {{
            .register-panel {{
              padding: 18px 2vw;
              width: 98vw;
            }}
          }}
        </style>
      </head>
      <body>
        <div class="register-panel">
          {header_html}
          {sub_header_html}
          <form action='/register' method='post'>
            <label>Name:<br>
                <input style="width:95%;font-size:1.1em;" type='text' name='name' required>
            </label><br><br>
            <label>Email:<br>
                <input style="width:95%;font-size:1.1em;" type='email' name='email' required>
            </label><br><br>
            <label>Phone Number:<br>
                <input style="width:95%;font-size:1.1em;" type='text' name='phone' pattern="[\d ]{{7,}}" required>
            </label><br><br>
            <label>Position to Apply:<br>
                <input style="width:95%;font-size:1.1em;" type='text' name='position_applied' required>
            </label><br><br>
            <label>Dhan Client ID (provided by HR):<br>
                <input style="width:95%;font-size:1.1em;" type='text' name='dhan_client_id' required>
            </label><br><br>
            <label>Dhan Access Token (provided by HR):<br>
                <input style="width:95%;font-size:1.1em;" type='text' name='dhan_access_token' required>
            </label><br><br>
            <input type='submit' value='Register' style="width:100%;font-size:1.15em;padding:12px 0;background:#1560bd;color:#fff;border:none;border-radius:5px;">
          </form>
        </div>
      </body>
    </html>
    """

@app.post("/register", response_class=HTMLResponse)
async def register(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    position_applied: str = Form(...),
    dhan_client_id: str = Form(...),
    dhan_access_token: str = Form(...)
):
    conn = get_db()
    cur = conn.cursor()
    # Check if this email or phone is already in candidate1.
    cur.execute(
        "SELECT user_id, email, phone FROM candidate1 WHERE lower(email) = lower(?) OR phone = ? COLLATE NOCASE",
        (email.strip(), phone.strip())
    )
    existing = cur.fetchone()
    if existing:
        # Render Already Registered message
        conn.close()
        return HTMLResponse("""
        <html>
        <body style='font-family:sans-serif;background:#fcf6f6;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;'>
            <div style='background:#fff;box-shadow:0 1.5px 9px #eee;border-radius:14px;padding:38px 26px;width:98vw;max-width:420px;'>
                <h2 style='color:#b72600;text-align:center;'>Exam Already Taken</h2>
                <p style='color:#444;font-size:1.13em;text-align:center;'>A candidate with this email or phone number has already registered and cannot take the exam again.</p>
                <p style='text-align:center;'><a href='/' style='color:#145db2;font-weight:bold;'>Return to Home</a></p>
            </div>
        </body>
        </html>
        """, status_code=409)
    cur.execute(
        "INSERT INTO candidate1 (name, email, phone, position_applied, dhan_client_id, dhan_access_token, reg_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, email, phone, position_applied, dhan_client_id, dhan_access_token, datetime.datetime.now().isoformat())
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    instructions_html = f"""
    <html>
      <head>
        <title>Exam Instructions - Python Coding Exam</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {{
            font-family: sans-serif;
            background: #f2f6fc;
            margin:0;
            padding:0;
            display:flex;
            flex-direction:column;
            min-height:100vh;
          }}
          .instructions-panel {{
            background: #fff;
            margin: 50px auto 0 auto;
            box-shadow: 0 2px 8px #cbe6f7;
            border-radius: 10px;
            max-width: 600px;
            width: 95vw;
            padding: 30px 26px 20px 26px;
            box-sizing: border-box;
          }}
          .instructions-panel h2 {{
            text-align:center;
          }}
          .instructions-list {{
            margin: 14px 0 16px 0;
            font-size: 1.11em;
            color: #223366;
          }}
          .checkbox-wrap {{
            margin: 24px 0 12px 0;
            display: flex;
            align-items: center;
          }}
          .start-btn {{
            padding: 10px 38px;
            font-size: 1.11em;
            border: none;
            border-radius: 5px;
            background: #1460b1;
            color: #fff;
            font-weight: 600;
            cursor: pointer;
            margin-left: 0;
          }}
          .start-btn[disabled] {{
            opacity: 0.65;
            background: #bbbbbb;
            cursor: not-allowed;
          }}
          @media (max-width:700px) {{
            .instructions-panel {{
              margin: 13vw 0 0 0;
              padding: 11px 2vw;
              max-width: 99vw;
            }}
          }}
        </style>
      </head>
      <body>
        <div class="instructions-panel">
          <h2>Exam Instructions</h2>
          <ul class="instructions-list">
            <li>The exam consists of several programming questions.</li>
            <li>No use of internet, books, notes, mobile phones, or calculators is permitted during the exam.</li>
            <li>You have to attempt each question in sequence (direct navigation is restricted).</li>
            <li><b>Anti-cheating:</b> Switching browser tabs or copying/pasting code will result in warnings, and after 5 violations, your exam will be forcibly closed.</li>
            <li>Do <b>not</b> refresh or close your browser during the exam; your progress may be lost.</li>
            <li>Each question has its own expected output panel for reference.</li>
            <li>You may use the 'Run Code' button to check your code output before final submission.</li>
            <li>Click the checkbox below to confirm you have read and understood the instructions.</li>
          </ul>
          <form method="get" action="/start_exam">
            <input type="hidden" name="user_id" value="{user_id}">
            <div class="checkbox-wrap">
              <input type="checkbox" id="agree" name="agree" value="yes" onchange="document.getElementById('startbtn').disabled=!this.checked">
              <label for="agree" style="margin-left:9px;user-select:none;cursor:pointer;">I have read and understood the instructions.</label>
            </div>
            <button id="startbtn" type="submit" class="start-btn" disabled>Start Exam</button>
          </form>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(instructions_html)

@app.get("/start_exam")
async def start_exam(user_id: int, agree: Optional[str] = None):
    if agree != "yes":
        return HTMLResponse(
            "<h3 style='font-family:sans-serif;color:red;margin:2vw;'>You must check the confirmation box before starting the exam.<br><a href='/'>Return to Home</a></h3>",
            status_code=403,
        )
    return RedirectResponse(url=f"/question?user_id={user_id}&question_idx=0", status_code=302)

@app.get("/question")
async def jump_question(user_id: int, question_idx: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT code FROM attempt WHERE user_id=? AND question_idx=? ORDER BY created DESC LIMIT 1", (user_id, question_idx))
    row = cur.fetchone()
    cur.execute("SELECT dhan_client_id, dhan_access_token FROM candidate1 WHERE user_id=?", (user_id,))
    creds = cur.fetchone()
    conn.close()
    last_code = row["code"] if row else ""
    dhan_client_id, dhan_access_token = (creds["dhan_client_id"], creds["dhan_access_token"]) if creds else ("", "")
    return HTMLResponse(render_question(user_id, question_idx, last_code, dhan_client_id, dhan_access_token))

@app.post("/skip", response_class=HTMLResponse)
async def skip_question(
    user_id: str = Form(...),
    question_idx: str = Form(...)
):
    try:
        uid = int(user_id)
        q_idx = int(question_idx)
        # Mark the skip as an attempt with special code/output, only if not already submitted for this q_idx
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM attempt WHERE user_id=? AND question_idx=?", (uid, q_idx))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO attempt (user_id, question_idx, code, output, created) VALUES (?, ?, ?, ?, ?)",
                (uid, q_idx, "[SKIPPED]", "[SKIPPED]", datetime.datetime.now().isoformat())
            )
            conn.commit()
        conn.close()
        # Move to next question
        questions = get_exam_questions()
        if q_idx + 1 >= len(questions):
            # On skip at last question, before marking exam as submitted, fill in [NOT ATTEMPTED] for all unanswered questions
            fill_notattempted(uid, len(questions))
            send_hr_email(uid)
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("INSERT INTO exam_completion (user_id, completed_at) VALUES (?, ?)", (uid, datetime.datetime.now().isoformat()))
                conn.commit()
                conn.close()
            except:
                pass
            return RedirectResponse(f"/submit_exam?user_id={uid}", status_code=302)
        # Prefill credentials for next question if required
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT dhan_client_id, dhan_access_token FROM candidate1 WHERE user_id=?", (uid,))
        creds = cur.fetchone()
        conn.close()
        dhan_client_id = creds["dhan_client_id"] if creds else ""
        dhan_access_token = creds["dhan_access_token"] if creds else ""
        return render_question(uid, q_idx + 1, "", dhan_client_id, dhan_access_token)
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return HTMLResponse(f"<h3>Oops, error occurred during skipping.<br>Error: {e}</h3><pre>{trace}</pre>", status_code=500)

def fill_notattempted(user_id, num_questions):
    # This helper will insert [NOT ATTEMPTED] for all questions not yet in attempt for the given user
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT question_idx FROM attempt WHERE user_id=?", (user_id,))
    existing = set([row["question_idx"] for row in cur.fetchall()])
    now = datetime.datetime.now().isoformat()
    for idx in range(num_questions):
        if idx not in existing:
            cur.execute(
                "INSERT INTO attempt (user_id, question_idx, code, output, created) VALUES (?, ?, ?, ?, ?)",
                (user_id, idx, "[NOT ATTEMPTED]", "[NOT ATTEMPTED]", now)
            )
    conn.commit()
    conn.close()

def render_question(user_id, question_idx, last_code="", dhan_client_id=None, dhan_access_token=None):
    questions = get_exam_questions()
    total = len(questions)
    if question_idx >= total:
        # Before final submit, ensure all unanswered questions are marked as NOT ATTEMPTED
        fill_notattempted(user_id, total)
        send_hr_email(user_id)
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO exam_completion (user_id, completed_at) VALUES (?, ?)", (user_id, datetime.datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except:
            pass
        return RedirectResponse(f"/submit_exam?user_id={user_id}", status_code=302)
    if dhan_client_id is None or dhan_access_token is None:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT dhan_client_id, dhan_access_token FROM candidate1 WHERE user_id=?", (user_id,))
        creds = cur.fetchone()
        conn.close()
        if creds:
            dhan_client_id = creds["dhan_client_id"]
            dhan_access_token = creds["dhan_access_token"]
        else:
            dhan_client_id = ""
            dhan_access_token = ""
    q = questions[question_idx]["question"]
    expected_output = questions[question_idx].get("expected_output", "")

    code_default = ""
    if last_code:
        preload = f"document.getElementById('code').value = {repr(last_code)};"
    else:
        if dhan_client_id or dhan_access_token:
            code_default = f'''# Your Dhan API credentials from registration:\nclient_id = "{dhan_client_id or ''}"\naccess_token = "{dhan_access_token or ''}"\n\n'''
        preload = f'document.getElementById("code").value = {repr(code_default)};'

    tl_words = [
        "TIME", "LINE", "INVESTMENT", "PRIVATE", "LIMITED"
    ]
    header_html = '<div style="text-align:center;margin-bottom:8px;margin-top:6px;font-family:sans-serif;"><span style="font-size:1.73em;font-weight:bold;">'
    for word in tl_words:
        header_html += f'<span style="color: red;">{word[0]}</span><span style="color: black;">{word[1:]}</span> '
    header_html += '</span></div>'
    sub_header_html = '<div style="text-align:center;margin-bottom:14px;"><span style="font-size:1.08em;color:#333;font-weight:500;letter-spacing:0.03em;">Candidate Selection Process</span></div>'

    qbar_html = '<div id="qnav" style="text-align:center;padding:10px 0 12px 0;">'
    for idx in range(total):
        selected = "background:#145db2;color:#fff" if idx == question_idx else "background:#e2e8fc;color:#222"
        qbar_html += f"""<button type="button" onclick="jumpToQuestion({idx})" style="margin:0 5px 0 0;padding:8px 17px;font-size:1.04em;border-radius:5px;border:1px solid #145db2;{selected};cursor:pointer;min-width:46px;font-weight:600;">Q{idx+1}</button>"""
    qbar_html += "</div>"

    # ANTI-CHEAT JS LOGIC: Adjusted so that submit/skip/Run Code clicks are not considered as violation.
    anticheat_js = """
    <script>
    (function() {
        // Track user actions that should "legitimately" blur or hide the page, such as submit/skip/run buttons.
        let allowAntiCheatClear = false;
        // Utility: Attach event to a selector to set allowAntiCheatClear flag for next blur/visibilitychange
        function clearViolationForClick(ids) {
            ids.forEach(function(id) {
                var el = document.getElementById(id);
                if (el) {
                    el.addEventListener('click', function(e){
                        allowAntiCheatClear = true;
                        // Make sure it resets shortly after
                        setTimeout(() => { allowAntiCheatClear = false; }, 1800); // allow up to 1.8 seconds for action
                    }, true);
                }
            });
        }
        // Run this on DOM load
        document.addEventListener('DOMContentLoaded', function() {
            // Main submit button in .submitForm
            clearViolationForClick(['submitForm']);
            // The skip button form
            clearViolationForClick(['skipForm']);
            // The Run Code button
            clearViolationForClick(['runCodeBtn']);
            // Any "Next" button, if present. (Optional: any button you want user to legitimately click)
            // If your html uses name or id for other buttons, add here
        });

        function getOrCreateTabId() {
            if (!window.sessionStorage) return "default";
            var tid = window.sessionStorage.getItem("exam_tabid");
            if (!tid) {
                tid = Math.random().toString(36).substring(2) + Date.now().toString(36);
                window.sessionStorage.setItem("exam_tabid", tid);
            }
            return tid;
        }
        var tabid = getOrCreateTabId();
        function violateKey() { return "exam_violations:" + tabid; }
        function getViolationCount() {
            if (!window.sessionStorage) return 0;
            var n = window.sessionStorage.getItem(violateKey());
            return n ? parseInt(n, 10) : 0;
        }
        function setViolationCount(n) {
            if (!window.sessionStorage) return;
            window.sessionStorage.setItem(violateKey(), n.toString());
        }
        function hardCrashExam() {
            document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;"><div style="background:#fff;padding:44px 34px;font-family:sans-serif;border-radius:12px;box-shadow:0 2px 10px #f2caca;text-align:center;"><h2 style="color:#b00716;">Exam Terminated</h2><p style="font-size:1.18em;">Your exam was forcibly closed due to 5 anti-cheating violations (tab switch or copy-paste).</p><p style="color:#ca3f1a;font-size:1.06em;">Please contact the test supervisor.</p></div></div>';
            document.body.style.background = "#ffe6e6";
            try { document.querySelectorAll("input,button,textarea").forEach(function(e){ e.disabled = true; }); } catch(e){}
            setTimeout(function(){
                window.close();
                setTimeout(function(){
                    window.location.replace("about:blank");
                },700);
            }, 1600);
            throw new Error('Exam forcibly closed due to 5 violations.');
        }
        function incrementViolation(reason) {
            var count = getViolationCount();
            var confirmText = "Warning #" + (count+1) + " of 5: " + reason + "\\nYou are not allowed to switch tabs or use copy/paste/select all.\\n\\nClick OK if action was accidental -- the violation will NOT be counted;\\nClick Cancel if you admit this was a violation -- the violation WILL be counted.";
            var ok = window.confirm(confirmText);
            if (ok) {
                // User claims accidental, do NOT increment
                return;
            }
            count += 1;
            setViolationCount(count);
            if (count < 5) {
                alert("Violation acknowledged. Counted #" + count + " of 5. After 5, your exam will be forcibly closed.");
            } else if (count === 5) {
                if (window.confirm("Violation acknowledged. Counted #" + count + " of 5. This was your last warning. The exam will now terminate.\\nClick OK to close this page.")) {
                    hardCrashExam();
                } else {
                    setTimeout(hardCrashExam, 200);
                }
            }
        }
        function handlePasteCutCopyContext(evtName, humanLabel) {
            document.addEventListener(evtName, function(e){
                incrementViolation(humanLabel + " is not allowed during the exam.");
                e.preventDefault();
                return false;
            }, true);
        }
        document.addEventListener('DOMContentLoaded', function() {
            handlePasteCutCopyContext('copy', 'Copy');
            handlePasteCutCopyContext('paste', 'Paste');
            handlePasteCutCopyContext('cut', 'Cut');
            handlePasteCutCopyContext('contextmenu', 'Right-click');
            document.addEventListener('keydown', function(e){
                if ((e.ctrlKey || e.metaKey) && [65,67,86,88].includes(e.keyCode)) {
                    incrementViolation("Keyboard shortcut for Copy/Paste/Select All/Cut is disabled.");
                    e.preventDefault();
                    return false;
                }
            }, true);
            var code = document.getElementById('code');
            if (code) {
                code.addEventListener('focus', function() {
                    // Optionally handle per-question logic
                });
            }
        });
        // ---- Improved anti-tab switch detection ----
        // Track focus and visibility state robustly

        var isWindowVisible = true;
        var lastFocus = performance.now(), tabLossTimeout = null;

        // Use focus/blur on window (reliable in most browsers)
        window.addEventListener('blur', function () {
            setTimeout(function () {
                if (!document.hasFocus()) {
                    // Before increment violation, check allowAntiCheatClear.
                    if (!allowAntiCheatClear) {
                        isWindowVisible = false;
                        incrementViolation("Tab/window switch detected (blur/loss of focus).");
                    }
                }
            }, 240);
        });

        window.addEventListener('focus', function () {
            isWindowVisible = true;
            lastFocus = performance.now();
        });

        // Also listen for visibilitychange (consistent across tabs/minimized)
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) {
                if (!allowAntiCheatClear) {
                    isWindowVisible = false;
                    incrementViolation("Tab/window switch detected (visibilitychange, browser tab left).");
                }
            } else {
                isWindowVisible = true;
                lastFocus = performance.now();
            }
        });

        // Show warning if already have violations
        document.addEventListener('DOMContentLoaded', function() {
            var cnt = getViolationCount();
            if (cnt > 0 && cnt < 5) {
                alert(
                    "Warning: You already have " + cnt + " violation(s) in this exam tab. On 5, your exam will close."
                );
            }
        });

        // Prevent printscreen
        document.addEventListener('keydown', function(e){
            if (e.keyCode === 44) { // PrtSc (PrintScreen)
                incrementViolation("PrintScreen is disabled.");
                e.preventDefault();
                return false;
            }
        }, true);
    })();
    </script>
    """

    webcam_html = ""
    webcam_script = f"""
    <script>
    window.onload = function() {{
        {preload}
        var examBox = document.querySelector('.exam-box');
        if (examBox) {{
            examBox.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
    }};
    </script>
    """

    is_last_question = (question_idx + 1) >= total
    submit_button_text = "Next →" if not is_last_question else "Submit Exam"
    submit_button_color = "#fa8202" if not is_last_question else "#218838"
    # Add id for submit and skip buttons for anti-cheat flag use.
    submit_button_html = f'''<button id="submitForm" type='submit' style='margin-top:9px;font-size:1.09em;background:{submit_button_color};color:#fff;padding:8px 20px;border:none;border-radius:4px;'
            >{submit_button_text}</button>'''

    skip_button_html = f'''
    <form id="skipForm" action="/skip" method="post" style="display:inline;margin-left:18px;" onsubmit="return confirmSkip();">
        <input type="hidden" name="user_id" value="{user_id}">
        <input type="hidden" name="question_idx" value="{question_idx}">
        <button type="submit" style="font-size:1.07em;background:#b6bac3;color:#000;border:none;padding:7px 22px;border-radius:4px;cursor:pointer;">Skip Question</button>
    </form>
    '''

    # For Run Code, ensure a unique id is present for anti-cheat allow
    return f"""
    <html style="height: 100%;">
      <head>
        <title>Python Exam - Question {question_idx+1}/{total}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          html, body {{
            min-height: 100vh;
            width: 100vw;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }}
          body {{
            font-family:sans-serif;
            width:100vw;
            margin:0;
            padding:0;
            background:#f7fafc;
            display:flex;
            flex-direction:column;
            justify-content:flex-start;
            align-items:stretch;
            min-height:100vh;
            box-sizing: border-box;
          }}
          .container-root {{
            box-sizing:border-box;
            margin:0;
            padding:0;
            width:100vw;
            min-height:100vh;
            display:flex;
            flex-direction:column;
            justify-content:flex-start;
            align-items:stretch;
          }}
          .headline-bar {{
            width:100%;
            background:#11459c;
            color:#fff;
            font-size:1.25em;
            font-weight:600;
            padding:10px 0;
            margin-bottom:0;
            text-align:center;
            letter-spacing:0.03em;
            box-shadow:0 2px 5px #dde4f7;
            position:sticky;
            top:0;
            z-index:100;
          }}
          .exam-content-outer {{
            flex:1 1 auto;
            display: flex;
            flex-direction:column;
            justify-content:flex-start;
            align-items:center;
            min-height:0;
            width:100vw;
            box-sizing:border-box;
            padding-bottom: 30px;
          }}
          .exam-box {{
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 1.2px 8px #e0e0ef;
            padding: 30px 16px 18px 16px;
            width: 95vw;
            max-width: 980px;
            min-width: 0;
            box-sizing: border-box;
            margin: 16px auto 0 auto;
            flex:0 1 auto;
          }}
          .flex-row-panel {{
            display: flex;
            gap: 13px;
            flex-wrap: wrap;
            width: 100%;
            box-sizing: border-box;
            margin-bottom: 17px;
          }}
          .panel-box {{
            background: #f6f8fa;
            border-radius: 6px;
            padding: 13px 10px 14px 10px;
            margin-bottom: 2px;
            flex: 1 1 260px;
            min-width: 200px;
            border: 1.5px solid #e1e3ec;
            box-shadow: 0 1px 2.5px #eee;
            box-sizing: border-box;
            max-height: 320px;
            display: flex;
            flex-direction: column;
          }}
          .panel-title {{
            font-size:1.08em; padding-bottom:5px; margin-bottom:7px; border-bottom:1px solid #e0e0ef;font-weight:bold;
            color:#285197;
            flex: 0 0 auto;
          }}
          .panel-question-content, .panel-output-content {{
            font-family:inherit;
            font-size:1em;
            overflow-y: auto;
            flex: 1 1 auto;
            min-height: 0;
            max-height: 230px;
            padding-right: 1px;
            scrollbar-color: #d1d1e0 #f6f8fa;
            scrollbar-width: thin;
          }}
          .panel-output-content {{
            font-family:monospace;
            font-size:1.06em;
          }}
          .panel-question-content::-webkit-scrollbar, .panel-output-content::-webkit-scrollbar {{
            width:10px;
            background: #eee;
          }}
          .panel-question-content::-webkit-scrollbar-thumb, .panel-output-content::-webkit-scrollbar-thumb {{
            background: #c4c4d5;
            border-radius: 7px;
          }}
          #code {{
            width: 100%;
            min-height: 120px;
            max-height: 300px;
            height: 170px;
            font-family: monospace;
            font-size: 1.07em;
            border-radius: 7px;
            border: 1.2px solid #888;
            padding: 8px 10px;
            resize: vertical;
            box-sizing: border-box;
            overflow: auto;
            background: #f9f9fb;
            display: block;
          }}
          #code::-webkit-scrollbar {{
            width: 10px;
            background: #eee;
          }}
          #code::-webkit-scrollbar-thumb {{
            background: #ddd;
            border-radius: 6px;
          }}
          #result {{
            background: #212121;
            color: #fafafa;
            padding: 10px;
            border-radius: 8px;
            font-size: 1em;
            white-space: pre-wrap;
            min-height: 55px;
            max-height: 180px;
            overflow-y: auto;
            overflow-x: auto;
            margin-top: 6px;
            margin-bottom: 0.7em;
            box-sizing: border-box;
            display: block;
          }}
          #result::-webkit-scrollbar {{
            width: 10px;
            background: #333;
          }}
          #result::-webkit-scrollbar-thumb {{
            background: #444;
            border-radius: 6px;
          }}
          @media (max-width: 1280px) {{
            .exam-box {{ max-width: 99vw; }}
          }}
          @media (max-width: 960px) {{
            .flex-row-panel {{ flex-direction: column; }}
            .exam-box {{ padding:10px 1vw 13px 1vw; min-width:0;}}
          }}
          @media (max-width: 800px) {{
              .panel-box {{ max-height: 220px; }}
              .panel-question-content, .panel-output-content {{ max-height: 105px; font-size:0.99em; }}
              #code {{
                  height: 110px;
                  min-height: 80px;
                  max-height: 200px;
              }}
              #result {{
                  min-height: 36px;
                  max-height: 120px;
              }}
              .exam-box {{ padding:5px 0.5vw 7px 0.5vw; min-width:0;}}
          }}
          body, html {{
            overflow-x: hidden;
            overflow-y: auto;
          }}
        </style>
      </head>
      <body>
        <div class="container-root">
          {header_html}
          {sub_header_html}
          {qbar_html}
          <div class="exam-content-outer">
            <div class="exam-box">
              <h2 style='margin-top:0.15em;margin-bottom:17px;'>Question {question_idx + 1} of {total}</h2>
              <div class='flex-row-panel'>
                <div class='panel-box'>
                  <div class='panel-title'>Question</div>
                  <div class='panel-question-content'>{q.replace('\n', '<br>')}</div>
                </div>
                <div class='panel-box'>
                  <div class='panel-title'>Expected Output</div>
                  <div class='panel-output-content'>{expected_output.replace('\n','<br>')}</div>
                </div>
              </div>
              <textarea id='code' placeholder='Write your code here...'></textarea>
              <br>
              <button id='runCodeBtn' type='button' onclick='runCode()' style='font-size:1em;padding:10px 23px;background:#058a14;color:#fff;border-radius:4px;border:none;cursor:pointer;'>Run Code</button>
              <span id='runstatus' style='margin-left:1.2em;font-weight:bold;'></span>
              <div style='margin-top:12px;'>
                  <b>Output:</b>
                  <pre id='result'></pre>
              </div>
              <form id='submitForm' action='/submit' method='post' onsubmit='return onSubmitForm();' style="display:inline;">
                  <input type='hidden' name='user_id' value='{user_id}'>
                  <input type='hidden' name='question_idx' value='{question_idx}'>
                  <input type='hidden' name='code' id='codeinput'>
                  <input type='hidden' name='output' id='outputinput'>
                  {submit_button_html}
              </form>
              {skip_button_html}
              <div style="margin-top:18px;color:#8a1717;font-size:0.99em;"><b>Note:</b> Use the 'Skip Question' button if you wish not to attempt this question now. You cannot come back to skipped questions in this exam.</div>
            </div>
          </div>
        </div>
        {webcam_html}
        <script>
        function jumpToQuestion(idx) {{
            var codeVal = document.getElementById('code').value;
            var userId = document.querySelector('input[name="user_id"]').value;
            var goUrl = '/question?user_id=' + encodeURIComponent(userId) + '&question_idx=' + idx;
            window.location = goUrl;
        }}
        function runCode() {{
          document.getElementById('runstatus').innerText = 'Running...';
          document.getElementById('result').innerText = '';
          fetch('/run_code', {{
            method: "POST",
            headers: {{"Content-Type": "application/json"}},
            body: JSON.stringify({{"code": document.getElementById('code').value}})
          }})
            .then(resp => resp.json())
            .then(function(data) {{
              document.getElementById('result').innerText = data.output;
              document.getElementById('runstatus').innerText = data.error ? 'Error' : 'Success';
              document.getElementById('codeinput').value = document.getElementById('code').value;
              document.getElementById('outputinput').value = data.output;
            }});
        }}
        function onSubmitForm() {{
            var codeVal = document.getElementById('code').value;
            var outputVal = document.getElementById('result').innerText;
            if (!codeVal && {int(is_last_question)} && {int(total)>0}) {{
                return true;
            }}
            if (!codeVal) {{
                alert("Please write some code before submitting.");
                return false;
            }}
            document.getElementById('codeinput').value = codeVal;
            document.getElementById('outputinput').value = outputVal;
            return true;
        }}
        function confirmSkip() {{
            return confirm("Are you sure you want to skip this question? You will not be able to return to it later in this exam.");
        }}
        </script>
        {anticheat_js}
        {webcam_script}
      </body>
    </html>
    """

@app.get("/submit_exam", response_class=HTMLResponse)
def submit_exam(user_id: int):
    return """
    <html style="height:100%;">
    <body style='font-family:sans-serif;width:100vw;height:100vh;margin:0;padding:0;display:flex;flex-direction:column;justify-content:center;align-items:center;'>
    <div style='background:#fff;box-shadow:0 1px 5px #e0e0ee;border-radius:12px;padding:48px 28px;width:98vw;max-width:540px;'>
    <h2 style='text-align:center'>Thank you! You have submitted your exam.</h2>
    <p>All your answers have been sent to HR.</p>
    <a href='/' style="color:#145db2;font-size:1.18em;font-weight:bold;">Register Another</a>
    </div>
    </body></html>
    """

@app.post("/run_code")
async def runcode(payload: dict):
    code = payload.get("code", "")
    max_time = 3
    output = ""
    try:
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write(code)
            f.flush()
            tempname = f.name
        try:
            out = subprocess.run(
                [sys.executable, tempname],
                capture_output=True, text=True, timeout=max_time
            )
            output = (out.stdout or "") + (("\n" + out.stderr) if out.stderr else "")
            error = False
        except subprocess.TimeoutExpired:
            output = f"Error: Code timed out (> {max_time}s)"
            error = True
        except Exception as e:
            output = f"Error: {e}"
            error = True
        finally:
            try:
                os.unlink(tempname)
            except Exception:
                pass
    except Exception as e:
        output = f"Infra Error: {e}"
        error = True
    if len(output) > 1000:
        output = output[:1000] + "\n[Output Truncated]"
    return JSONResponse(content={"output": output, "error": error})

@app.post("/submit", response_class=HTMLResponse)
async def submit(
    user_id: str = Form(...),
    question_idx: str = Form(...),
    code: str = Form(...),
    output: str = Form(...)
):
    try:
        conn = get_db()
        cur = conn.cursor()
        q_idx = int(question_idx)
        uid = int(user_id)
        cur.execute(
            "INSERT INTO attempt (user_id, question_idx, code, output, created) VALUES (?, ?, ?, ?, ?)",
            (uid, q_idx, code, output, datetime.datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        questions = get_exam_questions()
        if q_idx + 1 >= len(questions):
            fill_notattempted(uid, len(questions))
            send_hr_email(uid)
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("INSERT INTO exam_completion (user_id, completed_at) VALUES (?, ?)", (uid, datetime.datetime.now().isoformat()))
                conn.commit()
                conn.close()
            except:
                pass
            return RedirectResponse(f"/submit_exam?user_id={uid}", status_code=302)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT dhan_client_id, dhan_access_token FROM candidate1 WHERE user_id=?", (uid,))
        creds = cur.fetchone()
        conn.close()
        dhan_client_id = creds["dhan_client_id"] if creds else ""
        dhan_access_token = creds["dhan_access_token"] if creds else ""
        return render_question(uid, q_idx + 1, "", dhan_client_id, dhan_access_token)
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return HTMLResponse(f"<h3>Oops, error occurred during submission.<br>Error: {e}</h3><pre>{trace}</pre>", status_code=500)
