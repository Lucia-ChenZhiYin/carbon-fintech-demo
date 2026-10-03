from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import hashlib
import os

app = Flask(__name__)

# 設定檔案上傳資料夾
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 1. 初始化 SQLite 資料庫
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

# 2. 動態 TSS 算力引擎邏輯 (根據金額與邏輯計算分數)
def calculate_tss(amount):
    # 根據金額大小微調分數（示範動態計算）
    base_env = 45.0
    base_cred = 28.0
    base_imp = 15.0
    
    # 金額超過 500 萬加強永續權重
    if amount >= 5000000:
        base_imp = 15.0
    else:
        base_imp = 12.0
        
    total_score = base_env + base_cred + base_imp
    rate_discount = "-0.35%" if total_score >= 80 else "-0.15%"
    return round(total_score, 1), base_env, base_cred, base_imp, rate_discount

# 3. 頁面路由設定
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
            "file_name": "範例單據.pdf",
            "tss_score": 88.0,
            "w1_env": 45.0,
            "w2_cred": 28.0,
            "w3_imp": 15.0,
            "rate_discount": "-0.35%",
            "file_hash": "8f3a9921b7c0d91c"
        }
    else:
        tx_data = {
            "tx_id": latest_tx[1],
            "company_name": latest_tx[2],
            "invoice_num": latest_tx[3],
            "amount": f"{latest_tx[4]:,.0f}",
            "file_name": latest_tx[5],
            "file_hash": latest_tx[6][:16],
            "tss_score": latest_tx[7],
            "w1_env": latest_tx[8],
            "w2_cred": latest_tx[9],
            "w3_imp": latest_tx[10],
            "rate_discount": latest_tx[11]
        }
        
    return render_template('dashboard.html', tx=tx_data)

# 4. API：處理真實上傳與動態數據修改
@app.route('/process_upload', methods=['POST'])
def process_upload():
    # 接收前端表單填寫的真實數據
    company = request.form.get('company_name', '台灣中鋼構股份有限公司')
    invoice_num = request.form.get('invoice_num', 'XX-88291034')
    try:
        amount = float(request.form.get('amount', 5250000))
    except ValueError:
        amount = 5250000.0

    # 處理上傳檔案
    uploaded_file = request.files.get('document_file')
    if uploaded_file and uploaded_file.filename != '':
        filename = uploaded_file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(filepath)
        
        # 讀取真實檔案內容並計算真 SHA-256 Hash
        with open(filepath, 'rb') as f:
            file_bytes = f.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()
    else:
        filename = "系統模擬單據.pdf"
        file_hash = hashlib.sha256(f"{invoice_num}_{amount}".encode('utf-8')).hexdigest()

    # 計算 TSS 分數與折扣
    total_score, w1, w2, w3, discount = calculate_tss(amount)
    tx_id = f"TX-20261009-{os.urandom(2).hex().upper()}"
    
    # 寫入 SQLite
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions 
        (tx_id, company_name, invoice_num, amount, file_name, file_hash, tss_score, w1_env, w2_cred, w3_imp, rate_discount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tx_id, company, invoice_num, amount, filename, file_hash, total_score, w1, w2, w3, discount, 'Pending'))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)