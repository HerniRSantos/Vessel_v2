import { useState, useEffect, useCallback } from 'react';
import VesselMap from './components/VesselMap';
import Sidebar from './components/Sidebar';
import VesselModal from './components/VesselModal';
import './index.css';

function App() {
  const [vessels, setVessels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedVessel, setSelectedVessel] = useState(null);
  const [modalMmsi, setModalMmsi] = useState(null);

  const fetchVessels = useCallback(async () => {
    try {
      const res = await fetch('/api/vessels/live', { credentials: 'include' });
      if (!res.ok) {
        if (res.status === 401) {
          setError('Unauthorized - please login');
          return;
        }
        throw new Error('Failed to fetch vessels');
      }
      const data = await res.json();
      setVessels(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchVessels();
    const interval = setInterval(fetchVessels, 5000);
    return () => clearInterval(interval);
  }, [fetchVessels]);

  const handleVesselClick = (vessel) => {
    setSelectedVessel(vessel);
    setModalMmsi(vessel.mmsi);
  };

  const handleModalClose = () => {
    setModalMmsi(null);
  };

  const handleVesselUpdate = (updatedVessel) => {
    setVessels(prev => prev.map(v => 
      v.mmsi === updatedVessel.mmsi ? { ...v, ...updatedVessel } : v
    ));
    if (selectedVessel && selectedVessel.mmsi === updatedVessel.mmsi) {
      setSelectedVessel({ ...selectedVessel, ...updatedVessel });
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      {/* Map */}
      <div className="flex-1 relative">
        <VesselMap 
          vessels={vessels} 
          onVesselClick={handleVesselClick}
        />
        
        {/* Top Bar */}
        <div className="absolute top-5 left-1/2 -translate-x-1/2 z-[1000]">
          <div className="flex items-center gap-4 bg-[rgba(16,20,30,0.92)] px-6 py-3 rounded-full border border-white/15 backdrop-blur-xl shadow-lg">
            <div className={`w-2.5 h-2.5 rounded-full ${error ? 'bg-red-500' : 'bg-green-400'} shadow-[0_0_10px_currentColor]`} />
            <h1 className="text-sm uppercase tracking-[3px] font-semibold">
              VesselControl <span className="font-light opacity-60">Intel</span>
            </h1>
          </div>
        </div>

        {/* Loading/Error States */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-[1000]">
            <div className="text-cyan-400 animate-pulse">A carregar embarcações...</div>
          </div>
        )}
        
        {error && (
          <div className="absolute top-24 left-1/2 -translate-x-1/2 z-[1000] bg-red-500/20 border border-red-500 px-4 py-2 rounded-lg text-red-400">
            Erro: {error}
          </div>
        )}
      </div>

      {/* Sidebar */}
      <Sidebar 
        vessels={vessels} 
        onVesselClick={handleVesselClick}
      />

      {/* Modal */}
      {modalMmsi && (
        <VesselModal 
          mmsi={modalMmsi}
          onClose={handleModalClose}
          onSave={handleVesselUpdate}
        />
      )}
    </div>
  );
}

export default App;