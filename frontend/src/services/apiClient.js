// Centralized API Client Abstraction for Smart Bhopal
// Supports switching between persistent Mock Services and real REST API endpoints
import { supabase } from './supabaseClient';

export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = {
  async get(endpoint, params = {}) {
    if (USE_MOCK) {
      console.log(`[API Client - Mock GET]: ${endpoint}`, params);
      return { success: true, endpoint, params };
    }
    const query = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}${endpoint}${query ? `?${query}` : ''}`;
    const res = await fetch(url, { headers: await getHeaders() });
    if (!res.ok) handleApiError(res);
    return res.json();
  },

  async post(endpoint, body) {
    if (USE_MOCK) {
      console.log(`[API Client - Mock POST]: ${endpoint}`, body);
      return { success: true, endpoint, data: body };
    }
    const url = `${API_BASE_URL}${endpoint}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: await getHeaders(),
      body: JSON.stringify(body),
    });
    if (!res.ok) handleApiError(res);
    return res.json();
  },

  async put(endpoint, body) {
    if (USE_MOCK) {
      console.log(`[API Client - Mock PUT]: ${endpoint}`, body);
      return { success: true, endpoint, data: body };
    }
    const url = `${API_BASE_URL}${endpoint}`;
    const res = await fetch(url, {
      method: 'PUT',
      headers: await getHeaders(),
      body: JSON.stringify(body),
    });
    if (!res.ok) handleApiError(res);
    return res.json();
  },

  async patch(endpoint, body) {
    const url = `${API_BASE_URL}${endpoint}`;
    const res = await fetch(url, {
      method: 'PATCH',
      headers: await getHeaders(),
      body: JSON.stringify(body),
    });
    if (!res.ok) handleApiError(res);
    return res.json();
  },
};

async function getHeaders() {
  const { data } = supabase ? await supabase.auth.getSession() : { data: {} };
  const token = data.session?.access_token || localStorage.getItem('smart_bhopal_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function handleApiError(response) {
  if (response.status === 401) {
    window.location.href = '/login?expired=true';
    throw new Error('Session expired. Please log in again.');
  }
  if (response.status === 403) {
    throw new Error('Access denied. You do not have permission.');
  }
  throw new Error(`API Error ${response.status}: ${response.statusText}`);
}
