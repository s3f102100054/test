import openai
import json
import streamlit as st
from st_audiorec import st_audiorec
from tempfile import NamedTemporaryFile
from openai import OpenAI
import io
import time

st.set_page_config(page_title="居住者サポートシステム", page_icon="./image/DALL·E 2023-12-13.png")

if "all_text" not in st.session_state:
    st.session_state.all_text = []

with st.sidebar:
    st.markdown("## 居住者サポートシステム\n# 🤖いえなびくん🤖")

    api_key = st.text_input("OPEN_AI_KEY", type="password")
    mode = st.selectbox("モードを選択", options=["テキスト入力", "音声入力"])

if api_key:
    openai.api_key = api_key
    client = OpenAI(
    api_key=api_key
)

    thread = client.beta.threads.create()
    fileidlist = []

    if mode =="テキスト入力":
        user_prompt = st.chat_input("あなたの質問:")
        assistant_text = ""

        for text_info in st.session_state.all_text:
            with st.chat_message(text_info["role"], avatar=text_info["role"]):
                st.write(text_info["role"] + ":\n\n" + text_info["content"])

        if user_prompt:
            with st.chat_message("あなた", avatar="user"):
                    st.write("あなた" + ":\n\n" + user_prompt)
            st.session_state.all_text.append({
                "role": "あなた",
                "content": user_prompt,
                "avatar": "user" 
            })

            if len(st.session_state.all_text) > 10:
                st.session_state.all_text.pop(1)

            # Assistants APIを使って回答を取得
            messages = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_prompt
            )

            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id="asst_qE2cw2uUTwGpF4HADzrnAxQm"
            )

            while run.status != "completed":
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                time.sleep(1)

            # メッセージを時系列に並べて表示
            message_list = client.beta.threads.messages.list(thread_id=thread.id)
            sorted_messages = sorted(message_list.data, key=lambda x: x.created_at)

            # アシスタントからの最新のメッセージを取得
            for message in sorted_messages:
                if message.role == "assistant":
                    for content_item in message.content:
                        if content_item.type == 'text':
                            assistant_text = content_item.text.value
                            with st.chat_message("いえなびくん", avatar="./image/DALL·E 2023-12-13.png"):
                                    st.write("いえなびくん" + ":\n\n" + assistant_text)
                            break

            st.session_state.all_text.append(
                {"role": "いえなびくん", "content": assistant_text,"avatar": "./image/DALL·E 2023-12-13.png"}
            )

    elif mode == "音声入力":
        wav_audio_data = st_audiorec()
        if st.button("質問を送信"):
            if wav_audio_data:
                # 音声をテキストに変換
                with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(wav_audio_data)
                    temp_file.flush()

                    with open(temp_file.name, "rb") as audio_file:
                        transcript = openai.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="text",
                        )
                        user_prompt = transcript
                        if user_prompt:
                            with st.chat_message("user", avatar="user"):
                                st.write("あなた" + ":\n\n" + user_prompt)

                # Assistants APIを使って回答を取得
                messages = client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=user_prompt
                )

                # スレッドの実行
                run = client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id="asst_qE2cw2uUTwGpF4HADzrnAxQm"
                )

                # スレッドのステータスを確認
                while run.status != "completed":
                    run = client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    time.sleep(1)

                messages = client.beta.threads.messages.list(thread_id=thread.id)
                for message in messages:
                    if message.role == "assistant":
                        for content_item in message.content:
                            if content_item.type == 'text':
                                assistant_text = content_item.text.value
                                with st.chat_message("assistant", avatar="./image/DALL·E 2023-12-13.png"):
                                    st.write("いえなびくん" + ":\n\n" + assistant_text)
                                break

                # 回答を音声に変換
                audio_response = openai.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input=assistant_text,
                )

                audio_data = audio_response.content
                byte_stream = io.BytesIO(audio_data)
                st.audio(byte_stream)

else:
    st.info("👈OPEN_AI_KEYを入力してください")
