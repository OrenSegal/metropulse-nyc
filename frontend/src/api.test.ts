import { describe, it, expect, vi, beforeEach } from 'vitest';

const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }));

vi.mock('axios', () => ({
  default: {
    create: () => ({ get: mockGet }),
  },
}));

import { fetchStations, fetchClusterInfo, fetchStationAnalysis } from './api';

describe('api', () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it('fetchStations requests the stations endpoint and returns the payload', async () => {
    const stations = [
      { STATION: 'Union Sq', cluster_id: 1, lat: 40.7, lon: -73.99 },
    ];
    mockGet.mockResolvedValueOnce({ data: stations });

    const result = await fetchStations();

    expect(mockGet).toHaveBeenCalledWith('/intelligence/stations');
    expect(result).toEqual(stations);
  });

  it('fetchClusterInfo requests the clusters endpoint', async () => {
    mockGet.mockResolvedValueOnce({ data: { clusters: [] } });

    const result = await fetchClusterInfo();

    expect(mockGet).toHaveBeenCalledWith('/intelligence/clusters');
    expect(result).toEqual({ clusters: [] });
  });

  it('fetchStationAnalysis requests the narrative endpoint for a specific station', async () => {
    const payload = { persona: 'Night Owl', description: 'Busy after dark', is_ai_generated: true };
    mockGet.mockResolvedValueOnce({ data: payload });

    const result = await fetchStationAnalysis('Union Sq');

    expect(mockGet).toHaveBeenCalledWith('/intelligence/narrative/Union Sq');
    expect(result).toEqual(payload);
  });
});
