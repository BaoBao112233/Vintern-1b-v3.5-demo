import React from 'react';
import './ControlPanel.css';

const ControlPanel = ({ settings, onSettingsChange, modelStatus }) => {
  const handleChange = (key, value) => {
    onSettingsChange({ [key]: value });
  };

  return (
    <div className="control-panel">
      <h4>Settings</h4>
      
      <div className="control-section">
        <label className="control-group">
          <span className="control-label">Connection Mode:</span>
          <select
            value={settings.mode}
            onChange={(e) => handleChange('mode', e.target.value)}
            className="control-select"
          >
            <option value="websocket">WebSocket (Realtime)</option>
            <option value="http">HTTP API (Request-based)</option>
          </select>
        </label>

        <label className="control-group">
          <span className="control-label">FPS: {settings.fps}</span>
          <input
            type="range"
            min="1"
            max="30"
            value={settings.fps}
            onChange={(e) => handleChange('fps', parseInt(e.target.value))}
            className="control-range"
          />
        </label>

        <label className="control-group">
          <span className="control-label">Resolution:</span>
          <select
            value={`${settings.width}x${settings.height}`}
            onChange={(e) => {
              const [width, height] = e.target.value.split('x').map(Number);
              onSettingsChange({ width, height });
            }}
            className="control-select"
          >
            <option value="320x240">320x240 (Fast)</option>
            <option value="640x480">640x480 (Balanced)</option>
            <option value="800x600">800x600 (Quality)</option>
            <option value="1280x720">1280x720 (HD)</option>
          </select>
        </label>

        <label className="control-group checkbox">
          <input
            type="checkbox"
            checked={settings.showOverlay}
            onChange={(e) => handleChange('showOverlay', e.target.checked)}
            className="control-checkbox"
          />
          <span className="control-label">Show Results Overlay</span>
        </label>

        <label className="control-group checkbox">
          <input
            type="checkbox"
            checked={settings.autoStart}
            onChange={(e) => handleChange('autoStart', e.target.checked)}
            className="control-checkbox"
          />
          <span className="control-label">Auto-start Camera</span>
        </label>
      </div>

      <div className="control-section">
        <h5>Model Configuration</h5>
        
        <div className="model-status">
          <div className="model-item">
            <span className="model-label">Current Mode:</span>
            <span className="model-value">
              {modelStatus?.model_mode === 'hf' ? 'Hugging Face API' : 'Local Model'}
            </span>
          </div>
          
          <div className="model-item">
            <span className="model-label">Status:</span>
            <span className={`model-value ${modelStatus?.model_ready ? 'ready' : 'not-ready'}`}>
              {modelStatus?.model_ready ? 'Ready' : 'Loading/Error'}
            </span>
          </div>
        </div>

        <div className="model-note">
          <small>
            💡 <strong>Tip:</strong> {' '}
            {settings.mode === 'websocket' 
              ? 'WebSocket provides lower latency for realtime inference.'
              : 'HTTP mode is more reliable but has higher latency.'
            }
          </small>
        </div>
      </div>

      <div className="control-section">
        <h5>Performance Tips</h5>
        <ul className="tips-list">
          <li>Lower resolution = faster processing</li>
          <li>Lower FPS = less CPU usage</li>
          <li>WebSocket mode for minimal latency</li>
          <li>Good lighting improves accuracy</li>
        </ul>
      </div>
    </div>
  );
};

export default ControlPanel;