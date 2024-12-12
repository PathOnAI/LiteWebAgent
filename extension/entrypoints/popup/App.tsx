import React, { useState } from 'react';
import { Settings, Send, Filter, GitBranch, Target, Map } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

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
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  
  async function startAutomation(formData: FormData): Promise<void> {
    setIsLoading(true);
    setError('');
    
    try {
      const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
      if (!tab.url) throw new Error('No active tab URL found');

      const config: AutomationConfig = {
        starting_url: tab.url,
        goal: formData.get('goal') as string | null,
        plan: formData.get('plan') as string | null,
        model: formData.get('model') as string | null,
        features: formData.get('features') as string | null,
        elements_filter: formData.get('elementsFilter') as ElementsFilterType,
        branching_factor: parseInt(formData.get('branchingFactor') as string || '5', 10),
        agent_type: 'PromptAgent',
        storage_state: 'state.json',
        log_folder: 'log',
      };

      const response = await fetch('http://localhost:5001/automate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors',
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Automation result:', result);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      setError(errorMessage);
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    await startAutomation(formData);
  };
  

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-slate-100 min-h-screen p-6">
      <div className="max-w-md mx-auto backdrop-blur-sm bg-white/5 rounded-2xl p-6 shadow-xl border border-white/10">
        <h1 className="text-2xl font-bold flex items-center gap-3 mb-8 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          <Settings className="h-7 w-7 text-blue-400" />
          Automation Config
        </h1>

        {error && (
          <Alert variant="destructive" className="mb-6 bg-red-500/10 border border-red-500/50 rounded-xl">
            <AlertDescription className="text-red-200">{error}</AlertDescription>
          </Alert>
        )}

        <form action={startAutomation} className="space-y-5">
          <div className="space-y-5">
            {/* Form fields with enhanced styling */}
            <div className="space-y-2 group">
              <label htmlFor="goal" className="flex items-center gap-2 text-sm font-medium text-slate-300 group-focus-within:text-blue-400 transition-colors">
                <Target className="h-4 w-4" />
                Goal
              </label>
              <input
                id="goal"
                type="text"
                name="goal"
                placeholder="Enter automation goal"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 focus:border-blue-500/50 focus:bg-slate-800 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all duration-200"
              />
            </div>

            <div className="space-y-2 group">
              <label htmlFor="plan" className="flex items-center gap-2 text-sm font-medium text-slate-300 group-focus-within:text-blue-400 transition-colors">
                <Map className="h-4 w-4" />
                Plan
              </label>
              <input
                id="plan"
                type="text"
                name="plan"
                placeholder="Enter automation plan"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 focus:border-blue-500/50 focus:bg-slate-800 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all duration-200"
              />
            </div>

            <div className="space-y-2 group">
              <label htmlFor="model" className="flex items-center gap-2 text-sm font-medium text-slate-300 group-focus-within:text-blue-400 transition-colors">
                <Settings className="h-4 w-4" />
                Model
              </label>
              <input
                id="model"
                type="text"
                name="model"
                defaultValue="gpt-4o-mini"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 focus:border-blue-500/50 focus:bg-slate-800 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all duration-200"
              />
            </div>

            <div className="space-y-2 group">
              <label htmlFor="features" className="flex items-center gap-2 text-sm font-medium text-slate-300 group-focus-within:text-blue-400 transition-colors">
                <Filter className="h-4 w-4" />
                Features
              </label>
              <input
                id="features"
                type="text"
                name="features"
                defaultValue="axtree"
                placeholder="Comma-separated features"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 focus:border-blue-500/50 focus:bg-slate-800 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all duration-200"
              />
            </div>

            <div className="space-y-2 group">
              <label htmlFor="elementsFilter" className="flex items-center gap-2 text-sm font-medium text-slate-300 group-focus-within:text-blue-400 transition-colors">
                <Filter className="h-4 w-4" />
                Elements Filter
              </label>
              <select 
                id="elementsFilter"
                name="elementsFilter"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 focus:border-blue-500/50 focus:bg-slate-800 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all duration-200"
              >
                <option value="som">SoM (Set-of-Mark)</option>
                <option value="visibility">Visibility</option>
                <option value="none">None</option>
              </select>
            </div>

            <div className="space-y-2 group">
              <label htmlFor="branchingFactor" className="flex items-center gap-2 text-sm font-medium text-slate-300 group-focus-within:text-blue-400 transition-colors">
                <GitBranch className="h-4 w-4" />
                Branching Factor
              </label>
              <input
                id="branchingFactor"
                type="number"
                name="branchingFactor"
                defaultValue="5"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 focus:border-blue-500/50 focus:bg-slate-800 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all duration-200"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-8 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 text-white font-medium rounded-xl flex items-center justify-center gap-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20"
          >
            {isLoading ? (
              <>
                <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                Start Automation
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default App;