import axios from 'axios';

// Get backend URL from environment or default to localhost
const getBackendUrl = () => {
  if (process.env.NODE_ENV === 'production') {
    // In production with Docker, backend service name is 'backend'
    return process.env.REACT_APP_BACKEND_URL || 'http://backend:8000';
  } else {
    // In development
    return process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
  }
};

const BACKEND_URL = getBackendUrl();

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: BACKEND_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('[API] Response error:', error);
    
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.error || error.message;
      throw new Error(`Server error (${error.response.status}): ${message}`);
    } else if (error.request) {
      // Request was made but no response received
      throw new Error('Network error: Unable to reach server');
    } else {
      // Something else happened
      throw new Error(`Request error: ${error.message}`);
    }
  }
);

export const apiService = {
  // Health check endpoint
  async getHealth() {
    try {
      const response = await apiClient.get('/api/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },

  // Predict with base64 image
  async predictBase64(data) {
    try {
      const response = await apiClient.post('/api/predict', data);
      return response.data;
    } catch (error) {
      console.error('Base64 prediction failed:', error);
      throw error;
    }
  },

  // Predict with file upload
  async predictFile(file, options = {}) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      if (options.frame_id) {
        formData.append('frame_id', options.frame_id);
      }
      if (options.resize_width) {
        formData.append('resize_width', options.resize_width.toString());
      }
      if (options.resize_height) {
        formData.append('resize_height', options.resize_height.toString());
      }

      const response = await apiClient.post('/api/predict/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (error) {
      console.error('File prediction failed:', error);
      throw error;
    }
  },

  // Utility function to convert canvas to base64
  canvasToBase64(canvas, quality = 0.8) {
    return canvas.toDataURL('image/jpeg', quality).split(',')[1];
  },

  // Utility function to resize image
  async resizeImage(imageFile, maxWidth, maxHeight) {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();

      img.onload = () => {
        // Calculate new dimensions
        let { width, height } = img;
        const aspectRatio = width / height;

        if (width > height) {
          if (width > maxWidth) {
            width = maxWidth;
            height = width / aspectRatio;
          }
        } else {
          if (height > maxHeight) {
            height = maxHeight;
            width = height * aspectRatio;
          }
        }

        // Set canvas size and draw image
        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(img, 0, 0, width, height);

        // Convert to blob
        canvas.toBlob(resolve, 'image/jpeg', 0.8);
      };

      img.onerror = reject;
      img.src = URL.createObjectURL(imageFile);
    });
  },

  // Get current backend configuration
  getConfig() {
    return {
      backendUrl: BACKEND_URL,
      timeout: apiClient.defaults.timeout,
    };
  },

  // Test connection to backend
  async testConnection() {
    try {
      const start = Date.now();
      await this.getHealth();
      const latency = Date.now() - start;
      
      return {
        connected: true,
        latency,
        backendUrl: BACKEND_URL,
      };
    } catch (error) {
      return {
        connected: false,
        error: error.message,
        backendUrl: BACKEND_URL,
      };
    }
  },

  // Chat with vision and object detection
  async chatWithVision(data) {
    try {
      const response = await apiClient.post('/api/chat', data);
      return response.data;
    } catch (error) {
      console.error('[API] Chat with vision error:', error);
      throw error;
    }
  },

  // Analyze image for objects only
  async analyzeImage(imageFile) {
    try {
      const formData = new FormData();
      formData.append('file', imageFile);
      
      const response = await apiClient.post('/api/analyze-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (error) {
      console.error('[API] Analyze image error:', error);
      throw error;
    }
  },

  // Get model status
  async getModelStatus() {
    try {
      const response = await apiClient.get('/api/model-status');
      return response.data;
    } catch (error) {
      console.error('[API] Get model status error:', error);
      throw error;
    }
  },
};