import React, { useRef, useEffect, useState, useCallback } from 'react';
import './CameraFeed.css';
import { wsService } from '../services/websocket';
import { apiService } from '../services/api';

const CameraFeed = ({ settings, onResults, onError, isConnected }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);
  const frameCountRef = useRef(0);

  const [cameraStatus, setCameraStatus] = useState('idle'); // 'idle', 'initializing', 'active', 'error'
  const [isInferencing, setIsInferencing] = useState(false);
  const [lastResults, setLastResults] = useState(null);
  const [fps, setFps] = useState(0);
  const [cameraError, setCameraError] = useState(null);

  // Initialize camera
  const initializeCamera = useCallback(async () => {
    try {
      setCameraStatus('initializing');
      setCameraError(null);

      // Stop existing stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }

      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: settings.width },
          height: { ideal: settings.height },
          facingMode: 'user'
        },
        audio: false
      });

      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setCameraStatus('active');
      }

    } catch (error) {
      console.error('Camera initialization failed:', error);
      setCameraError(error.message);
      setCameraStatus('error');
      onError && onError(`Camera error: ${error.message}`);
    }
  }, [settings.width, settings.height, onError]);

  // Stop camera
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraStatus('idle');
  }, []);

  // Capture frame from video
  const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || cameraStatus !== 'active') {
      return null;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Set canvas size
    canvas.width = settings.width;
    canvas.height = settings.height;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to base64
    return canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
  }, [settings.width, settings.height, cameraStatus]);

  // Send frame for inference
  const processFrame = useCallback(async () => {
    if (isInferencing || !isConnected) {
      return;
    }

    const frameData = captureFrame();
    if (!frameData) {
      return;
    }

    setIsInferencing(true);
    frameCountRef.current += 1;
    
    const frameId = `frame_${Date.now()}_${frameCountRef.current}`;
    const timestamp = Date.now();

    try {
      let result;
      
      if (settings.mode === 'websocket') {
        // Use WebSocket
        result = await wsService.sendFrame({
          frame_id: frameId,
          timestamp: timestamp,
          image_base64: frameData,
          width: settings.width,
          height: settings.height
        });
      } else {
        // Use HTTP API
        result = await apiService.predictBase64({
          image_base64: frameData,
          frame_id: frameId,
          timestamp: timestamp,
          resize_width: settings.width,
          resize_height: settings.height
        });
      }

      setLastResults(result);
      onResults && onResults(result);

      // Draw overlay if enabled
      if (settings.showOverlay && result.success && result.results) {
        drawOverlay(result.results);
      }

    } catch (error) {
      console.error('Frame processing error:', error);
      onError && onError(error.message);
    } finally {
      setIsInferencing(false);
    }
  }, [isInferencing, isConnected, captureFrame, settings, onResults, onError]);

  // Draw inference overlay
  const drawOverlay = useCallback((results) => {
    if (!overlayCanvasRef.current) return;

    const canvas = overlayCanvasRef.current;
    const ctx = canvas.getContext('2d');

    // Clear previous overlay
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Set canvas size to match video
    canvas.width = settings.width;
    canvas.height = settings.height;

    // Draw detections if available
    if (results.detection_results && Array.isArray(results.detection_results)) {
      ctx.strokeStyle = '#ff0000';
      ctx.lineWidth = 2;
      ctx.fillStyle = '#ff0000';
      ctx.font = '14px Arial';

      results.detection_results.forEach(detection => {
        const { bbox, label, confidence } = detection;
        
        if (bbox && bbox.xmin !== undefined) {
          const { xmin, ymin, xmax, ymax } = bbox;
          
          // Draw bounding box
          ctx.strokeRect(xmin, ymin, xmax - xmin, ymax - ymin);
          
          // Draw label
          const text = `${label} (${(confidence * 100).toFixed(1)}%)`;
          const textMetrics = ctx.measureText(text);
          const textY = ymin > 20 ? ymin - 5 : ymin + 20;
          
          // Draw text background
          ctx.fillStyle = 'rgba(255, 0, 0, 0.8)';
          ctx.fillRect(xmin, textY - 15, textMetrics.width + 8, 18);
          
          // Draw text
          ctx.fillStyle = '#ffffff';
          ctx.fillText(text, xmin + 4, textY);
          ctx.fillStyle = '#ff0000';
        }
      });
    }

    // Draw text results if available
    if (results.generated_text || results.description) {
      const text = results.generated_text || results.description;
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(10, 10, canvas.width - 20, 60);
      
      ctx.fillStyle = '#ffffff';
      ctx.font = '16px Arial';
      const lines = text.match(/.{1,50}(\s|$)/g) || [text];
      lines.slice(0, 3).forEach((line, index) => {
        ctx.fillText(line.trim(), 20, 30 + (index * 20));
      });
    }
  }, [settings.width, settings.height]);

  // Start/stop processing based on settings
  useEffect(() => {
    if (cameraStatus === 'active' && isConnected) {
      // Start processing frames
      const interval = 1000 / settings.fps;
      intervalRef.current = setInterval(processFrame, interval);

      // FPS counter
      const fpsInterval = setInterval(() => {
        setFps(frameCountRef.current);
        frameCountRef.current = 0;
      }, 1000);

      return () => {
        clearInterval(intervalRef.current);
        clearInterval(fpsInterval);
      };
    } else {
      // Stop processing
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setFps(0);
    }
  }, [cameraStatus, isConnected, settings.fps, processFrame]);

  // Initialize WebSocket connection
  useEffect(() => {
    if (settings.mode === 'websocket' && isConnected) {
      wsService.connect();
    }
    
    return () => {
      if (settings.mode === 'websocket') {
        wsService.disconnect();
      }
    };
  }, [settings.mode, isConnected]);

  // Auto-start camera
  useEffect(() => {
    if (settings.autoStart) {
      initializeCamera();
    }
    return () => {
      stopCamera();
    };
  }, [settings.autoStart, initializeCamera, stopCamera]);

  return (
    <div className="camera-feed">
      <div className="camera-header">
        <h3>Live Camera Feed</h3>
        <div className="camera-controls">
          {cameraStatus === 'idle' && (
            <button 
              className="btn btn-primary" 
              onClick={initializeCamera}
              disabled={!isConnected}
            >
              Start Camera
            </button>
          )}
          {cameraStatus === 'active' && (
            <button 
              className="btn btn-danger" 
              onClick={stopCamera}
            >
              Stop Camera
            </button>
          )}
          <div className="status-info">
            <span className={`status-indicator ${cameraStatus}`}>
              {cameraStatus === 'initializing' && <div className="loading-spinner"></div>}
              Camera: {cameraStatus}
            </span>
            {fps > 0 && (
              <span className="fps-counter">
                {fps} FPS
              </span>
            )}
            {isInferencing && (
              <span className="status-indicator processing">
                <div className="loading-spinner"></div>
                Processing...
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="video-container">
        <video
          ref={videoRef}
          className="video-stream"
          width={settings.width}
          height={settings.height}
          autoPlay
          muted
          playsInline
        />
        <canvas
          ref={overlayCanvasRef}
          className="overlay-canvas"
          width={settings.width}
          height={settings.height}
        />
        <canvas
          ref={canvasRef}
          className="hidden-canvas"
          style={{ display: 'none' }}
        />
      </div>

      {cameraError && (
        <div className="error-message">
          <strong>Camera Error:</strong> {cameraError}
          <button onClick={initializeCamera} className="btn btn-sm">
            Retry
          </button>
        </div>
      )}

      {lastResults && (
        <div className="last-results">
          <small>
            Last inference: {lastResults.processing_time?.toFixed(2)}ms
            {lastResults.results?.total_objects && (
              ` | Objects detected: ${lastResults.results.total_objects}`
            )}
          </small>
        </div>
      )}
    </div>
  );
};

export default CameraFeed;