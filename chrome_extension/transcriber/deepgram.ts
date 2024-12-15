export const requestDeepgram = async (blob: Blob): Promise<{
  transcription: string;
  error: string;
}> => {
  // Create a FormData object to send the file
  const formData = new FormData();
  formData.append('file', blob, 'audio.wav');

  try {
    // Make the POST request to your server endpoint
    const response = await fetch('http://127.0.0.1:5002/stt/deepgram', {
      method: 'POST',
      body: formData,
    });

    // Parse and return the JSON response
    const data = await response.json();
    return {
      transcription: data.transcription,
      error: "",
    };
  } catch (error) {
    console.error('Error transcribing audio:', error);
    return {
      transcription: "",
      error: "Failed to transcribe!",
    };
  }
};