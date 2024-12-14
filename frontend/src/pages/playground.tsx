import React, { useState, useEffect } from 'react';
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
    ArrowRight
} from 'lucide-react';
import {
    startBrowserBase,
    runInitialSteps,
    runAdditionalSteps,
    endWebagentSession,
    WebAgentRequestBody
} from '@/services/webagentService'
import ActivityMonitor from '@/components/ActivityMonitor';

interface PlaygroundStep {
    id: string;
    action: string;
    status: 'pending' | 'running' | 'complete' | 'error';
    isInitializing: boolean;
}

interface PlaygroundProps {
    initialSteps_: PlaygroundStep[];
    processId: string;
    onSessionEnd: () => void;
}

export default function Playground({
    initialSteps_,
    processId,
    onSessionEnd
}: PlaygroundProps) {
    const [startingUrl, setStartingUrl] = useState('');
    const [command, setCommand] = useState('');
    const [longTermMemory, setLongTermMemory] = useState(false);
    const [sessionStarted, setSessionStarted] = useState(false);
    const [steps, setSteps] = useState<PlaygroundStep[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [browserUrl, setBrowserUrl] = useState('');
    const [sessionId, setSessionId] = useState('');

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

    const handleNewMessage = (message: string) => {
        setSteps(prev => {
            const lastStep = prev[prev.length - 1];
            if (lastStep && lastStep.status === 'running') {
                return prev.map(step =>
                    step.id === lastStep.id
                        ? { ...step, action: step.action + '\n' + message }
                        : step
                );
            }
            return prev;
        });
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

        const newStep: PlaygroundStep = {
            id: Date.now().toString(),
            action: command,
            status: 'running',
            isInitializing: false
        };

        setSteps(prev => [...prev, newStep]);
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

            setSteps(prev => prev.map(step =>
                step.id === newStep.id ? { ...step, status: 'complete' } : step
            ));
        } catch (error) {
            console.error('Command execution failed:', error);
            setSteps(prev => prev.map(step =>
                step.id === newStep.id ? { ...step, status: 'error' } : step
            ));
        } finally {
            setIsRunning(false);
        }
    };

    const handleReset = async () => {
        if (sessionId) {
            try {
                await endWebagentSession(sessionId);
            } catch (error) {
                console.error('Failed to end session:', error);
            }
        }
        setCommand('');
        setSteps([]);
        setSessionStarted(false);
        setBrowserUrl('');
        setSessionId('');
        onSessionEnd();
    };

    const exampleCommands = [
        {
            icon: <Command className="w-6 h-6" />,
            title: "Book a one-way flight",
            description: "from SFO to NYC for this Sat on Google Flights"
        },
        {
            icon: <Rocket className="w-6 h-6" />,
            title: "Add the book Zero to One in Hardcover",
            description: "to my Amazon cart"
        },
        {
            icon: <ArrowRight className="w-6 h-6" />,
            title: "What's the top post",
            description: "on Hackernews"
        },
        {
            icon: <Command className="w-6 h-6" />,
            title: "How much did NVIDIA stock",
            description: "gain today?"
        }
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
            <header className="border-b bg-white/80 backdrop-blur-sm supports-[backdrop-filter]:bg-white/60">
                <div className="flex items-center justify-between px-8 py-4">
                    <div className="flex items-center space-x-3">
                        <div className="bg-blue-500 text-white p-2 rounded-lg">
                            <Command className="w-5 h-5" />
                        </div>
                        <span className="font-semibold text-gray-800">Playground</span>
                    </div>
                    <div className="flex items-center space-x-4">
                        <ActivityMonitor
                            onInactive={handleReset}
                            isRunning={isRunning}
                            isSessionActive={sessionStarted}
                        // optionally you can add timeoutDuration={60} to change the default timeout
                        />
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={handleReset}
                            className="text-gray-600 hover:text-gray-900"
                        >
                            <AlertCircle className="w-5 h-5" />
                        </Button>
                    </div>
                </div>
            </header>

            <div className="flex h-[calc(100vh-64px)]">
                <div className="w-96 border-r bg-white/80 backdrop-blur-sm p-6 flex flex-col">
                    <div className="flex items-center space-x-3 mt-6 mb-6">
                        <div className="bg-blue-500 text-white p-2 rounded-lg">
                            <Command className="w-5 h-5" />
                        </div>
                        <div className="flex items-center space-x-2">
                            <span className="font-semibold text-lg text-gray-800">Lite Web Agent</span>
                            
                        </div>
                    </div>

                    {!sessionStarted && (
                        <div className="space-y-4 mb-6">
                            <Input
                                value={startingUrl}
                                onChange={(e) => setStartingUrl(e.target.value)}
                                placeholder="Enter starting URL..."
                                className="bg-gray-50/50 border-gray-200 focus:bg-white transition-all"
                            />
                            <Button
                                className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                                onClick={handleSessionStart}
                                disabled={!startingUrl || isRunning}
                            >
                                {isRunning ? 'Starting...' : 'Start Session'}
                            </Button>
                        </div>
                    )}

                    <div className="flex-1 overflow-y-auto space-y-3 scrollbar-thin scrollbar-thumb-gray-200">
                        {sessionStarted ? (
                            <>
                                {/* {steps.length === 0 && (
                                    <div className="text-sm text-gray-500 text-center p-8 bg-gray-50/50 rounded-lg">
                                        Enter your goal to begin the automated browsing session
                                    </div>
                                )} */}
                                {steps.map((step) => (
                                    <Card
                                        key={step.id}
                                        className={`p-4 border shadow-sm transition-all duration-300 hover:shadow-md ${step.status === 'running' ? 'border-blue-200 bg-blue-50/50 animate-pulse' :
                                            step.status === 'complete' ? 'border-green-100 bg-green-50/20' :
                                                step.status === 'error' ? 'border-red-100 bg-red-50/50' :
                                                    'border-gray-100'
                                            }`}
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <span className="text-sm font-medium text-gray-700">
                                                {steps.indexOf(step) === 0 ? 'Goal' : `Step ${steps.indexOf(step)}`}
                                            </span>
                                            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${step.status === 'running' ? 'bg-blue-100 text-blue-700' :
                                                step.status === 'complete' ? 'bg-green-100 text-green-700' :
                                                    step.status === 'error' ? 'bg-red-100 text-red-700' :
                                                        'bg-gray-100 text-gray-700'
                                                }`}>
                                                {step.status}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-800 whitespace-pre-wrap">{step.action}</p>
                                    </Card>
                                ))}
                            </>
                        ) : (
                            <>
                                {exampleCommands.map((command, index) => (
                                    <Card
                                        key={index}
                                        className="p-4 cursor-pointer hover:bg-gray-50/80 transition-all duration-200 border border-gray-100 shadow-sm hover:shadow-md"
                                        onClick={() => setCommand(command.title + " " + command.description)}
                                    >
                                        <div className="flex space-x-3">
                                            <div className="text-blue-500">
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

                    {sessionStarted ? (
                        <div className="mt-auto pt-6 border-t border-gray-100">
                            <div className="mb-4 px-1">
                                <div className="text-sm text-gray-500">Starting URL:</div>
                                <div className="text-sm font-medium text-gray-900 truncate">{startingUrl}</div>
                            </div>
                            <div className="relative">
                                <Input
                                    value={command}
                                    onChange={(e) => setCommand(e.target.value)}
                                    placeholder="Write a command..."
                                    className="pr-20 bg-gray-50/50 border-gray-200 focus:bg-white transition-all"
                                    onKeyPress={(e) => e.key === 'Enter' && handleCommandSubmit()}
                                    disabled={isRunning}
                                />
                                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex space-x-1">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        disabled={isRunning}
                                        className="text-gray-500 hover:text-gray-700"
                                    >
                                        <Mic2 className="w-4 h-4" />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="bg-blue-500 text-white hover:bg-blue-600 transition-all"
                                        onClick={handleCommandSubmit}
                                        disabled={isRunning}
                                    >
                                        <Play className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>

                            <div className="flex justify-between mt-4">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="text-gray-600 hover:text-gray-900"
                                    onClick={handleReset}
                                    disabled={isRunning}
                                >
                                    <RefreshCcw className="w-4 h-4 mr-2" />
                                    Start Over
                                </Button>
                            </div>
                        </div>
                    ) : null}
                </div>

                <div className="flex-1 bg-white">
                    {browserUrl ? (
                        <iframe
                            src={browserUrl}
                            className="w-full h-full border-none"
                            sandbox="allow-same-origin allow-scripts"
                            allow="clipboard-read; clipboard-write"
                        />
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full bg-gradient-to-br from-gray-50 to-gray-100">
                            <div className="bg-blue-500 text-white p-4 rounded-xl mb-6">
                                <Command className="w-8 h-8" />
                            </div>
                            <h2 className="text-2xl font-semibold text-gray-800 mb-2">Live Demo</h2>
                            <p className="text-gray-600">Your live preview will start here. To get started:</p>

                            <div className="mt-8 space-y-8 max-w-xl">
                                <div className="flex items-start space-x-4">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold">1</span>
                                    <p className="text-gray-600 mt-1">Enter your starting URL and goal to begin</p>
                                </div>

                                <div className="flex items-start space-x-4">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold">2</span>
                                    <p className="text-gray-600 mt-1">Once initialized, you can enter commands in the chat</p>
                                </div>

                                <div className="flex items-start space-x-4">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold">3</span>
                                    <p className="text-gray-600 mt-1">Watch as the automated browser follows your instructions</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}