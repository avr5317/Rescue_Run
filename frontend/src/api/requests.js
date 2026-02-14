import api from './axios';

export function fetchRequests({ bbox, status = null, sort = 'rank', limit = 200 }) {
  const params = new URLSearchParams();
  if (bbox) params.set('bbox', bbox);
  if (status) params.set('status', status);
  params.set('sort', sort);
  params.set('limit', limit);
  return api.get(`/requests?${params}`).then((r) => r.data);
}

export function fetchRequestDetail(id) {
  return api.get(`/requests/${id}`).then((r) => r.data);
}

export function createRequest(payload) {
  return api.post('/requests', payload).then((r) => r.data);
}

export function donateToRequest(id, amount) {
  return api.post(`/requests/${id}/donate`, { amount }).then((r) => r.data);
}

export function claimRequest(id) {
  return api.post(`/requests/${id}/claim`).then((r) => r.data);
}

export function invokeAI({ text, location, requester_afford = 0 }) {
  return api.post('/ai/invoke', { text, location, requester_afford }).then((r) => r.data);
}

export function findShops(id, lat, lng) {
  return api.post(`/requests/${id}/find-shops`, { lat, lng }).then((r) => r.data);
}

export function updateRequestStatus(id, status) {
  return api.patch(`/requests/${id}/status`, { status }).then((r) => r.data);
}
