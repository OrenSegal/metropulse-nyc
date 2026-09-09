import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { IntelligentStation } from './api';
import App from './App';

vi.mock('./api', () => ({
  fetchStations: vi.fn(),
}));

vi.mock('./components/Map', () => ({
  default: ({ stations }: { stations: IntelligentStation[] }) => (
    <div data-testid="station-map">
      {stations.map(s => (
        <div key={s.STATION} data-testid="map-station">{s.STATION}</div>
      ))}
    </div>
  ),
}));

const makeStation = (overrides: Partial<IntelligentStation>): IntelligentStation => ({
  STATION: 'Union Sq',
  cluster_id: 0,
  lat: 40.735,
  lon: -73.99,
  n_bars: 5,
  n_offices: 10,
  n_universities: 1,
  persona_name: 'Commuter Hub',
  time_dna: { morning: 0.8, lunch: 0.5, evening: 0.6, night: 0.2 },
  metrics: { weekend_vitality: 0.4, residential_type: 'mixed', retail_gap: 0.3, borough: 'Manhattan' },
  ...overrides,
});

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  );
}

describe('App', () => {
  it('shows a loading state before stations arrive', async () => {
    const { fetchStations } = await import('./api');
    vi.mocked(fetchStations).mockReturnValue(new Promise(() => {}));

    renderApp();

    expect(screen.getByText(/LOADING DATA STREAM/i)).toBeInTheDocument();
  });

  it('renders every fetched station on the map once loading finishes', async () => {
    const { fetchStations } = await import('./api');
    vi.mocked(fetchStations).mockResolvedValue([
      makeStation({ STATION: 'Union Sq' }),
      makeStation({ STATION: 'Bedford Ave' }),
    ]);

    renderApp();

    await waitFor(() => expect(screen.getAllByTestId('map-station')).toHaveLength(2));
    expect(screen.getByText('Union Sq')).toBeInTheDocument();
    expect(screen.getByText('Bedford Ave')).toBeInTheDocument();
  });

  it('filters stations passed to the map as the user types in the search box', async () => {
    const { fetchStations } = await import('./api');
    vi.mocked(fetchStations).mockResolvedValue([
      makeStation({ STATION: 'Union Sq' }),
      makeStation({ STATION: 'Bedford Ave' }),
    ]);

    renderApp();
    await waitFor(() => expect(screen.getAllByTestId('map-station')).toHaveLength(2));

    const user = userEvent.setup();
    await user.type(screen.getByPlaceholderText('Search Station...'), 'union');

    await waitFor(() => expect(screen.getAllByTestId('map-station')).toHaveLength(1));
    expect(screen.getByText('Union Sq')).toBeInTheDocument();
    expect(screen.queryByText('Bedford Ave')).not.toBeInTheDocument();
  });
});
