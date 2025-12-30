
import React, { useState, useEffect } from 'react';

const MESSAGES = [
  "Colhendo manchetes frescas...",
  "Mastigando os artigos...",
  "Limpando as gorduras publicitárias...",
  "Digerindo os dados complexos...",
  "Temperando com inteligência...",
  "Finalizando o banquete de notícias...",
  "Organizando a mesa informativa...",
  "Filtrando o ruído das redes..."
];

interface Props {
  progress: number;
  darkMode: boolean;
}

const DigestionProgress: React.FC<Props> = ({ progress, darkMode }) => {
  const [msgIndex, setMsgIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMsgIndex(prev => (prev + 1) % MESSAGES.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mb-10 animate-in fade-in slide-in-from-top-4 duration-500">
      <div className="flex justify-between items-end mb-3 px-1">
        <span className={`text-sm font-bold flex items-center gap-2 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>
          <i className="fa-solid fa-utensils animate-bounce"></i>
          {MESSAGES[msgIndex]}
        </span>
        <span className={`text-xs font-black ${darkMode ? 'text-slate-500' : 'text-gray-400'}`}>
          {Math.round(progress)}%
        </span>
      </div>
      <div className={`h-4 w-full rounded-full overflow-hidden p-1 border ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-gray-100 border-gray-200'}`}>
        <div 
          className="h-full rounded-full bg-gradient-to-r from-blue-600 via-indigo-500 to-blue-400 transition-all duration-700 ease-out relative"
          style={{ width: `${progress}%` }}
        >
          <div className="absolute top-0 right-0 h-full w-8 bg-white/20 blur-sm -skew-x-12 animate-[pulse_1s_infinite]"></div>
        </div>
      </div>
    </div>
  );
};

export default DigestionProgress;
