import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import plotly.express as px
from openai import OpenAI

# ====== 接続情報 ======
supabase = create_client(
    st.secrets["supabase_url"],
    st.secrets["supabase_key"]
)
client = OpenAI(api_key=st.secrets["openai_api_key"])

# ====== ページ基本設定 ======
st.set_page_config(page_title="RegLess", layout="wide")

# ====== スタイル（CSS） ======
st.markdown("""
<style>
body {
    background-color: #f4f7f9;
    font-family: 'Helvetica Neue', sans-serif;
}
section {
    background-color: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    margin-bottom: 2rem;
}
.stButton > button {
    background: linear-gradient(to right, #4facfe, #00f2fe);
    color: white;
    font-weight: bold;
    padding: 0.5rem 1.2rem;
    border: none;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ====== タイトル ======
st.markdown("<h1 style='color:#2c3e50'>🪄 RegLess：未来にやりたいことをログする</h1>", unsafe_allow_html=True)

# ====== 残り寿命計算 ======
with st.container():
    st.markdown("## 🧬 あなたの基本情報")
    birthdate = st.date_input("生年月日", value=date(1990, 1, 1))
    expected_lifespan = st.slider("想定寿命（年）", 50, 120, 85)

    today = date.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    death_date = date(birthdate.year + expected_lifespan, birthdate.month, birthdate.day)
    remaining_days = (death_date - today).days
    remaining_years = remaining_days // 365

    st.markdown(f"🌱 **現在年齢：{age}歳**")
    st.markdown(f"⏳ **残り寿命：約 {remaining_years}年（{remaining_days}日）**")

# ====== ユーザー登録（セッション制御） ======
if "user_id" not in st.session_state:
    new_user = supabase.table("users").insert({
        "email": f"guest_{datetime.now().timestamp()}@example.com",
        "name": "ゲスト"
    }).execute()
    st.session_state["user_id"] = new_user.data[0]["id"]

# ====== やりたいこと登録フォーム ======
with st.container():
    st.markdown("## ✏️ やりたいこと登録")
    goal = st.text_input("🎯 やりたいこと", placeholder="例：週3回ジムに行く")
    tag = st.text_input("🏷 タグ", placeholder="例：健康")
    deadline = st.date_input("📅 期限")

    if st.button("💡 OpenAIに提案をもらう"):
        prompt = f"以下のやりたいことに対して、所要時間・費用・次のアクションを簡潔に提案してください：{goal}"
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは行動計画アドバイザーです。"},
                    {"role": "user", "content": prompt}
                ]
            )
            suggestion = response.choices[0].message.content.strip()
            st.markdown("### ✨ OpenAIからの提案")
            st.success(suggestion)
        except Exception as e:
            st.error(f"OpenAIエラー: {e}")

    if st.button("✅ 登録する"):
        supabase.table("goals").insert({
            "user_id": st.session_state["user_id"],
            "goal": goal,
            "tag": tag,
            "deadline": str(deadline),
            "time_required": "",
            "cost_estimate": "",
            "next_action": "",
            "likes": 0,
            "comments": ""
        }).execute()
        st.success("📌 登録が完了しました！")

# ====== 一覧表示 ======
st.markdown("## 📋 みんなの目標一覧")
tag_filter = st.text_input("🔍 タグでフィルター", "")

try:
    goals = supabase.table("goals").select("*").order("deadline", desc=False).execute().data
    for g in goals:
        if tag_filter and tag_filter.lower() not in (g["tag"] or "").lower():
            continue
        st.markdown(f"""
---
✅ **{g['goal']}**  
🏷 タグ: {g['tag']}  
📅 期限: {g['deadline']}  
❤️ いいね: {g['likes']}  
💬 コメント: {g['comments'] or '（コメントなし）'}
        """)
except Exception as e:
    st.error(f"取得エラー: {e}")

# ====== ガントチャート ======
st.markdown("## 📊 ガントチャート（予定一覧）")
if goals:
    df = pd.DataFrame([{
        "Task": g["goal"],
        "Start": datetime.today().date(),
        "Finish": g["deadline"],
        "Tag": g["tag"]
    } for g in goals if g["deadline"]])
    if not df.empty:
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Tag")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig)
    else:
        st.info("表示できる目標がありません。")
