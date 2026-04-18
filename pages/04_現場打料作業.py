import streamlit as st
from datetime import datetime

# 🌟 1. 匯入你的超級小幫手模組
from config import airtable_api, BASE_ID, TABLES
from ui_core import setup_app_ui

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="打料作業 | KNH MMS", layout="wide", initial_sidebar_state="collapsed")
setup_app_ui(user_name="admin")


# --- 2. 資料庫抓取引擎 (精準分流版) ---

@st.cache_data(ttl=60)
def fetch_inventory_data():
    """抓取原料庫存，並利用【大類】直接拆分成新料與母粒兩個選單！"""
    try:
        table = airtable_api.table(BASE_ID, TABLES["新料庫存"])
        records = table.all()
        new_materials = {}
        aux_materials = {}
        
        for r in records:
            fields = r['fields']
            name = fields.get("原料名稱")
            category = fields.get("大類", "") # 抓取你說的大類欄位
            
            if name:
                # 如果大類包含母粒，就分到母粒選單；反之則去新料選單
                if "母粒" in category or "輔助母粒" in category:
                    aux_materials[name] = r['id']
                else:
                    new_materials[name] = r['id']
                    
        return new_materials, aux_materials
    except Exception as e:
        st.error(f"原料讀取失敗：{e}")
        return {}, {}
    
@st.cache_data(ttl=60)
def fetch_recycled_materials():
    """抓取【回用料庫存清單】，只抓取「🟢 在庫」的項目"""
    try:
        table = airtable_api.table(BASE_ID, TABLES["回用料庫存"])
        records = table.all()
        options = {}
        
        for r in records:
            fields = r['fields']
            name = fields.get("回用料編號")
            status = fields.get("使用狀態", "")
            
            if name and "在庫" in status: 
                supplier = fields.get("供應商", "未知供應商")
                mat_type = fields.get("原料種類", "未知種類")
                weight = fields.get("重量(KG)", 0)
                display_text = f"【{supplier}】{name} ｜ {mat_type} ｜ {weight} KG"
                options[display_text] = r['id']
                
        # 排序後回傳
        return dict(sorted(options.items()))
    except Exception as e:
        st.error(f"回用料讀取失敗：{e}")
        return {}

# --- 3. 資料庫寫入引擎 (雙目的地) ---

def create_feeding_new(data_dict):
    """將新料與母粒寫入【新料打料紀錄表】"""
    try:
        table = airtable_api.table(BASE_ID, TABLES["新料打料紀錄"])
        table.create(data_dict)
        return True
    except Exception as e:
        st.error(f"新料紀錄寫入失敗：{e}")
        return False

def create_feeding_rec(data_dict):
    """將回用料寫入專屬的【回用料打料紀錄表】"""
    try:
        table = airtable_api.table(BASE_ID, TABLES["回用料打料紀錄"])
        table.create(data_dict)
        return True
    except Exception as e:
        st.error(f"回用料紀錄寫入失敗：{e}")
        return False


# --- 4. 抓取下拉選單資料 ---
new_mapping, aux_mapping = fetch_inventory_data()
new_list = list(new_mapping.keys())
aux_list = list(aux_mapping.keys())

rec_mapping = fetch_recycled_materials()
rec_list = list(rec_mapping.keys())


# --- 5. 頁面標題與三頁籤 (Tabs) 設計 ---
st.markdown("""
    <h3 style='color: #111; margin-bottom: 0px;'>🏭 現場打料作業</h3>
    <hr style='margin-top: 5px; border-color: #DCDCDC; margin-bottom: 20px;'>
""", unsafe_allow_html=True)

# 🌟 建立三個獨立頁籤，就像三個不同的房間
tab1, tab2, tab3 = st.tabs(["🟦 領用新料", "🟪 輔助母粒", "🟧 領用回用料"])

