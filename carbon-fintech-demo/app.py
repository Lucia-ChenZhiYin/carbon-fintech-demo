import streamlit as st
import time

# 頁面標題與配置
st.set_page_config(page_title="碳個究竟 - 交易級永續評估平台", layout="wide", page_icon="🌱")

st.title("🌱 碳個究竟：交易級永續評估與綠色金融對接平台")
st.caption("交易級永續評估補充層 (Transaction-level Sustainability Assessment Layer)")

# 側邊欄設計
st.sidebar.image("https://img.icons8.com/color/96/leaf--v1.png", width=60)
st.sidebar.title("系統功能選單")
menu = st.sidebar.radio("請選擇操作項目", ["1. 單據進件與 AI 比對", "2. TSS 永續評估儀表板", "3. 金融機構授信審核"])

# Session State 初始化
if 'uploaded' not in st.session_state:
    st.session_state.uploaded = False

# ----------------- 頁面 1：單據進件 -----------------
if menu == "1. 單據進件與 AI 比對":
    st.header("📄 單筆交易資料進件 (Mock Ingestion)")
    st.markdown("請上傳該筆交易之相關憑證，系統將自動進行 **三單勾稽** 與 **發票 Hash 防重檢查**。")
    
    uploaded_file = st.file_uploader("拖曳或瀏覽上傳電子發票 / 採購單 (PO) / 綠電憑證 (TREC)", type=["pdf", "png", "jpg"])
    
    if uploaded_file is not None:
        st.success(f"已接收檔案：`{uploaded_file.name}`")
        if st.button("🚀 開始 AI 欄位解析與三單比對", type="primary"):
            with st.spinner("AI 解析中... 正在對接財政部 API 與進行 Hash 防重核驗..."):
                time.sleep(1.5)
            
            st.session_state.uploaded = True
            st.balloons() # 成功特效
            st.success("✅ 解析完成！單據勾稽一致，發票 Hash 查驗無重複融資風險。")
            
            # 展示勾稽結果卡片
            col1, col2 = st.columns(2)
            with col1:
                st.info("**基本交易欄位**\n- **交易編號**: TX-2026-08891\n- **買方**: 台積電供應鏈夥伴 A\n- **賣方**: 綠能零件股份有限公司\n- **金額**: NT$ 5,000,000")
            with col2:
                st.warning("**防偽與驗證機制**\n- **三單比對**: 完全吻合 (發票/PO/交貨單)\n- **防重融資**: 通過 (Hash 檢驗鎖定)\n- **第三方複審**: 待複審 (Pending)")

# ----------------- 頁面 2：TSS 儀表板 -----------------
elif menu == "2. TSS 永續評估儀表板":
    st.header("📊 交易級永續綜合得分 (TSS Dashboard)")
    
    if not st.session_state.uploaded:
        st.info("💡 提示：目前顯示為預設示範資料，可至「單據進件」頁面上傳測試單據。")
    
    # 核心指標展示
    col1, col2, col3 = st.columns(3)
    col1.metric("TSS 綜合評分", "88.1 / 100", "Level A (優良)", delta_color="normal")
    col2.metric("建議利率減碼", "-0.35%", "已達綠色優惠門檻", delta_color="normal")
    col3.metric("第三方驗證狀態", "待複審", "剛性必要流程", delta_color="off")
    
    st.divider()
    
    # 指標拆解
    st.subheader("三維度指標算式拆解")
    st.write("1. **環境表現指標 (E-Score, 權重 50%)**: **45.0** / 50 (引用環境部碳足跡資料庫)")
    st.progress(90)
    
    st.write("2. **資料可信度指標 (C-Score, 權重 30%)**: **28.1** / 30 (已包含三單勾稽 +15% 加算)")
    st.progress(93)
    
    st.write("3. **永續改善動能 (I-Score, 權重 20%)**: **15.0** / 20 (較前期同類交易減碳 12%)")
    st.progress(75)

# ----------------- 頁面 3：金融機構授信 -----------------
elif menu == "3. 金融機構授信審核":
    st.header("🏦 金融機構 API 授信對接區")
    st.markdown("本介面模擬銀行風控後台讀取 TSS 評估結果並核定優惠條件。")
    
    st.warning("⚠️ 實際核貸條件仍須依各金融機構之授信規範與作業程序決定。")
    
    if st.button("點擊模擬：透過 API 傳送授信結果至合作銀行"):
        with st.spinner("加密傳輸中..."):
            time.sleep(1)
        st.success("🎉 數據已順利寫入銀行授信系統！自動套用 **-0.35% (35 bps)** 綠色利率優惠！")