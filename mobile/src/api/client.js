/**
 * API client for ForexBot backend
 * Change API_BASE_URL to your computer's local IP address
 * e.g. http://192.168.1.100:8000
 *
 * To find your IP: run `ipconfig` on Windows or `ifconfig` on Mac/Linux
 */
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Default URL — user changes this in Settings screen
const DEFAULT_API_URL = 'http://192.168.1.100:8000';
const API_URL_KEY = '@forexbot_api_url';

let _baseURL = DEFAULT_API_URL;

export async function loadApiUrl() {
  try {
    const saved = await AsyncStorage.getItem(API_URL_KEY);
    if (saved) _baseURL = saved;
  } catch (_) {}
  return _baseURL;
}

export async function saveApiUrl(url) {
  _baseURL = url.replace(/\/$/, ''); // strip trailing slash
  await AsyncStorage.setItem(API_URL_KEY, _baseURL);
}

export function getApiUrl() {
  return _baseURL;
}

function client() {
  return axios.create({
    baseURL: _baseURL,
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
  });
}

export const api = {
  /** Health check — used to test connectivity */
  health: () => client().get('/health'),

  /** Dashboard summary */
  account: () => client().get('/account'),

  /** All trades with optional filters */
  trades: (params = {}) => client().get('/trades', { params }),

  /** Open trades only */
  openTrades: () => client().get('/trades/open'),

  /** Single trade detail */
  trade: (id) => client().get(`/trades/${id}`),

  /** Daily P&L chart data */
  dailyPnl: (days = 30) => client().get('/pnl/daily', { params: { days } }),

  /** Instruments list */
  instruments: () => client().get('/instruments'),

  /** Kill switch — state is 'on' or 'off' */
  killSwitch: (state) => client().post(`/killswitch/${state}`),
};
