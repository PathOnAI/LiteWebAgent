import { DeepgramContextProvider } from '@/context/DeepgramContextProvider';
import { MicrophoneContextProvider } from '@/context/MicrophoneContextProvider';
import { MantineProvider } from '@mantine/core';
import '@mantine/core/styles.css';
import type { AppProps } from 'next/app';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <MicrophoneContextProvider>
      <DeepgramContextProvider>
        <MantineProvider>
          <Component {...pageProps} />
        </MantineProvider>
      </DeepgramContextProvider>
    </MicrophoneContextProvider>
  );
}