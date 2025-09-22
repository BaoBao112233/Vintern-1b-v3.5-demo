"""
WebSocket Manager for realtime inference
"""
import asyncio
import time
import json
import logging
from typing import Set, Dict, Any
import base64
from io import BytesIO
from PIL import Image

from fastapi import WebSocket
from app.utils.image_processing import process_image, encode_result_image

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for realtime inference"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict] = {}
        
    async def connect(self, websocket: WebSocket):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_info[websocket] = {
            "connected_at": time.time(),
            "frames_processed": 0,
            "last_frame_time": 0
        }
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.connection_info:
            info = self.connection_info.pop(websocket)
            logger.info(f"WebSocket client disconnected. Processed {info['frames_processed']} frames.")
        
        logger.info(f"Active connections: {len(self.active_connections)}")
    
    async def cleanup(self):
        """Cleanup all connections"""
        for websocket in list(self.active_connections):
            try:
                await websocket.close()
            except:
                pass
        self.active_connections.clear()
        self.connection_info.clear()
    
    async def process_frame(self, websocket: WebSocket, data: Dict[str, Any]):
        """
        Process a frame from WebSocket client
        
        Expected data format:
        {
            "frame_id": "string",
            "timestamp": float,
            "image_base64": "string",
            "width": int,
            "height": int
        }
        """
        start_time = time.time()
        
        try:
            # Validate data
            if "image_base64" not in data:
                await self._send_error(websocket, "Missing image_base64", data.get("frame_id"))
                return
            
            frame_id = data.get("frame_id", f"frame_{time.time()}")
            client_timestamp = data.get("timestamp", time.time())
            
            # Update connection info
            if websocket in self.connection_info:
                self.connection_info[websocket]["last_frame_time"] = time.time()
                self.connection_info[websocket]["frames_processed"] += 1
            
            # Decode image
            try:
                image_data = base64.b64decode(data["image_base64"])
                image = Image.open(BytesIO(image_data))
            except Exception as e:
                await self._send_error(
                    websocket, 
                    f"Invalid image data: {str(e)}", 
                    frame_id
                )
                return
            
            # Process image
            target_width = data.get("width", 640)
            target_height = data.get("height", 480)
            
            processed_image = process_image(
                image, 
                target_width=target_width, 
                target_height=target_height
            )
            
            # Get model service and run inference
            model_service = self._get_model_service()
            if not model_service:
                await self._send_error(
                    websocket, 
                    "Model service not available", 
                    frame_id
                )
                return
            
            # Run inference
            results = await model_service.predict(processed_image)
            
            # Encode result image if available
            result_image_base64 = None
            if "annotated_image" in results:
                result_image_base64 = encode_result_image(results["annotated_image"])
            
            processing_time = time.time() - start_time
            
            # Send response
            response = {
                "frame_id": frame_id,
                "timestamp": client_timestamp,
                "processing_time": processing_time,
                "server_timestamp": time.time(),
                "success": True,
                "results": results,
                "result_image_base64": result_image_base64
            }
            
            await websocket.send_text(json.dumps(response))
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"WebSocket frame processing error: {e}")
            
            await self._send_error(
                websocket, 
                str(e), 
                data.get("frame_id"), 
                processing_time
            )
    
    async def _send_error(self, websocket: WebSocket, error: str, frame_id: str = None, processing_time: float = 0):
        """Send error response to WebSocket client"""
        try:
            response = {
                "frame_id": frame_id,
                "timestamp": time.time(),
                "processing_time": processing_time,
                "success": False,
                "error": error
            }
            await websocket.send_text(json.dumps(response))
        except Exception as e:
            logger.error(f"Failed to send error to WebSocket: {e}")
    
    def _get_model_service(self):
        """Get the appropriate model service"""
        import os
        from app.main import hf_client, local_runner
        
        model_mode = os.getenv("MODEL_MODE", "hf").lower()
        
        if model_mode == "hf":
            return hf_client if hf_client and hf_client.is_ready() else None
        elif model_mode == "local":
            return local_runner if local_runner and local_runner.is_ready() else None
        
        return None
    
    async def broadcast_status(self, status_data: Dict[str, Any]):
        """Broadcast status to all connected clients"""
        if not self.active_connections:
            return
        
        message = json.dumps({
            "type": "status",
            "data": status_data,
            "timestamp": time.time()
        })
        
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send broadcast to client: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections"""
        total_connections = len(self.active_connections)
        total_frames = sum(info["frames_processed"] for info in self.connection_info.values())
        
        return {
            "active_connections": total_connections,
            "total_frames_processed": total_frames,
            "connections_info": [
                {
                    "connected_at": info["connected_at"],
                    "frames_processed": info["frames_processed"],
                    "last_frame_time": info["last_frame_time"]
                }
                for info in self.connection_info.values()
            ]
        }