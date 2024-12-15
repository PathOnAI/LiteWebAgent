import { requestDeepgram } from "./deepgram";
import { SpeechChunks } from "./speech-chunks";
import { TranscriberState } from "./transcriber-store";

export class Transcriber {
  private MIN_SPEECH_DURATION = 1;
  private MAX_SPEECH_DURATION = 30;

  private speechChunks: SpeechChunks;
  private transcriberState: TranscriberState | null = null;
  private recording: boolean = false;
  constructor() {
    this.speechChunks = new SpeechChunks(this.onDurationChanged.bind(this));
  }

  async onDurationChanged(duration: number): Promise<void> {
    if (!this.recording) {
      return;
    }

    if (duration > this.MAX_SPEECH_DURATION) {
      this.transcriberState?.setTranscriptionError("Speech too long!");
      await this.stopSpeaking();
    }
  }

  async startSpeaking(transcriberState: TranscriberState) {
    this.transcriberState = transcriberState;
    this.transcriberState.setRecording(true);
    this.transcriberState.setTranscriptionError('');
    this.transcriberState.setTranscription('');
    this.recording = true;
    this.speechChunks.start();
  }

  async stopSpeaking() {
    if (!this.transcriberState) {
      return;
    }
    this.recording = false;
    this.transcriberState.setRecording(false);
    this.speechChunks.stop();
    const blob = this.speechChunks.getBlob();
    const chunkDuration = this.speechChunks.getChunkDuration();
    console.log("chunkDuration", chunkDuration);

    // this.saveWavForDebug(blob);

    if (chunkDuration > this.MIN_SPEECH_DURATION) {
      this.transcriberState.setTranscribing(true);
      const { transcription, error } = await requestDeepgram(blob);
      // const { transcription, error } = await this.testRequest(blob);
      if (error) {
        this.transcriberState.setTranscriptionError('Failed to transcribe!');
      } else if (!transcription) {
        this.transcriberState.setTranscriptionError('No speech detected!');
      } else {
        this.transcriberState.setTranscriptionError('');
        this.transcriberState.setTranscription(transcription);
      }
      this.transcriberState.setTranscribing(false);
    } else {
      this.transcriberState.setTranscriptionError('Speech too short!');
    }
  }

  async saveWavForDebug(blob: Blob) {
    const file = new File([blob], "speech.wav", { type: "audio/wav" });
    const url = URL.createObjectURL(file);
    const a = document.createElement("a");
    a.href = url;
    a.download = "speech.wav";
    a.click();
  };

  async testRequest(blob: Blob) {
    // wait for 1s
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {transcription: "test", error: null};
  };
}
const transcriber = new Transcriber();
export default transcriber;
