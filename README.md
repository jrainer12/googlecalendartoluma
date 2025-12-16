# Google Calendar to Luma Sync

Syncs upcoming events from a Google Calendar to Luma event payloads. This project consists of two independent modules: an **API microservice** and a **CronJob script**.

## Project Structure

```
googlecalendartoluma/
├── api/                    # REST API microservice
│   ├── api.py             # FastAPI application
│   ├── app/               # Application code
│   │   ├── models/        # Data models
│   │   ├── services/      # Business logic services
│   │   └── util/          # Utilities (config, setup)
│   ├── resources/         # Application configuration YAML files
│   │   ├── application.yaml
│   │   └── application-prod.yaml
│   ├── values/            # Helm values files
│   │   ├── values.yaml
│   │   └── values-prod.yaml
│   ├── Dockerfile         # Container image for API
│   ├── docker-compose.yml # Local API deployment
│   ├── requirements.txt   # Python dependencies
│   └── README.md          # API module documentation
│
├── cronjob/               # Scheduled job script
│   ├── main.py           # Main script
│   ├── Dockerfile        # Container image for cronjob
│   ├── docker-compose.yml # Local cronjob deployment
│   ├── requirements.txt  # Python dependencies
│   ├── deployment/       # Kubernetes CronJob manifests
│   └── README.md         # CronJob module documentation
│
├── .github/              # GitHub Actions workflows
│   └── workflows/       # CI/CD pipeline definitions
│
└── README.md             # This file (overview)
```

