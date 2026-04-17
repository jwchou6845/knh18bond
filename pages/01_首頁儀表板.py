import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# 🌟 1. 匯入你的超級小幫手模組
from config import airtable_api, BASE_ID, TABLES
from ui_core import setup_app_ui, alert_card

# --- 1. 頁面基本設定 (必須在第一行) ---
st.set_page_config(page_title="首頁儀表板 | KNH MMS", layout="wide", initial_sidebar_state="collapsed")
setup_app_ui(user_name="admin")

import os
from dotenv import load_dotenv # 🌟 確保引入這個套件來讀取本機 .env

# --- 1.5 警衛室：通關密語檢查 ---
def check_password():
    """檢查使用者是否輸入了正確的密碼"""
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("<h3 style='text-align: center; margin-top: 50px;'>🔒 紡黏原料管理系統</h3>", unsafe_allow_html=True)
    pwd = st.text_input("請輸入廠區登入密碼：", type="password", key="pwd_input")
    
    if pwd:
        # 1. 先嘗試從本機的 .env 讀取密碼
        load_dotenv()
        correct_password = os.getenv("APP_PASSWORD")
        
        # 2. 如果 .env 沒抓到 (代表系統現在在雲端上)
        if not correct_password:
            try:
                # 用 try-except 包起來，避免找不到 secrets.toml 時當機
                correct_password = st.secrets["APP_PASSWORD"]
            except Exception:
                # 3. 終極保底防線：如果都找不到，就預設這組密碼，確保你還是進得去！
                correct_password = "KNH888" 
        
        # 進行比對
        if pwd == correct_password:
            st.session_state["password_correct"] = True
            st.rerun() 
        else:
            st.error("😕 密碼錯誤，請重新輸入！")
            
    return False

# 🛑 攔截點：如果密碼不對，就卡在這裡
if not check_password():
    st.stop()

# --- 2. Airtable 資料抓取引擎 ---

@st.cache_data(ttl=60)
def fetch_inventory_data_v2():
    table = airtable_api.table(BASE_ID, TABLES["新料庫存"])
    records = table.all()
    
    data_list = []
    for record in records:
        fields = record.get('fields', {})
        data_list.append({
            "原料名稱": fields.get("原料名稱", "未知原料"), 
            "種類": fields.get("種類", "N/A"), 
            "目前庫存(包)": fields.get("目前庫存(包)", 0),
            "庫存狀態": fields.get("庫存狀態", "未知狀態") 
        })
    return pd.DataFrame(data_list)

@st.cache_data(ttl=60)
def fetch_recycled_inventory_data():
    table = airtable_api.table(BASE_ID, TABLES["回用料庫存"])
    records = table.all()
    
    data_list = []
    for record in records:
        fields = record.get('fields', {})
        if "在庫" in fields.get("使用狀態", ""):
            supplier = fields.get("供應商", "未知") 
            item_type = fields.get("原料種類", "未知")
            data_list.append({
                "供應商與種類": f"{supplier} {item_type}",
                "種類": item_type,
                "重量(KG)": fields.get("重量(KG)", 0)
            })
            
    df = pd.DataFrame(data_list)
    if not df.empty:
        df_grouped = df.groupby(["供應商與種類", "種類"], as_index=False)["重量(KG)"].sum()
        df_grouped["重量(KG)"] = df_grouped["重量(KG)"].round(1) 
        return df_grouped
    return df

