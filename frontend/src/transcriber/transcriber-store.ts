import { create } from 'zustand';

export interface TranscriberState {
  recording: boolean;
  transcribing: boolean;
  transcription: string;
  transcriptionError: string;
  setRecording: (recording: boolean) => void;
  setTranscribing: (transcribing: boolean) => void;
  setTranscription: (transcription: string) => void;
  setTranscriptionError: (transcriptionError: string) => void;
}

export const useTranscriberStore = create<TranscriberState>((set) => ({
  recording: false,
  transcribing: false,
  transcription: "",
  transcriptionError: "",
  setRecording: (recording) => set({ recording }),
  setTranscribing: (transcribing) => set({ transcribing }),
  setTranscription: (transcription) => set({ transcription }),
  setTranscriptionError: (transcriptionError) => set({ transcriptionError }),
}));