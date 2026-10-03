# carbon-fintech-demo
# 碳個究竟 (Carbon Secret) - 交易級永續評估與金融對接平台

> **2026 金融科技創新競賽 / 學術專題成果**  
> 本專案為兼具前端互動與後端真實算力邏輯的交易級永續評估（Transaction-level Sustainability Assessment, TSS）系統原型（Prototype）。系統透過 Python Flask 與 SQLite 搭建，實現單據上傳、SHA-256 哈希值防偽驗證、動態 TSS 評分演算與綠色金融授信報告產出。

---

## 🛠 技術架構與技術棧 (Tech Stack)

- **後端 (Backend)**: Python 3.x, Flask
- **資料庫 (Database)**: SQLite 3
- **前端 (Frontend)**: HTML5, Jinja2 Template, Tailwind CSS (CDN), FontAwesome Icons
- **安全與加密 (Security)**: SHA-256 Hash 演算法 (防重複融資驗證)

---

## 🚀 系統核心功能與機制

1. **單據進件與資料解析**
   - 支援 PDF / 影像單據檔案上傳，後端自動將檔案儲存於本地 `uploads/` 資料夾。
   - 允許自由動態調整企業名稱、發票號碼與交易金額。

2. **SHA-256 加密防偽機制**
   - 讀取上傳檔案之二進位內容，實時計算獨一無二的 `SHA-256` 哈希值（Hash），作為跨行防重複融資與勾稽憑證。

3. **TSS 動態算力引擎**
   - **$W_1$ 環境表現 (50%)**：依據交易金額與低碳資材效益進行演算法加權。
   - **$W_2$ 資料可信度 (30%)**：基於進件資料完整度與 Hash 防偽演算評分。
   - **$W_3$ 永續改善幅度 (20%)**：對齊雙軌基準（歷史軌跡與產業標竿 Top 15%）。

4. **綠色金融授信試算與報告產出**
   - 動態計算建議利率減碼（如 -0.35% / 35 bps）與授信額度。
   - 提供直覺的 TSS 儀表板，支援一鍵列印/匯出為標準 PDF 報告。

---

## 📅 開發流程與目前進度 (Development Status)

### 階段一：需求分析與 UI 原型設計 (Completed)
- [x] 確定系統三大模組：單據進件、TSS 算力引擎、金融機構儀表板。
- [x] 完成靜態 HTML/Tailwind CSS 視覺設計（符合金管會綠色金融 3.0 與 UI/UX 規範）。

### 階段二：Flask 後端與 SQLite 基礎架構 (Completed)
- [x] 建立 Flask 伺服器與路由系統（`/` 與 `/dashboard`）。
- [x] 初始化 SQLite 資料庫（`transactions` 資料表結構設計）。
- [x] 將靜態 HTML 重構為 Jinja2 動態樣板。

### 階段三：真實資料流與動態互動接通 (Completed - Current State)
- [x] **實作真實檔案上傳**：實現 `multipart/form-data` 傳輸，檔案實體儲存於 `uploads/`。
- [x] **SHA-256 防偽演算**：對上傳檔案計算真實 Hash 值並展示於儀表板。
- [x] **TSS 動態計算引擎**：接通前端表單數據，實現即時分數演算與利率折扣計算。
- [x] **資料庫持久化儲存**：完成表單送出後自動寫入 `database.db` 的完整 POST 流程。
- [x] **互動體驗優化**：完成「評估下一筆」、「匯出 PDF 報告」與「第三方複審」等按鈕之觸發邏輯。

### 階段四：未來擴充與正式部署規劃 (Roadmap)
- [ ] 串接 LLM / OCR API 實現發票與 PO 單據之自動文字辨識（AI 自動填表）。
- [ ] 擴充多筆交易之歷史趨勢統計與圖表分析（Chart.js）。
- [ ] 部署至雲端平台（如 Render / Heroku）以供線上實測。

---

## 💻 本地端快速啟動指南 (Quick Start)

### 1. 複製專案與建立虛擬環境
```bash
git clone <your-repository-url>
cd carbon-fintech-demo

# 建立虛擬環境 (以 Windows 為例)
python -m venv venv
venv\Scripts\activate