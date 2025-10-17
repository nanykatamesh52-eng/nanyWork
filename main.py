from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
import html
from assistant import AI_Assistant

app = FastAPI()
assistant = AI_Assistant()

@app.post("/webhook")
async def whatsapp_webhook(From: str = Form(...), Body: str = Form(...)):
    print(f"📩 WhatsApp from {From}: {Body}")

    try:
        reply_text = assistant.generate_ai_response(Body, "Arabic")
        print(f"✅ Generated reply: {reply_text}")
    except Exception as e:
        print(f"⚠️ Error generating reply: {e}")
        reply_text = "⚠️ Sorry, something went wrong. Please try again later."

    # ✅ Escape &, <, > for XML safety
    reply_text = html.escape(reply_text)

    # ✅ Support long messages by splitting into chunks
    MAX_LEN = 1500
    chunks = [reply_text[i:i+MAX_LEN] for i in range(0, len(reply_text), MAX_LEN)]
    xml_messages = "".join([f"<Message>{c}</Message>" for c in chunks])

    return PlainTextResponse(f"<Response>{xml_messages}</Response>", media_type="application/xml")
