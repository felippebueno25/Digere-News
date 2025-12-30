
import React, { useState, useEffect, useCallback } from 'react';
import { NewsTopic, AppState } from './types';
import { fetchNewsSummary } from './services/geminiService';
import TopicCard from './components/TopicCard';
import SummaryDisplay from './components/SummaryDisplay';
import Skeleton from './components/Skeleton';
import DigestionProgress from './components/DigestionProgress';

const TOPICS = [
  { id: NewsTopic.BRASIL, icon: 'fa-earth-americas' },
  { id: NewsTopic.MUNDO, icon: 'fa-globe' },
  { id: NewsTopic.TECNOLOGIA, icon: 'fa-microchip' },
  { id: NewsTopic.ECONOMIA, icon: 'fa-chart-line' },
  { id: NewsTopic.POLITICA, icon: 'fa-gavel' },
  { id: NewsTopic.ESPORTES, icon: 'fa-football' },
  { id: NewsTopic.CIENCIA, icon: 'fa-flask' },
  { id: NewsTopic.ENTRETENIMENTO, icon: 'fa-clapperboard' },
];

const App: React.FC = () => {
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'dark' || 
             (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    }
    return false;
  });

  const [state, setState] = useState<AppState>({
    currentTopic: NewsTopic.BRASIL,
    summaries: {},
    loading: false,
    error: null,
  });

  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  const loadTopic = useCallback(async (topic: NewsTopic) => {
    const existing = state.summaries[topic];
    const now = Date.now();
    const CACHE_TIME = 15 * 60 * 1000;

    if (existing && (now - existing.timestamp < CACHE_TIME)) {
      setState(prev => ({ ...prev, currentTopic: topic, error: null }));
      return;
    }

    setState(prev => ({ ...prev, currentTopic: topic, loading: true, error: null }));
    setProgress(0);

    // Simulação de progresso orgânico
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 95) return prev;
        const inc = Math.random() * 15;
        return Math.min(prev + inc, 95);
      });
    }, 800);

    try {
      const summary = await fetchNewsSummary(topic);
      clearInterval(interval);
      setProgress(100);
      
      setTimeout(() => {
        setState(prev => ({
          ...prev,
          summaries: { ...prev.summaries, [topic]: summary },
          loading: false,
        }));
        setProgress(0);
      }, 500);
    } catch (err: any) {
      clearInterval(interval);
      setState(prev => ({ ...prev, loading: false, error: err.message }));
      setProgress(0);
    }
  }, [state.summaries]);

  useEffect(() => {
    loadTopic(NewsTopic.BRASIL);
  }, []);

  const currentSummary = state.summaries[state.currentTopic];

  return (
    <div className={`min-h-screen transition-colors duration-500 ${darkMode ? 'bg-slate-950' : 'bg-gray-50'} pb-12`}>
      {/* Header */}
      <header className={`sticky top-0 z-30 shadow-sm transition-colors duration-500 border-b ${darkMode ? 'bg-slate-900/80 border-slate-800 backdrop-blur-md' : 'bg-white/80 border-gray-100 backdrop-blur-md'}`}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              <i className="fa-solid fa-bolt-lightning text-xl"></i>
            </div>
            <div>
              <h1 className={`text-xl font-black leading-tight tracking-tight ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                DIGERE <span className="text-blue-500">NEWS</span>
              </h1>
              <p className={`text-[10px] font-bold uppercase tracking-[0.2em] ${darkMode ? 'text-slate-500' : 'text-gray-400'}`}>O Banquete da Informação</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setDarkMode(!darkMode)}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${darkMode ? 'bg-slate-800 text-yellow-400 hover:bg-slate-700' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
            >
              <i className={`fa-solid ${darkMode ? 'fa-sun' : 'fa-moon'}`}></i>
            </button>
            <div className={`hidden sm:flex items-center text-xs font-bold px-4 py-2 rounded-full border ${darkMode ? 'text-blue-400 bg-blue-500/10 border-blue-500/20' : 'text-gray-500 bg-gray-50 border-gray-100'}`}>
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
              IA ONLINE
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 pt-8">
        {/* Topic Selector */}
        <div className="mb-10">
          <h2 className={`text-xs font-black uppercase tracking-widest mb-6 px-1 ${darkMode ? 'text-slate-500' : 'text-gray-400'}`}>
            Escolha seu prato informativo
          </h2>
          <div className="flex gap-4 overflow-x-auto pb-6 scrollbar-hide snap-x no-scrollbar">
            {TOPICS.map((topic) => (
              <div key={topic.id} className="snap-start">
                <TopicCard
                  topic={topic.id}
                  icon={topic.icon}
                  isActive={state.currentTopic === topic.id}
                  onClick={loadTopic}
                  darkMode={darkMode}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Progress Bar / Digestion Loader */}
        {state.loading && <DigestionProgress progress={progress} darkMode={darkMode} />}

        {/* Error State */}
        {state.error && (
          <div className={`rounded-3xl p-8 text-center mb-8 border animate-in zoom-in-95 duration-300 ${darkMode ? 'bg-red-500/10 border-red-500/20' : 'bg-red-50 border-red-100'}`}>
            <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <i className="fa-solid fa-face-frown-open text-2xl"></i>
            </div>
            <h3 className={`text-lg font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Indigestão de Dados!</h3>
            <p className={`${darkMode ? 'text-slate-400' : 'text-gray-600'} mb-6`}>{state.error}</p>
            <button
              onClick={() => loadTopic(state.currentTopic)}
              className="bg-red-600 text-white px-8 py-3 rounded-2xl font-bold shadow-lg hover:bg-red-700 transition-colors"
            >
              Tentar Novamente
            </button>
          </div>
        )}

        {/* Content Area */}
        <div className="relative">
          {state.loading ? (
            <Skeleton darkMode={darkMode} />
          ) : (
            currentSummary && <SummaryDisplay summary={currentSummary} darkMode={darkMode} />
          )}
        </div>
      </main>

      <footer className={`mt-12 text-center text-sm px-4 pb-8 ${darkMode ? 'text-slate-600' : 'text-gray-400'}`}>
        <p>© 2024 Digere News. IA alimentada por Gemini 2.5 & 3.</p>
      </footer>
    </div>
  );
};

export default App;
