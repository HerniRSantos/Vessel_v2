import { useState, useEffect } from 'react';
import { getVessel, updateVessel } from '../lib/api';

const VESSEL_TYPES = [
  'Desconhecido', 'Carga', 'Petroleiro', 'Pesca', 'Recreio', 
  'Passageiros', 'Rebocador', 'Militar', 'Veleiro', 'Lancha', 'Outro'
];

const SUSPECT_REASONS = [
  '', 'Tráfico de droga', 'Tráfico de pessoas', 'Contrabando', 
  'Pesca ilegal', 'Rota suspeita', 'AIS desligado', 'Identidade falsa', 'Outro'
];

export default function VesselModal({ mmsi, onClose, onSave }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [vessel, setVessel] = useState(null);
  const [form, setForm] = useState({
    name: '',
    vessel_type: 'Desconhecido',
    suspicious: false,
    suspect_reason: '',
    notes: ''
  });

  useEffect(() => {
    if (!mmsi) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    getVessel(mmsi)
      .then(data => {
        setVessel(data);
        setForm({
          name: data.name || '',
          vessel_type: data.vessel_type || 'Desconhecido',
          suspicious: data.suspicious || false,
          suspect_reason: data.suspect_reason || '',
          notes: data.notes || ''
        });
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [mmsi]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateVessel(mmsi, form);
      onSave({ ...vessel, ...form });
      onClose();
    } catch (err) {
      console.error('Save failed:', err);
    } finally {
      setSaving(false);
    }
  };

  if (!mmsi) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[2000] flex items-center justify-center p-4">
      <div className="bg-[rgba(16,20,30,0.95)] border border-white/15 rounded-2xl p-6 w-full max-w-md max-h-[85vh] overflow-y-auto shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold">
            {vessel?.name || `MMSI: ${mmsi}`}
          </h2>
          <button 
            onClick={onClose}
            className="w-8 h-8 rounded-full border border-white/20 flex items-center justify-center hover:bg-red-500/20 hover:border-red-500 transition-colors"
          >
            ✕
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">A carregar...</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 mb-4 p-3 bg-white/5 rounded-xl">
              <div>
                <div className="text-xs text-gray-500 uppercase">MMSI</div>
                <div className="font-mono text-cyan-400">{mmsi}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 uppercase">Posições</div>
                <div className="font-mono">{vessel?.position_count || 0}</div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs text-gray-500 uppercase mb-2">Nome</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="block text-xs text-gray-500 uppercase mb-2">Tipo</label>
                <select
                  value={form.vessel_type}
                  onChange={(e) => setForm({ ...form, vessel_type: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-cyan-400"
                >
                  {VESSEL_TYPES.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              <div>
                <button
                  onClick={() => setForm({ ...form, suspicious: !form.suspicious })}
                  className={`w-full p-4 rounded-xl border transition-all flex items-center gap-3
                    ${form.suspicious 
                      ? 'bg-red-500/15 border-red-500 text-red-400' 
                      : 'bg-white/5 border-white/10 hover:border-white/30'}`}
                >
                  <div className={`w-10 h-6 rounded-full transition-all ${form.suspicious ? 'bg-red-500' : 'bg-white/20'}`}>
                    <div className={`w-4 h-4 bg-white rounded-full mt-1 transition-transform ${form.suspicious ? 'translate-x-5' : 'translate-x-1'}`} />
                  </div>
                  <span className="font-semibold">Marcar como Suspeita</span>
                </button>
              </div>

              {form.suspicious && (
                <div>
                  <label className="block text-xs text-gray-500 uppercase mb-2">Motivo</label>
                  <select
                    value={form.suspect_reason}
                    onChange={(e) => setForm({ ...form, suspect_reason: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-cyan-400"
                  >
                    {SUSPECT_REASONS.map(r => (
                      <option key={r} value={r}>{r || 'Selecionar motivo...'}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs text-gray-500 uppercase mb-2">Notas</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="Observações, inteligência recolhida..."
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-cyan-400 h-24 resize-none"
                />
              </div>

              <button
                onClick={handleSave}
                disabled={saving}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-cyan-600 text-black font-bold uppercase tracking-wider hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {saving ? 'A guardar...' : '💾 Guardar Classificação'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}