@st.cache_data(ttl=60)
def fetch_monthly_material_usage():
    """🌟 終極三分流：新料、母粒、回用料各自加總"""
    current_month = date.today().strftime("%Y-%m")
    
    def get_weight(fields):
        for k, v in fields.items():
            if "重量" in k:
                try:
                    val = float(v[0] if isinstance(v, list) else v)
                    if val > 0: return val
                except: pass
        return 0
        
    def get_name(fields):
        for k, v in fields.items():
            if ("名稱" in k or "種類" in k) and all(ex not in k for ex in ["供應商", "批號", "來源", "編號", "數量"]):
                val = str(v[0] if isinstance(v, list) else v)
                if not val.startswith("rec") and val.strip() != "":
                    return val
        return "未知"
        
    def get_supplier(fields):
        for k, v in fields.items():
            if "供應商" in k:
                val = str(v[0] if isinstance(v, list) else v)
                if not val.startswith("rec") and val.strip() != "":
                    return val
        return "未知"

    # ==========================================
    # 1. 抓取【新料】與【母粒】本月用量
    # ==========================================
    table_new = airtable_api.table(BASE_ID, TABLES["新料打料紀錄"])
    records_new = table_new.all()
    new_list = []
    aux_list = [] # 🌟 新增母粒的籃子
    
    for r in records_new:
        fields = r.get('fields', {})
        date_val = str(fields.get("日期", fields.get("打料日期", "")))
        source = str(fields.get("原料來源", ""))
        
        if current_month in date_val:
            weight = get_weight(fields)
            if weight > 0:
                mat_type = get_name(fields)
                supplier = get_supplier(fields)
                final_name = mat_type if supplier in mat_type else f"{mat_type}-{supplier}".strip('-')
                
                # 🌟 智慧分流：看來源欄位，或是看名字有沒有「母粒」
                if "母粒" in source or "母粒" in final_name:
                    aux_list.append({"品項": final_name, "重量(KG)": weight})
                else:
                    new_list.append({"品項": final_name, "重量(KG)": weight})

    # ==========================================
    # 2. 抓取【回用料】本月用量
    # ==========================================
    table_rec = airtable_api.table(BASE_ID, TABLES["回用料打料紀錄"])
    records_rec = table_rec.all()
    rec_list = []
    
    for r in records_rec:
        fields = r.get('fields', {})
        date_val = str(fields.get("日期", fields.get("打料日期", "")))
        
        if current_month in date_val:
            weight = get_weight(fields)
            if weight > 0:
                mat_type = get_name(fields)
                supplier = get_supplier(fields)
                final_name = mat_type if supplier in mat_type else f"{mat_type}-{supplier}".strip('-')
                rec_list.append({"品項": final_name, "重量(KG)": weight})
    
    # ==========================================
    # 3. 整理加總
    # ==========================================
    df_new = pd.DataFrame(new_list)
    df_aux = pd.DataFrame(aux_list)
    df_rec = pd.DataFrame(rec_list)
    
    if not df_new.empty: df_new = df_new.groupby("品項", as_index=False)["重量(KG)"].sum()
    if not df_aux.empty: df_aux = df_aux.groupby("品項", as_index=False)["重量(KG)"].sum()
    if not df_rec.empty: df_rec = df_rec.groupby("品項", as_index=False)["重量(KG)"].sum()
        
    return df_new, df_aux, df_rec, current_month

# --- 4. 背景同步資料 ---
with st.spinner("⏳ 正在從 資料庫 同步最新數據..."):
    inventory_data = fetch_inventory_data_v2()
    usage_new_df, usage_aux_df, usage_rec_df, current_month_str = fetch_monthly_material_usage()

# --- 5. 🌟 四欄位看板區 (警示 30%，新料 24%，母粒 23%，回用料 23%) ---
col_alerts, col_new_usage, col_aux_usage, col_rec_usage = st.columns([3, 2.4, 2.3, 2.3]) 

# 👉 5-A: 左側低水位警示區
with col_alerts:
    st.markdown("<h4 style='color: #333; margin-bottom: 20px;'>🚨 低水位警示</h4>", unsafe_allow_html=True)
    if not inventory_data.empty:
        low_stock_items = inventory_data[inventory_data["庫存狀態"] == "⚠️ 庫存不足"]
        if not low_stock_items.empty:
            alert_cols = st.columns(2) # 為了適應版面，警示卡片改成一排兩張
            card_index = 0
            for _, row in low_stock_items.iterrows():
                with alert_cols[card_index % 2]:
                    alert_card(title=row['原料名稱'], value=f"{row['目前庫存(包)']} 包", subtitle="低於安全庫存")
                card_index += 1
        else:
            st.success("✅ 目前庫存充足")
    else:
        st.error("無法取得庫存資料。")

