import streamlit as st
import time
import base64
from pathlib import Path

# --- 1. 網頁基本設定 (設定開機完畢後，側邊欄預設為"收起") ---
st.set_page_config(page_title="KNH SPUNBOND MMS", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 圖片轉換工具 ---
def get_image_base64(image_path):
    try:
        data = Path(image_path).read_bytes()
        return base64.b64encode(data).decode()
    except Exception as e:
        return ""

logo_base64 = get_image_base64("logo.webp")

# --- 3. 全域 CSS 與 頂部導覽列 (Top Navigation Bar) ---
st.markdown(f"""
<style>
    /* 基礎底色與字體 */
    .stApp {{ background-color: #F4F5F5; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
    footer {{visibility: hidden;}} 
    #MainMenu {{visibility: hidden;}}
    header {{background-color: transparent !important;}}
    .stAppDeployButton {{display: none !important;}}
    
    /* 確保原生漢堡選單 (☰) 浮在 Top Bar 之上 */
    [data-testid="collapsedControl"] {{ z-index: 1001 !important; color: #111 !important; }}

    /* 頂部導覽列 */
    .custom-top-bar {{
        position: fixed; top: 0; left: 0; right: 0; height: 56px;
        background-color: #F4F5F5; border-bottom: 1px solid #DCDCDC;
        z-index: 1000; display: flex; justify-content: space-between;
        align-items: center; padding-right: 20px; padding-left: 60px; 
    }}
    .top-bar-left {{ display: flex; align-items: center; gap: 12px; }}
    .top-bar-logo {{ width: 28px; height: 28px; object-fit: contain; }}
    .top-bar-title {{ font-size: 16px; font-weight: 800; color: #111; letter-spacing: 0.5px; }}
    .top-bar-right {{ display: flex; align-items: center; gap: 10px; cursor: pointer; }}
    .top-bar-user-name {{ font-size: 14px; font-weight: 500; color: #333; }}
    .top-bar-avatar {{
        width: 30px; height: 30px; border-radius: 50%; 
        background-color: #EAEBEB; color: #555; display: flex; 
        justify-content: center; align-items: center; font-size: 14px;
        border: 1px solid #DCDCDC;
    }}

    /* 把主要內容區往下推，避免被頂部導覽列蓋住 */
    [data-testid="block-container"] {{ padding-top: 80px !important; }}

    /* 開機載入畫面排版 */
    .load-screen {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: #F4F5F5; display: flex; justify-content: center; align-items: center; z-index: 9999; }}
    .content-wrapper {{ display: flex; flex-direction: column; width: fit-content; }} 
    .horizontal-container {{ display: flex; flex-direction: row; align-items: center; gap: 25px; margin-bottom: 25px; }}
    .logo-img {{ width: 140px; height: 140px; object-fit: contain; }}
    .text-block {{ display: flex; flex-direction: column; justify-content: space-between; width: 340px; height: 135px; padding: 2px 0; box-sizing: border-box; }}
    .main-title {{ font-size: 32px; font-weight: 800; color: #111; line-height: 1.05; margin: 0; letter-spacing: -1px; text-transform: uppercase; }}
    .sub-title {{ font-size: 13px; color: #555; line-height: 1.4; font-weight: 400; margin: 0;}}
    .progress-bar-region {{ width: 395px; margin-left: 70px; margin-top: 15px; }}
    .progress-container {{ width: 100%; height: 3px; background-color: #E0E0E0; border-radius: 2px; overflow: hidden; }}
    .progress-bar {{ height: 100%; background-color: #111; width: 0%; animation: loading 4s cubic-bezier(0.4, 0.0, 0.2, 1) forwards; }}
    @keyframes loading {{ 0% {{ width: 0%; }} 20% {{ width: 30%; }} 50% {{ width: 70%; }} 100% {{ width: 100%; }} }}

    /* 隱藏側邊欄裡的 app_core 預設按鈕 */
    [data-testid="stSidebarNav"] ul li:first-child a {{ display: none !important; }}
</style>

<div class="custom-top-bar">
    <div class="top-bar-left">
        <img src="data:image/webp;base64,{logo_base64}" class="top-bar-logo">
        <span class="top-bar-title">紡黏原料管理系統</span>
    </div>
    <div class="top-bar-right">
        <span class="top-bar-user-name">周正偉</span>
        <div class="top-bar-avatar">👤</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 4. 實作開場畫面邏輯 ---
placeholder = st.empty()

if logo_base64:
    with placeholder.container():
        st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
            .custom-top-bar { display: none !important; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""<div class="load-screen"><div class="content-wrapper"><div class="horizontal-container"><img class="logo-img" src="data:image/webp;base64,{logo_base64}"><div class="text-block"><div class="main-title"><div>KNH</div><div>SPUNBOND</div><div>MMS</div></div><div class="sub-title"><div>Precision spunbond material management system.</div><div>Built for clarity, reliable performance.</div></div></div></div><div class="progress-bar-region"><div class="progress-container"><div class="progress-bar"></div></div></div></div></div>""", unsafe_allow_html=True)

    # 模擬系統載入 4 秒
    time.sleep(4)
    # 清空動畫
    placeholder.empty()
    
    # 👇 5. 拔除大廳廢話，直接將畫面切換至 Dashboard
    st.switch_page("pages/01_首頁儀表板.py")
    
else:
    st.error("⚠️ 找不到 'logo.webp'，請確認圖檔已放入正確資料夾。")