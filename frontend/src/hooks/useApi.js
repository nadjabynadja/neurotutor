import { useState, useEffect, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useApi = (endpoint, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setData(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint, options]);

  return { data, loading, error, refetch: fetchData };
};

export const usePost = (endpoint) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const post = useCallback(async (body) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  return { post, loading, error };
};

export const useWebSocket = (url) => {
  const [socket, setSocket] = useState(null);
  const [message, setMessage] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(`${API_BASE}${url}`);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = (e) => setError(e);
    ws.onmessage = (e) => {
      try {
        setMessage(JSON.parse(e.data));
      } catch {
        setMessage(e.data);
      }
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [url]);

  const send = useCallback((data) => {
    if (socket && connected) {
      socket.send(JSON.stringify(data));
    }
  }, [socket, connected]);

  return { socket, message, connected, error, send };
};

export default useApi;
