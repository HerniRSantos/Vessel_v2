import { useState, useMemo } from 'react';

function FilterTabs({ active, onChange }) {
  return (
    <div className="flex gap-2 mb-3">
      <button
        onClick={() => onChange('all')}
        className={`flex-1 py-2 px-3 rounded-lg text-xs uppercase font-medium border transition-all
          ${active === 'all' 
            ? 'bg-cyan-500/10 border-cyan-400 text-cyan-400' 
            : 'border-white/10 text-gray-400 hover:border-white/30'}`}
      >
        Todas
      </button>
      <button
        onClick={() => onChange('suspect')}
        className={`flex-1 py-2 px-3 rounded-lg text-xs uppercase font-medium border transition-all
          ${active === 'suspect' 
            ? 'bg-red-500/10 border-red-400 text-red-400' 
            : 'border-white/10 text-gray-400 hover:border-white/30'}`}
      >
        🔴 Suspeitas
      </button>
      <button
        onClick={() => onChange('clear')}
        className={`flex-1 py-2 px-3 rounded-lg text-xs uppercase font-medium border transition-all
          ${active === 'clear' 
            ? 'bg-green-500/10 border-green-400 text-green-400' 
            : 'border-white/10 text-gray-400 hover:border-white/30'}`}
      >
        🔵 Limpas
      </button>
    </div>
  );
}

function VesselList({ vessels, filter, search, onVesselClick }) {
  const filtered = useMemo(() => {
    let result = vessels;
    
    if (filter === 'suspect') {
      result = result.filter(v => v.suspicious);
    } else if (filter === 'clear') {
      result = result.filter(v => !v.suspicious);
    }
    
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(v => 
        (v.name && v.name.toLowerCase().includes(q)) || 
        v.mmsi.toString().includes(q)
      );
    }
    
    return result;
  }, [vessels, filter, search]);
  
  if (filtered.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8 text-sm">
        Nenhuma embarcação encontrada
      </div>
    );
  }
  
  return (
    <div className="overflow-y-auto flex-1">
      {filtered.map(vessel => (
        <div
          key={vessel.mmsi}
          onClick={() => onVesselClick(vessel)}
          className="p-3 border-b border-white/5 cursor-pointer hover:bg-cyan-500/10 transition-colors rounded-lg mb-1"
        >
          <div className="flex items-center gap-3">
            <div 
              className={`w-2 h-2 rounded-full flex-shrink-0 
                ${vessel.suspicious ? 'bg-red-500 shadow-[0_0_6px_#ff3d5a]' : 'bg-green-400 shadow-[0_0_6px_#00ff9d]'}`}
            />
            <div className="flex-1 min-w-0">
              <div className={`font-medium text-sm truncate ${vessel.suspicious ? 'text-red-400' : ''}`}>
                {vessel.name || `MMSI: ${vessel.mmsi}`}
              </div>
              <div className="text-xs text-gray-500 font-mono">
                MMSI: {vessel.mmsi} • {vessel.type || 'N/A'}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Sidebar({ vessels, onVesselClick }) {
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  
  const counts = useMemo(() => {
    const total = vessels.length;
    const suspects = vessels.filter(v => v.suspicious).length;
    const clear = total - suspects;
    return { total, suspects, clear };
  }, [vessels]);
  
  return (
    <div className="w-80 bg-[rgba(16,20,30,0.92)] border-l border-white/10 flex flex-col h-full backdrop-blur-xl">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 p-4 border-b border-white/10">
        <div className="bg-white/5 p-3 rounded-xl text-center">
          <div className="text-2xl font-mono text-cyan-400">{counts.total}</div>
          <div className="text-xs text-gray-500 uppercase mt-1">Total</div>
        </div>
        <div className="bg-white/5 p-3 rounded-xl text-center">
          <div className="text-2xl font-mono text-red-400">{counts.suspects}</div>
          <div className="text-xs text-gray-500 uppercase mt-1">Suspeitas</div>
        </div>
        <div className="bg-white/5 p-3 rounded-xl text-center">
          <div className="text-2xl font-mono text-green-400">{counts.clear}</div>
          <div className="text-xs text-gray-500 uppercase mt-1">Limpas</div>
        </div>
      </div>
      
      {/* Search */}
      <div className="p-4 border-b border-white/10">
        <input
          type="text"
          placeholder="Procurar Nome ou MMSI..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none 
            focus:border-cyan-400 transition-colors placeholder-gray-500"
        />
      </div>
      
      {/* Filters */}
      <div className="px-4 pt-4">
        <FilterTabs active={filter} onChange={setFilter} />
      </div>
      
      {/* Vessel List */}
      <div className="flex-1 overflow-hidden px-4 pb-4">
        <div className="text-xs text-gray-500 uppercase mb-2">Embarcações Ativas</div>
        <VesselList 
          vessels={vessels} 
          filter={filter} 
          search={search} 
          onVesselClick={onVesselClick} 
        />
      </div>
    </div>
  );
}