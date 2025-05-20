import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import {
    Mic2,
    RefreshCcw,
    Play,
    StepForward,
    AlertCircle,
    Command,
    Rocket,
    ArrowRight,
    Loader,
    CircleStop,
    AudioLines,
    Circle,
    Mic,
    Square,
    Globe,
    MessageSquare,
    BrainCircuit
} from 'lucide-react';
import {
    startBrowserBase,
    runInitialSteps,
    runAdditionalSteps,
    endWebagentSession,
    WebAgentRequestBody
} from '@/services/webagentService'
import ActivityMonitor from '@/components/ActivityMonitor';
import { useTranscriber } from '@/transcriber/use-transcriber';

import {
    LiveConnectionState,
    LiveTranscriptionEvent,
    LiveTranscriptionEvents,
    useDeepgram,
} from '@/context/DeepgramContextProvider'
import {
    MicrophoneEvents,
    MicrophoneState,
    useMicrophone,
} from '@/context/MicrophoneContextProvider'

import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { useRouter } from 'next/router';

type MessageType =
    | 'status'
    | 'browser'
    | 'thinking'
    | 'tool_calls'
    | 'tool_execution'
    | 'tool_result'
    | 'action'
    | 'complete';

interface WebAgentMessage {
    type: MessageType;
    message: string | {
        tool_call_id?: string;
        role?: string;
        name?: string;
        content?: string;
        response?: Array<{
            finish_reason: string;
            index: number;
            message: {
                content: string;
                role: string;
                tool_calls: null;
                function_call: null;
            }
        }>;
    };
}

interface PlaygroundStep {
    id: string;
    action: string;
    status: 'pending' | 'running' | 'complete' | 'error';
    isInitializing: boolean;
    type?: string;  // Add this for message type
    source: 'user' | 'system'; // Add this to distinguish between user and system messages
}

interface PlaygroundProps {
    initialSteps_: PlaygroundStep[];
    processId: string;
}

