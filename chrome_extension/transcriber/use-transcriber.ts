import { useTranscriberStore } from './transcriber-store';
import transcriber from "./transcriber";

export const useTranscriber = () => {
  const transcriberState = useTranscriberStore();
  const { 
    recording,
    transcribing,
    transcription,
    transcriptionError,
  } = transcriberState;

  const startSpeaking = async () => {
    transcriber.startSpeaking(transcriberState);
  };

  const stopSpeaking = async () => {
    transcriber.stopSpeaking();
  };

  return {
    startSpeaking,
    stopSpeaking,
    recording,
    transcribing,
    transcription,
    transcriptionError,
  };
};
