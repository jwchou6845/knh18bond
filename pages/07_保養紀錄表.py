import streamlit as st
# 🌟 1. 匯入你的超級小幫手模組
from config import airtable_api, BASE_ID, TABLES
from ui_core import setup_app_ui, alert_card

# --- 1. 頁面基本設定 (必須在第一行) ---
st.set_page_config(page_title="保養紀錄 | KNH MMS", layout="wide", initial_sidebar_state="collapsed")
setup_app_ui(user_name="admin")
