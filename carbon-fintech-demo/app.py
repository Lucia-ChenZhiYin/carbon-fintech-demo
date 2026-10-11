from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import hashlib
import os
from pdf_parser import parse_document

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_id TEXT,
            company_name TEXT,
            invoice_num TEXT,
            amount REAL,
            file_name TEXT,
            file_hash TEXT,
            tss_score REAL,
            w1_env REAL,
            w2_cred REAL,
            w3_imp REAL,
            rate_discount TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 🧮 企劃書全動態 TSS 算力引擎 (防偽嚴格阻斷)
def calculate_tss_engine(amount, is_duplicate=False, has_green_cert=True, align_po_inv=True):
    # W1: 交易環境表現 (50%)
    base_env = 60.0
    amount_factor = min(15.0, (amount / 1000000.0) * 1.8)
    mat_score = 10.0 + round(amount_factor, 1)
    energy_score = 14.5 if has_green_cert else 4.0
    logistics_score = 4.5
    w1_env = min(100.0, base_env + mat_score + energy_score + logistics_score)

    # W2: 資料可信度 (30%) - ⚠️ 重複融資重扣至 0 分 (極端風控機制)
    if is_duplicate:
        w2_cred = 0.0  # 判定重複進件，可信度直接歸零！
    else:
        base_cred = 70.0
        cross_check_score = 15.0 if align_po_inv else 5.0
        cert_score = 15.0 if has_green_cert else 0.0
        w2_cred = min(100.0, max(0.0, base_cred + cross_check_score + cert_score))

    # W3: 永續改善幅度 (20%)
    carbon_reduction_rate = min(22.0, 8.0 + (amount / 800000.0))
    w3_imp = min(100.0, max(0.0, 60.0 + (2.0 * carbon_reduction_rate)))

    # 綜合總分
    tss_score = round((w1_env * 0.50) + (w2_cred * 0.30) + (w3_imp * 0.20), 1)

    # 綠色金融授信門檻 (企劃書表 2-2)
    if is_duplicate or tss_score < 70.0:
        rate_discount = "0.00% (不給予優惠)"
    elif tss_score >= 85.0:
        rate_discount = "-0.35%"
    elif tss_score >= 70.0:
        rate_discount = "-0.15%"
    else:
        rate_discount = "0.00%"

    return tss_score, round(w1_env, 1), round(w2_cred, 1), round(w3_imp, 1), rate_discount

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 1")
    latest_tx = cursor.fetchone()
    conn.close()

    if not latest_tx:
        tx_data = {
            "tx_id": "TX-20261009-8829",
            "company_name": "台灣中鋼構股份有限公司",
            "invoice_num": "XX-88291034",
            "amount": "5,250,000",
            "file_name": "電子發票_INV-20261009.pdf",
            "tss_score": 88.1,
            "w1_env": 95.0,
            "w2_cred": 99.0,
            "w3_imp": 89.1,
            "rate_discount": "-0.35%",
            "file_hash": "8f3a9921b7c0d91c",
            "status": "Pending"
        }
    else:
        tx_data = {
            "tx_id": latest_tx[1],
            "company_name": latest_tx[2],
            "invoice_num": latest_tx[3],
            "amount": f"{latest_tx[4]:,.0f}",
            "file_name": latest_tx[5],
            "file_hash": latest_tx[6][:16] if latest_tx[6] else "",
            "tss_score": latest_tx[7],
            "w1_env": latest_tx[8],
            "w2_cred": latest_tx[9],
            "w3_imp": latest_tx[10],
            "rate_discount": latest_tx[11],
            "status": latest_tx[12]
        }
        
    return render_template('dashboard.html', tx=tx_data)

@app.route('/api/history')
def api_history():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT tx_id, company_name, invoice_num, amount, tss_score, status FROM transactions ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/process_upload', methods=['POST'])
def process_upload():
    uploaded_file = request.files.get('document_file')

    company = "台灣中鋼構股份有限公司"
    invoice_num = f"XX-{os.urandom(2).hex().upper()}{os.urandom(2).hex().upper()}"
    amount = 5250000.0

    if uploaded_file and uploaded_file.filename != '':
        filename = uploaded_file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(filepath)

        with open(filepath, 'rb') as f:
            file_bytes = f.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()

        parsed_data = parse_document(filepath)
        if parsed_data["invoice_num"]:
            invoice_num = parsed_data["invoice_num"]
        if parsed_data["amount"]:
            amount = parsed_data["amount"]
        if parsed_data["company_name"]:
            company = parsed_data["company_name"]
    else:
        filename = "電子發票_INV-20261009.pdf"
        file_hash = hashlib.sha256(f"{invoice_num}_{amount}".encode('utf-8')).hexdigest()

    # 🔍 防重複進件檢查 (精準 Hash 與號碼比對)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM transactions WHERE file_hash = ? OR (invoice_num = ? AND invoice_num != '')", (file_hash, invoice_num))
    existing_tx = cursor.fetchone()

    is_duplicate = True if existing_tx else False
    status = 'FLAGGED_DUPLICATE' if is_duplicate else 'Pending'

    # 4. 調用重扣機制算力引擎
    total_score, w1, w2, w3, discount = calculate_tss_engine(amount, is_duplicate=is_duplicate)
    tx_id = f"TX-20261009-{os.urandom(2).hex().upper()}"

    cursor.execute('''
        INSERT INTO transactions 
        (tx_id, company_name, invoice_num, amount, file_name, file_hash, tss_score, w1_env, w2_cred, w3_imp, rate_discount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tx_id, company, invoice_num, amount, filename, file_hash, total_score, w1, w2, w3, discount, status))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)