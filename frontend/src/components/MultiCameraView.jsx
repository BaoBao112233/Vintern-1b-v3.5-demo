import React, { useState, useEffect, useCallback } from 'react';
import './MultiCameraView.css';
import { apiService } from '../services/api';

const MultiCameraView = () => {
  const [cameras, setCameras] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(1000); // 1 second
  const [stats, setStats] = useState({
    totalDetections: 0,
    framesProcessed: 0
  });

  // Initialize cameras
  useEffect(() => {
    initializeCameras();
  }, []);

  // Auto-refresh frames
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchAllFrames();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const initializeCameras = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('http://localhost:8000/api/cameras/initialize', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        console.log('Cameras initialized:', data.cameras);
        fetchAllFrames();
      }
    } catch (err) {
      console.error('Failed to initialize cameras:', err);
      setError('Failed to initialize cameras');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAllFrames = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/cameras/all/frames?detect=true');
      const data = await response.json();
      
      if (data.success && data.cameras) {
        setCameras(data.cameras);
        
        // Update stats
        let totalDets = 0;
        Object.values(data.cameras).forEach(cam => {
          totalDets += (cam.detections || []).length;
        });
        
        setStats(prev => ({
          totalDetections: totalDets,
          framesProcessed: prev.framesProcessed + 1
        }));
        
        setError(null);
      }
    } catch (err) {
      console.error('Failed to fetch frames:', err);
      setError('Failed to fetch camera frames');
    }
  };

  const getCameraName = (cameraId) => {
    return cameraId === 'cam1' ? 'Camera 1 (192.168.1.11)' : 'Camera 2 (192.168.1.13)';
  };

  const renderCamera = (cameraId, cameraData) => {
    if (!cameraData) return null;

    return (
      <div key={cameraId} className="camera-card">
        <div className="camera-header">
          <h3>{getCameraName(cameraId)}</h3>
          <span className="detection-count">
            {cameraData.detections ? cameraData.detections.length : 0} objects
          </span>
        </div>
        
        <div className="camera-feed">
          {cameraData.image_base64 ? (
            <img 
              src={`data:image/jpeg;base64,${cameraData.image_base64}`}
              alt={getCameraName(cameraId)}
              className="camera-image"
            />
          ) : (
            <div className="no-image">No image available</div>
          )}
        </div>
        
        <div className="camera-info">
          {cameraData.summary && (
            <p className="detection-summary">{cameraData.summary}</p>
          )}
          
          {cameraData.detections && cameraData.detections.length > 0 && (
            <div className="detections-list">
              <h4>Detected Objects:</h4>
              <ul>
                {cameraData.detections.map((det, idx) => (
                  <li key={idx}>
                    <span className="object-label">{det.label}</span>
                    <span className="object-confidence">
                      {(det.confidence * 100).toFixed(1)}%
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="multi-camera-view">
      <div className="control-bar">
        <h2>Multi-Camera Object Detection</h2>
        
        <div className="controls">
          <button 
            onClick={initializeCameras}
            disabled={isLoading}
            className="btn-primary"
          >
            {isLoading ? 'Initializing...' : 'Reinitialize Cameras'}
          </button>
          
          <button 
            onClick={fetchAllFrames}
            disabled={isLoading}
            className="btn-secondary"
          >
            Refresh Now
          </button>
          
          <label className="auto-refresh-toggle">
            <input 
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
          
          <select 
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="interval-select"
          >
            <option value={500}>0.5s</option>
            <option value={1000}>1s</option>
            <option value={2000}>2s</option>
            <option value={5000}>5s</option>
          </select>
        </div>
        
        <div className="stats">
          <span>Frames: {stats.framesProcessed}</span>
          <span>Total Detections: {stats.totalDetections}</span>
        </div>
      </div>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      <div className="cameras-grid">
        {Object.entries(cameras).map(([cameraId, cameraData]) => 
          renderCamera(cameraId, cameraData)
        )}
        
        {Object.keys(cameras).length === 0 && !isLoading && (
          <div className="no-cameras">
            No cameras available. Click "Initialize Cameras" to start.
          </div>
        )}
      </div>
    </div>
  );
};

export default MultiCameraView;
