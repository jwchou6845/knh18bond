import streamlit as st

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