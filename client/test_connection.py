#!/usr/bin/env python3
"""
Test network connection từ Raspberry Pi sang PC

Script này giúp troubleshoot network issues
"""

import socket
import subprocess
import sys
import time
from typing import Tuple

import requests


def test_network_basic(pc_ip: str) -> bool:
    """Test basic network connectivity"""
    print(f"\n{'='*60}")
    print(f"🌐 Test 1: Basic Network Connectivity")
    print(f"{'='*60}")
    
    # Test 1: Ping
    print(f"\n1️⃣ Testing ping to {pc_ip}...")
    try:
        result = subprocess.run(
            ['ping', '-c', '4', '-W', '2', pc_ip],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Extract ping stats
            output = result.stdout
            if 'rtt min/avg/max' in output:
                stats_line = [l for l in output.split('\n') if 'rtt min/avg/max' in l][0]
                print(f"✅ Ping successful!")
                print(f"   {stats_line.strip()}")
            else:
                print(f"✅ Ping successful! (no stats available)")
            return True
        else:
            print(f"❌ Ping failed!")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Ping timeout!")
        return False
    except Exception as e:
        print(f"❌ Ping error: {e}")
        return False


def test_port_open(pc_ip: str, port: int, timeout: float = 3.0) -> bool:
    """Test xem port có mở không"""
    print(f"\n2️⃣ Testing port {port} on {pc_ip}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        result = sock.connect_ex((pc_ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is OPEN")
            return True
        else:
            print(f"❌ Port {port} is CLOSED or FILTERED")
            return False
    except socket.gaierror:
        print(f"❌ Hostname could not be resolved")
        return False
    except socket.timeout:
        print(f"❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_http_health(pc_ip: str, port: int, timeout: float = 5.0) -> bool:
    """Test HTTP health endpoint"""
    print(f"\n3️⃣ Testing HTTP health endpoint...")
    
    url = f"http://{pc_ip}:{port}/health"
    
    try:
        start = time.time()
        response = requests.get(url, timeout=timeout)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful!")
            print(f"   Status: {data.get('status')}")
            print(f"   Response time: {elapsed:.3f}s")
            return True
        else:
            print(f"❌ Health check failed!")
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection refused - server might not be running")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout after {timeout}s")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_bandwidth(pc_ip: str, port: int) -> Tuple[bool, float]:
    """Test bandwidth với small request"""
    print(f"\n4️⃣ Testing bandwidth with dummy request...")
    
    url = f"http://{pc_ip}:{port}/health"
    
    try:
        # Warm up
        requests.get(url, timeout=3)
        
        # Test multiple requests
        times = []
        for i in range(5):
            start = time.time()
            response = requests.get(url, timeout=3)
            elapsed = time.time() - start
            times.append(elapsed)
            
            if response.status_code != 200:
                print(f"❌ Request {i+1} failed")
                return False, 0
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"✅ Bandwidth test completed")
        print(f"   Average: {avg_time*1000:.1f}ms")
        print(f"   Min: {min_time*1000:.1f}ms")
        print(f"   Max: {max_time*1000:.1f}ms")
        
        if avg_time > 0.1:
            print(f"   ⚠️ Network latency is high (>100ms)")
        
        return True, avg_time
        
    except Exception as e:
        print(f"❌ Bandwidth test failed: {e}")
        return False, 0


def check_firewall_suggestion(pc_ip: str, port: int):
    """Đưa ra suggestions về firewall"""
    print(f"\n{'='*60}")
    print(f"🔧 Troubleshooting Suggestions")
    print(f"{'='*60}")
    
    print(f"\n📌 Nếu các test trên fail, hãy kiểm tra:")
    print(f"\n1️⃣ Trên PC ({pc_ip}):")
    print(f"   - Server có đang chạy không?")
    print(f"     ps aux | grep llama-server")
    print(f"   - Server có listen đúng port không?")
    print(f"     netstat -tlnp | grep {port}")
    print(f"   - Firewall có block port không?")
    print(f"     sudo ufw status")
    print(f"     sudo ufw allow {port}/tcp")
    print(f"   - Hoặc với iptables:")
    print(f"     sudo iptables -L -n | grep {port}")
    print(f"     sudo iptables -A INPUT -p tcp --dport {port} -j ACCEPT")
    
    print(f"\n2️⃣ Trên Raspberry Pi:")
    print(f"   - Pi có kết nối mạng LAN không?")
    print(f"     ip addr show")
    print(f"   - Pi và PC có cùng subnet không?")
    print(f"     ip route")
    
    print(f"\n3️⃣ Network:")
    print(f"   - Router có block traffic giữa devices không?")
    print(f"   - Có dùng VPN hoặc proxy không?")


def main():
    print(f"\n{'='*60}")
    print(f"  Raspberry Pi → PC Connection Test")
    print(f"{'='*60}")
    
    # PC configuration - THAY ĐỔI CHỖ NÀY!
    if len(sys.argv) > 1:
        PC_IP = sys.argv[1]
    else:
        PC_IP = "192.168.1.100"  # <-- Default, sửa thành IP của PC
    
    PC_PORT = 8080
    
    print(f"\n📊 Configuration:")
    print(f"   PC IP: {PC_IP}")
    print(f"   PC Port: {PC_PORT}")
    print(f"\n⚠️ Lưu ý: Nếu IP sai, sửa trong script hoặc chạy:")
    print(f"   python test_connection.py <PC_IP>")
    
    # Run tests
    results = []
    
    results.append(("Network Ping", test_network_basic(PC_IP)))
    results.append(("Port Check", test_port_open(PC_IP, PC_PORT)))
    results.append(("HTTP Health", test_http_health(PC_IP, PC_PORT)))
    
    bandwidth_ok, avg_latency = test_bandwidth(PC_IP, PC_PORT)
    results.append(("Bandwidth Test", bandwidth_ok))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Test Summary")
    print(f"{'='*60}\n")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name:20s} {status}")
        if not passed:
            all_passed = False
    
    print(f"\n{'='*60}")
    
    if all_passed:
        print(f"✅ Tất cả tests đều PASS!")
        print(f"✅ Raspberry Pi có thể giao tiếp với PC!")
        print(f"\n📌 Next steps:")
        print(f"   1. Test inference với client:")
        print(f"      python pc_inference_client.py <image.jpg>")
        print(f"   2. Integrate vào backend API của bạn")
    else:
        print(f"❌ Một số tests FAILED!")
        print(f"❌ Cần fix network/firewall issues")
        check_firewall_suggestion(PC_IP, PC_PORT)
    
    print(f"{'='*60}\n")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
