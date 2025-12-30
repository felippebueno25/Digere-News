
import React from 'react';
import { NewsTopic } from '../types';

interface TopicCardProps {
  topic: NewsTopic;
  isActive: boolean;
  onClick: (topic: NewsTopic) => void;
  icon: string;
  darkMode: boolean;
}

const TopicCard: React.FC<TopicCardProps> = ({ topic, isActive, onClick, icon, darkMode }) => {
  return (
    <button
      onClick={() => onClick(topic)}
      className={`flex flex-col items-center justify-center p-4 rounded-2xl transition-all duration-300 min-w-[100px] border-2 shadow-sm ${
        isActive 
          ? 'bg-blue-600 border-blue-600 text-white shadow-blue-500/30 scale-105 z-10' 
          : darkMode 
            ? 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800 hover:border-slate-700 hover:text-white'
            : 'bg-white border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-200 hover:text-blue-600'
      }`}
    >
      <i className={`fa-solid ${icon} text-xl mb-2 transition-transform duration-300 ${isActive ? 'scale-110' : ''}`}></i>
      <span className="text-[11px] font-black uppercase tracking-wider whitespace-nowrap">{topic}</span>
    </button>
  );
};

export default TopicCard;