# 👉 5-B: 新料卡片 (藍灰色)
with col_new_usage:
    st.markdown("<h4 style='color: #333; margin-bottom: 20px;'>🆕 本月新料用量</h4>", unsafe_allow_html=True)
    if not usage_new_df.empty:
        for _, row in usage_new_df.iterrows():
            st.markdown(f"""
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px 15px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <div style="font-size: 14px; font-weight: 700; color: #111; margin-bottom: 10px; display: flex; align-items: center;">
                    <span style="background-color: #f0f2f6; color: #31333F; padding: 2px 6px; border-radius: 4px; font-size: 12px; margin-right: 8px; font-weight: 600;">{current_month_str}</span>
                    {row['品項']}
                </div>
                <div style="font-size: 22px; font-weight: 800; color: #555;">
                    {row['重量(KG)']:,.0f} <span style="font-size: 13px; font-weight: 500; color: #888;">KG</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💡 尚無紀錄。")

# 👉 5-C: 母粒卡片 (紫色)
with col_aux_usage:
    st.markdown("<h4 style='color: #333; margin-bottom: 20px;'>🎨 本月母粒用量</h4>", unsafe_allow_html=True)
    if not usage_aux_df.empty:
        for _, row in usage_aux_df.iterrows():
            st.markdown(f"""
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px 15px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <div style="font-size: 14px; font-weight: 700; color: #111; margin-bottom: 10px; display: flex; align-items: center;">
                    <span style="background-color: #f4ebfa; color: #6b21a8; padding: 2px 6px; border-radius: 4px; font-size: 12px; margin-right: 8px; font-weight: 600;">{current_month_str}</span>
                    {row['品項']}
                </div>
                <div style="font-size: 22px; font-weight: 800; color: #555;">
                    {row['重量(KG)']:,.0f} <span style="font-size: 13px; font-weight: 500; color: #888;">KG</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💡 尚無紀錄。")

# 👉 5-D: 回用料卡片 (綠色)
with col_rec_usage:
    st.markdown("<h4 style='color: #333; margin-bottom: 20px;'>♻️ 本月回用料用量</h4>", unsafe_allow_html=True)
    if not usage_rec_df.empty:
        for _, row in usage_rec_df.iterrows():
            st.markdown(f"""
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px 15px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <div style="font-size: 14px; font-weight: 700; color: #111; margin-bottom: 10px; display: flex; align-items: center;">
                    <span style="background-color: #e6f4ea; color: #1e8e3e; padding: 2px 6px; border-radius: 4px; font-size: 12px; margin-right: 8px; font-weight: 600;">{current_month_str}</span>
                    {row['品項']}
                </div>
                <div style="font-size: 22px; font-weight: 800; color: #555;">
                    {row['重量(KG)']:,.0f} <span style="font-size: 13px; font-weight: 500; color: #888;">KG</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💡 尚無紀錄。")


# --- 6. 繪製圖表 ---
st.markdown("<h4 style='color: #333; margin-top: 40px;'>📊 即時庫存</h4>", unsafe_allow_html=True)
if not inventory_data.empty:
    fig = px.bar(
        inventory_data, x="原料名稱", y="目前庫存(包)", color="種類", text="目前庫存(包)",        
        color_discrete_map={"N/A": "#82D277", "未結晶": "#3498db", "已結晶": "#f5913a"}
    )
    fig.update_traces(textposition='outside', textfont_size=14, texttemplate='%{text} 包')
    fig.update_layout(xaxis_tickangle=-50, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=30, b=80), xaxis_title=None, yaxis_title="庫存數量 (包)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<h4 style='color: #333; margin-top: 40px;'>♻️ 即時回用料庫存</h4>", unsafe_allow_html=True)
with st.spinner("⏳ 正在計算回用料總重量..."):
    recycled_data = fetch_recycled_inventory_data()

if not recycled_data.empty:
    fig_rec = px.bar(recycled_data, x="供應商與種類", y="重量(KG)", color="種類", text="重量(KG)")
    fig_rec.update_traces(textposition='outside', textfont_size=14, texttemplate='%{text} KG')
    fig_rec.update_layout(xaxis_tickangle=-45, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=30, b=80), xaxis_title=None, yaxis_title="庫存重量 (KG)", showlegend=True)
    st.plotly_chart(fig_rec, use_container_width=True)
else:
    st.info("💡 目前倉庫中沒有「在庫」狀態的回用料。")