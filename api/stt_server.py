import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranscriptionResponse(BaseModel):
    transcription: str

def create_app() -> FastAPI:
    app = FastAPI(
        title="Speech-to-Text API",
        description="API for transcribing audio using Deepgram",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

app = create_app()

async def get_deepgram_client() -> DeepgramClient:
    load_dotenv()
    api_key = os.getenv("DEEPGRAM_API_KEY")
    return DeepgramClient(api_key)

@app.post("/stt/deepgram", response_model=TranscriptionResponse)
async def transcribe(
    file: UploadFile = File(...),
    client: DeepgramClient = Depends(get_deepgram_client)
) -> Dict[str, Any]:
    try:
        logger.info(f"Processing transcription request for file: {file.filename}")
        
        content = await file.read()
        payload: FileSource = {"buffer": content}
        
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
        )

        response = client.listen.rest.v("1").transcribe_file(payload, options)
        
        if not response or not response.results:
            raise HTTPException(
                status_code=500,
                detail="Failed to get transcription from Deepgram"
            )
        logger.info("Received Deepgram response: %s", response.to_dict())
        
        transcription = response.results.channels[0].alternatives[0].transcript
        
        logger.info("Transcription completed successfully")
        return {
            "transcription": transcription
        }

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error during transcription: {str(e)}"
        )

def main() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(description="Speech-to-Text API Server")
    parser.add_argument('--port', type=int, default=5002, help="Port to run the server on")
    parser.add_argument('--host', type=str, default="127.0.0.1", help="Host to run the server on")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "api.stt_server:app",
        host=args.host,
        port=args.port,
        reload=True,
        log_level="debug"
    )

if __name__ == "__main__":
    main()