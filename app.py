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

# カスタムスタイル（スマホ対応）
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

# アプリタイトル
st.markdown("<div class='app-title'>📘 RegLess：未来にログする人生設計アプリ</div>", unsafe_allow_html=True)

# -----------------------------
# 接続設定
# -----------------------------
supabase = create_client(st.secrets["supabase_url"], st.secrets["supabase_key"])
client = OpenAI(api_key=st.secrets["openai_api_key"])

# -----------------------------
# セッションユーザー管理
# -----------------------------
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
# タブ分割（ガントチャート除外）
# -----------------------------
tab1, tab2, tab3 = st.tabs([
    "📝 やりたいこと登録",
    "👤 自分の目標",
    "🌍 みんなの目標"
])

# -----------------------------
# 📝 やりたいこと登録
# -----------------------------
with tab1:
    st.markdown("## ✏️ やりたいこと登録")
    goal = st.text_input("🎯 やりたいこと", placeholder="例：毎週3回ジムに行く")
    tag = st.text_input("🏷 タグ", placeholder="例：健康")
    deadline = st.date_input("📅 期限", min_value=date.today())
    time_required = st.slider("🕒 所要時間（時間）", 0, 100, 5)
    cost_estimate = st.slider("💰 想定費用（千円）", 0, 100, 0)
    next_action = st.text_input("▶️ 次のアクション")
    comments = st.text_area("💬 コメント")

    if st.button("💡 OpenAIに提案してもらう"):
        prompt = f"やりたいこと「{goal}」に対して、所要時間・費用・次アクションを提案してください"
        with st.spinner("OpenAIが考え中..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "あなたは行動計画アドバイザーです。"},
                        {"role": "user", "content": prompt}
                    ]
                )
                st.success(response.choices[0].message.content.strip())
                st.snow()
            except Exception as e:
                st.error(f"OpenAIエラー: {e}")

    if st.button("✅ 登録する"):
        supabase.table("goals").insert({
            "user_id": user_id,
            "goal": goal,
            "tag": tag,
            "deadline": str(deadline),
            "time_required": str(time_required),
            "cost_estimate": str(cost_estimate),
            "next_action": next_action,
            "likes": 0,
            "comments": comments
        }).execute()
        st.success("📌 登録が完了しました！")
        st.balloons()

# -----------------------------
# 👤 自分の目標一覧
# -----------------------------
with tab2:
    st.markdown("## 👤 あなたの目標一覧")
    my_goals = supabase.table("goals").select("*").eq("user_id", user_id).order("deadline").execute().data
    if my_goals:
        for g in my_goals:
            st.markdown(f"""
---
📌 **{g['goal']}**  
🏷 タグ: {g['tag']}  
📅 期限: {g['deadline']}  
🕒 所要時間: {g['time_required']} 時間  
💰 想定費用: {g['cost_estimate']} 千円  
▶️ 次のアクション: {g['next_action'] or '未設定'}  
💬 コメント: {g['comments'] or 'なし'}  
❤️ いいね: {g['likes']}
""")
    else:
        st.info("まだ登録された目標がありません。")

# -----------------------------
# 🌍 みんなの目標検索
# -----------------------------
with tab3:
    st.markdown("## 🌍 みんなの目標検索")
    tag_filter = st.text_input("🔍 タグでフィルター", "")
    all_goals = supabase.table("goals").select("*").order("deadline").execute().data

    for g in all_goals:
        if tag_filter and tag_filter.lower() not in (g["tag"] or "").lower():
            continue
        st.markdown(f"""
---
🎯 **{g['goal']}**  
🏷 タグ: {g['tag']}  
📅 期限: {g['deadline']}  
❤️ いいね: {g['likes']}  
💬 コメント: {g['comments'] or '（コメントなし）'}
""")
