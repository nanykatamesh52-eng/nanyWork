import streamlit as st
from assistant import AI_Assistant
import re

# Initialize session state
if "assistant" not in st.session_state:
    st.session_state.assistant = AI_Assistant()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! I'm your AI receptionist. How may I help you today?"}
    ]

if "language" not in st.session_state:
    st.session_state.language = "English"

if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
# ✅ Force sync assistant language with UI choice
st.session_state.assistant.set_language(st.session_state.language)

# Language translations
translations = {
    "English": {
        "title": "🏥 AI Receptionist",
        "welcome": "👋 Hello! I'm your AI receptionist. How may I help you today?",
        "input_placeholder": "Type your request here...",
        "start_recording": "🎤 Start Recording",
        "stop_recording": "⏹ Stop Recording",
        "thinking": "Thinking...",
        "recording_complete": "✅ Recording complete",
        "transcription_error": "Transcription error:",
        "play_audio": "🔊 Play Last Response as Audio",
        "audio_success": "Audio played successfully",
        "audio_error": "Failed to generate audio",
        "language_select": "Select Language",
        "change_language": "Change Language"
    },
    "Arabic": {
        "title": "🏥 مساعد الاستقبال الافتراضي",
        "welcome": "👋 مرحبًا! أنا مساعد الاستقبال الافتراضي. كيف يمكنني مساعدتك اليوم؟",
        "input_placeholder": "اكتب طلبك هنا...",
        "start_recording": "🎤 بدء التسجيل",
        "stop_recording": "⏹ إيقاف التسجيل",
        "thinking": "جاري التفكير...",
        "recording_complete": "✅ اكتمل التسجيل",
        "transcription_error": "خطأ في التحويل إلى نص:",
        "play_audio": "🔊 تشغيل آخر رد بصوت",
        "audio_success": "تم تشغيل الصوت بنجاح",
        "audio_error": "فشل توليد الصوت",
        "language_select": "اختر اللغة",
        "change_language": "تغيير اللغة"
    }
}

# Page config
st.set_page_config(page_title="AI Receptionist", page_icon="🤖")

# Sidebar language selector
with st.sidebar:
    st.subheader(translations[st.session_state.language]["change_language"])
    language_options = ["English", "Arabic"]
    selected_language = st.selectbox(
        translations[st.session_state.language]["language_select"],
        language_options,
        index=language_options.index(st.session_state.language)
    )

    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.session_state.assistant.set_language(selected_language)

        if len(st.session_state.messages) == 1 and st.session_state.messages[0]["role"] == "assistant":
            st.session_state.messages[0]["content"] = translations[selected_language]["welcome"]

        st.rerun()

# Get translations
t = translations[st.session_state.language]

st.title(t["title"])

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])
    else:
        st.chat_message("user").write(msg["content"])


# --- Recording logic ---
def start_recording():
    st.session_state.is_recording = True
    st.session_state.recorded_file = "recorded_audio.wav"
    st.session_state.assistant.start_recording(st.session_state.recorded_file)


def stop_recording():
    st.session_state.is_recording = False
    filename = st.session_state.assistant.stop_recording()
    st.success(t["recording_complete"])

    # Transcribe
    user_text = st.session_state.assistant.transcribe_audio(filename)
    if user_text and not user_text.startswith("Error"):
        st.session_state.messages.append({"role": "user", "content": user_text})
        st.chat_message("user").write(user_text)

        with st.spinner(t["thinking"]):
            reply = st.session_state.assistant.generate_ai_response(user_text, st.session_state.language)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)
    elif user_text:
        st.error(f"{t['transcription_error']} {user_text}")


# --- Input + Voice ---
col1, col2 = st.columns([4, 1])
with col1:
    prompt = st.chat_input(t["input_placeholder"])
with col2:
    if not st.session_state.is_recording:
        st.button(t["start_recording"], use_container_width=True, on_click=start_recording)
    else:
        st.button(t["stop_recording"], use_container_width=True, on_click=stop_recording)

# Handle text input
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner(t["thinking"]):
        reply = st.session_state.assistant.generate_ai_response(prompt,st.session_state.language)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)

# Play last response as audio
st.session_state.play_audio = True
if (st.session_state.messages and
    st.session_state.messages[-1]["role"] == "assistant" and
    st.session_state.play_audio):

    last_response = st.session_state.messages[-1]["content"]
    if st.button(t["play_audio"]):
        with st.spinner(t["thinking"]):
            text_to_speak = last_response
            if st.session_state.language == "Arabic":
                text_to_speak = st.session_state.assistant.convert_english_to_arabic_text(text_to_speak)

            success = st.session_state.assistant.generate_audio(text_to_speak)
        if success:
            st.success(t["audio_success"])
        else:
            st.error(t["audio_error"])
