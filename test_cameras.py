# Test camera RTSP connection
import cv2
import sys

def test_camera(ip, username, password):
    rtsp_url = f"rtsp://{username}:{password}@{ip}/cam/realmonitor?channel=1&subtype=1"
    
    print(f"Testing camera: {ip}")
    print(f"RTSP URL: {rtsp_url}")
    
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print(f"❌ Failed to open camera {ip}")
        return False
    
    print(f"✅ Successfully opened camera {ip}")
    
    # Try to read a frame
    ret, frame = cap.read()
    if ret:
        print(f"✅ Successfully read frame: {frame.shape}")
    else:
        print(f"❌ Failed to read frame from {ip}")
        cap.release()
        return False
    
    cap.release()
    return True

if __name__ == "__main__":
    username = "admin"
    password = "abcd12345"
    
    cam1_ip = "192.168.1.11"
    cam2_ip = "192.168.1.13"
    
    print("=" * 50)
    print("Camera Connection Test")
    print("=" * 50)
    
    print("\nCamera 1:")
    cam1_ok = test_camera(cam1_ip, username, password)
    
    print("\nCamera 2:")
    cam2_ok = test_camera(cam2_ip, username, password)
    
    # Try fallback for cam2
    if not cam2_ok:
        print("\nTrying fallback IP for Camera 2...")
        cam2_ip_fallback = "192.168.1.9"
        cam2_ok = test_camera(cam2_ip_fallback, username, password)
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"  Camera 1 ({cam1_ip}): {'✅ OK' if cam1_ok else '❌ FAILED'}")
    print(f"  Camera 2 ({cam2_ip}): {'✅ OK' if cam2_ok else '❌ FAILED'}")
    print("=" * 50)
