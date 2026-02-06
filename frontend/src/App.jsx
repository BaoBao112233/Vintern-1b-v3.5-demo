import React, { useState, useEffect } from 'react';
import './App.css';
import CameraFeed from './components/CameraFeed';
import StatusPanel from './components/StatusPanel';
import ControlPanel from './components/ControlPanel';
import ResultsPanel from './components/ResultsPanel';
import ChatInterface from './components/ChatInterface';
import MultiCameraView from './components/MultiCameraView';
import { apiService } from './services/api';

function App() {
  const [viewMode, setViewMode] = useState('multi-camera'); // 'single-camera' or 'multi-camera'
  const [isConnected, setIsConnected] = useState(false);
  const [modelStatus, setModelStatus] = useState(null);
  const [currentResults, setCurrentResults] = useState(null);
  const [detectedObjects, setDetectedObjects] = useState([]);
  const [currentImageData, setCurrentImageData] = useState(null);
  const [connectionStats, setConnectionStats] = useState({
    framesProcessed: 0,
    averageLatency: 0,
    errors: 0
  });
  const [settings, setSettings] = useState({
    mode: 'websocket', // 'websocket' or 'http'
    fps: 5,
    width: 640,
    height: 480,
    showOverlay: true,
    autoStart: false,
    enableObjectDetection: true
  });

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 10000); // Check every 10s
    return () => clearInterval(interval);
  }, []);

  const checkBackendHealth = async () => {
    try {
      const status = await apiService.getHealth();
      setModelStatus(status);
      setIsConnected(true);
    } catch (error) {
      console.error('Backend health check failed:', error);
      setIsConnected(false);
      setModelStatus(null);
    }
  };

  const handleResults = (results) => {
    setCurrentResults(results);
    
    // Update detected objects if available
    if (results.detected_objects) {
      setDetectedObjects(results.detected_objects);
    }
    
    // Update current image data for chat
    if (results.image_data) {
      setCurrentImageData(results.image_data);
    }
    
    // Update stats
    setConnectionStats(prev => ({
      ...prev,
      framesProcessed: prev.framesProcessed + 1,
      averageLatency: results.processing_time || prev.averageLatency
    }));
  };

  const handleError = (error) => {
    console.error('Inference error:', error);
    setConnectionStats(prev => ({
      ...prev,
      errors: prev.errors + 1
    }));
  };

  const handleSettingsChange = (newSettings) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  };

  const handleChatResponse = (chatResponse) => {
    // Update detected objects from chat response
    if (chatResponse.detected_objects) {
      setDetectedObjects(chatResponse.detected_objects);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Vintern-1B Realtime Camera Inference Demo</h1>
        <div className="view-mode-toggle">
          <button 
            className={viewMode === 'multi-camera' ? 'active' : ''}
            onClick={() => setViewMode('multi-camera')}
          >
            Multi-Camera View
          </button>
          <button 
            className={viewMode === 'single-camera' ? 'active' : ''}
            onClick={() => setViewMode('single-camera')}
          >
            Single Camera View
          </button>
        </div>
        <StatusPanel 
          isConnected={isConnected}
          modelStatus={modelStatus}
          connectionStats={connectionStats}
        />
      </header>

      <main className="App-main">
        {viewMode === 'multi-camera' ? (
          <MultiCameraView />
        ) : (
          <div className="demo-container">
            <div className="left-panel">
              <div className="camera-section">
                <CameraFeed
                  settings={settings}
                  onResults={handleResults}
                  onError={handleError}
                  isConnected={isConnected}
                />
              </div>
              
              <div className="controls-section">
                <ControlPanel
                  settings={settings}
                  onSettingsChange={handleSettingsChange}
                  modelStatus={modelStatus}
                />
              </div>
            </div>
            
            <div className="right-panel">
              <div className="results-section">
                <ResultsPanel
                  results={currentResults}
                  showDetails={true}
                  detectedObjects={detectedObjects}
                />
              </div>
              
              <div className="chat-section">
                <ChatInterface
                  currentImageData={currentImageData}
                  detectedObjects={detectedObjects}
                  onChatResponse={handleChatResponse}
                />
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>
          Powered by <strong>5CD-AI/Vintern-1B-v3_5</strong> + Coral TPU | 
          <a 
            href="https://github.com/ngxson/vintern-realtime-demo" 
            target="_blank" 
            rel="noopener noreferrer"
          >
            Reference Implementation
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;