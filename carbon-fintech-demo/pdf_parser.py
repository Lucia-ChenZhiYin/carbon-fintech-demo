import re
from pypdf import PdfReader

def parse_document(file_path):
    """
    動態掃描檔案 (支援 .pdf 與 .txt)，提取：
    1. 發票/單據號碼 (invoice_num)
    2. 交易總金額 (amount)
    3. 企業名稱 (company_name)
    """
    extracted_data = {
        "invoice_num": None,
        "amount": None,
        "company_name": None,
        "raw_text": ""
    }

    full_text = ""
    try:
        # 判斷是否為 PDF 檔案
        if file_path.lower().endswith('.pdf'):
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        # 判斷是否為 TXT 純文字檔案
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                full_text = f.read()

        extracted_data["raw_text"] = full_text

        # 1. 抓取發票/單據號碼 (包含 INV-xxxx, XX-xxxx, PO-xxxx)
        invoice_match = re.search(r'(?:發票號碼|採購單號|單號|Invoice)[：:\s]*([A-Z0-9-]+)', full_text, re.IGNORECASE)
        if not invoice_match:
            invoice_match = re.search(r'([A-Z]{2}-\d{8}|INV-\d+|PO-\d+)', full_text)
        if invoice_match:
            extracted_data["invoice_num"] = invoice_match.group(1).strip()

        # 2. 抓取金額 (相容 NT$, 金額：, 3,100,000 等多元格式)
        amount_match = re.search(r'(?:NT\$|金額|總金額|總計)[：:\s]*([0-9,]+)', full_text, re.IGNORECASE)
        if amount_match:
            clean_amount = amount_match.group(1).replace(',', '').strip()
            try:
                extracted_data["amount"] = float(clean_amount)
            except ValueError:
                pass

        # 3. 抓取企業名稱
        company_match = re.search(r'(?:買方企業|企業|公司名稱)[：:\s]*([^\n]+)', full_text)
        if company_match:
            extracted_data["company_name"] = company_match.group(1).strip()
        else:
            company_match = re.search(r'([^\s\n]+(?:股份有限公司|有限公司|企業|公司))', full_text)
            if company_match:
                extracted_data["company_name"] = company_match.group(1).strip()

    except Exception as e:
        print(f"📄 檔案解析過程發生例外: {e}")

    return extracted_data