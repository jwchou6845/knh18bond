import streamlit as st
from datetime import datetime, timedelta

# 🌟 匯入你的超級小幫手模組
from config import airtable_api, BASE_ID, TABLES
from ui_core import setup_app_ui

# --- 1. 頁面基本設定與全域 UI 注入 ---
st.set_page_config(page_title="噴頭組件狀態 | KNH MMS", layout="wide", initial_sidebar_state="collapsed")

# 啟動警衛室與頂部導覽列
current_user = st.session_state.get("登入者姓名", "admin")
setup_app_ui(user_name=current_user)

# 注入噴頭卡片「專屬」的 CSS 樣式 (保留你原本漂亮的外觀設定)
st.markdown("""
    <style>
    .spinneret-card {
        background-color: #FFFFFF; padding: 20px; border-radius: 8px; 
        border: 1px solid #E0E0E0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .card-title { font-size: 20px; font-weight: bold; color: #333; margin-bottom: 10px; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
    .status-text { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
    .spec-text { font-size: 16px; color: #555; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 資料庫操作引擎 ---

@st.cache_data(ttl=5)
def fetch_spinneret_data():
    try:
        # 直接從 config 拿表單 ID，如果 config 忘記設，也有預設值防呆保底
        table_id = TABLES.get("噴頭組件狀態", "tblVJYfoPmhlXaflh")
        table = airtable_api.table(BASE_ID, table_id)
        records = table.all(sort=["組件編號"]) 
        return records
    except Exception as e:
        st.error(f"連線失敗：{e}")
        return []

def update_spinneret(record_id, update_fields):
    try:
        table_id = TABLES.get("噴頭組件狀態", "tblVJYfoPmhlXaflh")
        table = airtable_api.table(BASE_ID, table_id)
        table.update(record_id, update_fields)
        return True
    except Exception as e:
        st.error(f"狀態變更失敗：{e}")
        return False

# --- 3. 頁面內容與視覺渲染 ---
st.markdown("""
    <h3 style='color: #111; margin-bottom: 0px;'>噴頭組件狀態</h3>
    <hr style='margin-top: 5px; border-color: #DCDCDC; margin-bottom: 20px;'>
""", unsafe_allow_html=True)

# 抓取資料
with st.spinner("⏳ 載入組件狀態中..."):
    records = fetch_spinneret_data()

if records:
    col1, col2 = st.columns(2)
    columns = [col1, col2, col1, col2] 
    
    status_options = ["上機生產中(S1)", "上機生產中(S2)", "真空燒解中", "超音波清潔中", "組裝中", "預熱爐備用中", "尚未組裝", "尚未燒解", "尚未清潔", "待下機"]

    for index, record in enumerate(records):
        rec_id = record['id']
        fields = record['fields']
        
        comp_name = fields.get("組件編號", f"未知組件 {index+1}")
        current_status = fields.get("當前狀態", "未知狀態")
        current_spec = fields.get("分配板規格", "無")
        raw_time = fields.get("狀態最後更新時間") 

        # 🌟 時間處理
        last_updated_str = "尚無紀錄"
        if raw_time:
            try:
                dt = datetime.strptime(raw_time[:19], "%Y-%m-%dT%H:%M:%S")
                dt_tw = dt + timedelta(hours=8)
                last_updated_str = dt_tw.strftime("%Y/%m/%d %H:%M")
            except Exception:
                last_updated_str = str(raw_time)
        
        # 🌟 決定膠囊顏色
        text_color = "#555555" 
        bg_color = "#EAEAEA"  
        
        if current_status in ["上機生產中(S1)", "上機生產中(S2)"]: 
            text_color = "#27ae60" 
            bg_color = "rgba(39, 174, 96, 0.15)"
        elif current_status in ["預熱爐備用中", "尚未組裝", "待下機"]: 
            text_color = "#2980b9" 
            bg_color = "rgba(41, 128, 185, 0.15)"
        elif current_status in ["真空燒解中", "超音波清潔中", "組裝中", "尚未燒解", "尚未清潔"]: 
            text_color = "#d35400" 
            bg_color = "rgba(211, 84, 0, 0.15)"
            
        with columns[index % 4]:
            st.markdown(f"""
            <div class="spinneret-card">
                <div class="card-title">🧩 {comp_name}</div>
                <div class="status-text" style="color: #333; margin-bottom: 12px;">
                    當前狀態：<span style="background-color: {bg_color}; color: {text_color}; padding: 4px 12px; border-radius: 20px; font-size: 15px; font-weight: bold; display: inline-block;">{current_status}</span>
                </div>
                <div class="spec-text">分配板規格：<b>{current_spec}</b></div>
                <div style="font-size: 13px; color: #888; border-top: 1px dashed #E0E0E0; padding-top: 8px; margin-top: 10px;">
                    🕒 狀態最後更新時間：{last_updated_str}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"⚙️ 變更 {comp_name} 狀態與規格"):
                with st.form(key=f"form_{rec_id}"):
                    try:
                        default_index = status_options.index(current_status)
                    except ValueError:
                        default_index = 0
                        
                    new_status = st.selectbox("更新狀態", status_options, index=default_index, key=f"status_{rec_id}")
                    new_spec = st.text_input("更新分配板規格", value=current_spec, key=f"spec_{rec_id}")
                    
                    submit_btn = st.form_submit_button("💾 儲存變更", use_container_width=True)
                    
                    if submit_btn:
                        updates = {
                            "當前狀態": new_status,
                            "分配板規格": new_spec
                        }
                        with st.spinner("更新中..."):
                            if update_spinneret(rec_id, updates):
                                st.success(f"{comp_name} 更新成功！")
                                st.cache_data.clear()
                                st.rerun()
else:
    st.warning("⚠️ 找不到噴頭組件資料，請確認資料表連線或 Airtable 內是否已有建檔。")