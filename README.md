# Google Calendar to Luma Sync

Syncs upcoming events from a Google Calendar to Luma event payloads.

## Features

- Fetches upcoming events from a Google Calendar ICS feed
- Converts events to Luma-compatible JSON payloads
- Configurable via environment variables
- Dockerized for easy deployment
- Kubernetes-ready (Job and CronJob manifests included)
- Can be scheduled to run automatically

## Prerequisites

Choose one deployment method:

- **Container runtime** (choose one):
  - **Podman** (recommended - free, open-source, no daemon required)
  - **Docker** (requires Docker Desktop on Windows/Mac, or Docker Engine on Linux)
- **Kubernetes** (minikube for local, or any K8s cluster for production)
- OR **Python 3.13+** (for local development)

## Configuration

The application can be configured using environment variables:

- `GCAL_EMBED_URL` - Google Calendar embed URL (required)
- `LUMA_CALENDAR_API_ID` - Luma calendar API ID (required)
- `COVER_URL` - Cover image URL for events
- `TINT_COLOR` - Color tint for events (hex format)
- `FONT_TITLE` - Font family for event titles
- `TIMEZONE_NAME` - Timezone for event processing (default: America/New_York)
- `LIMIT` - Maximum number of events to process (default: 5)
- `OUT_DIR` - Output directory for JSON files (default: luma_payloads)

## Container Deployment

You can use either **Podman** (free, recommended) or **Docker**. Both work with the same files!

### Using Podman (Free Alternative)

Podman is a free, open-source alternative to Docker that doesn't require a daemon. It's fully compatible with Docker images and docker-compose files.

**Installation Steps:**

