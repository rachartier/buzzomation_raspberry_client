# Buzzer System - Raspberry Pi Client

A Streamlit application that runs on Raspberry Pi to manage physical buzzers for the buzzer game system.

## Installation

### Docker Deployment (Recommended for Raspberry Pi)

The easiest way to deploy on Raspberry Pi is using Docker:

1. **Prerequisites**: Install Docker and Docker Compose on your Raspberry Pi:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt update
sudo apt install docker-compose-plugin

# Reboot to apply group changes
sudo reboot
```

2. **Clone and deploy**:
```bash
git clone https://github.com/rachartier/buzzomation_raspberry_client
cd raspberry_client
docker compose up -d
```

3. **Access the application**:
   - Open http://your-raspberry-pi-ip:8501 in your browser
   - The application will be available and ready to configure

