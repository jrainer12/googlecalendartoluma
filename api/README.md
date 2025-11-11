# API Module

REST API microservice that exposes Google Calendar events as Luma-compatible JSON payloads via HTTP endpoints.

## Features

- RESTful API with Flask
- Health check endpoint
- Fetch all upcoming events or specific event by ID
- Containerized with Docker/Podman
- Kubernetes-ready with Helm chart
- Horizontal Pod Autoscaler (HPA) support
- Ingress support for external access
- Development and production value files

## Prerequisites

- **Container runtime** (choose one):
  - **Podman** (recommended - free, open-source)
  - **Docker** (requires Docker Desktop on Windows/Mac)
- **Kubernetes** (minikube for local, or any K8s cluster for production)
- OR **Python 3.13+** (for local development)

## Configuration

The API can be configured using environment variables:

- `GCAL_EMBED_URL` - Google Calendar embed URL (required)
- `LUMA_CALENDAR_API_ID` - Luma calendar API ID (required)
- `COVER_URL` - Cover image URL for events
- `TINT_COLOR` - Color tint for events (hex format)
- `FONT_TITLE` - Font family for event titles
- `TIMEZONE_NAME` - Timezone for event processing (default: America/New_York)
- `LIMIT` - Maximum number of events to process (default: 5)
- `OUT_DIR` - Output directory for JSON files (default: luma_payloads)
- `PORT` - API server port (default: 5000)
- `HOST` - API server host (default: 0.0.0.0)

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (optional, defaults are provided):
```bash
export GCAL_EMBED_URL="your_embed_url"
export LUMA_CALENDAR_API_ID="your_api_id"
export PORT=5000
```

3. Run the API:
```bash
python api.py
```

4. Access the API:
- Health check: `http://localhost:5000/health`
- All events: `http://localhost:5000/events`
- Specific event: `http://localhost:5000/events/1`

## Container Deployment

### Using Podman (Recommended)

**Prerequisites:** See main README for Podman installation instructions.

1. Create a `.env` file with your configuration:
```bash
GCAL_EMBED_URL=https://calendar.google.com/calendar/embed?src=YOUR_CALENDAR_ID%40group.calendar.google.com&ctz=America%2FNew_York
LUMA_CALENDAR_API_ID=cal-YOUR_CALENDAR_API_ID
TIMEZONE_NAME=America/New_York
LIMIT=5
PORT=5000
```

2. Run with Podman Compose:
```bash
podman-compose up
```

**Using Podman directly:**

1. Build the image:
```bash
podman build -t googlecalendartoluma-api .
```

2. Run the container:
```bash
podman run --rm \
  -p 5000:5000 \
  -v $(pwd)/luma_payloads:/app/luma_payloads \
  -e GCAL_EMBED_URL="your_embed_url" \
  -e LUMA_CALENDAR_API_ID="your_api_id" \
  googlecalendartoluma-api
```

### Using Docker Compose

1. Create a `.env` file with your configuration (same as Podman)

2. Run with Docker Compose:
```bash
docker-compose up
```

3. Access the API at `http://localhost:5000`

### Using Docker directly

1. Build the image:
```bash
docker build -t googlecalendartoluma-api .
```

2. Run the container:
```bash
docker run --rm \
  -p 5000:5000 \
  -v $(pwd)/luma_payloads:/app/luma_payloads \
  -e GCAL_EMBED_URL="your_embed_url" \
  -e LUMA_CALENDAR_API_ID="your_api_id" \
  googlecalendartoluma-api
```

## Kubernetes Deployment with Helm

Deploy the API service to Kubernetes using Helm.

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
podman build -t googlecalendartoluma-api:latest .

# Save the image to a tar file
podman save googlecalendartoluma-api:latest -o googlecalendartoluma-api.tar

# Load the image into minikube
minikube image load googlecalendartoluma-api.tar

# Optional: Verify image is available
minikube image ls | grep googlecalendartoluma-api
```

**Alternative: Using Docker:**
```bash
# Set Docker environment to use minikube's Docker daemon
eval $(minikube docker-env)

# Build the API image
docker build -t googlecalendartoluma-api:latest .

# Optional: Verify image is available
minikube image ls | grep googlecalendartoluma-api
```

3. **Update configuration** for your environment:

**For Production/Default** - Edit `helm/googlecalendartoluma/values.yaml`:
```yaml
config:
  gcalEmbedUrl: "your_google_calendar_embed_url"
  lumaCalendarApiId: "your_luma_calendar_api_id"
  timezoneName: "America/New_York"
  limit: 5
```

**For Development** - Edit `helm/googlecalendartoluma/values-dev.yaml`:
```yaml
config:
  gcalEmbedUrl: "your_google_calendar_embed_url"
  lumaCalendarApiId: "your_luma_calendar_api_id"
  timezoneName: "America/New_York"
  limit: 3
