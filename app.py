# RegLessアプリ - Supabase完全移行版

import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import plotly.express as px
from config import supabase_url, supabase_key

supabase = create_client(supabase_url, supabase_key)

st.set_page_config(page_title="RegLess", layout="wide")
st.markdown("""
<style>
html, body, [class*="css"]  { font-size: 16px; }
h1 {text-align: center; color: #336699;}
.block-container {padding-top: 1rem;}
@media only screen and (max-width: 768px) {
  html, body, [class*="css"]  { font-size: 14px; }
}
</style>
""", unsafe_allow_html=True)

st.title("🌟 RegLess：やりたいことを未来にログする")

# --- 認証ステート管理 ---
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False
    st.session_state.user = None

# --- 認証フロー ---
def signup(email, password, name):
    result = supabase.auth.sign_up({"email": email, "password": password})
    if result.user:
        supabase.table("users").insert({
            "id": result.user.id,
            "email": email,
            "name": name
        }).execute()
        return True
    return False

def login(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def get_user():
    return supabase.auth.get_user().user

# --- DB操作 ---
def add_goal(user_id, goal, tag, deadline, time_required, cost, action):
    supabase.table("goals").insert({
        "user_id": user_id,
        "goal": goal,
        "tag": tag,
        "deadline": str(deadline),
        "time_required": time_required,
        "cost_estimate": cost,
        "next_action": action,
        "likes": 0,
        "comments": ""
    }).execute()

def fetch_goals(user_id=None):
    if user_id:
        return supabase.table("goals").select("*").eq("user_id", user_id).execute().data
    else:
        return supabase.table("goals").select("*").execute().data

def like_goal(goal_id):
    row = supabase.table("goals").select("likes").eq("id", goal_id).single().execute()
    likes = row.data["likes"] + 1
    supabase.table("goals").update({"likes": likes}).eq("id", goal_id).execute()

def add_comment(goal_id, comment):
    row = supabase.table("goals").select("comments").eq("id", goal_id).single().execute()
    combined = (row.data["comments"] or "") + "\n" + comment
    supabase.table("goals").update({"comments": combined.strip()}).eq("id", goal_id).execute()

# --- UI処理 ---
if not st.session_state.auth_status:
    auth_tab = st.sidebar.radio("認証", ["ログイン", "新規登録"])
    email = st.sidebar.text_input("メールアドレス")
    password = st.sidebar.text_input("パスワード", type="password")

    if auth_tab == "新規登録":
        name = st.sidebar.text_input("ユーザー名")
        if st.sidebar.button("登録"):
            if signup(email, password, name):
                st.success("登録完了。メールを確認してください。")
    else:
        if st.sidebar.button("ログイン"):
            result = login(email, password)
            if result.session:
                st.session_state.auth_status = True
                st.session_state.user = result.user
                st.rerun()
else:
    user = st.session_state.user
    uid = user.id

    with st.sidebar:
        menu = st.selectbox("メニュー", ["やりたいこと登録", "ダッシュボード", "みんなの目標", "ガントチャート"])
        if st.button("ログアウト"):
            supabase.auth.sign_out()
            st.session_state.auth_status = False
            st.session_state.user = None
            st.rerun()

    if menu == "やりたいこと登録":
        st.header("📝 やりたいこと登録")
        goal = st.text_input("やりたいこと")
        tag = st.text_input("タグ")
        deadline = st.date_input("期限")

        if st.button("登録"):
            add_goal(uid, goal, tag, deadline, "", "", "")
            st.success("登録しました")

    elif menu == "ダッシュボード":
        st.header("📋 あなたの目標一覧")
        for g in fetch_goals(uid):
            st.markdown(f"""
---
🎯 {g['goal']}
🏷️ {g['tag']}  📅 {g['deadline']}
📝 {g['next_action']}  ❤️ {g['likes']}
💬 {g['comments'] or '（コメントなし）'}
""")
            comment = st.text_input("コメント", key=f"c{g['id']}")
            if st.button("送信", key=f"cm{g['id']}"):
                add_comment(g['id'], comment)
                st.rerun()
            if st.button("👍", key=f"lk{g['id']}"):
                like_goal(g['id'])
                st.rerun()

    elif menu == "みんなの目標":
        st.header("🌍 他ユーザーの目標")
        tag_filter = st.text_input("タグで検索")
        for g in fetch_goals():
            if tag_filter and tag_filter.lower() not in g["tag"].lower():
                continue
            st.markdown(f"""
---
👤 ユーザーID: {g['user_id']}
🎯 {g['goal']}
🏷️ {g['tag']}  📅 {g['deadline']}  ❤️ {g['likes']}
💬 {g['comments'] or '（コメントなし）'}
""")

    elif menu == "ガントチャート":
        st.header("📊 ガントチャート")
        goals = fetch_goals(uid)
        if goals:
            df = pd.DataFrame([{"Task": g['goal'], "Start": datetime.today().date(), "Finish": g['deadline'], "Tag": g['tag']} for g in goals])
            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Tag")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig)
        else:
            st.info("目標が登録されていません。")