interface MicrophoneAudioOptions {
  sampleRate?: number;
  channels?: number;
  windowSizeSamples: number;
  onAudioData: (audioData: Float32Array) => void;
}

class MicrophoneAudio {
  private stream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private processorNode: ScriptProcessorNode | null = null;
  private options: MicrophoneAudioOptions;
  private buffer: Float32Array = new Float32Array();

  constructor(options: MicrophoneAudioOptions) {
    this.options = {
      sampleRate: 16000,
      channels: 1,
      ...options,
    };
  }

  async getDeviceId(): Promise<string> {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const deviceId = stream.getTracks()[0].getSettings().deviceId;
    return deviceId!;
  }

  async start(): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.options.sampleRate,
          channelCount: this.options.channels,
          echoCancellation: true,
        },
      });

      this.getDeviceId().then(() => {});
      this.audioContext = new AudioContext({
        sampleRate: this.options.sampleRate,
      });

      this.sourceNode = this.audioContext.createMediaStreamSource(this.stream);
      
      // Create ScriptProcessorNode
      this.processorNode = this.audioContext.createScriptProcessor(
        4096, // bufferSize
        this.options.channels!, // input channels
        this.options.channels!, // output channels
      );

      // Handle audio processing
      this.processorNode.onaudioprocess = (audioProcessingEvent) => {
        const inputBuffer = audioProcessingEvent.inputBuffer;
        const inputData = inputBuffer.getChannelData(0);
        
        // Append new data to buffer
        const newBuffer = new Float32Array(this.buffer.length + inputData.length);
        newBuffer.set(this.buffer);
        newBuffer.set(inputData, this.buffer.length);
        this.buffer = newBuffer;

        // Process chunks of windowSizeSamples
        while (this.buffer.length >= this.options.windowSizeSamples) {
          const chunk = this.buffer.slice(0, this.options.windowSizeSamples);
          this.options.onAudioData(chunk);
          this.buffer = this.buffer.slice(this.options.windowSizeSamples);
        }
      };

      // Connect the nodes
      this.sourceNode.connect(this.processorNode);
      this.processorNode.connect(this.audioContext.destination);

    } catch (error) {
      console.error("Error starting microphone:", error);
      throw error;
    }
  }

  async stop(): Promise<void> {
    if (this.processorNode) {
      this.processorNode.disconnect();
      this.processorNode = null;
    }

    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }

    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    // Send any remaining data in the buffer
    if (this.buffer.length > 0) {
      this.options.onAudioData(this.buffer);
      this.buffer = new Float32Array();
    }
  }
}

export default MicrophoneAudio;