# ==========================================
# 🟦 頁籤 1：新料作業
# ==========================================
with tab1:
    with st.form("form_new", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            input_batch_new = st.text_input("🔢 原料批號", placeholder='輸入原料包裝上之批號')
            input_date_new = st.date_input("🗓️ 日期", datetime.today(), key="d_new")
            input_machine_new = st.selectbox("⚙️ 選擇乾燥塔", ["S1-PET", "S1-PA6", "S2-PET", "S2-PA6"], key="mac_new")
        with col2:
            input_material_new = st.selectbox("🏷️ 領用新料", new_list if new_list else ["無新料資料"], key="m_new")
            input_qty_new = st.number_input("📦 領用數量 (包)", min_value=1, step=1, key="q_new")

        if st.form_submit_button("🚀 送出新料紀錄", use_container_width=True):
            rec_id = new_mapping.get(input_material_new)
            data = {
                "原料批號": str(input_batch_new),
                "日期": str(input_date_new),
                "原料來源": "新料",
                "領用新料": [rec_id] if rec_id else [],
                "領用數量(包)": input_qty_new,
                "機台選擇": input_machine_new,
            }
            with st.spinner("寫入中..."):
                if create_feeding_new(data):
                    st.success(f"✅ {input_material_new} 打料紀錄已寫入！")
                    st.cache_data.clear()

# ==========================================
# 🟪 頁籤 2：輔助母粒作業
# ==========================================
with tab2:
    with st.form("form_aux", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            today_str = datetime.today().strftime("%Y%m%d")
            input_batch_aux = st.text_input("🔢 原料批號", value=f"MB{today_str}", help="預設今日日期，請補上流水號")
            input_date_aux = st.date_input("🗓️ 日期", datetime.today(), key="d_aux")
            input_machine_aux = st.selectbox("⚙️ 機台選擇", ["S1-PET", "S2-PET"], key="mac_aux")
        with col2:
            input_material_aux = st.selectbox("🎨 領用母粒", aux_list if aux_list else ["無母粒資料"], key="m_aux")
            input_qty_aux = st.number_input("📦 領用數量 (包)", min_value=1, step=1, key="q_aux")

        if st.form_submit_button("🚀 送出母粒紀錄", use_container_width=True):
            rec_id = aux_mapping.get(input_material_aux)
            data = {
                "原料批號": str(input_batch_aux),
                "日期": str(input_date_aux),
                "原料來源": "輔助母粒",
                "領用新料": [rec_id] if rec_id else [],
                "領用數量(包)": input_qty_aux,
                "機台選擇": input_machine_aux,
            }
            with st.spinner("寫入中..."):
                if create_feeding_new(data):
                    st.success(f"✅ {input_material_aux} 紀錄已寫入！")
                    st.cache_data.clear()

# ==========================================
# 🟧 頁籤 3：回用料作業
# ==========================================
with tab3:
    with st.form("form_rec", clear_on_submit=True):
        #st.info("💡 提示：送出後系統會自動寫入【回用料專屬表】，並透過 Airtable 公式自動將該包料變更為「🔴 已領用」。")
        col1, col2 = st.columns(2)
        with col1:
            input_date_rec = st.date_input("🗓️ 日期", datetime.today(), key="d_rec")
            input_machine_rec = st.selectbox("⚙️ 選擇乾燥塔", ["S1-PET", "S1-PA6", "S2-PET", "S2-PA6"], key="mac_rec")
        with col2:
            input_material_rec = st.selectbox("♻️ 領用回用料", rec_list if rec_list else ["目前無在庫回用料"], key="m_rec")
            
            # 🌟 升級版：填單人下拉選單
            operator_list = ["請選擇...", "周正偉", "賴永祥", "黃信維", "林子欽"] # 👈 請改成實際名單
            input_user_rec = st.selectbox("👤 填單人", operator_list, key="user_rec") 

        if st.form_submit_button("🚀 送出回用料紀錄", use_container_width=True):
            if not rec_list:
                st.error("🚨 目前沒有在庫的回用料！")
            elif input_user_rec == "請選擇...": 
                st.error("🚨 請選擇填單人！")
            else:
                rec_id = rec_mapping.get(input_material_rec)
                
                # 🌟 時間魔法：把選好的日期，加上「按下按鈕當下的時間」！
                current_time = datetime.now().time()
                full_datetime = datetime.combine(input_date_rec, current_time).strftime("%Y-%m-%d %H:%M")

                data = {
                    "日期": full_datetime, # 👈 現在它會送出完整的 "2026-04-17 14:42"
                    "機台選擇": input_machine_rec,
                    "領用回用料": [rec_id] if rec_id else [],
                    "填單人": input_user_rec,
                }
                
                
                with st.spinner("寫入資料庫中..."):
                    if create_feeding_rec(data):
                        st.success(f"✅ 紀錄寫入成功！{input_material_rec} 已自動標記為領用。")
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
