import React, { useState, useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE = API_BASE.replace(/^http/, 'ws');

const NeuroTutor = () => {
  const [sessionId] = useState(`session_${Date.now()}`);
  const [cognitiveState, setCognitiveState] = useState(null);
  const [directives, setDirectives] = useState([]);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isCalibrated, setIsCalibrated] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const wsRef = useRef(null);
  const chatEndRef = useRef(null);

  // Auto-scroll to newest message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // Connect to WebSocket for real-time cognitive state
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/cognitive/${sessionId}`);

    ws.onopen = () => {
      setIsConnected(true);
      setConnectionError(false);
      fetch(`${API_BASE}/cognitive/start/${sessionId}`, { method: 'POST' })
        .catch(() => {}); // Non-critical — WS already started tracking
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (!data.error && data.attention_level !== undefined) {
          setCognitiveState(data);
        }
      } catch (e) {
        // Ignore parse errors
      }
    };

    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => {
      setIsConnected(false);
      setConnectionError(true);
    };

    wsRef.current = ws;

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      fetch(`${API_BASE}/cognitive/stop/${sessionId}`, { method: 'POST' })
        .catch(() => {});
    };
  }, [sessionId]);

  const handleCalibrate = async () => {
    try {
      await fetch(`${API_BASE}/cognitive/calibrate/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      setIsCalibrated(true);
    } catch (e) {
      // Still mark calibrated — simulator doesn't need it
      setIsCalibrated(true);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim() || isSending) return;

    const userMessage = message;
    setMessage('');
    setIsSending(true);

    // Optimistically add user message
    setChatHistory(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          cognitive_state: cognitiveState
            ? {
                cognitive_load: cognitiveState.cognitive_load,
                attention_level: cognitiveState.attention_level,
                engagement: cognitiveState.engagement,
                confusion_indicator: cognitiveState.confusion_indicator,
                fatigue_indicator: cognitiveState.fatigue_indicator,
              }
            : null,
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      setChatHistory(prev => [...prev, { role: 'assistant', content: data.response }]);
      if (data.directives?.length) {
        setDirectives(data.directives);
      }
    } catch (e) {
      setChatHistory(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I could not reach the backend. Make sure the server is running on port 8000.',
          isError: true,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getStatusColor = (value) => {
    if (value >= 0.7) return '#4caf50';
    if (value >= 0.4) return '#ff9800';
    return '#f44336';
  };

  const DIRECTIVE_LABELS = {
    simplify: 'Simplifying',
    elaborate: 'Elaborating',
    slow_down: 'Slowing Down',
    speed_up: 'Speeding Up',
    encourage: 'Encouraging',
    break: 'Suggesting Break',
    summarize: 'Summarizing',
    interactive: 'Interactive Mode',
    example: 'Adding Examples',
    analogy: 'Using Analogies',
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>NeuroTutor</h1>
          <span style={styles.subtitle}>Adaptive AI Tutoring</span>
        </div>
        <div style={styles.headerRight}>
          <span style={{
            ...styles.status,
            color: isConnected ? '#4caf50' : connectionError ? '#f44336' : '#ff9800',
          }}>
            {isConnected ? '● Connected' : connectionError ? '● Connection Error' : '● Connecting...'}
          </span>
          <a href="/professor" style={styles.profLink}>Professor View →</a>
        </div>
      </header>

      <div style={styles.main}>
        {/* Cognitive State Panel */}
        <div style={styles.panel}>
          <h2 style={styles.panelTitle}>Cognitive State</h2>

          {!isCalibrated && (
            <button style={styles.calibrateBtn} onClick={handleCalibrate}>
              Calibrate Baseline
            </button>
          )}
          {isCalibrated && (
            <div style={styles.calibratedBadge}>✓ Calibrated</div>
          )}

          {cognitiveState ? (
            <div style={styles.metrics}>
              <MetricBar
                label="Attention"
                value={cognitiveState.attention_level}
                color={getStatusColor(cognitiveState.attention_level)}
              />
              <MetricBar
                label="Cognitive Load"
                value={cognitiveState.cognitive_load}
                color={getStatusColor(1 - cognitiveState.cognitive_load)}
                invertLabel
              />
              <MetricBar
                label="Engagement"
                value={cognitiveState.engagement}
                color={getStatusColor(cognitiveState.engagement)}
              />
              <MetricBar
                label="Fatigue"
                value={cognitiveState.fatigue_indicator}
                color={getStatusColor(1 - cognitiveState.fatigue_indicator)}
                invertLabel
              />
            </div>
          ) : (
            <div style={styles.metricsPlaceholder}>
              <p>Waiting for cognitive data...</p>
              <p style={styles.metricsHint}>
                {isConnected
                  ? 'Simulator running — metrics will appear shortly.'
                  : 'Connect to backend to see real-time cognitive state.'}
              </p>
            </div>
          )}

          {directives.length > 0 && (
            <div style={styles.directives}>
              <h3 style={styles.directivesTitle}>Active Adaptations</h3>
              <div style={styles.directiveTags}>
                {directives.map((d, i) => (
                  <span key={i} style={styles.directiveTag}>
                    {DIRECTIVE_LABELS[d] || d}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div style={styles.modeIndicator}>
            Simulator Mode — no camera required
          </div>
        </div>

        {/* Chat Panel */}
        <div style={styles.chatPanel}>
          <div style={styles.chatHistory}>
            {chatHistory.length === 0 && (
              <div style={styles.emptyState}>
                <div style={styles.emptyIcon}>🧠</div>
                <p style={styles.emptyTitle}>Welcome to NeuroTutor</p>
                <p style={styles.emptyText}>
                  I adapt my teaching style in real-time based on your cognitive state.
                  Ask me anything to get started!
                </p>
                <div style={styles.suggestions}>
                  {[
                    'Explain recursion with an example',
                    'What is machine learning?',
                    'How do neural networks work?',
                  ].map((s) => (
                    <button
                      key={s}
                      style={styles.suggestionBtn}
                      onClick={() => { setMessage(s); }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {chatHistory.map((msg, i) => (
              <div
                key={i}
                style={{
                  ...styles.message,
                  ...(msg.role === 'user' ? styles.userMessage : styles.assistantMessage),
                }}
              >
                {msg.role === 'assistant' && (
                  <div style={styles.messageLabel}>NeuroTutor</div>
                )}
                <div style={{
                  ...styles.messageContent,
                  backgroundColor: msg.role === 'user' ? '#2196f3' : msg.isError ? '#fff3f3' : '#f5f5f5',
                  color: msg.role === 'user' ? 'white' : msg.isError ? '#c62828' : '#333',
                }}>
                  {msg.content}
                </div>
              </div>
            ))}

            {isSending && (
              <div style={{ ...styles.message, ...styles.assistantMessage }}>
                <div style={styles.messageLabel}>NeuroTutor</div>
                <div style={styles.typingIndicator}>
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          <div style={styles.inputArea}>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              style={{
                ...styles.input,
                opacity: isSending ? 0.7 : 1,
              }}
              disabled={isSending}
            />
            <button
              onClick={handleSendMessage}
              disabled={isSending || !message.trim()}
              style={{
                ...styles.sendBtn,
                opacity: (isSending || !message.trim()) ? 0.6 : 1,
                cursor: (isSending || !message.trim()) ? 'not-allowed' : 'pointer',
              }}
            >
              {isSending ? '...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricBar = ({ label, value, color, invertLabel = false }) => (
  <div style={styles.metric}>
    <div style={styles.metricHeader}>
      <span style={styles.metricLabel}>{label}</span>
      <span style={{ ...styles.metricValue, color }}>
        {(value * 100).toFixed(0)}%
      </span>
    </div>
    <div style={styles.metricBar}>
      <div
        style={{
          ...styles.metricFill,
          width: `${value * 100}%`,
          backgroundColor: color,
        }}
      />
    </div>
  </div>
);

const styles = {
  container: {
    fontFamily: 'system-ui, -apple-system, sans-serif',
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '20px',
    backgroundColor: '#f5f5f5',
    minHeight: '100vh',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    padding: '16px 24px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.08)',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '12px',
  },
  title: {
    fontSize: '22px',
    fontWeight: '700',
    color: '#1a1a1a',
    margin: 0,
  },
  subtitle: {
    fontSize: '13px',
    color: '#888',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
  },
  status: {
    fontSize: '13px',
    fontWeight: '500',
  },
  profLink: {
    fontSize: '13px',
    color: '#2196f3',
    textDecoration: 'none',
    fontWeight: '500',
  },
  main: {
    display: 'grid',
    gridTemplateColumns: '300px 1fr',
    gap: '20px',
    alignItems: 'start',
  },
  panel: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '12px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.08)',
  },
  panelTitle: {
    fontSize: '16px',
    fontWeight: '600',
    marginBottom: '16px',
    color: '#1a1a1a',
  },
  calibrateBtn: {
    width: '100%',
    padding: '10px',
    backgroundColor: '#2196f3',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    marginBottom: '16px',
    fontWeight: '500',
  },
  calibratedBadge: {
    display: 'inline-block',
    padding: '4px 12px',
    backgroundColor: '#e8f5e9',
    color: '#2e7d32',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '600',
    marginBottom: '16px',
  },
  metrics: {
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
  },
  metricsPlaceholder: {
    padding: '20px 0',
    color: '#999',
    fontSize: '14px',
    textAlign: 'center',
  },
  metricsHint: {
    marginTop: '8px',
    fontSize: '12px',
    lineHeight: '1.5',
  },
  metric: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  metricHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: '13px',
    fontWeight: '500',
    color: '#555',
  },
  metricValue: {
    fontSize: '13px',
    fontWeight: '700',
  },
  metricBar: {
    height: '8px',
    backgroundColor: '#eeeeee',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  metricFill: {
    height: '100%',
    borderRadius: '4px',
    transition: 'width 0.4s ease, background-color 0.4s ease',
  },
  directives: {
    marginTop: '20px',
    paddingTop: '16px',
    borderTop: '1px solid #f0f0f0',
  },
  directivesTitle: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: '10px',
  },
  directiveTags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  directiveTag: {
    padding: '4px 10px',
    backgroundColor: '#e3f2fd',
    color: '#1565c0',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: '500',
  },
  modeIndicator: {
    marginTop: '16px',
    paddingTop: '12px',
    borderTop: '1px solid #f0f0f0',
    fontSize: '11px',
    color: '#bbb',
    textAlign: 'center',
  },
  chatPanel: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.08)',
    display: 'flex',
    flexDirection: 'column',
    height: 'calc(100vh - 140px)',
    minHeight: '400px',
  },
  chatHistory: {
    flex: 1,
    padding: '20px',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    padding: '40px 20px',
    textAlign: 'center',
    color: '#888',
  },
  emptyIcon: {
    fontSize: '52px',
    marginBottom: '16px',
  },
  emptyTitle: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#444',
    marginBottom: '8px',
  },
  emptyText: {
    fontSize: '14px',
    lineHeight: '1.6',
    maxWidth: '340px',
    marginBottom: '24px',
  },
  suggestions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    width: '100%',
    maxWidth: '380px',
  },
  suggestionBtn: {
    padding: '10px 16px',
    backgroundColor: '#f5f5f5',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    color: '#444',
    textAlign: 'left',
    transition: 'background-color 0.15s',
  },
  message: {
    maxWidth: '80%',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  userMessage: {
    alignSelf: 'flex-end',
  },
  assistantMessage: {
    alignSelf: 'flex-start',
  },
  errorMessage: {
    opacity: 0.7,
  },
  messageLabel: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#888',
    paddingLeft: '4px',
  },
  messageContent: {
    padding: '12px 16px',
    borderRadius: '12px',
    fontSize: '14px',
    lineHeight: '1.6',
    whiteSpace: 'pre-wrap',
  },
  typingIndicator: {
    display: 'flex',
    gap: '4px',
    padding: '12px 16px',
    backgroundColor: '#f5f5f5',
    borderRadius: '12px',
    alignItems: 'center',
  },
  inputArea: {
    display: 'flex',
    padding: '16px 20px',
    borderTop: '1px solid #f0f0f0',
    gap: '10px',
  },
  input: {
    flex: 1,
    padding: '12px 16px',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  sendBtn: {
    padding: '12px 24px',
    backgroundColor: '#2196f3',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '600',
    minWidth: '72px',
  },
};

export default NeuroTutor;
