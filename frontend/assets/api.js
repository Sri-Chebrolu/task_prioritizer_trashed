const DEFAULT_PROTOCOL = window.location.protocol.startsWith('http') ? window.location.protocol : 'http:';
const DEFAULT_HOST = window.location.hostname || 'localhost';
const DEFAULT_PORT = 8000;
const FALLBACK_BASE = `${DEFAULT_PROTOCOL}//${DEFAULT_HOST || 'localhost'}:${DEFAULT_PORT}/api`;

const API_BASE = (window.__PRIORITY_API_BASE__ && window.__PRIORITY_API_BASE__.replace(/\/$/, '')) || FALLBACK_BASE;

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = options.headers || {};
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  try {
    const response = await fetch(url, {
      credentials: 'include',
      ...options,
      headers,
    });
    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `Request failed with status ${response.status}`);
    }
    const text = await response.text();
    return text ? JSON.parse(text) : null;
  } catch (error) {
    throw error instanceof Error ? error : new Error(String(error));
  }
}

export async function fetchTasks() {
  try {
    const data = await request('/tasks');
    return Array.isArray(data) ? data : null;
  } catch (error) {
    console.warn('[PriorityOS] Backend unavailable, using local seed data.', error.message || error);
    return null;
  }
}

export async function createTask(payload) {
  return request('/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateTask(id, payload) {
  return request(`/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function autoScheduleTask(id, params = {}) {
  const search = new URLSearchParams();
  if (params.minutes) {
    search.set('minutes', String(params.minutes));
  }
  const suffix = search.toString() ? `?${search.toString()}` : '';
  return request(`/tasks/${id}/auto_schedule${suffix}`, {
    method: 'POST',
  });
}
