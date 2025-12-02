import { motion } from 'framer-motion';
import { X, Clock, Building, Coffee, Sparkles, MapPin, Info, ShoppingBag, HeartPulse } from 'lucide-react';
import { type IntelligentStation, fetchStationAnalysis } from '../api';
import { useState, useEffect } from 'react';

interface AnalysisData {
  persona: string;
  description: string;
  is_ai_generated?: boolean;
  vitality_score?: number;
  office_score?: number;
}

export default function StationDrawer({ station, onClose, mode }: { station: IntelligentStation, onClose: () => void, mode: string }) {
  const { time_dna, metrics } = station;
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [showExplainer, setShowExplainer] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setAnalysis(null);

    fetchStationAnalysis(station.STATION)
      .then(data => {
        if (active) setAnalysis(data as AnalysisData);
      })
      .catch((err) => console.error("Analysis error", err))
      .finally(() => { if (active) setLoading(false); });

    return () => { active = false; };
  }, [station.STATION]);

  const displayVitality = analysis?.vitality_score 
    ? Math.round(analysis.vitality_score) 
    : Math.round(metrics.weekend_vitality * 100);

  const getBoroughColor = () => {
    if (metrics.borough === 'Manhattan') return 'bg-blue-600';
    if (metrics.borough === 'Brooklyn') return 'bg-yellow-600';
    if (metrics.borough === 'Queens') return 'bg-purple-600';
    if (metrics.borough === 'Bronx') return 'bg-orange-600';
    return 'bg-gray-600';
  };

  const getPeakTime = () => {
    const times = {
      'Morning': time_dna.morning,
      'Lunch': time_dna.lunch,
      'Evening': time_dna.evening,
      'Night': time_dna.night
    };
    return Object.entries(times).reduce((a, b) => a[1] > b[1] ? a : b)[0];
  };

  // --- Dynamic Content based on Mode ---
  const renderModeSpecificContent = () => {
    if (mode === 'retail') {
      const gap = (metrics as any).retail_gap || 0;
      const isOpportunity = gap > 0.6;
      
      return (
        <div className={`p-5 rounded-xl border ${isOpportunity ? 'bg-emerald-900/20 border-emerald-800/50' : 'bg-gray-800/40 border-gray-700/50'} mb-6`}>
          <div className="flex items-center gap-2 mb-3">
            <ShoppingBag size={16} className={isOpportunity ? "text-emerald-400" : "text-gray-400"} />
            <span className="text-[10px] font-bold uppercase tracking-widest text-gray-300">Retail Scout Report</span>
          </div>
          <div className="text-xl font-bold text-white mb-2">
            {isOpportunity ? "High Market Opportunity" : "Saturated Market"}
          </div>
          <p className="text-sm text-gray-400 leading-relaxed">
            {isOpportunity 
              ? `High office traffic (${Math.round((metrics as any).office_density || 0)}%) with low social amenities creates a gap for lunch/coffee spots.`
              : "Balanced supply and demand. Amenities match the current foot traffic levels."
            }
          </p>
        </div>
      );
    }

    if (mode === 'lifestyle') {
      const isNightlife = displayVitality > 70;
      return (
        <div className="p-5 rounded-xl bg-purple-900/10 border border-purple-800/30 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <HeartPulse size={16} className="text-purple-400" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-gray-300">Vibe Check</span>
          </div>
          <div className="text-xl font-bold text-white mb-2">
            {isNightlife ? "High Social Pulse" : "Quiet Sanctuary"}
          </div>
          <p className="text-sm text-gray-400 leading-relaxed">
            {isNightlife 
              ? `Top ${100 - displayVitality}% for social energy. A hub for dining, nightlife, and off-work activity.`
              : `A low-pulse residential area. Activity drops significantly after 7 PM.`
            }
          </p>
        </div>
      );
    }

    // Default General Mode
    return (
      <div className="p-5 rounded-xl bg-gray-800/40 border border-gray-700/50 relative overflow-hidden group mb-6">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 group-hover:opacity-100 transition-opacity" />
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={14} className="text-amber-400" />
            <span className="text-[10px] font-bold uppercase text-gray-400 tracking-widest">
              {analysis?.is_ai_generated ? "AI Analysis" : "Classification"}
            </span>
          </div>
          {loading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-6 bg-gray-700 rounded w-3/4"></div>
              <div className="h-4 bg-gray-700/50 rounded w-full"></div>
            </div>
          ) : (
            <>
              <div className="text-xl font-bold text-white tracking-tight mb-2">
                {analysis ? analysis.persona : station.persona_name}
              </div>
              <div className="text-sm text-gray-300 leading-relaxed opacity-90">
                {analysis ? analysis.description : `Defined by ${displayVitality}% social pulse and ${getPeakTime()} activity.`}
              </div>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ x: 400 }} animate={{ x: 0 }} exit={{ x: 400 }}
      className="absolute top-4 right-4 w-[400px] bg-[#09090b]/95 backdrop-blur-2xl border border-gray-800 shadow-2xl z-30 h-[calc(100vh-2rem)] overflow-y-auto rounded-2xl flex flex-col font-sans"
    >
      {/* Header */}
      <div className="p-6 border-b border-gray-800 relative bg-gradient-to-b from-gray-900 to-[#09090b]">
        <button onClick={onClose} className="absolute top-6 right-6 text-gray-400 hover:text-white transition bg-gray-800/50 p-1.5 rounded-full">
          <X size={18} />
        </button>

        <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest text-white mb-4 ${getBoroughColor()} shadow-lg`}>
          <MapPin size={10} />
          {metrics.borough || 'NYC'}
        </div>

        <h2 className="text-4xl font-black text-white leading-none tracking-tight mb-6">{station.STATION}</h2>

        {/* DYNAMIC CARD */}
        {renderModeSpecificContent()}
      </div>

      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        
        {/* Explanation Toggle */}
        <div className="flex items-center justify-between text-xs text-gray-500 border-b border-gray-800 pb-2">
          <span className="uppercase font-bold tracking-widest">Station Analytics</span>
          <button 
            onClick={() => setShowExplainer(!showExplainer)}
            className={`flex items-center gap-1 transition-colors ${showExplainer ? 'text-blue-400' : 'hover:text-white'}`}
          >
            <Info size={12} /> {showExplainer ? "Close Guide" : "Metric Guide"}
          </button>
        </div>

        {showExplainer && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }} 
            animate={{ opacity: 1, height: 'auto' }} 
            className="bg-blue-900/10 border border-blue-800/30 p-4 rounded-lg text-xs space-y-4"
          >
            <div>
                <div className="flex items-center gap-2 mb-1">
                    <HeartPulse size={12} className="text-emerald-400" />
                    <strong className="text-blue-100">Social Pulse (0-100)</strong>
                </div>
                <p className="text-gray-400 leading-relaxed pl-5">
                    The <strong>"Off-Work"</strong> Index. A high score means this neighborhood comes alive on evenings and weekends. It combines the density of social amenities (Bars/Restaurants) with late-night ridership data.
                </p>
            </div>

            <div>
                <div className="flex items-center gap-2 mb-1">
                    <Building size={12} className="text-blue-400" />
                    <strong className="text-blue-100">Office Density</strong>
                </div>
                <p className="text-gray-400 leading-relaxed pl-5">
                    Measures the concentration of corporate workspace. High scores indicate a "Commuter" destination that goes quiet after 6 PM.
                </p>
            </div>

            <div>
                <div className="flex items-center gap-2 mb-1">
                    <ShoppingBag size={12} className="text-orange-400" />
                    <strong className="text-blue-100">Retail Gap</strong>
                </div>
                <p className="text-gray-400 leading-relaxed pl-5">
                    Calculated by `Office Density - Social Pulse`. Identifies areas with high foot traffic but few social outlets—a prime opportunity for new businesses.
                </p>
            </div>
          </motion.div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-3">
          <StatCard icon={<HeartPulse size={14} />} label="Pulse" value={displayVitality} sub="%" color="text-emerald-400" />
          <StatCard icon={<Building size={14} />} label="Offices" value={Math.round((metrics as any).office_density || 0)} sub="%" color="text-blue-400" />
          <StatCard icon={<Coffee size={14} />} label="Amenities" value={station.n_bars} sub="Spots" color="text-amber-400" />
        </div>

        {/* Time DNA */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="text-gray-400" size={16} />
              <h3 className="text-[10px] font-bold uppercase text-white tracking-widest">24h Pulse</h3>
            </div>
            <span className="text-[9px] text-gray-500 font-mono uppercase border border-gray-800 px-2 py-1 rounded">
              Peak: {getPeakTime()}
            </span>
          </div>
          
          <div className="space-y-3 bg-gray-900/50 p-4 rounded-xl border border-gray-800">
            <TimeRow label="Morning" time="6a-10a" value={time_dna.morning} color="bg-blue-500" />
            <TimeRow label="Lunch" time="11a-2p" value={time_dna.lunch} color="bg-yellow-500" />
            <TimeRow label="Evening" time="4p-8p" value={time_dna.evening} color="bg-orange-500" />
            <TimeRow label="Night" time="10p-4a" value={time_dna.night} color="bg-purple-500" />
          </div>
        </div>

      </div>
    </motion.div>
  );
}

function StatCard({ icon, label, value, sub, color }: any) {
  return (
    <div className="bg-[#151517] p-3 rounded-xl border border-gray-800 hover:border-gray-700 transition-all hover:bg-[#1a1a1d] group text-center">
      <div className="flex items-center justify-center gap-2 text-gray-500 group-hover:text-gray-400 mb-2 transition-colors">
        {icon} <span className="text-[9px] uppercase font-bold tracking-wider">{label}</span>
      </div>
      <div className={`text-xl font-mono font-bold ${color || 'text-white'}`}>
        {value} <span className="text-xs text-gray-600 font-sans font-normal ml-1">{sub}</span>
      </div>
    </div>
  );
}

function TimeRow({ label, time, value, color }: any) {
  const width = Math.max(value, 4); // Min width for visibility
  return (
    <div className="flex items-center gap-3 group">
      <div className="w-20 flex flex-col items-end justify-center">
        <span className="text-xs font-bold text-gray-300 leading-tight">{label}</span>
        <span className="text-[9px] text-gray-600 font-mono leading-tight">{time}</span>
      </div>
      
      <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden relative flex items-center">
        <div 
          className={`h-full ${color} transition-all duration-500 ease-out opacity-80 group-hover:opacity-100`} 
          style={{ width: `${width}%` }} 
        />
      </div>
      
      <div className="w-8 flex items-center justify-center">
        <span className="text-xs font-mono text-gray-500 tabular-nums text-center">{Math.round(value)}</span>
      </div>
    </div>
  );
}