export default function Playground({
    initialSteps_,
    processId,
    onSessionEnd = () => {},
}: PlaygroundProps & { onSessionEnd?: () => void }) {

    const [startingUrl, setStartingUrl] = useState('');
    const [command, setCommand] = useState('');
    const [longTermMemory, setLongTermMemory] = useState(false);
    const [isResetting, setIsResetting] = useState(false);
    const [sessionStarted, setSessionStarted] = useState(false);
    const [steps, setSteps] = useState<PlaygroundStep[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [browserUrl, setBrowserUrl] = useState('');
    const [sessionId, setSessionId] = useState('');

    const [isSpeaking, setIsSpeaking] = useState(false);
    const messageQueue = useRef<WebAgentMessage[]>([]);
    const isProcessingQueue = useRef(false);

    // Deepgram and Microphone Setup
    const { connection, connectToDeepgram, connectionState } = useDeepgram();
    const {
        setupMicrophone,
        microphone,
        startMicrophone,
        microphoneState,
        stopMicrophone,
    } = useMicrophone();

    // Additional State for Mic Control
    const [transcriber, setTranscriber] = useState<boolean | null>(null);
    const [firstTimeListening, setFirstTimeListening] = useState<boolean | null>(null);
    const captionTimeout = useRef<any>();
    const keepAliveInterval = useRef<any>();

    // Add welcome modal state
    const [showWelcomeModal, setShowWelcomeModal] = useState(true);

    // Set up Deepgram when microphone is ready
    useEffect(() => {
        if (microphoneState === MicrophoneState.Ready) {
            connectToDeepgram({
                model: "nova-2",
                interim_results: true,
                smart_format: true,
                filler_words: true,
                utterance_end_ms: 3000,
            });
        }
    }, [microphoneState]);

    // Handle microphone data streaming
    useEffect(() => {
        if (!microphone || !connection) return;

        const onData = (e: BlobEvent) => {
            connection?.send(e.data);
        };

        const onTranscript = (data: LiveTranscriptionEvent) => {

            const { is_final: isFinal, speech_final: speechFinal } = data;
            const thisCaption = data.channel.alternatives[0].transcript;
            console.log(thisCaption)

            if (thisCaption !== "" && isFinal && speechFinal) {
                setCommand(prev => prev + ' ' + thisCaption);
            }
        };

        if (connectionState === 1) {
            console.log('her??')
            connection.addListener(LiveTranscriptionEvents.Transcript, onTranscript);
            microphone.addEventListener(MicrophoneEvents.DataAvailable, onData);
            startMicrophone();
        }

        console.log('connection state is', connectionState == 1)

        return () => {
            connection?.removeListener(LiveTranscriptionEvents.Transcript, onTranscript);
            microphone?.removeEventListener(MicrophoneEvents.DataAvailable, onData);
            clearTimeout(captionTimeout.current);
        };


    }, [connectionState]);

    // Keep-alive connection management
    useEffect(() => {
        if (!connection) return;

        if (microphoneState !== MicrophoneState.Open) {
            connection.keepAlive();
            keepAliveInterval.current = setInterval(() => {
                connection.keepAlive();
            }, 10000);
        } else {
            clearInterval(keepAliveInterval.current);
        }

        return () => {
            clearInterval(keepAliveInterval.current);
        };
    }, [microphoneState, connectionState]);

    // Handle Microphone Toggle
    const handleMicrophoneToggle = async () => {
        if (transcriber === null) {
            if (firstTimeListening === null) {
                setupMicrophone();
                await new Promise(resolve => setTimeout(resolve, 2500));
                setFirstTimeListening(false);
            } else {
                setCommand("");
                startMicrophone();
            }
            setTranscriber(true);
        } else {
            stopMicrophone();
            setTranscriber(null);
        }
    };


    useEffect(() => {
        if (initialSteps_ && initialSteps_.length > 0) {
            setSteps(initialSteps_);
        }
        return () => {
            if (sessionId) {
                endWebagentSession(sessionId).catch(console.error);
            }
        };
    }, [initialSteps_]);

    // Function to speak text and return a promise
    const speakText = async (text: string): Promise<void> => {
        setIsSpeaking(true);

        try {
            const response = await fetch("/api/voice", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model: "aura-asteria-en",
                    text: text,
                })
            });

            if (!response.ok) throw new Error("Voice API error");

            const blob = await response.blob();
            const audioUrl = URL.createObjectURL(blob);
            const audioPlayer = document.getElementById("audio-player") as HTMLAudioElement;

            return new Promise((resolve) => {
                if (audioPlayer) {
                    audioPlayer.src = audioUrl;
                    audioPlayer.onended = () => {
                        setIsSpeaking(false);
                        resolve();
                    };
                    audioPlayer.play();
                } else {
                    setIsSpeaking(false);
                    resolve();
                }
            });
        } catch (error) {
            console.error("Error in speech synthesis:", error);
            setIsSpeaking(false);
        }
    };

    // Process message queue
    const processMessageQueue = async () => {
        if (isProcessingQueue.current || messageQueue.current.length === 0) return;

        isProcessingQueue.current = true;

        while (messageQueue.current.length > 0) {
            const message = messageQueue.current[0];

            // First, display the message immediately
            setSteps(prev => {
                const updatedSteps = prev.map(step => ({
                    ...step,
                    status: step.status === 'running' ? 'complete' : step.status
                }));

                if (message.type === 'complete') return [...updatedSteps];

                return [...updatedSteps, {
                    id: Date.now().toString(),
                    action: typeof message.message === 'string'
                        ? message.message
                        : message.message.content || JSON.stringify(message.message),
                    status: 'running',
                    isInitializing: false,
                    type: message.type,
                    source: 'system'
                }];
            });

            // Then, if it's a thinking message, speak it and wait
            if (message.type != 'browser' && message.type != 'complete') {
                const textToSpeak = typeof message.message === 'string'
                    ? message.message
                    : message.message.content!;
                await speakText(textToSpeak);
            }

            messageQueue.current.shift();
        }

        isProcessingQueue.current = false;
    };

    function extractLiveBrowserUrl(input: string): string | null {
        const keyword = "at ";
        const index = input.indexOf(keyword);
        if (index !== -1) {
            return input.substring(index + keyword.length).trim();
        }
        return null; // Return null if "at " is not found
    }

    // Modified handleNewMessage to use queue
    const handleNewMessage = (message: string) => {
        try {
            const parsedMessage: WebAgentMessage = JSON.parse(message);

            if (parsedMessage.type == 'browser') {
                setBrowserUrl(extractLiveBrowserUrl(parsedMessage.message! as string)!)
                return
            }
            messageQueue.current.push(parsedMessage);
            if (!isProcessingQueue.current) {
                processMessageQueue();
            }
        } catch (e) {
            console.error('Error parsing message:', e);
        }
    };

    const handleSessionStart = async () => {
        if (!startingUrl) return;
        setIsRunning(true);

        try {
            const browserData = await startBrowserBase();
            if (browserData.live_browser_url && browserData.session_id) {
                setBrowserUrl(browserData.live_browser_url);
                setSessionId(browserData.session_id);
                setSessionStarted(true);
            }
        } catch (error) {
            console.error('Failed to start browser session:', error);
        } finally {
            setIsRunning(false);
        }
    };

    const handleCommandSubmit = async () => {
        if (!command.trim() || !sessionId) return;

        // Add user message
        const userStep: PlaygroundStep = {
            id: Date.now().toString(),
            action: command,
            status: 'complete',
            isInitializing: false,
            source: 'user'
        };

        setSteps(prev => [...prev, userStep]);
        setCommand('');
        setIsRunning(true);

        try {
            const requestBody: WebAgentRequestBody = {
                goal: command,
                starting_url: startingUrl,
                plan: '',
                session_id: sessionId
            };

            if (steps.length === 0) {
                await runInitialSteps(requestBody, handleNewMessage);
            } else {
                await runAdditionalSteps(requestBody, handleNewMessage);
            }
        } catch (error) {
            console.error('Command execution failed:', error);
            setSteps(prev => [...prev, {
                id: Date.now().toString(),
                action: 'Error executing command',
                status: 'error',
                isInitializing: false,
                source: 'system'
            }]);
        } finally {
            setIsRunning(false);
        }
    };

    const router = useRouter();

    const handleReset = async () => {
        setIsResetting(true);
        
        // Force stop all audio and clear queue
        stopAudio();
        
        // Stop transcription if active
        if (transcriber !== null) {
            stopMicrophone();
            setTranscriber(null);
        }
        
        // End web agent session
        if (sessionId) {
            try {
                await endWebagentSession(sessionId);
            } catch (error) {
                console.error('Failed to end session:', error);
            }
        }
        
        // Reset all state variables
        setCommand('');
        setSteps([]);
        setSessionStarted(false);
        setBrowserUrl('');
        setSessionId('');
        setStartingUrl('');
        onSessionEnd();
        
        setIsResetting(false);

        router.reload();
    };

    const exampleCommands = [
        {
            icon: <Command className="w-6 h-6" />,
            title: "Search dining table",
            description: "https://google.com"
        },
    ];

    const handleExampleClick = async (command: any) => {
        setStartingUrl(command.description);
        // Start the session
        try {
            setIsRunning(true);
            const browserData = await startBrowserBase();
            if (browserData.live_browser_url && browserData.session_id) {
                setBrowserUrl(browserData.live_browser_url);
                setSessionId(browserData.session_id);
                setSessionStarted(true);

                // After session starts, submit the command
                const newStep = {
                    id: Date.now().toString(),
                    action: command.title,
                    status: 'running',
                    isInitializing: false
                };

                setSteps((prev: any) => [...prev, newStep]);

                const requestBody = {
                    goal: command.title,
                    starting_url: command.description,
                    plan: '',
                    session_id: browserData.session_id
                };

                await runInitialSteps(requestBody, handleNewMessage);

                setSteps(prev => prev.map(step =>
                    step.id === newStep.id ? { ...step, status: 'complete' } : step
                ));
            }
        } catch (error) {
            console.error('Failed to start session or run command:', error);
        } finally {
            setIsRunning(false);
        }
    };

    // Modified Input Section with Microphone Integration
    const renderCommandInput = () => (
        <div className="relative">
            <Input
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                placeholder="Write a command..."
                className="h-12 pr-24 bg-gray-50/50 border-gray-200 focus:bg-white transition-all"
                onKeyPress={(e) => e.key === 'Enter' && handleCommandSubmit()}
                disabled={isRunning}
            />
            <div className="absolute right-1 top-1/2 -translate-y-1/2 flex space-x-1">
                <Button
                    variant="ghost"
                    size="icon"
                    className={`rounded-full w-10 h-10 ${transcriber === null
                        ? 'bg-blue-500 hover:bg-blue-600'
                        : 'bg-red-500 hover:bg-red-600'
                        }`}
                    onClick={handleMicrophoneToggle}
                    disabled={isRunning}
                >
                    {transcriber === null ? (
                        <Mic className="h-5 w-5 text-white" />
                    ) : (
                        <Square className="h-5 w-5 text-white" />
                    )}
                </Button>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleCommandSubmit}
                    disabled={isRunning}
                >
                    <Play className="w-5 h-5" />
                </Button>
            </div>
        </div>
    );

    // Helper functions
    const getMessageTypeStyle = (type?: string) => {
        switch (type) {
            case 'status':
                return 'border-blue-100 bg-blue-50/30';
            case 'browser':
                return 'border-purple-100 bg-purple-50/30';
            case 'thinking':
                return 'border-yellow-100 bg-yellow-50/30';
            case 'tool_calls':
            case 'tool_execution':
            case 'tool_result':
                return 'border-green-100 bg-green-50/30';
            case 'action':
                return 'border-orange-100 bg-orange-50/30';
            default:
                return 'border-gray-100';
        }
    };

    const getMessageTypeBadgeStyle = (type?: string) => {
        switch (type) {
            case 'status':
                return 'bg-blue-100 text-blue-700';
            case 'browser':
                return 'bg-purple-100 text-purple-700';
            case 'thinking':
                return 'bg-yellow-100 text-yellow-700';
            case 'tool_calls':
            case 'tool_execution':
            case 'tool_result':
                return 'bg-green-100 text-green-700';
            case 'action':
                return 'bg-orange-100 text-orange-700';
            default:
                return 'bg-gray-100 text-gray-700';
        }
    };

    const getMessageTypeLabel = (type?: string) => {
        switch (type) {
            case 'status':
                return 'Status Update';
            case 'browser':
                return 'Browser';
            case 'thinking':
                return 'Thinking';
            case 'tool_calls':
                return 'Tool Calls';
            case 'tool_execution':
                return 'Executing';
            case 'tool_result':
                return 'Result';
            case 'action':
                return 'Action';
            default:
                return 'System';
        }
    };

    const stopAudio = () => {
        // Stop the audio player
        const audioPlayer = document.getElementById("audio-player") as HTMLAudioElement;
        if (audioPlayer) {
            audioPlayer.pause();
            audioPlayer.currentTime = 0;
            audioPlayer.src = ''; // Clear the source completely
        }
    
        // Clear any queued messages
        messageQueue.current = [];
        isProcessingQueue.current = false;
        
        // Reset speaking state
        setIsSpeaking(false);
    };


    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-blue-50">
            <div className="flex h-[calc(100vh-73px)]">
                <div className="w-96 border-r bg-white shadow-lg relative flex flex-col">
                    <div className="p-6 border-b bg-gradient-to-br from-gray-50 to-gray-100">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-2.5 rounded-xl shadow-md">
                                <MessageSquare className="w-5 h-5" />
                            </div>
                            <div>
                                <span className="font-semibold text-lg text-gray-800">Command Center</span>
                                <p className="text-sm text-gray-500">Control your web assistant</p>
                            </div>
                        </div>

                        {!sessionStarted && (
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-700">Starting URL</label>
                                    <Input
                                        value={startingUrl}
                                        onChange={(e) => setStartingUrl(e.target.value)}
                                        placeholder="Enter starting URL..."
                                        className="bg-white/90 border-gray-200 focus:bg-white transition-all"
                                    />
                                </div>
                                <Button
                                    className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-md"
                                    onClick={handleSessionStart}
                                    disabled={!startingUrl || isRunning}
                                >
                                    {isRunning ? (
                                        <div className="flex items-center space-x-2">
                                            <Loader className="w-4 h-4 animate-spin" />
                                            <span>Starting Session...</span>
                                        </div>
                                    ) : (
                                        <div className="flex items-center space-x-2">
                                            <Globe className="w-4 h-4" />
                                            <span>Start Browser Session</span>
                                        </div>
                                    )}
                                </Button>
                            </div>
                        )}
                    </div>

                    <div className="flex-1 overflow-y-auto space-y-3 p-4 scrollbar-thin scrollbar-thumb-gray-200">
                        {sessionStarted ? (
                            <>
                                {steps.map((step) => (
                                    <Card
                                        key={step.id}
                                        className={`p-4 border shadow-sm transition-all duration-300 hover:shadow-md ${step.source === 'user'
                                            ? 'border-blue-200 bg-blue-50/30'
                                            : getMessageTypeStyle(step.type)
                                            }`}
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <div className="flex items-center space-x-2">
                                                {step.source === 'user' ? (
                                                    <div className="bg-blue-100 p-1 rounded-md">
                                                        <MessageSquare className="w-4 h-4 text-blue-600" />
                                                    </div>
                                                ) : (
                                                    <div className="bg-gray-100 p-1 rounded-md">
                                                        <BrainCircuit className="w-4 h-4 text-gray-600" />
                                                    </div>
                                                )}
                                                <span className="text-sm font-medium text-gray-700">
                                                    {getMessageTypeLabel(step.type)}
                                                </span>
                                            </div>
                                            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${getMessageTypeBadgeStyle(step.type)}`}>
                                                {step.type}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-800 whitespace-pre-wrap pl-7 break-words">{step.action}</p>
                                    </Card>
                                ))}
                            </>
                        ) : (
                            <>
                                {!isRunning && exampleCommands.map((command, index) => (
                                    <Card
                                        key={index}
                                        className="p-4 cursor-pointer hover:bg-gray-50/80 transition-all duration-200 border border-gray-200 shadow-sm hover:shadow-md"
                                        onClick={() => handleExampleClick(command)}
                                    >
                                        <div className="flex space-x-3">
                                            <div className="bg-blue-100 p-2 rounded-lg">
                                                {command.icon}
                                            </div>
                                            <div>
                                                <div className="font-medium text-gray-800">{command.title}</div>
                                                <div className="text-sm text-gray-500">{command.description}</div>
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </>
                        )}
                    </div>

                    {sessionStarted && (
                        <div className="p-4 border-t bg-white">
                            <div className="mb-4 px-1">
                                <div className="text-xs font-medium text-gray-500 uppercase tracking-wider">Active Session</div>
                                <div className="text-sm font-medium text-gray-900 truncate mt-1">{startingUrl}</div>
                            </div>
                            <div className="space-y-3">
                                {renderCommandInput()}
                                <div className="flex justify-between">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="text-gray-600 hover:text-gray-900 border-gray-200"
                                        onClick={handleReset}
                                    >
                                        <RefreshCcw className="w-4 h-4 mr-2" />
                                        Reset Session
                                    </Button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex-1 bg-white relative">
                    {browserUrl ? (
                        <iframe
                            src={browserUrl}
                            className="w-full h-full border-none"
                            sandbox="allow-same-origin allow-scripts"
                            allow="clipboard-read; clipboard-write"
                        />
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full bg-gradient-to-br from-gray-50 to-blue-50/30">
                            <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-2xl shadow-lg mb-8">
                                <Globe className="w-12 h-12" />
                            </div>
                            <h2 className="text-3xl font-semibold text-gray-800 mb-3">Web Browser Preview</h2>
                            <p className="text-gray-600 mb-12">Your automated browsing session will appear here</p>

                            <div className="space-y-8 max-w-xl">
                                <div className="flex items-start space-x-6">
                                    <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-100 text-blue-600 font-semibold">1</div>
                                    <div>
                                        <h3 className="font-medium text-gray-800 mb-1">Enter Starting URL</h3>
                                        <p className="text-gray-600">Begin by providing the website URL you want to navigate</p>
                                    </div>
                                </div>

                                <div className="flex items-start space-x-6">
                                    <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-100 text-blue-600 font-semibold">2</div>
                                    <div>
                                        <h3 className="font-medium text-gray-800 mb-1">Issue Commands</h3>
                                        <p className="text-gray-600">Use natural language to tell the agent what to do</p>
                                    </div>
                                </div>

                                <div className="flex items-start space-x-6">
                                    <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-100 text-blue-600 font-semibold">3</div>
                                    <div>
                                        <h3 className="font-medium text-gray-800 mb-1">Watch & Interact</h3>
                                        <p className="text-gray-600">See the automated browser follow your instructions in real-time</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
            <audio id='audio-player' className='hidden'></audio>

            <AlertDialog open={isResetting}>
                <AlertDialogContent className="max-w-md !bg-white/80">
                    <div className="flex items-center space-x-4">
                        <div className="bg-blue-100 p-3 rounded-full">
                            <Loader className="w-6 h-6 text-blue-600 animate-spin" />
                        </div>
                        <div>
                            <AlertDialogTitle className="text-lg font-semibold text-gray-900">
                                Resetting Session
                            </AlertDialogTitle>
                            <AlertDialogDescription className="text-gray-600 mt-1">
                                Cleaning up resources and preparing a fresh session...
                            </AlertDialogDescription>
                        </div>
                    </div>
                </AlertDialogContent>
            </AlertDialog>

            {/* Add Welcome Modal */}
            <AlertDialog open={showWelcomeModal} onOpenChange={setShowWelcomeModal}>
                <AlertDialogContent className="max-w-xl !bg-white/95">
                    <div className="space-y-4">
                        <AlertDialogTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                            <AlertCircle className="w-6 h-6 text-yellow-500" />
                            Important Notice
                        </AlertDialogTitle>
                        <AlertDialogDescription className="text-gray-700 text-base leading-relaxed">
                            We are using the BrowserBase hobby plan 🔄, which only supports 3 concurrent browsers. If you are not able to get the web agent up and running ⚠️, it is most likely because someone else is using a remote BrowserBase browser 💻. The BrowserBase startup and scale plans 💰 are too expensive for our open source project 🔓.
                        </AlertDialogDescription>
                        <div className="flex justify-end pt-4">
                            <Button 
                                onClick={() => setShowWelcomeModal(false)}
                                className="bg-blue-600 hover:bg-blue-700 text-white"
                            >
                                I Understand
                            </Button>
                        </div>
                    </div>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}