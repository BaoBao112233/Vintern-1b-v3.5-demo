class WebSocketService {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.maxReconnectDelay = 30000; // Max 30 seconds
    this.pendingFrames = new Map(); // Store pending frame requests
    this.eventHandlers = {
      onOpen: null,
      onClose: null,
      onError: null,
      onMessage: null,
    };
    
    // Bind methods to preserve 'this' context
    this.handleOpen = this.handleOpen.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleMessage = this.handleMessage.bind(this);
  }

  // Get WebSocket URL
  getWebSocketUrl() {
    if (process.env.NODE_ENV === 'production') {
      // In production with Docker
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = process.env.REACT_APP_BACKEND_WS_URL || 
                  window.location.host.replace('3000', '8000'); // Replace frontend port with backend port
      return `${protocol}//${host}/ws/predict`;
    } else {
      // In development
      const wsUrl = process.env.REACT_APP_BACKEND_WS_URL || 'ws://localhost:8000/ws/predict';
      return wsUrl;
    }
  }

  // Connect to WebSocket
  connect() {
    if (this.isConnected || this.isConnecting) {
      console.log('[WS] Already connected or connecting');
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        this.isConnecting = true;
        const wsUrl = this.getWebSocketUrl();
        
        console.log(`[WS] Connecting to ${wsUrl}`);
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          this.handleOpen();
          resolve();
        };
        
        this.ws.onclose = this.handleClose;
        this.ws.onerror = (error) => {
          this.handleError(error);
          reject(error);
        };
        this.ws.onmessage = this.handleMessage;

        // Set timeout for connection
        setTimeout(() => {
          if (!this.isConnected) {
            reject(new Error('WebSocket connection timeout'));
          }
        }, 5000);

      } catch (error) {
        this.isConnecting = false;
        console.error('[WS] Connection error:', error);
        reject(error);
      }
    });
  }

  // Disconnect from WebSocket
  disconnect() {
    if (this.ws) {
      console.log('[WS] Disconnecting...');
      this.ws.close(1000, 'User initiated disconnect');
      this.ws = null;
    }
    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    
    // Reject all pending frames
    this.pendingFrames.forEach(({ reject }) => {
      reject(new Error('WebSocket disconnected'));
    });
    this.pendingFrames.clear();
  }

  // Handle WebSocket open event
  handleOpen() {
    console.log('[WS] Connected successfully');
    this.isConnected = true;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000; // Reset delay
    
    if (this.eventHandlers.onOpen) {
      this.eventHandlers.onOpen();
    }
  }

  // Handle WebSocket close event
  handleClose(event) {
    console.log(`[WS] Connection closed: ${event.code} - ${event.reason}`);
    this.isConnected = false;
    this.isConnecting = false;
    
    if (this.eventHandlers.onClose) {
      this.eventHandlers.onClose(event);
    }

    // Auto-reconnect if not a normal closure
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }

    // Reject all pending frames
    this.pendingFrames.forEach(({ reject }) => {
      reject(new Error('WebSocket connection lost'));
    });
    this.pendingFrames.clear();
  }

  // Handle WebSocket error event
  handleError(error) {
    console.error('[WS] Error:', error);
    this.isConnecting = false;
    
    if (this.eventHandlers.onError) {
      this.eventHandlers.onError(error);
    }
  }

  // Handle WebSocket message event
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      if (this.eventHandlers.onMessage) {
        this.eventHandlers.onMessage(data);
      }

      // Handle frame response
      if (data.frame_id && this.pendingFrames.has(data.frame_id)) {
        const { resolve, reject } = this.pendingFrames.get(data.frame_id);
        this.pendingFrames.delete(data.frame_id);

        if (data.success) {
          resolve(data);
        } else {
          reject(new Error(data.error || 'Unknown error'));
        }
      }

    } catch (error) {
      console.error('[WS] Message parsing error:', error);
    }
  }

  // Schedule reconnection
  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);
    
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (!this.isConnected && !this.isConnecting) {
        this.connect().catch((error) => {
          console.error('[WS] Reconnection failed:', error);
        });
      }
    }, delay);
  }

  // Send frame for inference
  async sendFrame(frameData) {
    if (!this.isConnected) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      const frameId = frameData.frame_id || `frame_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Store promise resolvers
      this.pendingFrames.set(frameId, { resolve, reject });

      // Set timeout for frame processing
      const timeoutId = setTimeout(() => {
        if (this.pendingFrames.has(frameId)) {
          this.pendingFrames.delete(frameId);
          reject(new Error('Frame processing timeout'));
        }
      }, 15000); // 15 second timeout

      // Update resolve to clear timeout
      const originalResolve = resolve;
      const wrappedResolve = (data) => {
        clearTimeout(timeoutId);
        originalResolve(data);
      };
      
      const wrappedReject = (error) => {
        clearTimeout(timeoutId);
        reject(error);
      };

      this.pendingFrames.set(frameId, { 
        resolve: wrappedResolve, 
        reject: wrappedReject 
      });

      // Send frame data
      const message = {
        ...frameData,
        frame_id: frameId,
        timestamp: frameData.timestamp || Date.now() / 1000,
      };

      try {
        this.ws.send(JSON.stringify(message));
      } catch (error) {
        this.pendingFrames.delete(frameId);
        clearTimeout(timeoutId);
        reject(error);
      }
    });
  }

  // Set event handlers
  onOpen(handler) {
    this.eventHandlers.onOpen = handler;
  }

  onClose(handler) {
    this.eventHandlers.onClose = handler;
  }

  onError(handler) {
    this.eventHandlers.onError = handler;
  }

  onMessage(handler) {
    this.eventHandlers.onMessage = handler;
  }

  // Get connection status
  getStatus() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      pendingFrames: this.pendingFrames.size,
      wsUrl: this.getWebSocketUrl(),
    };
  }

  // Utility method to check if WebSocket is ready for sending data
  isReady() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

// Create singleton instance
export const wsService = new WebSocketService();

// Export class for creating additional instances if needed
export default WebSocketService;