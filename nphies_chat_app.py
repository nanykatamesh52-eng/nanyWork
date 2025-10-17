# nphies_chat_app.py
import streamlit as st
from nphies_rag_multilang import get_nphies_answer

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! I'm your NPHIES assistant. How may I help you today?"}
    ]
if "language" not in st.session_state:
    st.session_state.language = "English"

# translations
translations = {
    "English": {
        "title": "🏥 NPHIES Chat Assistant",
        "welcome": "👋 Hello! I'm your NPHIES assistant. How may I help you today?",
        "input_placeholder": "Type your NPHIES question here...",
        "thinking": "Thinking...",
        "language_select": "Select Language",
        "change_language": "Change Language",
    },
    "Arabic": {
        "title": "🏥 مساعد نفيس",
        "welcome": "👋 مرحبًا! أنا مساعد نفيس الذكي. كيف يمكنني مساعدتك اليوم؟",
        "input_placeholder": "اكتب سؤالك حول نظام نفيس هنا...",
        "thinking": "جاري التفكير...",
        "language_select": "اختر اللغة",
        "change_language": "تغيير اللغة",
    },
}

st.set_page_config(page_title="NPHIES Assistant", page_icon="💬")

# sidebar language selector
with st.sidebar:
    st.subheader(translations[st.session_state.language]["change_language"])
    language_options = ["English", "Arabic"]
    selected_language = st.selectbox(
        translations[st.session_state.language]["language_select"],
        language_options,
        index=language_options.index(st.session_state.language),
    )
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        if len(st.session_state.messages) == 1 and st.session_state.messages[0]["role"] == "assistant":
            st.session_state.messages[0]["content"] = translations[selected_language]["welcome"]
        st.rerun()

t = translations[st.session_state.language]
st.title(t["title"])

# display chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# chat input
prompt = st.chat_input(t["input_placeholder"])
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner(t["thinking"]):
        reply = get_nphies_answer(prompt, st.session_state.language)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)
