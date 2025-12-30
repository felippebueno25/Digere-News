
import React, { useState, useRef } from 'react';
import ReactMarkdown from 'https://esm.sh/react-markdown';
import { NewsSummary } from '../types';
import { generateSpeech, decodeAudioData } from '../services/geminiService';

interface SummaryDisplayProps {
  summary: NewsSummary;
  darkMode: boolean;
}

const SummaryDisplay: React.FC<SummaryDisplayProps> = ({ summary, darkMode }) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null);

  const handlePlayAudio = async () => {
    if (isSpeaking) {
      sourceNodeRef.current?.stop();
      setIsSpeaking(false);
      return;
    }

    try {
      setIsLoadingAudio(true);
      const audioData = await generateSpeech(summary.content);
      
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
      }

      const audioBuffer = await decodeAudioData(
        audioData,
        audioContextRef.current,
        24000,
        1
      );

      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      
      source.onended = () => setIsSpeaking(false);
      
      sourceNodeRef.current = source;
      source.start(0);
      setIsSpeaking(true);
    } catch (error) {
      console.error("Erro ao reproduzir áudio:", error);
      alert("Não foi possível reproduzir o áudio.");
    } finally {
      setIsLoadingAudio(false);
    }
  };

  return (
    <div className={`rounded-3xl shadow-xl border overflow-hidden animate-in fade-in slide-in-from-bottom-6 duration-700 ${darkMode ? 'bg-slate-900 border-slate-800 shadow-black/40' : 'bg-white border-gray-100 shadow-gray-200/50'}`}>
      <div className={`p-6 sm:p-8 text-white relative overflow-hidden ${darkMode ? 'bg-gradient-to-br from-indigo-950 via-slate-900 to-blue-900' : 'bg-gradient-to-br from-blue-600 via-indigo-600 to-blue-700'}`}>
        {/* Animated background element */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -mr-20 -mt-20 blur-3xl animate-pulse"></div>
        
        <div className="relative z-10 flex flex-col sm:flex-row justify-between items-start gap-6">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="px-3 py-1 bg-white/10 rounded-full text-[10px] font-black uppercase tracking-widest backdrop-blur-md border border-white/10">
                {summary.topic}
              </span>
              <span className="flex items-center gap-1.5 text-[10px] font-bold bg-green-500/20 px-2 py-1 rounded-full border border-green-500/30">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-ping"></span>
                FONTE DIRETA
              </span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight">Digestão Finalizada</h2>
          </div>

          <button
            onClick={handlePlayAudio}
            disabled={isLoadingAudio}
            className={`flex items-center gap-3 px-6 py-3 rounded-2xl transition-all font-black text-sm shadow-xl ${
              isSpeaking 
                ? 'bg-red-500 text-white animate-pulse hover:bg-red-600' 
                : 'bg-white text-blue-700 hover:scale-105 active:scale-95'
            } disabled:opacity-50 disabled:cursor-wait`}
          >
            {isLoadingAudio ? (
              <i className="fa-solid fa-spinner animate-spin"></i>
            ) : isSpeaking ? (
              <i className="fa-solid fa-square"></i>
            ) : (
              <i className="fa-solid fa-headphones"></i>
            )}
            {isLoadingAudio ? 'PREPARANDO VOZ...' : isSpeaking ? 'PARAR' : 'OUVIR RESUMO'}
          </button>
        </div>
        
        <div className={`mt-6 flex items-center text-[11px] font-bold gap-4 ${darkMode ? 'text-slate-400' : 'text-blue-100'}`}>
          <span className="flex items-center gap-1.5"><i className="fa-regular fa-clock opacity-60"></i> {new Date(summary.timestamp).toLocaleTimeString('pt-BR')}</span>
          <span className="flex items-center gap-1.5"><i className="fa-solid fa-brain opacity-60"></i> Gemini Intelligence</span>
        </div>
      </div>
      
      <div className="p-6 sm:p-10">
        {isSpeaking && (
          <div className={`mb-10 p-5 rounded-2xl border flex items-center gap-5 animate-in fade-in zoom-in duration-300 ${darkMode ? 'bg-blue-500/5 border-blue-500/20' : 'bg-blue-50 border-blue-100'}`}>
            <div className="flex gap-1.5 items-center h-6">
              {[1,2,3,4,5,6,7,8,9,10].map(i => (
                <div 
                  key={i} 
                  className={`w-1 rounded-full animate-bounce ${darkMode ? 'bg-blue-500' : 'bg-blue-400'}`} 
                  style={{ height: `${Math.random() * 100 + 30}%`, animationDelay: `${i * 0.08}s` }}
                ></div>
              ))}
            </div>
            <span className={`text-sm font-bold ${darkMode ? 'text-blue-400' : 'text-blue-700'}`}>NARRADOR DIGITAL ATIVO...</span>
          </div>
        )}

        <div className={`prose max-w-none leading-relaxed mb-12 ${darkMode ? 'prose-invert text-slate-300' : 'text-gray-700'}`}>
          <ReactMarkdown
            components={{
              h1: ({node, ...props}) => <h1 className={`text-2xl sm:text-3xl font-black mb-8 mt-2 border-l-8 pl-5 ${darkMode ? 'text-white border-blue-500' : 'text-gray-900 border-blue-600'}`} {...props} />,
              h2: ({node, ...props}) => <h2 className={`text-xl font-bold mb-5 mt-10 flex items-center gap-3 ${darkMode ? 'text-slate-100' : 'text-gray-800'}`} {...props} />,
              p: ({node, ...props}) => <p className="mb-6 text-lg sm:text-xl leading-relaxed" {...props} />,
              ul: ({node, ...props}) => <ul className="list-none pl-0 mb-8 space-y-4" {...props} />,
              li: ({node, ...props}) => (
                <li className={`flex gap-3 items-start text-lg ${darkMode ? 'text-slate-300' : 'text-gray-700'}`}>
                  <span className="mt-2.5 w-2 h-2 rounded-full bg-blue-500 shrink-0"></span>
                  <span {...props} />
                </li>
              ),
              strong: ({node, ...props}) => <strong className={`font-black px-1.5 rounded ${darkMode ? 'text-blue-300 bg-blue-900/40' : 'text-blue-900 bg-blue-50'}`} {...props} />
            }}
          >
            {summary.content}
          </ReactMarkdown>
        </div>

        {summary.sources.length > 0 && (
          <div className={`mt-10 pt-8 border-t ${darkMode ? 'border-slate-800' : 'border-gray-100'}`}>
            <div className="flex items-center justify-between mb-6">
              <h3 className={`text-[10px] font-black uppercase tracking-[0.2em] ${darkMode ? 'text-slate-500' : 'text-gray-400'}`}>Ingredientes (Fontes)</h3>
              <span className={`text-[10px] font-bold px-2 py-1 rounded-md ${darkMode ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'bg-blue-50 text-blue-600'}`}>IA Grounding Enabled</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {summary.sources.map((source, index) => (
                <a
                  key={index}
                  href={source.uri}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`flex items-center p-4 rounded-2xl border transition-all group shadow-sm ${
                    darkMode 
                      ? 'bg-slate-800/50 border-slate-700 hover:border-blue-500/50 hover:bg-slate-800' 
                      : 'bg-white border-gray-100 hover:border-blue-200 hover:bg-blue-50/50'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center mr-4 transition-colors ${darkMode ? 'bg-slate-700 group-hover:bg-blue-500/20' : 'bg-gray-50 group-hover:bg-white'}`}>
                    <i className={`fa-solid fa-link text-xs ${darkMode ? 'text-slate-500 group-hover:text-blue-400' : 'text-gray-400 group-hover:text-blue-500'}`}></i>
                  </div>
                  <span className={`text-sm truncate font-bold ${darkMode ? 'text-slate-400 group-hover:text-white' : 'text-gray-600 group-hover:text-blue-700'}`}>
                    {source.title}
                  </span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SummaryDisplay;
