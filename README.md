# Buzzer System - Raspberry Pi Client

### Prerequisites

First, make sure your Raspberry Pi has Docker installed:

```bash
# Install Docker (one-time setup)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt update
sudo apt install docker-compose-plugin

# Reboot to apply changes
sudo reboot
```

### Get the Project

```bash
git clone https://github.com/rachartier/buzzomation_raspberry_client
cd raspberry_client
```

## Choose Your Interface

You have two options to run the buzzer system:
- **GUI (Web Interface)**: for more modern raspberry (Raspberry 5)
- **CLI (Command Line Interface)**: for older models or if you prefer terminal control

### Option 1: GUI (Web Interface)

```bash
# Start only the web interface
docker compose up -d gui
```

**Access your buzzer dashboard:**
- Open your web browser
- Go to `http://your-raspberry-pi-ip:8501`
- Start configuring your buzzers with the friendly web interface

### Option 2: CLI (Command Line)

```bash
docker compose up -d cli
```

**Access the CLI:**
```bash
docker compose exec cli python -m raspberry_buzzer.cli
```


## GPIO Configuration

The system needs access to your Pi's GPIO pins. The Docker setup handles this automatically, but make sure:

- Your buzzers are connected to GPIO pins (not power pins!)
- Each player uses a unique GPIO pin
- Your Pi user is in the `gpio` group (Docker setup does this)

##  Troubleshooting

### GPIO Permission Issues
```bash
# Check GPIO access
ls -la /dev/gpiomem

# Should show: crw-rw---- 1 root gpio
# If not, run: sudo usermod -aG gpio $USER
```

### Can't Access Web Interface
- Make sure port 8501 isn't blocked by firewall
- Check your Pi's IP address: `hostname -I`
- Try accessing from the Pi itself: `http://localhost:8501`

### Buzzers Not Working
- Verify GPIO pin connections
- Test with a simple LED first
- Check logs: `docker compose logs`

### Container Won't Start
```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker if needed
sudo systemctl restart docker
```

