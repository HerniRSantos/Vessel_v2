const API_BASE = '/api';

async function fetchWithAuth(url) {
  const res = await fetch(url, {
    credentials: 'include',
  });
  if (!res.ok) {
    if (res.status === 401) {
      throw new Error('Unauthorized');
    }
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export async function getVessels() {
  return fetchWithAuth(`${API_BASE}/vessels`);
}

export async function getLiveVessels() {
  return fetchWithAuth(`${API_BASE}/vessels/live`);
}

export async function getVessel(mmsi) {
  return fetchWithAuth(`${API_BASE}/vessel/${mmsi}`);
}

export async function updateVessel(mmsi, data) {
  const res = await fetch(`${API_BASE}/vessel/${mmsi}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error('Failed to update vessel');
  }
  return res.json();
}

export async function getVesselHistory(mmsi, hours = 24) {
  return fetchWithAuth(`${API_BASE}/vessel/${mmsi}/history?hours=${hours}`);
}

export async function getVesselTrail(mmsi) {
  return fetchWithAuth(`${API_BASE}/vessels/trail/${mmsi}`);
}

export async function exportVessels() {
  const res = await fetch(`${API_BASE}/vessels/export`, {
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Export failed');
  return res.blob();
}