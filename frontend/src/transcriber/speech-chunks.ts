import MicrophoneAudio from "./microphone-audio";

export type OnSpeechStart = () => void;
export type OnSpeechEnd = ({
  blob,
  float32Array,
}: {
  blob: Blob;
  float32Array: Float32Array;
}) => Promise<void>;

export type OnDurationChanged = (duration: number) => Promise<void>;
export class SpeechChunks {
  private static readonly SAMPLE_RATE = 16000;
  private static readonly WINDOW_SIZE_SAMPLES = 512;

  private chunks: Float32Array[];
  private chunkDuration: number;
  private microphoneAudio: MicrophoneAudio;
  private startTime: number = 0;
  private onDurationChanged: OnDurationChanged;
  public stopping: boolean = false;
  constructor(onDurationChanged: OnDurationChanged) {
    this.onDurationChanged = onDurationChanged;
    this.chunks = [];
    this.chunkDuration = 0;
    this.microphoneAudio = new MicrophoneAudio({
      sampleRate: SpeechChunks.SAMPLE_RATE,
      windowSizeSamples: SpeechChunks.WINDOW_SIZE_SAMPLES,
      onAudioData: this.processAudioData.bind(this),
    });
  }

  private async processAudioData(audioData: Float32Array): Promise<void> {
    this.chunks.push(audioData);
    this.chunkDuration = (Date.now() - this.startTime) / 1000;
    await this.onDurationChanged(this.chunkDuration);
  }

  async start(): Promise<void> {
    this.chunks = [];
    await this.microphoneAudio.start();
    this.startTime = Date.now();
  }

  async stop(): Promise<void> {
    await this.microphoneAudio.stop();
  }

  getFlot32Array(): Float32Array {
    // Combine all chunks into a single Float32Array
    const combinedChunks = this.chunks;
    const combinedLength = combinedChunks.reduce(
      (sum, chunk) => sum + chunk.length,
      0,
    );
    const combinedAudio = new Float32Array(combinedLength);
    let offset = 0;
    for (const chunk of combinedChunks) {
      combinedAudio.set(chunk, offset);
      offset += chunk.length;
    }

    return combinedAudio;
  }

  getChunkDuration(): number {
    return this.chunkDuration;
  }

  getBlob(): Blob {
    const float32Array = this.getFlot32Array();
    return this._getBlob(float32Array);
  }

  _getBlob(combinedAudio: Float32Array): Blob {
    // Convert Float32Array to Int16Array (common format for WAV files)
    const intData = new Int16Array(combinedAudio.length);
    for (let i = 0; i < combinedAudio.length; i++) {
      const s = Math.max(-1, Math.min(1, combinedAudio[i]));
      intData[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }

    // Create WAV file header
    const header = new ArrayBuffer(44);
    const view = new DataView(header);

    // RIFF chunk descriptor
    this.writeString(view, 0, "RIFF");
    view.setUint32(4, 36 + intData.length * 2, true);
    this.writeString(view, 8, "WAVE");

    // FMT sub-chunk
    this.writeString(view, 12, "fmt ");
    view.setUint32(16, 16, true); // subchunk1size
    view.setUint16(20, 1, true); // audio format (1 for PCM)
    view.setUint16(22, 1, true); // num of channels
    view.setUint32(24, SpeechChunks.SAMPLE_RATE, true); // sample rate
    view.setUint32(28, SpeechChunks.SAMPLE_RATE * 2, true); // byte rate
    view.setUint16(32, 2, true); // block align
    view.setUint16(34, 16, true); // bits per sample

    // Data sub-chunk
    this.writeString(view, 36, "data");
    view.setUint32(40, intData.length * 2, true);

    // Combine header and data
    return new Blob([header, intData], { type: "audio/wav" });
  }

  // Helper function to write strings to DataView
  private writeString(view: DataView, offset: number, string: string): void {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  async close(): Promise<void> {
    this.stop();
  }
}
