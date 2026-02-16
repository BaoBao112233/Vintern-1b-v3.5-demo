import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8001/ws';

function App() {
  const [connected, setConnected] = useState(false);
  const [cameras, setCameras] = useState([]);
  const [results, setResults] = useState({});
  const [stats, setStats] = useState({});
  const [error, setError] = useState(null);

  // WebSocket connection
  useEffect(() => {
    let ws;
    let reconnectTimeout;

    const connect = () => {
      try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
          console.log('✅ WebSocket connected');
          setConnected(true);
          setError(null);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'update') {
              setResults(data.results || {});
              setStats(data.stats || {});
            } else if (data.type === 'status') {
              setStats(data.data || {});
            }
          } catch (err) {
            console.error('Failed to parse message:', err);
          }
        };

        ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          setError('WebSocket connection error');
        };

        ws.onclose = () => {
          console.log('🔌 WebSocket disconnected');
          setConnected(false);
          
          // Reconnect after 3 seconds
          reconnectTimeout = setTimeout(() => {
            console.log('🔄 Reconnecting...');
            connect();
          }, 3000);
        };
      } catch (err) {
        console.error('Failed to connect:', err);
        setError(err.message);
      }
    };

    connect();

    // Cleanup
    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) {
        ws.close();
      }
    };
  }, []);

  // Fetch cameras info
  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const response = await fetch(`${API_URL}/cameras`);
        const data = await response.json();
        setCameras(data.cameras || []);
      } catch (err) {
        console.error('Failed to fetch cameras:', err);
      }
    };

    fetchCameras();
    const interval = setInterval(fetchCameras, 10000); // Refresh every 10s

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
      {/* Header */}
      <header className="App-header">
        <h1>🎥 Vintern Vision AI</h1>
        <div className="status-bar">
          <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? '🟢 Connected' : '🔴 Disconnected'}
          </div>
          {stats.frames_received > 0 && (
            <div className="stats-summary">
              📊 Frames: {stats.frames_received} | 
              🔍 Detected: {stats.frames_detected} | 
              🧠 Analyzed: {stats.frames_analyzed}
            </div>
          )}
        </div>
      </header>

      {/* Error Message */}
      {error && (
        <div className="error-banner">
          ⚠️ {error}
        </div>
      )}

      {/* Cameras Grid */}
      <main className="cameras-grid">
        {cameras.map((camera) => (
          <div key={camera.id} className="camera-card">
            <div className="camera-header">
              <h2>{camera.name}</h2>
              <span className={`camera-status ${camera.connected ? 'online' : 'offline'}`}>
                {camera.connected ? '🟢 Online' : '🔴 Offline'}
              </span>
            </div>

            <div className="camera-info">
              <div>Frame Count: {camera.frame_count}</div>
            </div>

            {results[camera.id] && (
              <div className="camera-results">
                {/* Detection Results */}
                <div className="result-section">
                  <h3>🔍 Detection</h3>
                  <div className="detection-summary">
                    {results[camera.id].detection_summary || 'No objects detected'}
                  </div>
                  <div className="frame-number">
                    Frame #{results[camera.id].frame_number}
                  </div>
                </div>

                {/* VLM Analysis */}
                {results[camera.id].vlm_analysis && (
                  <div className="result-section">
                    <h3>🧠 AI Analysis</h3>
                    <div className="vlm-output">
                      {results[camera.id].vlm_analysis}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!results[camera.id] && camera.connected && (
              <div className="camera-results">
                <div className="loading">⏳ Waiting for data...</div>
              </div>
            )}
          </div>
        ))}
      </main>

      {/* Footer */}
      <footer className="App-footer">
        <p>Vintern-1B v3.5 | Real-time Vision AI Pipeline</p>
      </footer>
    </div>
  );
}

export default App;
