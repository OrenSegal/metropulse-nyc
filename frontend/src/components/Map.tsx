import { useMemo } from 'react';
import Map, { Source, Layer } from 'react-map-gl/maplibre';
import type { MapLayerMouseEvent } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { IntelligentStation } from '../api';

const MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

interface Props {
  stations: IntelligentStation[];
  mode: 'general' | 'lifestyle' | 'retail';
  onSelect: (s: IntelligentStation | null) => void;
  selectedName: string | null;
}

export default function StationMap({ stations, mode, onSelect, selectedName }: Props) {

  const geoJson = useMemo(() => ({
    type: 'FeatureCollection',
    features: stations.map(s => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [s.lon, s.lat] },
      properties: { ...s, ...s.metrics } 
    }))
  }), [stations]);

  const getCircleColor = () => {
    // 1. Retail Scout: Market Gap Analysis (Green = High Opportunity)
    if (mode === 'retail') {
      return [
        'interpolate', ['linear'], ['get', 'retail_gap'],
        0, '#4b5563',      // Gray (Saturated/Low Demand)
        0.5, '#f59e0b',    // Orange (Moderate)
        0.8, '#10b981',    // Green (High Opportunity)
        1, '#34d399'       // Bright Green (Prime)
      ];
    }
    
    // 2. Lifestyle: Vitality Heatmap (Purple = Nightlife, Blue = Quiet)
    if (mode === 'lifestyle') {
      return [
        'interpolate', ['linear'], ['get', 'weekend_vitality'],
        0, '#1e293b',      // Dark Slate (Residential)
        0.3, '#3b82f6',    // Blue (Quiet/Local)
        0.6, '#a855f7',    // Purple (Active)
        0.9, '#f472b6',    // Pink (High Energy)
        1, '#facc15'       // Yellow (Hotspot)
      ];
    }
    
    // 3. General: Cluster Archetypes
    return [
      'match', ['get', 'cluster_id'],
      0, '#a855f7',   // Night Owls
      1, '#3b82f6',   // Commuters
      2, '#eab308',   // Students
      3, '#ef4444',   // Tourists
      4, '#22c55e',   // Locals
      '#6b7280'
    ];
  };

  return (
    <Map
      initialViewState={{ longitude: -73.95, latitude: 40.72, zoom: 12 }}
      style={{ width: '100%', height: '100%' }}
      mapStyle={MAP_STYLE}
      interactiveLayerIds={['stations']}
      onClick={(e: MapLayerMouseEvent) => {
        const feature = e.features?.[0];
        if (feature) {
          const stationName = feature.properties?.STATION;
          const originalStation = stations.find(s => s.STATION === stationName);
          if (originalStation) {
            onSelect(originalStation);
          }
        }
      }}
    >
      <Source type="geojson" data={geoJson as any}>
        <Layer
          id="stations"
          type="circle"
          paint={{
            'circle-radius': ['interpolate', ['linear'], ['zoom'], 11, 3, 15, 8],
            'circle-color': getCircleColor() as any,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#000',
            'circle-opacity': 0.9
          }}
        />
        {selectedName && (
          <Layer
            id="highlight"
            type="circle"
            paint={{
              'circle-radius': 12,
              'circle-color': 'transparent',
              'circle-stroke-width': 3,
              'circle-stroke-color': '#fff'
            }}
            filter={['==', 'STATION', selectedName]}
          />
        )}
      </Source>
    </Map>
  );
}