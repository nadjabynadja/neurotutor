const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

const handleResponse = async (response) => {
  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    throw new ApiError(
      data?.detail || `HTTP error ${response.status}`,
      response.status,
      data
    );
  }
  return response.json();
};

const api = {
  async get(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    return handleResponse(response);
  },

  async post(endpoint, body, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(body),
      ...options,
    });
    return handleResponse(response);
  },

  async put(endpoint, body, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(body),
      ...options,
    });
    return handleResponse(response);
  },

  async patch(endpoint, body, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: JSON.stringify(body),
      ...options,
    });
    return handleResponse(response);
  },

  async delete(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    return handleResponse(response);
  },
};

export const cognitive = {
  start: (sessionId) => api.post(`/cognitive/start/${sessionId}`),
  stop: (sessionId) => api.post(`/cognitive/stop/${sessionId}`),
  getState: (sessionId) => api.get(`/cognitive/state/${sessionId}`),
  calibrate: (sessionId, duration) => 
    api.post(`/cognitive/calibrate/${sessionId}?duration=${duration}`),
};

export const directives = {
  analyze: (state) => api.post('/directive/analyze', state),
};

export const chat = {
  send: (message, cognitiveState, context) => 
    api.post('/chat', { message, cognitive_state: cognitiveState, context }),
};

export const courses = {
  list: () => api.get('/courses'),
  get: (courseId) => api.get(`/courses/${courseId}`),
  create: (course) => api.post('/courses', course),
  getAnalytics: (courseId) => api.get(`/courses/${courseId}/analytics`),
};

export default api;
