import { Search, Map, ShoppingBag, Moon } from 'lucide-react';
import Legend from './Legend';

interface Props {
  mode: 'general' | 'lifestyle' | 'retail';
  setMode: (m: 'general' | 'lifestyle' | 'retail') => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
}

export default function Sidebar({ mode, setMode, searchQuery, setSearchQuery }: Props) {
  return (
    <div className="absolute top-4 left-4 w-80 flex flex-col gap-3 z-20 pointer-events-none font-sans">

      {/* Brand Header */}
      <div className="bg-[#09090b]/95 backdrop-blur-2xl border border-gray-800 p-5 rounded-xl pointer-events-auto shadow-2xl">
        <h1 className="text-3xl font-black text-white tracking-tighter mb-1">
          METRO<span className="text-blue-500">PULSE</span>
        </h1>
        <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-4">NYC Urban Intelligence</p>

        {/* Search */}
        <div className="relative group">
          <Search className="absolute left-3 top-2.5 text-gray-500 group-focus-within:text-blue-400 transition-colors" size={16} />
          <input
            type="text"
            placeholder="Search Station..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full bg-[#151517] border border-gray-800 text-white text-sm py-2.5 pl-10 pr-4 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 transition-all font-medium placeholder:text-gray-600"
          />
        </div>
      </div>

      {/* Mode Switcher */}
      <div className="bg-[#09090b]/95 backdrop-blur-2xl border border-gray-800 p-3 rounded-xl pointer-events-auto shadow-2xl flex flex-col gap-1">
        <p className="text-[9px] uppercase font-bold text-gray-500 mb-2 px-2">Analysis Mode</p>

        <ModeBtn
          active={mode === 'general'}
          onClick={() => setMode('general')}
          icon={<Map size={16} />}
          label="Overview"
          desc="Cluster archetypes"
        />
        <ModeBtn
          active={mode === 'lifestyle'}
          onClick={() => setMode('lifestyle')}
          icon={<Moon size={16} />}
          label="Lifestyle"
          desc="Borough & Vibe"
        />
        <ModeBtn
          active={mode === 'retail'}
          onClick={() => setMode('retail')}
          icon={<ShoppingBag size={16} />}
          label="Retail Scout"
          desc="Market gaps"
        />
      </div>

      {/* Legend */}
      <Legend mode={mode} />
    </div>
  );
}

function ModeBtn({ active, onClick, icon, label, desc }: any) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-3 w-full p-3 rounded-lg text-left transition-all border
        ${active 
          ? 'bg-blue-600/10 border-blue-500/50 text-white' 
          : 'border-transparent text-gray-400 hover:bg-[#151517] hover:text-white'}
      `}
    >
      <div className={`${active ? 'text-blue-400' : 'text-gray-500'}`}>{icon}</div>
      <div className="flex-1">
        <div className="text-sm font-bold leading-none mb-1">{label}</div>
        <div className="text-[10px] opacity-60 uppercase tracking-wider leading-none">{desc}</div>
      </div>
    </button>
  );
}