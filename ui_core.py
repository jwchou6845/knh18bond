import streamlit as st
import os
from dotenv import load_dotenv

def check_password():
    """全域警衛室：檢查登入狀態與隱藏側邊欄"""
    # 1. 如果已經有 VIP 手環 (已登入)，直接放行
    if st.session_state.get("password_correct", False):
        return True

    # 2. 🌟 終極魔法：如果還沒登入，強制把左側邊欄、頂部選單按鈕全部隱藏！
    st.markdown(
        """
        <style>
            [data-testid="collapsedControl"] {display: none !important;}
            [data-testid="stSidebar"] {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True
    )

    # 3. 顯示純淨的登入畫面
    st.markdown("<h3 style='text-align: center; margin-top: 50px;'>🔒 紡黏原料管理APP</h3>", unsafe_allow_html=True)
    pwd = st.text_input("請輸入密碼：", type="password", key="pwd_input")
    
    if pwd:
        load_dotenv()
        correct_password = os.getenv("APP_PASSWORD")
        
        if not correct_password:
            try:
                correct_password = st.secrets["APP_PASSWORD"]
            except Exception:
                correct_password = "KNH888" 
        
        if pwd == correct_password:
            st.session_state["password_correct"] = True
            st.rerun() # 密碼正確，重新整理頁面，這時上面的 CSS 隱藏魔法就會解除！
        else:
            st.error("😕 密碼錯誤，請重新輸入！")
            
    return False


def setup_app_ui(user_name="admin"):
    """
    設定全域 UI，包含防護鎖、隱藏預設選單、設定頂部導覽列
    """
    # 🛑 絕對攔截點：在載入任何 UI 之前，先查驗密碼！
    if not check_password():
        st.stop() # 如果沒登入，整個頁面的渲染就停在這裡，完全保護資料！

    # ==========================================
    # 以下是你原本的頂部導覽列與樣式設定 (只有登入成功才會執行到這裡)
    # ==========================================
    
    # 嘗試抓取 Logo
    import base64
    from pathlib import Path
    try:
        logo_data = Path("logo.webp").read_bytes()
        logo_base64 = base64.b64encode(logo_data).decode()
    except Exception:
        logo_base64 = ""

    # 注入 CSS 與頂部導覽列 HTML
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{ background-color: transparent !important; z-index: 999999 !important; }}
        button[kind="header"] {{ color: #111 !important; }}
        .stAppDeployButton {{ display: none !important; }}
        .custom-top-bar {{ position: fixed; top: 0; left: 0; right: 0; height: 56px; background-color: #F4F5F5; border-bottom: 1px solid #DCDCDC; z-index: 999990; display: flex; justify-content: space-between; align-items: center; padding-right: 20px; padding-left: 60px; }}
        .top-bar-left {{ display: flex; align-items: center; gap: 12px; }}
        .top-bar-logo {{ width: 28px; height: 28px; object-fit: contain; }}
        .top-bar-title {{ font-size: 16px; font-weight: 800; color: #111; letter-spacing: 0.5px; }}
        .top-bar-right {{ display: flex; align-items: center; gap: 10px; cursor: pointer; }}
        .top-bar-user-name {{ font-size: 14px; font-weight: 500; color: #333; }}
        .top-bar-avatar {{ width: 30px; height: 30px; border-radius: 50%; background-color: #EAEBEB; color: #555; display: flex; justify-content: center; align-items: center; font-size: 14px; border: 1px solid #DCDCDC; }}
        [data-testid="stSidebar"] {{ margin-top: 56px !important; height: calc(100vh - 56px) !important; }}
        [data-testid="block-container"] {{ padding-top: 80px !important; }}
        [data-testid="stSidebarNav"] li:first-child {{ display: none !important; }}
        /* 隱藏標題旁邊的定錨小鎖鏈 */
        a.header-anchor {{ display: none !important; }}
        .stMarkdown a svg {{ display: none !important; }}
    </style>
    <div class="custom-top-bar">
        <div class="top-bar-left">
            <img src="data:image/webp;base64,{logo_base64}" class="top-bar-logo">
            <span class="top-bar-title">紡黏原料管理APP</span>
        </div>
        <div class="top-bar-right">
            <span class="top-bar-user-name">{user_name}</span>
            <div class="top-bar-avatar">👤</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def alert_card(title, value, subtitle=""):
    """
    Dieter Rams 風格的紅色警報卡片 (用於低水位預警)
    特色：極簡背景、經典警戒紅左側邊框、無圓角或微圓角、高對比字體
    """
    st.markdown(f"""
    <div style="
        background-color: #F9F9F9;
        border-left: 6px solid #D32F2F; /* 經典警戒紅 */
        padding: 16px 24px;
        border-radius: 2px; /* 極簡微圓角 */
        box-shadow: 0 1px 3px rgba(0,0,0,0.08); /* 非常輕微的陰影，避免過度立體 */
        margin-bottom: 16px;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    ">
        <div style="font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">
            {title}
        </div>
        <div style="font-size: 32px; font-weight: 700; color: #111; margin-bottom: 2px; line-height: 1.2;">
            {value}
        </div>
        <div style="font-size: 13px; color: #D32F2F; font-weight: 500;">
            {subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)

def metric_card(title, value, subtitle=""):
    """
    標準數據卡片 (用於一般庫存顯示)
    特色：乾淨、冷靜的工業灰藍色調
    """
    st.markdown(f"""
    <div style="
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-top: 4px solid #607D8B; /* 工業灰藍色 */
        padding: 16px 24px;
        border-radius: 2px;
        margin-bottom: 16px;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    ">
        <div style="font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">
            {title}
        </div>
        <div style="font-size: 32px; font-weight: 700; color: #111; margin-bottom: 2px; line-height: 1.2;">
            {value}
        </div>
        <div style="font-size: 13px; color: #888;">
            {subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)