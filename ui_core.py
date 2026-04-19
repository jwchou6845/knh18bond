import streamlit as st
import os
from dotenv import load_dotenv
import streamlit.components.v1 as components # 🌟 引入 components 以執行 JS

def check_password():
    """全域警衛室：檢查登入狀態與隱藏側邊欄"""
    if st.session_state.get("password_correct", False):
        return True

    # 如果還沒登入，強制把左側邊欄、頂部選單按鈕全部隱藏！
    st.markdown(
        """
        <style>
            [data-testid="collapsedControl"] {display: none !important;}
            [data-testid="stSidebar"] {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True
    )

    # 顯示純淨的登入畫面
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
            st.rerun() 
        else:
            st.error("😕 密碼錯誤，請重新輸入！")
            
    return False


def setup_app_ui(user_name="admin"):
    """
    設定全域 UI，包含防護鎖、雙重隱藏防禦 (CSS+JS)、手機全螢幕設定
    """
    # 🛑 絕對攔截點
    if not check_password():
        st.stop() 

    # --- 1. 抓取 Logo ---
    import base64
    from pathlib import Path
    try:
        logo_data = Path("logo.webp").read_bytes()
        logo_base64 = base64.b64encode(logo_data).decode()
    except Exception:
        logo_base64 = ""

    # ==========================================
    # 🛡️ 防禦第一層：無敵 CSS 靜態防禦與 UI 樣式
    # ==========================================
    css_style = """
    <style>
        /* 🧹 隱藏 Streamlit 原生元素 */
        [data-testid="stToolbar"] { display: none !important; visibility: hidden !important; }
        [data-testid="stAppToolbar"] { display: none !important; } /* 針對最新版 Cloud 工具列 */
        [data-testid="stAppDeployButton"] { display: none !important; }
        .viewerBadge_container__1QSob, .viewerBadge_link__1S137, div[class^="viewerBadge"] { display: none !important; }
        footer { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        
        /* 🔗 隱藏標題旁邊的定錨小鎖鏈 */
        a.header-anchor { display: none !important; }
        .stMarkdown a svg { display: none !important; }
        
        /* 📐 處理 Header 與 Sidebar 空間 */
        header[data-testid="stHeader"] { background-color: transparent !important; z-index: 999999 !important; }
        button[kind="header"] { color: #111 !important; }
        [data-testid="stSidebar"] { margin-top: 56px !important; height: calc(100vh - 56px) !important; }
        [data-testid="block-container"] { padding-top: 80px !important; }
        [data-testid="stSidebarNav"] li:first-child { display: none !important; }

        /* 🎨 自訂頂部導覽列 */
        .custom-top-bar { position: fixed; top: 0; left: 0; right: 0; height: 56px; background-color: #F4F5F5; border-bottom: 1px solid #DCDCDC; z-index: 999990; display: flex; justify-content: space-between; align-items: center; padding-left: 60px; }
        
        /* 🛡️ 領空防撞機制 */
        @media (min-width: 768px) { .custom-top-bar { padding-right: 170px; } }
        @media (max-width: 767px) { .custom-top-bar { padding-right: 20px; } }

        .top-bar-left { display: flex; align-items: center; gap: 12px; }
        .top-bar-logo { width: 28px; height: 28px; object-fit: contain; }
        .top-bar-title { font-size: 16px; font-weight: 800; color: #111; letter-spacing: 0.5px; }
        .top-bar-right { display: flex; align-items: center; gap: 10px; cursor: pointer; }
        .top-bar-user-name { font-size: 14px; font-weight: 500; color: #333; }
        .top-bar-avatar { width: 30px; height: 30px; border-radius: 50%; background-color: #EAEBEB; color: #555; display: flex; justify-content: center; align-items: center; font-size: 14px; border: 1px solid #DCDCDC; }
    </style>
    """
    st.markdown(css_style, unsafe_allow_html=True)

    # ==========================================
    # 📱 介面渲染：手機全螢幕咒語 & 頂部導覽列 HTML
    # ==========================================
    html_ui = f"""
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#F4F5F5">

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
    """
    st.markdown(html_ui, unsafe_allow_html=True)

    # ==========================================
    # ⚔️ 防禦第二層：JS 刺客動態巡邏 (含 CSP 保護)
    # ==========================================
    js_assassin = """
    <script>
        let parentDoc;
        try {
            parentDoc = window.parent.document;
        } catch(e) {
            // 被 CSP 擋住時，退回操作自身 document
            parentDoc = document;
            console.warn('無法存取 parent document，CSP 限制:', e);
        }

        const hitList = [
            '[data-testid="stToolbar"]',
            '[data-testid="stAppToolbar"]',
            '[data-testid="stAppDeployButton"]',
            '[class^="viewerBadge"]',
            'footer'
        ];

        function executeAssassination() {
            hitList.forEach(selector => {
                parentDoc.querySelectorAll(selector).forEach(target => {
                    target.style.setProperty('display', 'none', 'important');
                    target.style.setProperty('visibility', 'hidden', 'important');
                    target.style.setProperty('opacity', '0', 'important');
                    target.style.setProperty('pointer-events', 'none', 'important');
                });
            });
        }

        executeAssassination();

        const observer = new MutationObserver(executeAssassination);
        observer.observe(parentDoc.body, { childList: true, subtree: true });
    </script>
    """
    # 執行 JS 刺客 (隱形模式)
    components.html(js_assassin, width=0, height=0)


# ==========================================
# 下方為你原本的卡片元件 (維持不變)
# ==========================================
def alert_card(title, value, subtitle=""):
    """Dieter Rams 風格的紅色警報卡片"""
    st.markdown(f"""
    <div style="background-color: #F9F9F9; border-left: 6px solid #D32F2F; padding: 16px 24px; border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 16px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <div style="font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">{title}</div>
        <div style="font-size: 32px; font-weight: 700; color: #111; margin-bottom: 2px; line-height: 1.2;">{value}</div>
        <div style="font-size: 13px; color: #D32F2F; font-weight: 500;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def metric_card(title, value, subtitle=""):
    """標準數據卡片"""
    st.markdown(f"""
    <div style="background-color: #FFFFFF; border: 1px solid #E0E0E0; border-top: 4px solid #607D8B; padding: 16px 24px; border-radius: 2px; margin-bottom: 16px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <div style="font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">{title}</div>
        <div style="font-size: 32px; font-weight: 700; color: #111; margin-bottom: 2px; line-height: 1.2;">{value}</div>
        <div style="font-size: 13px; color: #888;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)