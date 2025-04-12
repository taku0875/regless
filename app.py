import streamlit as st
from supabase import create_client
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
import openai

# SupabaseとOpenAIの接続設定（Streamlit Secretsに設定）
supabase_url = st.secrets["supabase_url"]
supabase_key = st.secrets["supabase_key"]
openai.api_key = st.secrets["openai_api_key"]
supabase = create_client(supabase_url, supabase_key)

# ページレイアウト設定
st.set_page_config(page_title="RegLess", layout="wide")
st.title("RegLess：やりたいことを未来にログする")

# ----------------------------
# 📝 やりたいこと登録 + OpenAI壁打ち
# ----------------------------
st.header("やりたいこと登録（ログイン不要）")
goal = st.text_input("やりたいこと")
tag = st.text_input("タグ")
deadline = st.date_input("期限")

if st.button("OpenAIに相談してみる"):
    prompt = f"以下のやりたいことに対して、所要時間・費用・次のアクションを簡潔に提案してください：{goal}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは行動計画アドバイザーです。"},
                {"role": "user", "content": prompt}
            ]
        )
        suggestion = response.choices[0].message.content.strip()
        st.markdown("### OpenAIからの提案")
        st.success(suggestion)
    except Exception as e:
        st.error(f"OpenAIエラー: {e}")

if st.button("登録"):
    supabase.table("goals").insert({
        "user_id": "public-user",
        "goal": goal,
        "tag": tag,
        "deadline": str(deadline),
        "time_required": "",
        "cost_estimate": "",
        "next_action": "",
        "likes": 0,
        "comments": ""
    }).execute()
    st.success("登録しました")

# ----------------------------
# 🌍 みんなの目標一覧
# ----------------------------
st.header("みんなの目標")
tag_filter = st.text_input("タグで検索")
goals = supabase.table("goals").select("*").execute().data

for g in goals:
    if tag_filter and tag_filter.lower() not in g["tag"].lower():
        continue
    st.markdown(f'''
---
{g['goal']}
タグ: {g['tag']}  期限: {g['deadline']}  いいね: {g['likes']}
コメント: {g['comments'] or '（コメントなし）'}
''')

# ----------------------------
# 📊 ガントチャート可視化
# ----------------------------
st.header("ガントチャート")
if goals:
    df = pd.DataFrame([{
        "Task": g["goal"],
        "Start": datetime.today().date(),
        "Finish": g["deadline"],
        "Tag": g["tag"]
    } for g in goals])
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Tag")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig)
else:
    st.info("目標がまだ登録されていません。")
