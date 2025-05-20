import { DeepgramContextProvider } from '@/context/DeepgramContextProvider';
import { MicrophoneContextProvider } from '@/context/MicrophoneContextProvider';
import { MantineProvider } from '@mantine/core';
import { Inter } from "next/font/google";
import Layout from "@/components/layout/Layout";
import '@mantine/core/styles.css';
import type { AppProps } from 'next/app';

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export default function App({ Component, pageProps }: AppProps) {
  return (
    <MicrophoneContextProvider>
      <DeepgramContextProvider>
        <MantineProvider>
          <div className={inter.variable}>
            <Layout>
              <Component {...pageProps} />
            </Layout>
          </div>
        </MantineProvider>
      </DeepgramContextProvider>
    </MicrophoneContextProvider>
  );
}