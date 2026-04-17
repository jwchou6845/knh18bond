import streamlit as st
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components

from config import airtable_api, BASE_ID, TABLES
from ui_core import setup_app_ui

# --- 1. 基本設定與全域 UI 注入 ---
st.set_page_config(page_title="歷史報表與統計 | KNH MMS", layout="wide")
current_user = st.session_state.get("登入者姓名", "admin")
setup_app_ui(user_name=current_user)

st.markdown("""
    <style>
    @media print {
        [data-testid="stSidebar"], .custom-top-bar, .stButton, iframe { display: none !important; }
        [data-testid="block-container"] { padding-top: 0px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 資料抓取引擎 ---
@st.cache_data(ttl=60)
def get_report_data(table_key):
    table_id = TABLES.get(table_key)
    if not table_id: return pd.DataFrame()
    
    table = airtable_api.table(BASE_ID, table_id)
    records = table.all()
    
    data = []
    for r in records:
        row = r['fields']
        for key, val in row.items():
            if isinstance(val, list):
                row[key] = str(val[0]) if val else ""
        data.append(row)
        
    df = pd.DataFrame(data)
    
    if not df.empty:
        # 🌟 修復 1-A：擴大日期雷達，辨識「時間」
        date_cols = [col for col in df.columns if "日期" in col or "時間" in col]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    return df

# --- 3. 頁面標題 ---
st.markdown("### 📊 歷史報表與用料統計")

# --- 4. 篩選控制區 ---
with st.container(border=True):
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        report_type = st.selectbox("1. 選擇報表類型", ["進貨入庫報表", "打料作業紀錄"])
    with r1c2:
        if report_type == "進貨入庫報表":
            sub_type = st.selectbox("2. 細項分類", ["原料新料入庫", "回用料庫存"]) 
        else:
            sub_type = st.selectbox("2. 細項分類", ["新料打料紀錄", "回用料打料紀錄"])
            
    with r1c3:
        date_range = st.date_input("3. 設定時間區間", [date.today().replace(day=1), date.today()])

df_all = get_report_data(sub_type)

if not df_all.empty:
    df_filtered = df_all.copy()
    
    # 🌟 修復 1-B：更聰明的過濾邏輯與明確提示
    date_col = next((c for c in df_filtered.columns if "日期" in c or "時間" in c), None)
    
    if len(date_range) == 2 and date_col:
        start, end = date_range
        df_filtered = df_filtered[(df_filtered[date_col] >= start) & (df_filtered[date_col] <= end)]
        st.caption(f"ℹ️ 系統目前依據 **【{date_col}】** 欄位進行時間篩選。")
    elif len(date_range) == 2 and not date_col:
        st.warning("⚠️ 此資料表找不到日期相關欄位，因此顯示所有紀錄。")

    # --- 5. 統計看板區 ---
    val_col = next((c for c in df_filtered.columns if "重量" in c or "數量" in c or "包數" in c), None)
    
    cat_col = None
    valid_keywords = ["原料名稱", "供應商", "種類", "回用料編號", "領用新料", "領用回用料"]
    
    for k in valid_keywords:
        if k in df_filtered.columns:
            cat_col = k
            break
            
    if not cat_col:
        for col in df_filtered.columns:
            if any(k in col for k in valid_keywords):
                if col not in ["關聯原料", "回用料ID", "系統紀錄", "每月用料彙整表"]:
                    cat_col = col
                    break

    if val_col and cat_col:
        # 強制轉數字
        df_filtered[val_col] = pd.to_numeric(df_filtered[val_col], errors='coerce').fillna(0)
        
        summary_df = df_filtered.groupby([cat_col])[val_col].sum().reset_index()
        summary_df.columns = [cat_col, f"累積總{val_col}"]
        
        total_sum = summary_df[f"累積總{val_col}"].sum()
        st.markdown(f"#### 📈 數據加總統計 ｜ 總計： **{total_sum:,.1f}**")
        
        sc1, sc2 = st.columns([1, 2])
        with sc1:
            st.dataframe(summary_df, hide_index=True, use_container_width=True)
        with sc2:
            st.bar_chart(summary_df.set_index(cat_col))
    else:
        st.markdown("#### 📈 數據加總統計")
        st.warning("無法自動生成統計圖表，請確認資料表中包含『日期』、『供應商/原料名稱』及『重量/數量』欄位。")

    # --- 6. 詳細清單與匯出 ---
    with st.expander("查看詳細紀錄清單", expanded=True):
        if cat_col and cat_col in df_filtered.columns:
            unique_vals = df_filtered[cat_col].dropna().astype(str).unique().tolist()
            search_vals = ["全部"] + sorted(unique_vals)
            
            selected_val = st.selectbox(f"依 {cat_col} 過濾清單", search_vals)
            if selected_val != "全部":
                df_filtered = df_filtered[df_filtered[cat_col].astype(str) == selected_val]
        
        columns_to_hide = ["關聯原料", "回用料ID", "系統紀錄", "每月用料彙整表"] 
        df_display = df_filtered.drop(columns=columns_to_hide, errors='ignore')
        
        # 🌟 修復 2：列印模式切換開關
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        print_mode = st.toggle("🖨️ 開啟列印模式 (展開完整表格，避免列印被截斷)")
        
        if print_mode:
            # 開啟時：使用靜態原生 HTML 表格，無限長度完美列印
            st.table(df_display)
        else:
            # 關閉時：使用互動表格，網頁瀏覽體驗好
            st.dataframe(df_display, use_container_width=True)
        
        # --- 7. 匯出與列印按鈕區 ---
        st.markdown("<hr style='margin: 15px 0px;'>", unsafe_allow_html=True)
        btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 6])
        
        with btn_col1:
            csv = df_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 匯出 Excel (CSV)", data=csv, file_name=f"Report_{sub_type}_{date.today()}.csv", mime="text/csv", use_container_width=True)
            
        with btn_col2:
            components.html(
                """
                <script>
                function printPage() {
                    window.parent.print();
                }
                </script>
                <button onclick="printPage()" 
                        style="width: 100%; background-color: #ffffff; color: #31333F; 
                               border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; 
                               padding: 0.25rem 0.75rem; font-size: 1rem; line-height: 1.6; 
                               min-height: 38.4px; font-family: 'Source Sans Pro', sans-serif;
                               cursor: pointer; transition: border-color 0.2s, color 0.2s;">
                    🖨️ 列印此頁
                </button>
                <style>
                    button:hover { border-color: #FF4B4B; color: #FF4B4B; }
                </style>
                """,
                height=45
            )
else:
    st.error("此時段內查無資料。")