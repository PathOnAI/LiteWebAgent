// pages/api/speak.ts
import type { NextApiRequest, NextApiResponse } from 'next'
import { createClient } from '@deepgram/sdk'

const deepgram = createClient(
    process.env.DEEPGRAM_API_KEY
)

const getAudioBuffer = async (response: ReadableStream): Promise<Buffer> => {
    const reader = response.getReader();
    const chunks: Uint8Array[] = [];
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
    }
    
    const dataArray = chunks.reduce(
        (acc, chunk) => Uint8Array.from([...acc, ...chunk]),
        new Uint8Array(0)
    );
    
    return Buffer.from(dataArray.buffer);
};

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    // Only allow POST requests
    if (req.method !== 'POST') {
        return res.status(405).json({ message: 'Method not allowed' });
    }

    try {
        const { text, model } = req.body;
        const response = await deepgram.speak.request({ text }, { model });
        const stream = await response.getStream();
        const body = await getAudioBuffer(stream!);

        // Set appropriate headers
        res.setHeader('Content-Type', 'audio/mp3');
        res.send(body);
    } catch (err) {
        console.error(err);
        res.status(500).json({ message: 'Internal Server Error' });
    }
}