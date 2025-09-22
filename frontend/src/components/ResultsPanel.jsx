import React, { useState } from 'react';
import './ResultsPanel.css';

const ResultsPanel = ({ results, showDetails = true }) => {
  const [expandedSection, setExpandedSection] = useState(null);

  if (!results) {
    return (
      <div className="results-panel">
        <h4>Inference Results</h4>
        <div className="no-results">
          <p>No inference results yet...</p>
          <small>Start the camera and inference will appear here</small>
        </div>
      </div>
    );
  }

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const renderDetectionResults = (detectionResults) => {
    if (!detectionResults || !Array.isArray(detectionResults)) return null;

    return (
      <div className="detection-results">
        <h6>Detected Objects ({detectionResults.length})</h6>
        <div className="detection-list">
          {detectionResults.map((detection, index) => (
            <div key={index} className="detection-item">
              <div className="detection-header">
                <span className="detection-label">{detection.label || 'Unknown'}</span>
                <span className="detection-confidence">
                  {((detection.confidence || 0) * 100).toFixed(1)}%
                </span>
              </div>
              {detection.bbox && (
                <div className="detection-bbox">
                  <small>
                    Box: [{detection.bbox.xmin || detection.bbox.x || 0}, {' '}
                    {detection.bbox.ymin || detection.bbox.y || 0}, {' '}
                    {detection.bbox.xmax || (detection.bbox.x + detection.bbox.width) || 0}, {' '}
                    {detection.bbox.ymax || (detection.bbox.y + detection.bbox.height) || 0}]
                  </small>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderTextResults = (text) => {
    if (!text) return null;

    return (
      <div className="text-results">
        <h6>Generated Text / Description</h6>
        <div className="text-content">
          {text}
        </div>
      </div>
    );
  };

  const renderResultImage = (base64Image) => {
    if (!base64Image) return null;

    return (
      <div className="result-image-section">
        <h6>Annotated Result</h6>
        <img 
          src={`data:image/jpeg;base64,${base64Image}`}
          alt="Inference result"
          className="result-image"
        />
      </div>
    );
  };

  return (
    <div className="results-panel">
      <div className="results-header">
        <h4>Inference Results</h4>
        <div className="results-meta">
          <span className={`status-badge ${results.success ? 'success' : 'error'}`}>
            {results.success ? '✅' : '❌'} {results.success ? 'Success' : 'Failed'}
          </span>
          <span className="processing-time">
            {(results.processing_time * 1000).toFixed(0)}ms
          </span>
        </div>
      </div>

      {!results.success && results.error && (
        <div className="error-section">
          <strong>Error:</strong> {results.error}
        </div>
      )}

      {results.success && results.results && (
        <div className="results-content">
          {/* Detection Results */}
          {results.results.detection_results && (
            <div className="result-section">
              <button
                className={`section-toggle ${expandedSection === 'detections' ? 'expanded' : ''}`}
                onClick={() => toggleSection('detections')}
              >
                🎯 Object Detection Results
                <span className="toggle-icon">
                  {expandedSection === 'detections' ? '▼' : '▶'}
                </span>
              </button>
              {expandedSection === 'detections' && renderDetectionResults(results.results.detection_results)}
            </div>
          )}

          {/* Text Results */}
          {(results.results.generated_text || results.results.description) && (
            <div className="result-section">
              <button
                className={`section-toggle ${expandedSection === 'text' ? 'expanded' : ''}`}
                onClick={() => toggleSection('text')}
              >
                💬 Text Analysis
                <span className="toggle-icon">
                  {expandedSection === 'text' ? '▼' : '▶'}
                </span>
              </button>
              {expandedSection === 'text' && renderTextResults(
                results.results.generated_text || results.results.description
              )}
            </div>
          )}

          {/* Classification Results */}
          {results.results.predictions && (
            <div className="result-section">
              <button
                className={`section-toggle ${expandedSection === 'classification' ? 'expanded' : ''}`}
                onClick={() => toggleSection('classification')}
              >
                🏷️ Classification Results
                <span className="toggle-icon">
                  {expandedSection === 'classification' ? '▼' : '▶'}
                </span>
              </button>
              {expandedSection === 'classification' && (
                <div className="classification-results">
                  {results.results.predictions.map((pred, index) => (
                    <div key={index} className="prediction-item">
                      <span className="prediction-label">{pred.label}</span>
                      <span className="prediction-score">{(pred.score * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Result Image */}
          {results.result_image_base64 && (
            <div className="result-section">
              <button
                className={`section-toggle ${expandedSection === 'image' ? 'expanded' : ''}`}
                onClick={() => toggleSection('image')}
              >
                🖼️ Annotated Image
                <span className="toggle-icon">
                  {expandedSection === 'image' ? '▼' : '▶'}
                </span>
              </button>
              {expandedSection === 'image' && renderResultImage(results.result_image_base64)}
            </div>
          )}

          {/* Raw Results (for debugging) */}
          {showDetails && (
            <div className="result-section">
              <button
                className={`section-toggle ${expandedSection === 'raw' ? 'expanded' : ''}`}
                onClick={() => toggleSection('raw')}
              >
                🔧 Raw Results (Debug)
                <span className="toggle-icon">
                  {expandedSection === 'raw' ? '▼' : '▶'}
                </span>
              </button>
              {expandedSection === 'raw' && (
                <div className="raw-results">
                  <pre>{JSON.stringify(results, null, 2)}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="results-footer">
        <small>
          Frame ID: {results.frame_id || 'N/A'} | 
          Timestamp: {new Date(results.timestamp * 1000).toLocaleTimeString()}
        </small>
      </div>
    </div>
  );
};

export default ResultsPanel;