import { useState, useEffect, useCallback } from 'react';
import { getLiveVessels, updateVessel } from '../lib/api';

export function useVessels() {
  const [vessels, setVessels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchVessels = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getLiveVessels();
      setVessels(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    try {
      const data = await getLiveVessels();
      setVessels(data);
    } catch (err) {
      console.error('Refresh failed:', err);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchVessels();
  }, [fetchVessels]);

  return { vessels, loading, error, refresh, refetch: fetchVessels };
}

export function useVesselUpdate(mmsi) {
  const [current, setCurrent] = useState(null);
  const [updating, setUpdating] = useState(false);

  const saveClassification = useCallback(async (data) => {
    setUpdating(true);
    try {
      const result = await updateVessel(mmsi, data);
      setCurrent(result.vessel);
      return result;
    } finally {
      setUpdating(false);
    }
  }, [mmsi]);

  return { current, updating, saveClassification, setCurrent };
}