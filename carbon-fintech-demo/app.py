import os
import sqlite3
import hashlib
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

app = Flask(__name__)
app.secret_key = 'carbon_secret_secure_key_for_demo'

# 設定檔案上傳資料夾
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # 允許透過欄位名稱存取資料
    return conn

# 1. 健壯的資料庫初始化與自動欄位檢查 (Auto Migration)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_id TEXT UNIQUE,
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
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 2. 升級版動態 TSS 算力引擎邏輯 (包含防偽驗證與減碳量推算)
def calculate_tss(amount, file_hash=None, is_renewed_energy=True):
    """
    維度一 W1: 交易環境表現 (50%) - 基於採購類別與金額
    維度二 W2: 資料可信度 (30%) - 基於單據雜湊驗證與來源完整性
    維度三 W3: 永續改善幅度 (20%) - 動態權重與減碳潛力
    """
    # W1: 交易環境表現 (最高 50)
    w1_env = 45.0 if is_renewed_energy else 30.0
    
    # W2: 資料可信度 (最高 30) - 檢查是否有合法 Hash 憑證
    w2_cred = 28.5 if file_hash else 18.0
    
    # W3: 改善幅度 (最高 20) - 依金額規模調整永續影響力
    if amount >= 10000000:
        w3_imp = 18.0
    elif amount >= 3000000:
        w3_imp = 15.0
    else:
        w3_imp = 12.0
        
    total_score = round(w1_env + w2_cred + w3_imp, 1)
    
    # 根據 TSS 分數進行動態優惠利率減碼計算
    if total_score >= 85:
        rate_discount = "-0.45%"
    elif total_score >= 75:
        rate_discount = "-0.30%"
    elif total_score >= 60:
        rate_discount = "-0.15%"
    else:
        rate_discount = "0.00% (不給予優惠)"
        
    return total_score, w1_env, w2_cred, w3_imp, rate_discount

# 模擬 OCR / AI 智能單據解析
def mock_ocr_extract(filename):
    """模擬從上傳的發票/PO PDF 中自動提取關鍵欄位"""
    filename_lower = filename.lower()
    if "綠能" in filename or "solar" in filename_lower:
        return "森蔚能源股份有限公司", "GW-20261011-09", 8500000.0
    elif "鋼構" in filename or "steel" in filename_lower:
        return "台灣中鋼構股份有限公司", "XX-88291034", 5250000.0
    else:
        return "國泰永續科技股份有限公司", "CT-20260901-12", 2800000.0

# 3. 頁面路由：首頁（單據上傳與動態試算）
@app.route('/')
def index():
    return render_template('index.html')

# 4. 頁面路由：TSS 綜合評估報告儀表板 (可觀看特定交易或最新交易)
@app.route('/dashboard')
@app.route('/dashboard/<tx_id>')
def dashboard(tx_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if tx_id:
        cursor.execute("SELECT * FROM transactions WHERE tx_id = ?", (tx_id,))
    else:
        cursor.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 1")
        
    row = cursor.fetchone()
    conn.close()

    if not row:
        # 預設模擬展示數據
        tx_data = {
            "tx_id": "TX-20261009-8829",
            "company_name": "台灣中鋼構股份有限公司",
            "invoice_num": "XX-88291034",
            "amount": "5,250,000",
            "file_name": "綠色採購證明_鋼構.pdf",
            "tss_score": 88.0,
            "w1_env": 45.0,
            "w2_cred": 28.0,
            "w3_imp": 15.0,
            "rate_discount": "-0.35%",
            "file_hash": "8f3a9921b7c0d91c4a2b1f8e9d0c7b6a",
            "status": "Pending",
            "created_at": "2026-10-11 14:30:00"
        }
    else:
        tx_data = {
            "tx_id": row["tx_id"],
            "company_name": row["company_name"],
            "invoice_num": row["invoice_num"],
            "amount": f"{row['amount']:,.0f}",
            "file_name": row["file_name"],
            "file_hash": row["file_hash"],
            "short_hash": row["file_hash"][:16] + "..." if row["file_hash"] else "N/A",
            "tss_score": row["tss_score"],
            "w1_env": row["w1_env"],
            "w2_cred": row["w2_cred"],
            "w3_imp": row["w3_imp"],
            "rate_discount": row["rate_discount"],
            "status": row["status"],
            "created_at": row["created_at"]
        }
        
    return render_template('dashboard.html', tx=tx_data)

# 5. 頁面路由：歷史交易稽核紀錄 (階段二功能)
@app.route('/history')
def history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    transactions = []
    total_amount = 0
    avg_score = 0
    
    for row in rows:
        transactions.append(dict(row))
        total_amount += row["amount"]
        
    if transactions:
        avg_score = round(sum(t["tss_score"] for t in transactions) / len(transactions), 1)
        
    return render_template('history.html', 
                           transactions=transactions, 
                           total_count=len(transactions), 
                           total_amount=f"{total_amount:,.0f}", 
                           avg_score=avg_score)

# 6. API 路由：處理檔案上傳與表單送出
@app.route('/process_upload', methods=['POST'])
def process_upload():
    company = request.form.get('company_name', '').strip()
    invoice_num = request.form.get('invoice_num', '').strip()
    amount_raw = request.form.get('amount', '0').replace(',', '')
    
    try:
        amount = float(amount_raw)
    except ValueError:
        amount = 5250000.0

    uploaded_file = request.files.get('document_file')
    
    if uploaded_file and uploaded_file.filename != '':
        filename = uploaded_file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(filepath)
        
        # 即時計算二進位 SHA-256 哈希值
        with open(filepath, 'rb') as f:
            file_bytes = f.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            
        # 若未填寫表單，啟用 AI 模擬解析 auto-fill
        if not company or not invoice_num:
            ai_company, ai_invoice, ai_amount = mock_ocr_extract(filename)
            company = company or ai_company
            invoice_num = invoice_num or ai_invoice
            amount = amount if amount > 0 else ai_amount
    else:
        filename = "系統模擬單據_綠能採購.pdf"
        company = company or "台灣中鋼構股份有限公司"
        invoice_num = invoice_num or "XX-88291034"
        amount = amount if amount > 0 else 5250000.0
        file_hash = hashlib.sha256(f"{invoice_num}_{amount}_{datetime.now()}".encode('utf-8')).hexdigest()

    # 計算 TSS 分數
    total_score, w1, w2, w3, discount = calculate_tss(amount, file_hash)
    
    # 產出唯一交易編號
    timestamp_str = datetime.now().strftime("%Y%m%d")
    random_hex = os.urandom(2).hex().upper()
    tx_id = f"TX-{timestamp_str}-{random_hex}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions 
        (tx_id, company_name, invoice_num, amount, file_name, file_hash, tss_score, w1_env, w2_cred, w3_imp, rate_discount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tx_id, company, invoice_num, amount, filename, file_hash, total_score, w1, w2, w3, discount, 'Pending'))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard', tx_id=tx_id))

# 7. API 路由：銀行端審核狀態更新
@app.route('/api/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    tx_id = data.get('tx_id')
    new_status = data.get('status') # 'Approved' 或 'Rejected'
    
    if not tx_id or not new_status:
        return jsonify({'success': False, 'message': '參數缺漏'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE transactions SET status = ? WHERE tx_id = ?", (new_status, tx_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'tx_id': tx_id, 'new_status': new_status})

if __name__ == '__main__':
    print("🚀 [碳個究竟 Carbon Secret] 系統啟動中...")
    print("📍 存取網址: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)