import api, { setDeviceToken, getDeviceToken } from './axios';

export async function ensureDeviceToken() {
  let token = getDeviceToken();
  if (token) return token;
  const { data } = await api.post('/device');
  token = data.device_token;
  setDeviceToken(token);
  return token;
}
