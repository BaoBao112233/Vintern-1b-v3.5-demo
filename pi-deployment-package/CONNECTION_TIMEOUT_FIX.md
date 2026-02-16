# 🔧 Connection Timeout - Quick Fix Guide

## ❌ Error You're Seeing

```
Connection to 192.168.1.3 timed out. (connect timeout=60)
```

## ✅ PC Server Status (Verified)

- ✅ Server running (PID 68847)
- ✅ Listening on 0.0.0.0:8080
- ✅ Health check: OK
- ✅ Firewall port 8080: OPENED

## 🔍 Troubleshooting on Raspberry Pi

### Step 1: Run Network Debug Script

```bash
# On Raspberry Pi
cd pi-deployment-package
./network_debug.sh 192.168.1.3

# This will test:
# 1. Ping connectivity
# 2. Port accessibility
# 3. HTTP health endpoint
# 4. Inference API
```

### Step 2: Manual Tests

#### A. Test Ping
```bash
ping -c 3 192.168.1.3

# Expected: 3 packets received, 0% loss
# If fails: Network/routing issue
```

#### B. Test Port
```bash
# Option 1: Using netcat (if installed)
nc -zv 192.168.1.3 8080

# Option 2: Using telnet
telnet 192.168.1.3 8080

# Expected: Connection successful
# If fails: Firewall or server not listening
```

#### C. Test HTTP
```bash
curl -v http://192.168.1.3:8080/health

# Expected: {"status":"ok"}
# If timeout: Firewall rule not applied or network routing issue
```

#### D. Test Inference
```bash
curl -X POST http://192.168.1.3:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"max_tokens":10}'

# Expected: JSON response with "choices" field
```

### Step 3: Common Fixes

#### Fix 1: Pi Firewall (if enabled)
```bash
# On Raspberry Pi
sudo ufw allow out to 192.168.1.3 port 8080
```

#### Fix 2: Wrong Subnet/Router
```bash
# Check Pi's IP
ip addr show

# Check if on same network as PC (192.168.1.x)
# If different subnet, may need router configuration
```

#### Fix 3: WiFi Power Saving
```bash
# Disable WiFi power management (can cause timeouts)
sudo iwconfig wlan0 power off
```

#### Fix 4: Increase Timeout in Scripts

Edit `smart_analyze.py` line 20:
```python
# Before
self.client = PCInferenceClient(host=pc_host, port=pc_port, timeout=60)

# After (increase to 120 seconds)
self.client = PCInferenceClient(host=pc_host, port=pc_port, timeout=120)
```

Or in `pc_inference_client.py`:
```python
# Line ~35
self.timeout = timeout if timeout else 120  # Increased from 60
```

## 🚀 Quick Working Test

If network tests pass, try simpler script first:

```bash
# On Pi
cd pi-deployment-package/client

# Test connection only
python3 test_connection.py 192.168.1.3

# If that works, try quick test
python3 ../quick_test.py ../test_image.jpg
```

## 🔍 Advanced Debugging

### Check Routing
```bash
traceroute 192.168.1.3
# Should show direct route (1-2 hops)
```

### Check DNS
```bash
# If using hostname instead of IP
nslookup baobao-System-Product-Name
```

### Monitor Network
```bash
# On Pi, monitor traffic
sudo tcpdump -i any host 192.168.1.3 and port 8080

# Then in another terminal, run test
python3 smart_analyze.py test_image.jpg
```

### Check PC Server Logs
```bash
# On PC
tail -f /tmp/llama-server-*.log

# Look for incoming connections from Pi
# Should see: "connection from 192.168.1.X"
```

## 📊 Expected Behavior

**Working scenario:**
1. Pi sends request → PC receives within 1-2s
2. PC processes image → 2-5s for simple, 10-15s for comprehensive
3. PC sends response → Pi receives within 1s
4. Total: 5-20 seconds depending on analysis type

**Timeout scenario (your current issue):**
1. Pi sends request → **Never reaches PC**
2. After 60 seconds → Timeout error
3. Cause: Network/firewall blocking

## ✅ Solution Checklist

Run these on Raspberry Pi:

```bash
# 1. Verify network
ping -c 3 192.168.1.3

# 2. Test port directly
timeout 5 bash -c "</dev/tcp/192.168.1.3/8080" && echo "Port OK" || echo "Port blocked"

# 3. Test HTTP
curl -s -m 10 http://192.168.1.3:8080/health

# 4. All tests pass? Run debug script
./network_debug.sh 192.168.1.3

# 5. Still failing? Try with longer timeout
# Edit script to use timeout=120 instead of 60
```

## 🆘 If Nothing Works

### Plan B: Use PC's Hostname

```python
# Instead of IP, try hostname
service = VisionAIService(pc_host="baobao-System-Product-Name.local")
```

### Plan C: Check Network Topology

```
Pi WiFi → Router → PC Ethernet
  ↓                    ↓
192.168.1.X      192.168.1.3

# Make sure both on same network!
```

### Plan D: Direct Ethernet Connection

If WiFi issues persist, connect Pi directly to PC via Ethernet cable and use:
- PC: `192.168.2.1`
- Pi: `192.168.2.2`

## 📞 Still Need Help?

Share output of:
```bash
# On Pi
./network_debug.sh 192.168.1.3 > debug.log 2>&1
cat debug.log

# And
ip addr show
ip route show
```

---

**Most Common Issue:** Firewall on PC - but we already fixed that!  
**Second Most Common:** Different network subnets  
**Solution:** Run `network_debug.sh` to identify the exact issue
