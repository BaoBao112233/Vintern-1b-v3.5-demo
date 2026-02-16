# Cách cài systemd service (tự động start khi boot)

## Install service

```bash
# Copy service file to systemd
sudo cp vintern-inference.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable vintern-inference

# Start service now
sudo systemctl start vintern-inference

# Check status
sudo systemctl status vintern-inference
```

## Manage service

```bash
# Start
sudo systemctl start vintern-inference

# Stop
sudo systemctl stop vintern-inference

# Restart
sudo systemctl restart vintern-inference

# View logs
sudo journalctl -u vintern-inference -f

# Disable auto-start
sudo systemctl disable vintern-inference
```

## Uninstall

```bash
sudo systemctl stop vintern-inference
sudo systemctl disable vintern-inference
sudo rm /etc/systemd/system/vintern-inference.service
sudo systemctl daemon-reload
```
