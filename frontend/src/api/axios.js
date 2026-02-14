import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '/v1';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

const DEVICE_TOKEN_KEY = 'crisis_mutual_aid_device_token';

export function getDeviceToken() {
  return localStorage.getItem(DEVICE_TOKEN_KEY);
}

export function setDeviceToken(token) {
  localStorage.setItem(DEVICE_TOKEN_KEY, token);
}

api.interceptors.request.use((config) => {
  const token = getDeviceToken();
  if (token) {
    config.headers['X-Device-Token'] = token;
  }
  return config;
});

export default api;
