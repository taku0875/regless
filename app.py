import streamlit as st
from supabase import create_client
from openai import OpenAI
import pandas as pd
from datetime import datetime, date

# -----------------------------
# ページ設定 & カラーテーマ選択
# -----------------------------
st.set_page_config(page_title="RegLess", layout="wide")

theme = st.sidebar.selectbox("🎨 カラーテーマ", ["ライト", "ダーク", "ブルー"])
if theme == "ダーク":
    bg_color = "#1e1e1e"; text_color = "white"; accent = "#0ff"
elif theme == "ブルー":
    bg_color = "#e6f7ff"; text_color = "#003366"; accent = "#3399ff"
else:
    bg_color = "#f9f9f9"; text_color = "#333"; accent = "#4facfe"

# カスタムスタイル
st.markdown(f"""
<style>
body {{
    background-color: {bg_color};
    color: {text_color};
    font-family: 'Helvetica Neue', sans-serif;
}}
.stButton > button {{
    background: {accent};
    color: white;
    font-weight: bold;
    padding: 0.5rem 1.2rem;
    border: none;
    border-radius: 8px;
}}
.app-title {{
    text-align: center;
    font-size: 2rem;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    color: {text_color};
}}
</style>
""", unsafe_allow_html=True)

# タイトル
st.markdown("<div class='app-title'>📘 RegLess：未来にログする人生設計アプリ</div>", unsafe_allow_html=True)

# -----------------------------
# 接続設定
# -----------------------------
supabase = create_client(st.secrets["supabase_url"], st.secrets["supabase_key"])
client = OpenAI(api_key=st.secrets["openai_api_key"])

# ユーザーID管理
if "user_id" not in st.session_state:
    new_user = supabase.table("users").insert({
        "email": f"guest_{datetime.now().timestamp()}@example.com",
        "name": "ゲスト"
    }).execute()
    st.session_state["user_id"] = new_user.data[0]["id"]
    st.session_state["welcomed"] = False

if not st.session_state.get("welcomed", False):
    st.success("ようこそ RegLess へ！")
    st.balloons()
    st.session_state["welcomed"] = True

user_id = st.session_state["user_id"]

# -----------------------------
# タブ分割
# -----------------------------
tab1, tab2, tab3 = st.tabs([
    "📝 やりたいこと登録",
    "👤 自分の目標",
    "🌍 みんなの目標"
])

# 以下、各タブの処理を残し、
# ガントチャートタブを削除

# やりたいこと登録 (tab1)
# 自分の目標 (tab2)
# みんなの目標 (tab3)
# …（それぞれの中身はそのまま）
