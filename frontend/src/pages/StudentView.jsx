import React, { useState, useEffect, useRef } from 'react';

const NeuroTutor = () => {
  const [sessionId] = useState(`session_${Date.now()}`);
  const [cognitiveState, setCognitiveState] = useState(null);
  const [directives, setDirectives] = useState([]);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isCalibrated, setIsCalibrated] = useState(false);
  const wsRef = useRef(null);

  // Connect to WebSocket for real-time cognitive state
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/cognitive/${sessionId}`);
    
    ws.onopen = () => {
      setIsConnected(true);
      // Start cognitive tracking
      fetch(`http://localhost:8000/cognitive/start/${sessionId}`, { method: 'POST' });
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (!data.error) {
        setCognitiveState(data);
      }
    };
    
    ws.onclose = () => setIsConnected(false);
    wsRef.current = ws;
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      fetch(`http://localhost:8000/cognitive/stop/${sessionId}`, { method: 'POST' });
    };
  }, [sessionId]);

  const handleCalibrate = async () => {
    await fetch(`http://localhost:8000/cognitive/calibrate/${sessionId}`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    setIsCalibrated(true);
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;
    
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        cognitive_state: cognitiveState ? {
          cognitive_load: cognitiveState.cognitive_load,
          attention_level: cognitiveState.attention_level,
          engagement: cognitiveState.engagement,
          confusion_indicator: cognitiveState.confusion_indicator,
          fatigue_indicator: cognitiveState.fatigue_indicator
        } : null
      })
    });
    
    const data = await response.json();
    setChatHistory([...chatHistory, { role: 'user', content: message }]);
    setChatHistory(prev => [...prev, { role: 'assistant', content: data.response }]);
    setDirectives(data.directives);
    setMessage('');
  };

  const getStatusColor = (value) => {
    if (value >= 0.7) return '#4caf50'; // Good
    if (value >= 0.4) return '#ff9800'; // Warning
    return '#f44336'; // Poor
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1>🧠 NeuroTutor</h1>
        <span style={styles.status}>
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </span>
      </header>

      <div style={styles.main}>
        {/* Cognitive State Panel */}
        <div style={styles.panel}>
          <h2>Your Cognitive State</h2>
          
          {!isCalibrated && (
            <button style={styles.calibrateBtn} onClick={handleCalibrate}>
              🎯 Calibrate (60s)
            </button>
          )}
          
          {cognitiveState && (
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
              />
            </div>
          )}
          
          {directives.length > 0 && (
            <div style={styles.directives}>
              <h3>Active Adaptations:</h3>
              <div style={styles.directiveTags}>
                {directives.map((d, i) => (
                  <span key={i} style={styles.directiveTag}>{d}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Chat Panel */}
        <div style={styles.chatPanel}>
          <div style={styles.chatHistory}>
            {chatHistory.map((msg, i) => (
              <div 
                key={i} 
                style={{
                  ...styles.message,
                  ...(msg.role === 'user' ? styles.userMessage : styles.assistantMessage)
                }}
              >
                {msg.content}
              </div>
            ))}
          </div>
          
          <div style={styles.inputArea}>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Ask a question..."
              style={styles.input}
            />
            <button onClick={handleSendMessage} style={styles.sendBtn}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricBar = ({ label, value, color }) => (
  <div style={styles.metric}>
    <div style={styles.metricHeader}>
      <span>{label}</span>
      <span>{(value * 100).toFixed(0)}%</span>
    </div>
    <div style={styles.metricBar}>
      <div 
        style={{
          ...styles.metricFill,
          width: `${value * 100}%`,
          backgroundColor: color
        }} 
      />
    </div>
  </div>
);

const styles = {
  container: {
    fontFamily: 'system-ui, sans-serif',
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '20px',
    backgroundColor: '#f5f5f5',
    minHeight: '100vh'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    padding: '20px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  status: {
    fontSize: '14px'
  },
  main: {
    display: 'grid',
    gridTemplateColumns: '300px 1fr',
    gap: '20px'
  },
  panel: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '12px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  calibrateBtn: {
    width: '100%',
    padding: '12px',
    backgroundColor: '#2196f3',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '16px',
    marginBottom: '20px'
  },
  metrics: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px'
  },
  metric: {
    marginBottom: '10px'
  },
  metricHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '5px',
    fontSize: '14px',
    fontWeight: '500'
  },
  metricBar: {
    height: '8px',
    backgroundColor: '#e0e0e0',
    borderRadius: '4px',
    overflow: 'hidden'
  },
  metricFill: {
    height: '100%',
    borderRadius: '4px',
    transition: 'width 0.3s ease'
  },
  directives: {
    marginTop: '20px',
    paddingTop: '20px',
    borderTop: '1px solid #eee'
  },
  directiveTags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginTop: '10px'
  },
  directiveTag: {
    padding: '4px 12px',
    backgroundColor: '#e3f2fd',
    color: '#1976d2',
    borderRadius: '16px',
    fontSize: '12px'
  },
  chatPanel: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    flexDirection: 'column',
    height: '500px'
  },
  chatHistory: {
    flex: 1,
    padding: '20px',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px'
  },
  message: {
    padding: '12px 16px',
    borderRadius: '12px',
    maxWidth: '80%'
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#2196f3',
    color: 'white'
  },
  assistantMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#f5f5f5',
    color: '#333'
  },
  inputArea: {
    display: 'flex',
    padding: '20px',
    borderTop: '1px solid #eee',
    gap: '10px'
  },
  input: {
    flex: 1,
    padding: '12px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '16px'
  },
  sendBtn: {
    padding: '12px 24px',
    backgroundColor: '#4caf50',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '16px'
  }
};

export default NeuroTutor;