**Note:** The Helm chart is maintained in a separate repository: [Reusable_Helm_Chart](https://github.com/jrainer12/Reusable_Helm_Chart)

## Features

- Fetches upcoming events from a Google Calendar ICS feed
- Converts events to Luma-compatible JSON payloads
- Configurable via environment variables
- Dockerized for easy deployment
- Kubernetes-ready (Helm chart for API, CronJob for scheduled tasks)
- REST API for on-demand event fetching
- Scheduled execution support

## Prerequisites

Choose one deployment method:

- **Container runtime** (choose one):
  - **Podman** (recommended - free, open-source, no daemon required)
  - **Docker** (requires Docker Desktop on Windows/Mac, or Docker Engine on Linux)
- **Kubernetes** (minikube for local, or any K8s cluster for production)
- OR **Python 3.13+** (for local development)

## Configuration

Both modules use the same environment variables:

- `GCAL_EMBED_URL` - Google Calendar embed URL (required)
- `LUMA_CALENDAR_API_ID` - Luma calendar API ID (required)
- `COVER_URL` - Cover image URL for events
- `TINT_COLOR` - Color tint for events (hex format)
- `FONT_TITLE` - Font family for event titles
- `TIMEZONE_NAME` - Timezone for event processing (default: America/New_York)
- `LIMIT` - Maximum number of events to process (default: 5)
- `OUT_DIR` - Output directory for JSON files (default: luma_payloads)

## Module Overview

### 📡 API Module

**TLDR:** REST API microservice that exposes Google Calendar events as Luma payloads via HTTP endpoints.

- **Use case:** On-demand event fetching via API calls
- **Deployment:** Docker/Podman or Kubernetes with Helm
- **Features:** Health checks, HPA support, Ingress support
- **Quick start:**
  ```bash
  cd api
  podman-compose up
  # Access at http://localhost:5000
  ```

📖 **Full documentation:** See [api/README.md](api/README.md)

### ⏰ CronJob Module

**TLDR:** Standalone script that generates Luma payloads and saves them to files. Designed for scheduled execution.

- **Use case:** Scheduled/automated event sync (e.g., daily at 2 AM)
- **Deployment:** Docker/Podman or Kubernetes CronJob
- **Features:** File-based output, event-name-based filenames
- **Quick start:**
  ```bash
  cd cronjob
  podman-compose up
  # Output files in luma_payloads/
  ```

📖 **Full documentation:** See [cronjob/README.md](cronjob/README.md)

## Podman Setup (Windows)

Podman is a free, open-source alternative to Docker. For detailed setup instructions, see the troubleshooting section below.

**Quick Setup:**

1. **Install Podman Desktop** (recommended) - handles everything automatically
   - Download from [podman-desktop.io](https://podman-desktop.io/)

2. **OR Install Podman CLI manually:**
   ```powershell
   # Enable WSL (run PowerShell as Administrator)
   wsl --install
   # Restart computer, then:
   podman machine init
   podman machine start
   ```

3. **Install podman-compose:**
   ```bash
   pip install podman-compose
   ```

**Common Podman Commands:**
- Start machine: `podman machine start`
- Stop machine: `podman machine stop`
- View containers: `podman ps`

## Quick Start Examples

### API Module (Local)

```bash
cd api
podman-compose up
# API available at http://localhost:5000
curl http://localhost:5000/health
curl http://localhost:5000/events
```

### CronJob Module (Local)

```bash
cd cronjob
podman-compose up
# Check output files
ls luma_payloads/
```

### API Module (Kubernetes)

The Helm chart is maintained in a separate repository. For Kubernetes deployment, see the [API README](api/README.md) for detailed instructions.

**Quick deployment:**
```bash
cd api
# Build and load image
podman build -t googlecalendartoluma-api:latest .
podman save googlecalendartoluma-api:latest -o api.tar
minikube image load api.tar

# Deploy with Helm (uses external chart from Reusable_Helm_Chart repo)
# See api/README.md for full deployment instructions
```

### CronJob Module (Kubernetes)

```bash
cd cronjob
# Build and load image
podman build -t googlecalendartoluma-cron:latest .
podman save googlecalendartoluma-cron:latest -o cron.tar
minikube image load cron.tar

# Deploy CronJob
kubectl apply -f deployment/configmap.yaml
kubectl apply -f deployment/cronjob.yaml
```

## Troubleshooting Podman on Windows

**Error: "Cannot connect to Podman" or "unable to connect to Podman socket"**

1. **If using Podman Desktop:** Make sure Podman Desktop is running and the VM is started
2. **If using Podman CLI:** Run `podman machine start`

**Error: "HCS_E_SERVICE_NOT_AVAILABLE" or "required feature is not installed"**

WSL (Windows Subsystem for Linux) or Virtual Machine Platform is not enabled. Fix it:

```powershell
# Run PowerShell as Administrator
wsl --install
# OR enable features manually:
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
# Then restart your computer
```

After restart, try `podman machine init` again.

**Error: "podman: command not found"**

Podman is not in your PATH. Either:
- Install Podman Desktop (recommended)
- Or add Podman installation directory to your system PATH (usually `C:\Program Files\RedHat\Podman\`)

**Verify Podman is Working:**

```powershell
podman ps
# Should return an empty list (no error means it's working)
```

## Cleanup

When you're done working with the application:

### Stop Podman Machine

```powershell
podman machine stop
```

### Stop Minikube

```bash
minikube stop
# Optional: Delete cluster
# minikube delete
```

### Remove Helm Deployments

```bash
# API module
helm uninstall googlecalendartoluma  # Release name (can be anything)

# CronJob module
kubectl delete cronjob googlecalendartoluma-cron
kubectl delete configmap googlecalendartoluma-cron-config
```

## Usage with Luma API

After generating payloads (via API or CronJob), send them to Luma:

```bash
curl 'https://api2.luma.com/event/create' \
  -H 'content-type: application/json' \
  -H 'accept: */*' \
  -H 'origin: https://luma.com' \
  -H 'referer: https://luma.com/' \
  -H 'x-luma-client-type: luma-web' \
  -b 'YOUR_FRESH_LUMA_COOKIES_HERE' \
  --data-binary '@luma_payloads/event-name.json'
```

## Module Documentation

For detailed instructions on each module:

- **API Module:** [api/README.md](api/README.md) - REST API deployment, Helm chart, endpoints
- **CronJob Module:** [cronjob/README.md](cronjob/README.md) - Scheduled jobs, Kubernetes CronJob
