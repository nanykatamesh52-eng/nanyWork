import assemblyai as aai
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
from openai import OpenAI
from dotenv import load_dotenv
import pyaudio
import wave
import requests
import os
import json
from datetime import datetime, timedelta
import re

load_dotenv()


class AI_Assistant:
    def __init__(self):
        # API keys
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

        # Debug check
        print("🔑 OpenAI key loaded:", bool(openai_api_key))

        # Clients
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.eleven_client = ElevenLabs(api_key=elevenlabs_api_key)

        # Conversation history
        self.full_transcript = [
            {"role": "system", "content": "You are a receptionist at a medical clinic. Be resourceful and efficient. When booking appointments, make sure to collect all necessary information including patient details, doctor, date, and time slot."},
        ]

        # API setup
        self.base_url = "https://demonitcotekapitabebcom.careofme.net"
        self.common_headers = {
            "ProviderId": "5b7596f1-565f-4b5f-b1bb-8b31a9f076ea",
            "BranchId": "23",
            "org": "12",
            "Content-Type": "application/json",
            "Authorization": "Basic QXBwdEZhcmFiaTpBcHB0RmFyYWJpMjk1"
        }

    # ------------------ Audio Functions ------------------

    def record_audio(self, filename, duration=5):
        """Record audio for a specified duration"""
        p = pyaudio.PyAudio()
        stream_in = p.open(format=pyaudio.paInt16,
                           channels=1,
                           rate=16000,
                           input=True,
                           frames_per_buffer=1024)

        print("🎙️ Recording...")
        frames = []
        for _ in range(0, int(16000 / 1024 * duration)):
            data = stream_in.read(1024)
            frames.append(data)

        stream_in.stop_stream()
        stream_in.close()
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
        """Transcribe audio file with AssemblyAI"""
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(filename)
        return transcript.text if transcript else ""

    def generate_audio(self, text):
        """Convert AI text response to speech"""
        self.full_transcript.append({"role": "assistant", "content": text})
        print(f"🤖 AI: {text}")

        audio_stream = self.eleven_client.text_to_speech.stream(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            model_id="eleven_multilingual_v2",
            text=text,
        )
        stream(audio_stream)

    # ------------------ API Calls ------------------

    def get_clinics(self):
        """Get all clinics"""
        url = f"{self.base_url}/api/wa/Lookup"
        payload = {"Type": "1"}
        r = requests.post(url, headers=self.common_headers, json=payload, verify=False)

        try:
            return r.json()
        except Exception:
            print("❌ get_clinics failed")
            print("Status:", r.status_code)
            print("Response:", r.text[:500])
            return {"error": "Invalid response from get_clinics"}

    def get_doctors(self, clinic_code: str):
        """Get doctors in a clinic by clinic code"""
        url = f"{self.base_url}/api/wa/Lookup"
        payload = {"Type": "2", "Id": clinic_code}
        r = requests.post(url, headers=self.common_headers, json=payload, verify=False)

        try:
            return r.json()
        except Exception:
            print("❌ get_doctors failed")
            print("Status:", r.status_code)
            print("Response:", r.text[:500])
            return {"error": "Invalid response from get_doctors"}

    def check_doctor_availability(self, doctor_code: str, date: str = None):
        """Check if a doctor is available on a specific date"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Validate date format (YYYY-MM-DD)
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            return {"error": f"Invalid date format: {date}. Please use YYYY-MM-DD format."}
        
        url = f"{self.base_url}/api/Appointment/GetPatientAppointments"
        payload = {
            "StartDate": date,
            "DoctorCode": doctor_code,
            "IS_TeleMed": False,
            "PatientCode": "",
            "Lang": ""
        }
        
        try:
            r = requests.post(url, headers=self.common_headers, json=payload, verify=False)
            response_data = r.json()
            
            # Analyze the response to determine availability
            if isinstance(response_data, list):
                # If we get a list of appointments, check availability
                available_slots = len([appt for appt in response_data if appt.get('Available', True)])
                total_slots = len(response_data)
                
                return {
                    "available": available_slots > 0,
                    "available_slots": available_slots,
                    "total_slots": total_slots,
                    "date": date,
                    "doctor_code": doctor_code,
                    "details": f"Found {available_slots} available slots out of {total_slots} total slots on {date}"
                }
            elif isinstance(response_data, dict):
                # Handle dictionary response
                return {
                    "available": response_data.get('Available', False),
                    "date": date,
                    "doctor_code": doctor_code,
                    "details": response_data
                }
            else:
                return {
                    "available": False,
                    "date": date,
                    "doctor_code": doctor_code,
                    "details": response_data,
                    "error": "Unexpected response format"
                }
                
        except Exception as e:
            print(f"❌ check_doctor_availability failed: {e}")
            print("Status:", r.status_code if 'r' in locals() else "No response")
            print("Response:", r.text[:500] if 'r' in locals() else "No response")
            return {
                "error": f"Failed to check availability: {str(e)}",
                "date": date,
                "doctor_code": doctor_code
            }

    def book_appointment(self, app_date: str, slot_id: str, pat_code: str, pat_nameAr: str, 
                        identity_no: str, mobile_no: str, dr_code: str, cinicDept_code: str,
                        pat_age: str = "", dr_codeText: str = ""):
        """Book an appointment with the given details"""
        
        payload = {
            "app_Date": app_date,
            "slot_id": slot_id,
            "pat_code": pat_code,
            "pat_nameAr": pat_nameAr,
            "identity_no": identity_no,
            "mobile_no": mobile_no,
            "pat_age": pat_age,
            "dr_code": dr_code,
            "dr_codeText": dr_codeText,
            "CinicDept_Code": cinicDept_code
        }
        
        url = f"{self.base_url}/api/Appointment/InsertAppointment"
        
        try:
            r = requests.post(url, headers=self.common_headers, json=payload, verify=False)
            
            if r.status_code == 200:
                try:
                    response_data = r.json()
                    return {
                        "success": True,
                        "message": "Appointment booked successfully",
                        "appointment_details": response_data,
                        "booking_data": payload
                    }
                except:
                    # If response is not JSON, return text
                    return {
                        "success": True,
                        "message": "Appointment booked successfully",
                        "raw_response": r.text,
                        "booking_data": payload
                    }
            else:
                return {
                    "success": False,
                    "error": f"Failed to book appointment. Status code: {r.status_code}",
                    "response": r.text,
                    "booking_data": payload
                }
                
        except Exception as e:
            print(f"❌ book_appointment failed: {e}")
            return {
                "success": False,
                "error": f"Failed to book appointment: {str(e)}",
                "booking_data": payload
            }

    def extract_date_from_text(self, text):
        """Extract date information from user text using simple pattern matching"""
        text_lower = text.lower()
        
        # Today
        if 'today' in text_lower:
            return datetime.now().strftime("%Y-%m-%d")
        
        # Tomorrow
        if 'tomorrow' in text_lower:
            tomorrow = datetime.now() + timedelta(days=1)
            return tomorrow.strftime("%Y-%m-%d")
        
        # Specific date patterns
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY
            r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY
            r'(\d{1,2}/\d{1,2})',    # MM/DD (current year)
            r'(\d{1,2}-\d{1,2})',    # MM-DD (current year)
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    if len(date_str.split('/')) == 2 or len(date_str.split('-')) == 2:
                        date_str = f"{datetime.now().year}-{date_str.replace('/', '-')}"
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue
        
        return None

    def extract_time_slot(self, text):
        """Extract time slot information from user text"""
        text_lower = text.lower()
        
        # Common time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',
            r'(\d{1,2}:\d{2})',
            r'(\d{1,2}\s*(?:AM|PM|am|pm))',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                time_str = match.group(1)
                # Convert to 24-hour format if needed
                try:
                    if 'am' in time_str.lower() or 'pm' in time_str.lower():
                        time_obj = datetime.strptime(time_str.upper(), '%I:%M %p')
                    else:
                        time_obj = datetime.strptime(time_str, '%H:%M')
                    
                    # Format as HH:MM:SS-HH:MM:SS (15-minute slot)
                    start_time = time_obj.strftime('%H:%M:00')
                    end_time = (time_obj + timedelta(minutes=15)).strftime('%H:%M:00')
                    return f"{start_time}-{end_time}"
                except ValueError:
                    continue
        
        return None

    # ------------------ AI Reasoning ------------------

    def generate_ai_response(self, text):
        """Send user text to OpenAI with tool calling"""
        self.full_transcript.append({"role": "user", "content": text})

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_clinics",
                    "description": "Get a list of available clinics in the branch"
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_doctors",
                    "description": "Get a list of doctors in a clinic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "clinic_code": {
                                "type": "string",
                                "description": "The code of the clinic, e.g. SPLDRM for Dental Clinic"
                            }
                        },
                        "required": ["clinic_code"]
                    }
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_doctor_availability",
                    "description": "Check if a specific doctor is available for appointments on a specific date",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doctor_code": {
                                "type": "string",
                                "description": "The code of the doctor to check availability for, e.g. 14"
                            },
                            "date": {
                                "type": "string",
                                "description": "The date to check availability for in YYYY-MM-DD format. If not specified, uses today's date."
                            }
                        },
                        "required": ["doctor_code"]
                    }
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Book an appointment for a patient",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_date": {
                                "type": "string",
                                "description": "Appointment date in YYYY-MM-DD format"
                            },
                            "slot_id": {
                                "type": "string",
                                "description": "Time slot in HH:MM:SS-HH:MM:SS format, e.g. 08:00:00-08:15:00"
                            },
                            "pat_code": {
                                "type": "string",
                                "description": "Patient code, e.g. 340585"
                            },
                            "pat_nameAr": {
                                "type": "string",
                                "description": "Patient name in Arabic, e.g. YOSAF SOLTAN YOSAF"
                            },
                            "identity_no": {
                                "type": "string",
                                "description": "Identity number, e.g. 1"
                            },
                            "mobile_no": {
                                "type": "string",
                                "description": "Mobile number, e.g. 0500876733"
                            },
                            "pat_age": {
                                "type": "string",
                                "description": "Patient age (optional)"
                            },
                            "dr_code": {
                                "type": "string",
                                "description": "Doctor code, e.g. 36"
                            },
                            "dr_codeText": {
                                "type": "string",
                                "description": "Doctor code text (optional)"
                            },
                            "cinicDept_code": {
                                "type": "string",
                                "description": "Clinic department code, e.g. SPLOPT"
                            }
                        },
                        "required": [
                            "app_date", "slot_id", "pat_code", "pat_nameAr", 
                            "identity_no", "mobile_no", "dr_code", "cinicDept_code"
                        ]
                    }
                },
            },
        ]

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.full_transcript,
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message
        
        # Append the assistant's message with tool calls to the transcript FIRST
        assistant_message = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
                for tool_call in msg.tool_calls
            ]
        
        self.full_transcript.append(assistant_message)

        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                fn = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")

                if fn == "get_clinics":
                    result = self.get_clinics()
                elif fn == "get_doctors":
                    result = self.get_doctors(args["clinic_code"])
                elif fn == "check_doctor_availability":
                    # Extract date from user text if not provided in function call
                    if "date" not in args or not args["date"]:
                        date_from_text = self.extract_date_from_text(text)
                        if date_from_text:
                            args["date"] = date_from_text
                    
                    result = self.check_doctor_availability(args["doctor_code"], args.get("date"))
                elif fn == "book_appointment":
                    # Extract date and time from user text if not provided
                    if "app_date" not in args or not args["app_date"]:
                        date_from_text = self.extract_date_from_text(text)
                        if date_from_text:
                            args["app_date"] = date_from_text
                    
                    if "slot_id" not in args or not args["slot_id"]:
                        time_from_text = self.extract_time_slot(text)
                        if time_from_text:
                            args["slot_id"] = time_from_text
                    
                    result = self.book_appointment(
                        args["app_date"], args["slot_id"], args["pat_code"], 
                        args["pat_nameAr"], args["identity_no"], args["mobile_no"], 
                        args["dr_code"], args["cinicDept_code"],
                        args.get("pat_age", ""), args.get("dr_codeText", "")
                    )
                else:
                    result = {"error": "Unknown tool"}

                # Append tool response with the correct tool_call_id
                self.full_transcript.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })

            # ask AI again with tool output
            follow_up = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.full_transcript,
            )
            ai_response = follow_up.choices[0].message.content
            
            # Append the final assistant response
            self.full_transcript.append({"role": "assistant", "content": ai_response})
        else:
            ai_response = msg.content
            # Assistant message was already appended above

        self.generate_audio(ai_response)

    # ------------------ Main Loop ------------------

    def start_listening(self):
        """Main listening loop"""
        while True:
            input("Press Enter to start recording (Ctrl+C to exit)...")
            audio_file = "temp_audio.wav"
            self.record_audio(audio_file, duration=5)
            text = self.transcribe_audio(audio_file)

            if text:
                print(f"👤 You said: {text}")
                self.generate_ai_response(text)


# ------------------ Run ------------------

if __name__ == "__main__":
    greeting = "Thank you for calling the clinic, how may I assist you?"
    ai_assistant = AI_Assistant()
    ai_assistant.generate_audio(greeting)
    ai_assistant.start_listening()