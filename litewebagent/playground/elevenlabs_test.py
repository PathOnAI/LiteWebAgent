from elevenlabs import play
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import os
_ = load_dotenv()

# Retrieve the API key from environment variables
# API_KEY = os.getenv("ELEVEN_API_KEY")

# Initialize the Eleven Labs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

audio = elevenlabs_client.generate(
  text="Hello! 你好! Hola! नमस्ते! Bonjour! こんにちは! مرحبا! 안녕하세요! Ciao! Cześć! Привіт! வணக்கம்!",
  voice="Rachel",
  model="eleven_multilingual_v2"
)
play(audio)