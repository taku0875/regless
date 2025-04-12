import streamlit as st
from supabase import create_client
from openai import OpenAI
import pandas as pd
from datetime import datetime, date
import plotly.express as px

# -----------------------------
# 페ージ設定 & カラーテーマ選択
# -----------------------------

# カラーテーマ選択
theme = st.sidebar.selectbox("🎨 カラーテーマ", ["ライト", "ダーク", "ブルー"])

# テーマに応じたスタイルを定義
if theme == "ダーク":
    bg_color = "#1e1e1e"
    text_color = "white"
    accent = "#0ff"
elif theme == "ブルー":
    bg_color = "#e6f7ff"
    text_color = "#003366"
    accent = "#3399ff"
else:
    bg_color = "#f9f9f9"
    text_color = "#333"
    accent = "#4facfe"

# CSSを埋め込んでテーマカラーを適用
st.markdown(
    f"""
    <style>
        body {{
            background-color: {bg_color};
            color: {text_color};
        }}
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        h1, h2, h3, h4, h5, h6, p, span {{
            color: {text_color};
        }}
        .css-1emrehy edgvbvh3 {{
            color: {text_color} !important;
        }}
        .stButton > button {{
            background-color: {accent};
            color: white;
            border-radius: 8px;
            border: none;
        }}
        .stSelectbox {{
            color: {text_color};
        }}
        .stTextInput > div > div > input {{
            background-color: #fff;
            color: {text_color};
        }}
    </style>
    """,
    unsafe_allow_html=True
)
# タイトル
st.markdown("<div class='app-title'>📘 RegLess：あなたの人生を彩るバケットリスト</div>", unsafe_allow_html=True)

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
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 やりたいこと登録",
    "👤 自分の目標",
    "🌍 みんなの目標",
    "📊 ガントチャート"
])

# -----------------------------
# やりたいこと登録
# -----------------------------
with tab1:
    st.markdown("## ✏️ やりたいこと登録")
    goal = st.text_input("🌟 やりたいこと", placeholder="例：毎週3回ジムに行く")
    tag = st.text_input("🏷 タグ", placeholder="例：健康")
    deadline = st.date_input("🗓 期限", min_value=date.today())
    time_required = st.slider("🕒 所要時間（時間）", 0, 100, 5)
    cost_estimate = st.slider("💰 想定費用（千円）", 0, 100, 0)
    next_action = st.text_input("▶️ 次のアクション")
    comments = st.text_area("💬 コメント")

    if st.button("💡 OpenAIに提案してもらう"):
        prompt = f"やりたいこと「{goal}」に対して、所要時間・費用・次アクションを提案して下さい"
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

    if st.button("\u2705 登録する"):
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
# 自分の目標
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
🗓 期限: {g['deadline']}  
🕒 所要時間: {g['time_required']} 時間  
💰 想定費用: {g['cost_estimate']} 千円  
▶️ 次のアクション: {g['next_action'] or '未設定'}  
💬 コメント: {g['comments'] or 'なし'}  
️ いいね: {g['likes']}
""")
    else:
        st.info("まだ登録された目標がありません。")

# -----------------------------
# みんなの目標
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
🌟 **{g['goal']}**  
🏷 タグ: {g['tag']}  
🗓 期限: {g['deadline']}  
️ いいね: {g['likes']}  
💬 コメント: {g['comments'] or '（コメントなし）'}
""")

# -----------------------------
# ガントチャート
# -----------------------------
with tab4:
    st.markdown("## 📊 ガントチャート")
    if all_goals:
        df = pd.DataFrame([{
            "Task": g["goal"],
            "Start": datetime.today().date(),
            "Finish": g["deadline"],
            "Tag": g["tag"]
        } for g in all_goals if g["deadline"]])
        if not df.empty:
            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Tag")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ガントチャートに表示できる目標がありません。")
    else:
        st.info("まだ目標が登録されていません。")