1. **Install Podman first** (required - `podman-compose` needs the Podman binary):
   - **Windows** (Recommended: Podman Desktop):
     - Download and install [Podman Desktop](https://podman-desktop.io/) - this handles VM setup automatically
     - OR install Podman CLI and manually set up the VM (see "Complete Podman Setup for Windows" below)
   - **Mac**: `brew install podman` then run `podman machine init` and `podman machine start`
   - **Linux**: `sudo apt install podman` (Ubuntu/Debian) or `sudo dnf install podman` (Fedora/RHEL)

2. **Install podman-compose** (Python wrapper - install after Podman):
```bash
pip install podman-compose
```

### Complete Podman Setup for Windows (CLI)

If you're using Podman CLI on Windows, follow these steps in order:

**Step 1: Enable WSL (Windows Subsystem for Linux)**
```powershell
# Run PowerShell as Administrator, then:
wsl --install
# Or if WSL is already installed, enable Virtual Machine Platform:
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
# Restart your computer after running these commands
```

**Step 2: Initialize Podman Machine** (first time only)
```powershell
podman machine init
```

**Step 3: Start Podman Machine**
```powershell
podman machine start
```

**Step 4: Verify Podman is Working**
```powershell
podman ps
# Should return an empty list (no error means it's working)
```

**Step 5: Check Machine Status**
```powershell
podman machine list
```

**Common Podman Commands:**

- **Start machine**: `podman machine start`
- **Stop machine**: `podman machine stop`
- **Restart machine**: `podman machine stop` then `podman machine start`
- **List machines**: `podman machine list`
- **Remove machine**: `podman machine rm` (removes the default machine)
- **Check Podman version**: `podman --version`
- **View running containers**: `podman ps`
- **View all containers**: `podman ps -a`

**Using Podman Compose:**

1. Create a `.env` file with your configuration (same as Docker):
```bash
GCAL_EMBED_URL=https://calendar.google.com/calendar/embed?src=YOUR_CALENDAR_ID%40group.calendar.google.com&ctz=America%2FNew_York
LUMA_CALENDAR_API_ID=cal-YOUR_CALENDAR_API_ID
TIMEZONE_NAME=America/New_York
LIMIT=5
```

2. Run with Podman Compose:
```bash
podman-compose up
```

**Using Podman directly:**

1. Build the image:
```bash
podman build -t googlecalendartoluma .
```

2. Run the container:
```bash
podman run --rm \
  -v $(pwd)/luma_payloads:/app/luma_payloads \
  -e GCAL_EMBED_URL="your_embed_url" \
  -e LUMA_CALENDAR_API_ID="your_api_id" \
  googlecalendartoluma
```

### Using Docker Compose (Recommended)

1. Create a `.env` file with your configuration:
```bash
GCAL_EMBED_URL=https://calendar.google.com/calendar/embed?src=YOUR_CALENDAR_ID%40group.calendar.google.com&ctz=America%2FNew_York
LUMA_CALENDAR_API_ID=cal-YOUR_CALENDAR_API_ID
TIMEZONE_NAME=America/New_York
LIMIT=5
```

2. Run with Docker Compose:
```bash
docker-compose up
```

3. Generated JSON files will be saved in the `luma_payloads/` directory on your host machine.

### Using Docker directly

1. Build the image:
```bash
docker build -t googlecalendartoluma .
```

2. Run the container:
```bash
docker run --rm \
  -v $(pwd)/luma_payloads:/app/luma_payloads \
  -e GCAL_EMBED_URL="your_embed_url" \
  -e LUMA_CALENDAR_API_ID="your_api_id" \
  googlecalendartoluma
```

**Note:** On Windows, replace `$(pwd)` with `%cd%` in PowerShell or use the full path.

### Kubernetes Deployment with Helm (Minikube)

Deploy the API service to Kubernetes using Helm. The service exposes a REST API to fetch Google Calendar events as Luma payloads.

**Prerequisites:**
- [Minikube](https://minikube.sigs.k8s.io/docs/start/) installed and running
- [Helm](https://helm.sh/docs/intro/install/) installed (v3.x)
- `kubectl` configured to use minikube

**Setup Steps:**

1. **Start minikube** (if not already running):
```bash
minikube start
```

2. **Build the image and load it into minikube**:

**Using Podman:**
```bash
# Build the API image with Podman
podman build -f Dockerfile.api -t googlecalendartoluma:latest .

# Save the image to a tar file
podman save googlecalendartoluma:latest -o googlecalendartoluma.tar

# Load the image into minikube
minikube image load googlecalendartoluma.tar

# Optional: Verify image is available
minikube image ls | grep googlecalendartoluma
```

**Alternative: Using Docker (if you have Docker available):**
```bash
# Set Docker environment to use minikube's Docker daemon
eval $(minikube docker-env)

# Build the API image
docker build -f Dockerfile.api -t googlecalendartoluma:latest .

# Optional: Verify image is available
minikube image ls | grep googlecalendartoluma
```

3. **Update configuration** in `helm/googlecalendartoluma/values.yaml`:
```yaml
config:
  gcalEmbedUrl: "your_google_calendar_embed_url"
  lumaCalendarApiId: "your_luma_calendar_api_id"
  timezoneName: "America/New_York"
  limit: 5
```

4. **Install with Helm**:
```bash
helm install googlecalendartoluma ./helm/googlecalendartoluma
```

5. **Wait for deployment** and check status:
```bash
kubectl get pods -l app.kubernetes.io/name=googlecalendartoluma
kubectl get svc googlecalendartoluma
```

6. **Access the API**:

**Option 1: Port forward (recommended for testing)**
```bash
kubectl port-forward svc/googlecalendartoluma 8080:80
# Then access: http://localhost:8080
```

**Option 2: Use minikube service (exposes to host)**
```bash
minikube service googlecalendartoluma
# This will open the service URL in your browser
```

**Option 3: Get the service URL**
```bash
minikube service googlecalendartoluma --url
# Use the returned URL to access the API
```

**API Endpoints:**

- `GET /` - API information
- `GET /health` - Health check endpoint
- `GET /events` - Get all upcoming events as Luma payloads
- `GET /events/<id>` - Get a specific event by ID (1-indexed)

**Example API Calls:**

```bash
# Health check
curl http://localhost:8080/health

# Get all events
curl http://localhost:8080/events

# Get specific event (ID 1)
curl http://localhost:8080/events/1

# Get API info
curl http://localhost:8080/
```

**Response Format:**

```json
{
  "success": true,
  "count": 3,
  "events": [
    {
      "name": "Event Name",
      "start_at": "2024-01-15T10:00:00.000Z",
      "duration_interval": "PT2H",
      ...
    }
  ],
  "timezone": "America/New_York"
}
```

**Updating Configuration:**

```bash
# Edit values.yaml, then upgrade
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma

# Or override values directly
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma \
  --set config.limit=10 \
  --set config.timezoneName="America/Los_Angeles"
```

**Managing the Deployment:**

```bash
# View Helm releases
helm list

# View deployment status
helm status googlecalendartoluma

# View logs
kubectl logs -l app.kubernetes.io/name=googlecalendartoluma

# Uninstall
helm uninstall googlecalendartoluma
```

**Enable/Disable Horizontal Pod Autoscaler (HPA):**

Edit `helm/googlecalendartoluma/values.yaml`:

```yaml
autoscaling:
  enabled: true  # Set to true to enable HPA
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80
```

Then upgrade:
```bash
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma
```

**Or enable via command line:**
```bash
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=5
```

**Check HPA status:**
```bash
kubectl get hpa
kubectl describe hpa googlecalendartoluma
```

**Enable Ingress (for external access):**

Edit `helm/googlecalendartoluma/values.yaml`:

```yaml
ingress:
  enabled: true
  className: "nginx"  # or your ingress controller class
  hosts:
    - host: googlecalendartoluma.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  # Optional: TLS configuration
  # tls:
  #   - secretName: googlecalendartoluma-tls
  #     hosts:
  #       - googlecalendartoluma.yourdomain.com
```

Then upgrade:
```bash
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma
```

**For Production:**

- Push the image to a container registry
- Update `values.yaml` to use the registry image
- Change `image.pullPolicy` to `Always` or `IfNotPresent`
- Consider using Secrets for sensitive configuration
- Enable Ingress for external access (see above)

### Troubleshooting Podman on Windows

**Error: "Cannot connect to Podman" or "unable to connect to Podman socket"**

1. **If using Podman Desktop**: Make sure Podman Desktop is running and the VM is started (check the Desktop app)

2. **If using Podman CLI**: See "Complete Podman Setup for Windows (CLI)" section above for full setup instructions.

**Error: "HCS_E_SERVICE_NOT_AVAILABLE" or "required feature is not installed"**

This means WSL (Windows Subsystem for Linux) or Virtual Machine Platform is not enabled. Fix it with:

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

**Quick Reference - Managing the Podman Machine:**

- **Start machine**: `podman machine start`
- **Stop machine**: `podman machine stop` (use this when done to free up resources)
- **Check status**: `podman machine list`
- **View containers**: `podman ps` (running) or `podman ps -a` (all)

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (optional, defaults are provided):
```bash
export GCAL_EMBED_URL="your_embed_url"
export LUMA_CALENDAR_API_ID="your_api_id"
```

3. Run the script:
```bash
python main.py
```

## Output

The script generates JSON files in the `luma_payloads/` directory, one per event:
- `event_1.json`
- `event_2.json`
- etc.

Each file contains a Luma-compatible event payload that can be sent to the Luma API.

## Usage with Luma API

After generating the payloads, you can send them to Luma using curl:

```bash
curl 'https://api2.luma.com/event/create' \
  -H 'content-type: application/json' \
  -H 'accept: */*' \
  -H 'origin: https://luma.com' \
  -H 'referer: https://luma.com/' \
  -H 'x-luma-client-type: luma-web' \
  -b 'YOUR_FRESH_LUMA_COOKIES_HERE' \
  --data-binary '@luma_payloads/event_1.json'
```
