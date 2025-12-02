import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AnimatePresence } from 'framer-motion';
import { fetchStations, type IntelligentStation } from './api';
import StationMap from './components/Map';
import Sidebar from './components/Sidebar';
import StationDrawer from './components/StationDrawer';

export default function App() {
  const [selectedStation, setSelectedStation] = useState<IntelligentStation | null>(null);
  const [mode, setMode] = useState<'general' | 'lifestyle' | 'retail'>('general');
  const [search, setSearch] = useState("");

  const { data: stations, isLoading } = useQuery({ 
    queryKey: ['stations'], 
    queryFn: fetchStations,
    refetchOnWindowFocus: false 
  });

  const filtered = useMemo(() => {
    if (!stations) return [];
    if (!search) return stations;
    return stations.filter(s => s.STATION.toLowerCase().includes(search.toLowerCase()));
  }, [stations, search]);

  if (isLoading) return <div className="h-screen w-screen bg-black text-white flex items-center justify-center font-mono">LOADING DATA STREAM...</div>;

  return (
    <div className="relative w-screen h-screen bg-black overflow-hidden font-sans text-white">
      <div className="absolute inset-0 z-0">
        <StationMap 
          stations={filtered} 
          mode={mode}
          onSelect={setSelectedStation}
          selectedName={selectedStation?.STATION || null}
        />
      </div>

      <Sidebar 
        mode={mode} 
        setMode={setMode} 
        searchQuery={search} 
        setSearchQuery={setSearch} 
      />

      <AnimatePresence>
        {selectedStation && (
          <StationDrawer 
            station={selectedStation} 
            onClose={() => setSelectedStation(null)} 
            mode={mode}
          />
        )}
      </AnimatePresence>
    </div>
  );
}