import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useCognitiveState = (sessionId) => {
  const [cognitiveState, setCognitiveState] = useState(null);
  const [isTracking, setIsTracking] = useState(false);
  const [isCalibrated, setIsCalibrated] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const pollingRef = useRef(null);

  const startTracking = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/cognitive/start/${sessionId}`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to start tracking');
      setIsTracking(true);
    } catch (err) {
      setError(err.message);
    }
  }, [sessionId]);

  const stopTracking = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/cognitive/stop/${sessionId}`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to stop tracking');
      setIsTracking(false);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    } catch (err) {
      setError(err.message);
    }
  }, [sessionId]);

  const calibrate = useCallback(async (duration = 60) => {
    try {
      const response = await fetch(
        `${API_BASE}/cognitive/calibrate/${sessionId}?duration=${duration}`,
        { method: 'POST' }
      );
      if (!response.ok) throw new Error('Calibration failed');
      setIsCalibrated(true);
      return await response.json();
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [sessionId]);

  const fetchState = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/cognitive/state/${sessionId}`);
      if (!response.ok) return;
      const data = await response.json();
      setCognitiveState(data);
      if (data.is_calibrated) setIsCalibrated(true);
    } catch (err) {
      console.error('Failed to fetch cognitive state:', err);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!isTracking) return;

    const ws = new WebSocket(`${API_BASE}/ws/cognitive/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (!data.error) {
          setCognitiveState(data);
          if (data.is_calibrated) setIsCalibrated(true);
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onerror = (e) => {
      console.error('WebSocket error:', e);
      pollingRef.current = setInterval(fetchState, 1000);
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      pollingRef.current = setInterval(fetchState, 1000);
    };

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [isTracking, sessionId, fetchState]);

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  return {
    cognitiveState,
    isTracking,
    isCalibrated,
    error,
    startTracking,
    stopTracking,
    calibrate,
  };
};

export default useCognitiveState;
