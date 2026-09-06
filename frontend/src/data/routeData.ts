/**
 * Pre-configured route waypoints and transit schedule for RouteSense
 */

export const ROUTE_17_WAYPOINTS: [number, number][] = [
  [28.6139, 77.2091],
  [28.6150, 77.2105],
  [28.6170, 77.2138],
  [28.6190, 77.2165],
  [28.6215, 77.2195],
  [28.6240, 77.2225],
  [28.6275, 77.2255],
  [28.6310, 77.2285],
  [28.6345, 77.2315],
  [28.6380, 77.2345],
  [28.6420, 77.2375],
  [28.6455, 77.2405],
]

export const ROUTE_17_STOPS = [
  { name: 'Central Station', time: '09:30 AM', passed: true },
  { name: 'City Hospital', time: '10:15 AM', passed: true },
  { name: 'Main Market', time: '10:50 AM', current: true },
  { name: 'Tech Park', time: '11:05 AM', passed: false },
  { name: 'Railway Station', time: '11:20 AM', passed: false },
]

export const FLEET_DETAILS_MOCK: Record<string, { route: string; speed: number; eta: number; dist: string; next: string; pass: string }> = {
  bus_1: { route: 'Route 17: Central → Railway Station', speed: 28, eta: 8, dist: '32.4 km', next: 'Main Market 0.8 km', pass: '24/40' },
  bus_2: { route: 'Route 04: South Ext → Connaught Place', speed: 34, eta: 14, dist: '18.2 km', next: 'Defense Colony 1.2 km', pass: '31/40' },
  bus_3: { route: 'Route 22: Rohini → Kashmiri Gate', speed: 22, eta: 6, dist: '24.8 km', next: 'Pitampura 0.5 km', pass: '38/40' },
  bus_4: { route: 'Route 11: Dwarka → Airport T3', speed: 45, eta: 18, dist: '15.6 km', next: 'Aero City 2.1 km', pass: '19/40' },
  bus_5: { route: 'Route 09: Noida Sec 18 → ITO', speed: 0, eta: 0, dist: '29.0 km', next: 'Depot (Offline)', pass: '0/40' },
}
