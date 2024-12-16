import React, { useState, useEffect } from 'react';
import {
  Settings,
  Filter,
  GitBranch,
  AudioLines,
  Loader,
  Circle,
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AssistantRuntimeProvider,
  type ChatModelAdapter,
  useLocalRuntime,
  Thread,
  ThreadWelcome,
  Composer,
  useThreadConfig,
  useComposerRuntime,
} from '@assistant-ui/react';
import '@assistant-ui/react/styles/index.css';
import iconUrl from '@/assets/icon.jpeg';
import { useTranscriber } from '@@/transcriber/use-transcriber';

interface AutomationConfig {
  starting_url: string;
  goal: string | null;
  plan: string | null;
  model: string | null;
  features: string | null;
  elements_filter: string | null;
  branching_factor: number;
  agent_type: 'PromptAgent';
  storage_state: string;
  log_folder: string;
}

type ElementsFilterType = 'som' | 'visibility' | 'none';

const App: React.FC = () => {
  const {
    startSpeaking,
    stopSpeaking,
    recording,
    transcribing,
    transcription,
    transcriptionError,
  } = useTranscriber();
  const [form, setForm] = useState({
    model: 'gpt-4o-mini',
    features: 'axtree',
    elementsFilter: 'som',
  });

  const [error, setError] = useState<string>('');

  useEffect(() => {
    setError(transcriptionError);
  }, [transcriptionError]);

  const CustomModelAdapter: ChatModelAdapter = {
    async run({ messages, abortSignal }) {
      const [tab] = await browser.tabs.query({
        active: true,
        currentWindow: true,
      });
      if (!tab.url) throw new Error('No active tab URL found');

      const lastUserMessage = messages
        .filter((message) => message.role === 'user')
        .flatMap((message) => message.content)
        .filter((content) => content.type === 'text')
        .map((textContent) => textContent.text)
        .slice(-1)
        .join();

      const config: AutomationConfig = {
        starting_url: tab.url,
        goal: lastUserMessage,
        plan: '',
        model: form.model,
        features: form.features,
        elements_filter: form.elementsFilter as ElementsFilterType,
        branching_factor: 5,
        agent_type: 'PromptAgent',
        storage_state: 'state.json',
        log_folder: 'log',
      };

      const response = await fetch('http://localhost:5001/automate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors',
        body: JSON.stringify(config),
        signal: abortSignal,
      });

      const data = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: data,
          },
        ],
      };
    },
  };

  const TranscriptionHandler: React.FC = () => {
    const composer = useComposerRuntime();

    useEffect(() => {
      if (transcription) {
        composer.setText(transcription);
      }
    }, [transcription]);

    return null;
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-slate-100 min-h-screen p-6">
      <div className="max-w-md mx-auto backdrop-blur-sm bg-white/5 rounded-2xl p-6 shadow-xl border border-white/10">
        <h1 className="text-2xl font-bold flex items-center gap-3 mb-8 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          <Settings className="h-7 w-7 text-blue-400" />
          Configuration
        </h1>

        {error && (
          <Alert
            variant="destructive"
            className="mb-6 bg-red-500/10 border border-red-500/50 rounded-xl"
          >
            <AlertDescription className="text-red-200">
              {error}
            </AlertDescription>
          </Alert>
        )}

        <form className="space-y-5">
          <div className="space-y-5">
            {/* Form fields with enhanced styling */}
            <div className="space-y-2 group">
              <label
                htmlFor="model"
                className="flex items-center gap-2 text-sm font-medium text-slate-300 group-focus-within:text-blue-400 transition-colors"
              >
                <Settings className="h-4 w-4" />
                Model
              </label>
              <input
                id="model"
                type="text"
                name="model"
                value={form.model}
                onChange={(e) => {
                  setForm({
                    ...form,
                    model: e.target.value,
                  });
                }}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 focus:border-blue-500/50 focus:bg-slate-800 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all duration-200"
              />
            </div>

            <div className="space-y-2 group">
              <label
                htmlFor="features"
                className="flex items-center gap-2 text-sm font-medium text-slate-300 group-focus-within:text-blue-400 transition-colors"
              >
                <Filter className="h-4 w-4" />
                Features
              </label>
              <input
                id="features"
                type="text"
                name="features"
                value={form.features}
                onChange={(e) => {
                  setForm({
                    ...form,
                    features: e.target.value,
                  });
                }}
                placeholder="Comma-separated features"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 focus:border-blue-500/50 focus:bg-slate-800 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all duration-200"
              />
            </div>

            <div className="space-y-2 group">
              <label
                htmlFor="elementsFilter"
                className="flex items-center gap-2 text-sm font-medium text-slate-300 group-focus-within:text-blue-400 transition-colors"
              >
                <Filter className="h-4 w-4" />
                Elements Filter
              </label>
              <select
                id="elementsFilter"
                name="elementsFilter"
                value={form.elementsFilter}
                onChange={(e) => {
                  setForm({
                    ...form,
                    elementsFilter: e.target.value,
                  });
                }}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 focus:border-blue-500/50 focus:bg-slate-800 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all duration-200"
              >
                <option value="som">SoM (Set-of-Mark)</option>
                <option value="visibility">Visibility</option>
                <option value="none">None</option>
              </select>
            </div>
          </div>
        </form>
      </div>
      <div>
        <AssistantRuntimeProvider runtime={useLocalRuntime(CustomModelAdapter)}>
          <TranscriptionHandler />
          <Thread.Root
            config={{
              ...useThreadConfig(),
              assistantAvatar: { src: iconUrl },
              welcome: { message: 'A powerful LLM-based web agent!' },
            }}
          >
            <Thread.Viewport>
              <ThreadWelcome />
              <Thread.Messages />
              <Thread.FollowupSuggestions />
              <Thread.ViewportFooter>
                <Thread.ScrollToBottom />
                <Composer.Root>
                  <Composer.Input autoFocus />
                  <button
                    className="focus:outline-none mt-2.5 mb-2.5 w-8 h-8 p-2 flex items-center"
                    onClick={(e) => {
                      e.preventDefault();
                      if (transcribing) return;

                      if (recording) {
                        stopSpeaking();
                      } else {
                        startSpeaking();
                      }
                    }}
                  >
                    {transcribing ? (
                      <Loader size={16} className="animate-spin" />
                    ) : recording ? (
                      <Circle fill="#f50000" color="#f50000" strokeWidth={3} size={16} className="animate-pulse"/>
                    ) : (
                      <AudioLines size={16} />
                    )}
                  </button>
                  <Composer.Send />
                </Composer.Root>
              </Thread.ViewportFooter>
            </Thread.Viewport>
          </Thread.Root>
        </AssistantRuntimeProvider>
      </div>
    </div>
  );
};

export default App;
