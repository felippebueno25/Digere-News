
import React from 'react';

interface Props {
  darkMode: boolean;
}

const Skeleton: React.FC<Props> = ({ darkMode }) => {
  return (
    <div className={`rounded-3xl shadow-sm border overflow-hidden animate-pulse ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-gray-100'}`}>
      <div className={`h-40 ${darkMode ? 'bg-slate-800' : 'bg-gray-200'}`} />
      <div className="p-8 space-y-6">
        <div className={`h-8 rounded w-3/4 ${darkMode ? 'bg-slate-800' : 'bg-gray-100'}`} />
        <div className="space-y-3">
          <div className={`h-4 rounded ${darkMode ? 'bg-slate-800/50' : 'bg-gray-50'}`} />
          <div className={`h-4 rounded ${darkMode ? 'bg-slate-800/50' : 'bg-gray-50'}`} />
          <div className={`h-4 rounded w-5/6 ${darkMode ? 'bg-slate-800/50' : 'bg-gray-50'}`} />
        </div>
        <div className={`h-40 rounded-2xl ${darkMode ? 'bg-slate-800/30' : 'bg-gray-50'}`} />
        <div className="grid grid-cols-2 gap-4">
          <div className={`h-12 rounded-xl ${darkMode ? 'bg-slate-800' : 'bg-gray-50'}`} />
          <div className={`h-12 rounded-xl ${darkMode ? 'bg-slate-800' : 'bg-gray-50'}`} />
        </div>
      </div>
    </div>
  );
};

export default Skeleton;