```

4. **Install with Helm**:

**For Production/Default** (uses `values.yaml`):
```bash
helm install googlecalendartoluma ./helm/googlecalendartoluma
```

**For Development** (uses `values-dev.yaml`):
```bash
helm install googlecalendartoluma ./helm/googlecalendartoluma \
  -f ./helm/googlecalendartoluma/values-dev.yaml
```

5. **Wait for deployment** and check status:
```bash
kubectl get pods -l app.kubernetes.io/name=googlecalendartoluma-api
kubectl get svc googlecalendartoluma-api
```

6. **Access the API**:

**Option 1: Port forward (recommended for testing)**
```bash
kubectl port-forward svc/googlecalendartoluma-api 8080:80
# Then access: http://localhost:8080
```

**Option 2: Use minikube service (exposes to host)**
```bash
minikube service googlecalendartoluma-api
# This will open the service URL in your browser
```

**Option 3: Get the service URL**
```bash
minikube service googlecalendartoluma-api --url
# Use the returned URL to access the API
```

## API Endpoints

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

## Updating Configuration

**For Production/Default:**
```bash
# Edit values.yaml, then upgrade
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma

# Or override values directly
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma \
  --set config.limit=10 \
  --set config.timezoneName="America/Los_Angeles"
```

**For Development:**
```bash
# Edit values-dev.yaml, then upgrade with dev values
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma \
  -f ./helm/googlecalendartoluma/values-dev.yaml

# Or override values directly
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma \
  -f ./helm/googlecalendartoluma/values-dev.yaml \
  --set config.limit=10
```

## Managing the Deployment

```bash
# View Helm releases
helm list

# View deployment status
helm status googlecalendartoluma

# View logs
kubectl logs -l app.kubernetes.io/name=googlecalendartoluma-api

# Uninstall
helm uninstall googlecalendartoluma
```

## Enable/Disable Horizontal Pod Autoscaler (HPA)

**For Production** - Edit `helm/googlecalendartoluma/values.yaml`:
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

**For Development** - Edit `helm/googlecalendartoluma/values-dev.yaml` (autoscaling is disabled by default):
```yaml
autoscaling:
  enabled: false  # Disabled in dev
```

Then upgrade:
```bash
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma \
  -f ./helm/googlecalendartoluma/values-dev.yaml
```

**Or enable via command line:**
```bash
# Production
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=5

# Development
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma \
  -f ./helm/googlecalendartoluma/values-dev.yaml \
  --set autoscaling.enabled=true
```

**Check HPA status:**
```bash
kubectl get hpa
kubectl describe hpa googlecalendartoluma-api
```

## Enable Ingress (for external access)

**For Production** - Edit `helm/googlecalendartoluma/values.yaml`:
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

**For Development** - Edit `helm/googlecalendartoluma/values-dev.yaml`:
```yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: googlecalendartoluma-dev.local
      paths:
        - path: /
          pathType: Prefix
```

Then upgrade:
```bash
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma \
  -f ./helm/googlecalendartoluma/values-dev.yaml
```

## Environment-Specific Values

The Helm chart supports environment-specific configuration:

- **`values.yaml`** - Default/production values (used by default)
- **`values-dev.yaml`** - Development environment overrides

**Always specify the environment when installing or upgrading:**

```bash
# Production/Default (uses values.yaml)
helm install googlecalendartoluma ./helm/googlecalendartoluma
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma

# Development (uses values-dev.yaml)
helm install googlecalendartoluma ./helm/googlecalendartoluma \
  -f ./helm/googlecalendartoluma/values-dev.yaml
helm upgrade googlecalendartoluma ./helm/googlecalendartoluma \
  -f ./helm/googlecalendartoluma/values-dev.yaml
```

**The `values-dev.yaml` file overrides:**
- Image tag: `dev` (instead of `latest`)
- Event limit: `3` (instead of `5`)
- Autoscaling: `disabled` (instead of `enabled`)

**Note:** `values-dev.yaml` only contains differences from `values.yaml`. Helm merges them, so you only need to specify what's different for your environment.

## For Production

- Push the image to a container registry
- Update `values.yaml` to use the registry image
- Change `image.pullPolicy` to `Always` or `IfNotPresent`
- Consider using Secrets for sensitive configuration
- Enable Ingress for external access
- Configure HPA for automatic scaling
- Set appropriate resource limits and requests

## Cleanup

```bash
# Uninstall the Helm release
helm uninstall googlecalendartoluma

# Verify it's removed
helm list
kubectl get pods -l app.kubernetes.io/name=googlecalendartoluma-api
```

