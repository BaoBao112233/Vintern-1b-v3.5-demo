import React from 'react';
import './StatusPanel.css';

const StatusPanel = ({ isConnected, modelStatus, connectionStats }) => {
  return (
    <div className="status-panel">
      <div className="status-grid">
        <div className="status-item">
          <span className="status-label">Backend:</span>
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>

        <div className="status-item">
          <span className="status-label">Model:</span>
          <span className={`status-indicator ${modelStatus?.model_ready ? 'connected' : 'disconnected'}`}>
            {modelStatus?.model_ready ? '🟢 Ready' : '🟡 Loading'}
          </span>
        </div>

        <div className="status-item">
          <span className="status-label">Mode:</span>
          <span className="status-value">
            {modelStatus?.model_mode === 'hf' ? '☁️ Remote (HF)' : '💻 Local'}
          </span>
        </div>

        <div className="status-item">
          <span className="status-label">Processed:</span>
          <span className="status-value">
            {connectionStats.framesProcessed} frames
          </span>
        </div>

        <div className="status-item">
          <span className="status-label">Avg Latency:</span>
          <span className="status-value">
            {connectionStats.averageLatency ? 
              `${(connectionStats.averageLatency * 1000).toFixed(0)}ms` : 
              'N/A'
            }
          </span>
        </div>

        <div className="status-item">
          <span className="status-label">Errors:</span>
          <span className={`status-value ${connectionStats.errors > 0 ? 'error' : ''}`}>
            {connectionStats.errors}
          </span>
        </div>
      </div>

      {modelStatus?.model_info && (
        <div className="model-info">
          <details>
            <summary>Model Information</summary>
            <div className="model-details">
              {modelStatus.model_mode === 'hf' && (
                <div>
                  <strong>Model ID:</strong> {modelStatus.model_info.model_id}
                </div>
              )}
              {modelStatus.model_mode === 'local' && (
                <div>
                  <strong>Model Path:</strong> {modelStatus.model_info.model_path}
                </div>
              )}
            </div>
          </details>
        </div>
      )}
    </div>
  );
};

export default StatusPanel;