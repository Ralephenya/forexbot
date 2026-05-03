/**
 * API client for ForexBot backend
 *
 * In Settings, enter your EC2 public IP: http://54.x.x.x:8000
 * (or your computer's local IP for local testing: http://192.168.1.x:8000)
 */
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

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
  _baseURL = url.replace(/\/$/, '');
  await AsyncStorage.setItem(API_URL_KEY, _baseURL);
}

export function getApiUrl() {
  return _baseURL;
}

function client() {
  return axios.create({
    baseURL: _baseURL,
    timeout: 15000,
    headers: { 'Content-Type': 'application/json' },
  });
}

export const api = {
  // ---- Health & config ----
  health: () => client().get('/health'),

  // ---- Dashboard summary (SQLite) ----
  account: () => client().get('/account'),

  // ---- Live broker data (MetaAPI → XM) ----
  liveAccount: () => client().get('/live/account'),
  livePositions: () => client().get('/live/positions'),
  livePrice: (instrument) => client().get(`/live/price/${instrument}`),
  livePrices: (instruments = 'EURUSD,GBPUSD,USDJPY') =>
    client().get('/live/prices', { params: { instruments } }),

  // ---- Trade execution ----
  placeTrade: (body) => client().post('/live/trade', body),
  closeTrade: (positionId) => client().delete(`/live/trade/${positionId}`),

  // ---- Trade history (SQLite) ----
  trades: (params = {}) => client().get('/trades', { params }),
  openTrades: () => client().get('/trades/open'),
  trade: (id) => client().get(`/trades/${id}`),

  // ---- Charts ----
  dailyPnl: (days = 30) => client().get('/pnl/daily', { params: { days } }),

  // ---- Kill switch ----
  killSwitch: (state) => client().post(`/killswitch/${state}`),

  // ---- Instruments ----
  instruments: () => client().get('/instruments'),

  // ---- Strategy params (walk-forward optimized confluence settings) ----
  strategyParams: () => client().get('/strategy/params'),
};
