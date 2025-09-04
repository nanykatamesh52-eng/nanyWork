import assemblyai as aai
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
from openai import OpenAI
from dotenv import load_dotenv
import pyaudio
import wave
import threading
import os
load_dotenv()

class AI_Assistant:
    def __init__(self):
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        print(openai_api_key)
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.elevenlabs_api_key = elevenlabs_api_key
        self.eleven_client = ElevenLabs(api_key=self.elevenlabs_api_key)
        self.full_transcript = [
            {"role": "system", "content": "You are a receptionist at a dental clinic. Be resourceful and efficient."},
        ]
        self.is_recording = False

    def record_audio(self, filename, duration=5):
        """Record audio for a specified duration"""
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                       channels=1,
                       rate=16000,
                       input=True,
                       frames_per_buffer=1024)
        
        print("Recording...")
        frames = []
        for _ in range(0, int(16000 / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save to file
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return filename

    def transcribe_audio(self, filename):
        """Transcribe audio file"""
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(filename)
        return transcript.text if transcript else ""

    def start_listening(self):
        """Main listening loop"""
        while True:
            input("Press Enter to start recording (or Ctrl+C to exit)...")
            audio_file = "temp_audio.wav"
            self.record_audio(audio_file, duration=5)
            text = self.transcribe_audio(audio_file)
            
            if text:
                print(f"You said: {text}")
                self.generate_ai_response(text)

    def generate_ai_response(self, text):
        self.full_transcript.append({"role": "user", "content": text})
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.full_transcript,
        )

        ai_response = response.choices[0].message.content
        self.generate_audio(ai_response)

    def generate_audio(self, text):
        self.full_transcript.append({"role": "assistant", "content": text})
        print(f"AI: {text}")

        audio_stream = self.eleven_client.text_to_speech.stream(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            model_id="eleven_multilingual_v2",
            text=text,
        )
        stream(audio_stream)

# Run the assistant
greeting = "Thank you for calling Vancouver dental clinic. My name is Sandy, how may I assist you?"
ai_assistant = AI_Assistant()
ai_assistant.generate_audio(greeting)
ai_assistant.start_listening()