import streamlit as st
from datetime import datetime

# 🌟 匯入你的超級小幫手模組
from config import airtable_api, BASE_ID, TABLES
from ui_core import setup_app_ui

# --- 1. 頁面基本設定與全域 UI 注入 ---
st.set_page_config(page_title="入庫紀錄 | KNH MMS", layout="wide", initial_sidebar_state="collapsed")

# 啟動警衛室與頂部導覽列
current_user = st.session_state.get("登入者姓名", "admin")
setup_app_ui(user_name=current_user)

# --- 2. 資料庫引擎 ---

@st.cache_data(ttl=60)
def fetch_material_options():
    """抓取新料庫存清單，建立下拉選單"""
    try:
        # 直接使用 config 裡的 TABLES 字典
        table = airtable_api.table(BASE_ID, TABLES["新料庫存"]) 
        records = table.all()
        
        options_dict = {}
        for r in records:
            name = r['fields'].get("原料名稱")
            record_id = r['id'] 
            if name:
                options_dict[name] = record_id
        return options_dict
    except Exception as e:
        st.error(f"無法抓取原料選項：{e}")
        return {}

def submit_record(table_key, data_dict):
    """通用的 Airtable 寫入引擎"""
    try:
        table = airtable_api.table(BASE_ID, TABLES[table_key])
        table.create(data_dict)
        return True
    except Exception as e:
        st.error(f"寫入失敗，錯誤訊息：{e}")
        return False

# --- 3. 頁面標題 ---
st.markdown("""
    <h3 style='color: #111; margin-bottom: 0px;'>📦 原料入庫作業</h3>
    <hr style='margin-top: 5px; border-color: #DCDCDC; margin-bottom: 20px;'>
""", unsafe_allow_html=True)

# 載入原料清單
material_mapping = fetch_material_options()
material_names_list = list(material_mapping.keys()) 

# 🌟 升級為雙頁籤 (Tabs) 架構
tab1, tab2 = st.tabs(["📦 供應商新料入庫", "♻️ 廠內回用料入庫"])

# ==========================================
# 📦 頁籤 1：供應商新料
# ==========================================
with tab1:
    with st.form("new_material_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            today_str = datetime.today().strftime("%Y%m%d")
            input_batch = st.text_input("🔢 進貨批號", value=f"{today_str}")
            input_date = st.date_input("🗓️ 進貨日期", datetime.today())
            
        with col2:
            if material_names_list:
                input_material = st.selectbox("🏷️ 關聯原料", material_names_list)
            else:
                input_material = st.selectbox("🏷️ 關聯原料", ["無法取得資料"])
            
            input_qty = st.number_input("📦 進貨數量(包)", min_value=1, step=1)

        if st.form_submit_button("🚀 確認送出新料入庫", use_container_width=True):
            selected_rec_id = material_mapping.get(input_material)
            
            data_to_upload = {
                "進貨日期": str(input_date), 
                "關聯原料": [selected_rec_id] if selected_rec_id else [], 
                "進貨批號": input_batch,
                "進貨數量(包)": input_qty
            }
            
            with st.spinner("🔄 新料資料寫入中..."):
                if submit_record("原料新料入庫", data_to_upload):
                    st.success(f"✅ {input_material} 入庫紀錄成功！")
                    st.cache_data.clear()

# ==========================================
# ♻️ 頁籤 2：廠內回用料
# ==========================================
with tab2:
    with st.form("recycled_material_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            today_str = datetime.today().strftime("%Y%m%d")
            input_id_rec = st.text_input("🔢 原料編號", value=f"{today_str}", help="預設今日日期，請補兩碼流水號。")
            input_type_rec = st.selectbox("📌 原料種類", ["PET", "RPET", "PET-308A", "PA6"]) 
            input_machine_rec = st.selectbox("⚙️ 來源機台", ["S1", "S2"]) 
            
        with col2:
            # 🌟 新增：入庫日期欄位
            input_date_rec = st.date_input("🗓️ 入庫/造粒日期", datetime.today())
            input_weight_rec = st.number_input("⚖️ 重量 (KG)", min_value=0.0, value=None, placeholder="請輸入重量...") 
            input_vendor_rec = st.selectbox("📍 供應商", ["南紡", "南紡308A", "南亞", "遠東", "遠東RPET", "集盛", "力鵬", "中國岳化", "中國儀征"])

        if st.form_submit_button("♻️ 確認送出回用料入庫紀錄", use_container_width=True):
            # 🛑 檢查哨
            if not input_id_rec or input_id_rec == f"{today_str}":
                st.error("🚨 請完整填寫「原料編號」的流水號！")
            elif input_weight_rec is None or input_weight_rec <= 0:
                st.error("🚨 請輸入正確的「重量」！")
            else:
                data_to_upload = {
                    "回用料編號": input_id_rec,
                    "原料種類": input_type_rec,
                    "來源機台": input_machine_rec,
                    "重量(KG)": input_weight_rec,
                    "供應商": input_vendor_rec,
                    "入庫日期": str(input_date_rec) # 🌟 新增寫入包裹！
                    # 注意："使用狀態" 由 Airtable 公式自動生成
                }
                
                with st.spinner("🔄 回用料入庫資料寫入中..."):
                    if submit_record("回用料庫存", data_to_upload):
                        st.success("✅ 回用料入庫紀錄成功！")
                        st.cache_data.clear()