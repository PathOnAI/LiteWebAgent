from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
from typing import Optional, Callable
from threading import Event, Lock
import queue

class VoiceClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.deepgram = DeepgramClient(api_key=api_key)
        self.connection = None
        self.microphone = None
        self.message_queue = queue.Queue()
        self.is_listening = False
        self._stop_event = Event()
        self._message_lock = Lock()
        self._current_message = ""
        
    def _on_message(self, dg_self, result, **kwargs):  # Added dg_self parameter
        with self._message_lock:
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            self._current_message = sentence
            self.message_queue.put(sentence)

    def _on_error(self, dg_self, error, **kwargs):  # Added dg_self parameter
        print(f"Error occurred: {error}")
        
    def _setup_connection(self):
        self.connection = self.deepgram.listen.websocket.v("1")
        
        # Set up event handlers
        self.connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
        self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
        
        # Configure options
        options = LiveOptions(
            model="nova-2",
            punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
        )
        
        self.connection.start(options)
        
    def start(self):
        """Start the voice client and begin listening."""
        if self.is_listening:
            return
            
        self._stop_event.clear()
        self._setup_connection()
        
        # Set up and start microphone
        self.microphone = Microphone(self.connection.send)
        self.microphone.start()
        self.is_listening = True
        
    def stop(self):
        """Stop the voice client and clean up resources."""
        if not self.is_listening:
            return
            
        self._stop_event.set()
        
        if self.microphone:
            self.microphone.finish()
            
        if self.connection:
            self.connection.finish()
            
        self.is_listening = False
        self._current_message = ""
        
    def listen(self, timeout: Optional[float] = None) -> str:
        """
        Listen for and return a complete message.
        
        Args:
            timeout (float, optional): Maximum time to wait for a message in seconds.
                                     If None, wait indefinitely.
        
        Returns:
            str: The transcribed message
            
        Raises:
            queue.Empty: If timeout is specified and no message is received within the timeout period.
        """
        if not self.is_listening:
            raise RuntimeError("Voice client is not started. Call start() first.")
            
        return self.message_queue.get(timeout=timeout)

# Example usage:
if __name__ == "__main__":
    # Initialize the client
    client = VoiceClient(api_key='33f6d8a92671a841d055852e00603a1c3ada57de')
    
    try:
        # Start listening
        client.start()
        print("Listening... Press Ctrl+C to stop.")
        
        # Listen for messages until interrupted
        while True:
            message = client.listen()
            print(f"Transcribed: {message}")
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        client.stop()
        print("Finished")