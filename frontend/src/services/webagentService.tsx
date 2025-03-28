export const WEBAGENT_SERVER_URL_BASE = 'https://lite-web-agent-backend.vercel.app'

export interface WebAgentRequestBody {
    starting_url: string;
    goal: string;
    plan: string;
    session_id: string;
}

// Browser base API functions
export const startBrowserBase = async (storageStateS3Path = null) => {
    try {
        const response = await fetch(`${WEBAGENT_SERVER_URL_BASE}/start-browserbase`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                storage_state_s3_path: storageStateS3Path
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Extract all fields from the updated response
        const {
            live_browser_url,
            session_id,
            status,
            storage_state_path
        } = data;

        // Return all the fields from the updated API response
        return {
            live_browser_url,
            session_id,
            status,
            storage_state_path
        };
    } catch (error) {
        console.error('Error starting BrowserBase:', error);
        throw error;
    }
};


export const runAdditionalSteps = async (body: WebAgentRequestBody, onNewMessage: (message: string) => void): Promise<void> => {
    try {
        console.log(body);

        const response = await fetch(`${WEBAGENT_SERVER_URL_BASE}/run-agent-followup-steps-stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ "goal": body.goal, "session_id": body.session_id }),
        });

        const reader = response?.body?.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader!.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            lines.forEach(line => {
                if (line.startsWith('data:')) {
                    const newMessage = line.slice(5).trim();
                    onNewMessage(newMessage)
                }
            });
        }
    } catch (error) {
        console.error('Error:', error);
    }
};

export const runInitialSteps = async (
    body: WebAgentRequestBody, 
    onNewMessage: (message: string) => void
): Promise<void> => {
    try {
        const response = await fetch(`${WEBAGENT_SERVER_URL_BASE}/run-agent-initial-steps-stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache',
            },
            body: JSON.stringify({
                starting_url: body.starting_url,
                goal: body.goal,
                plan: body.plan,
                session_id: body.session_id
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error('No readable stream available');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.trim() === '') continue;
                
                if (line.startsWith('data: ')) {
                    const data = line.slice(5).trim();
                    try {
                        const parsedData = JSON.parse(data);
                        console.log(`[${new Date().toISOString()}] SSE packet:`, parsedData);
                        
                        onNewMessage(data);

                        // Check for completion message and close connection
                        if (parsedData.type === 'complete') {
                            reader.cancel();
                            return;
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};

export const endWebagentSession = async (id: string) => {
    console.log(id);
    try {
        const response = await fetch(
            `${WEBAGENT_SERVER_URL_BASE}/terminate-browserbase?session_id=${encodeURIComponent(id)}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            }
        );

        console.log(response);
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};