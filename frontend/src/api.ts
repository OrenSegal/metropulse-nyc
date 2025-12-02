import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 15000,
});

export interface TimeDNA {
  morning: number;
  lunch: number;
  evening: number;
  night: number;
}

export interface Metrics {
  weekend_vitality: number;
  residential_type: string;
  retail_gap: number;
  borough: string;
}

export interface IntelligentStation {
  STATION: string;
  cluster_id: number;
  lat: number;
  lon: number;
  n_bars: number;
  n_offices: number;
  n_universities: number;
  persona_name: string;
  time_dna: TimeDNA;
  metrics: Metrics;
}

export const fetchStations = async (): Promise<IntelligentStation[]> => {
  const { data } = await api.get('/intelligence/stations');
  return data;
};

export const fetchClusterInfo = async () => {
  const { data } = await api.get('/intelligence/clusters');
  return data;
};

export const fetchStationAnalysis = async (stationName: string): Promise<{ persona: string, description: string, is_ai_generated?: boolean }> => {
  const { data } = await api.get(`/intelligence/narrative/${stationName}`);
  return data;
};