# API Module

REST API microservice that exposes Google Calendar events as Luma-compatible JSON payloads via HTTP endpoints.

## Features

- RESTful API with FastAPI
- Automatic Swagger/OpenAPI documentation
- Interactive API testing via Swagger UI
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

The API can be configured using:

1. **YAML configuration files** in `resources/` directory:
   - `resources/application.yaml` - Base configuration
   - `resources/application-prod.yaml` - Production overrides

2. **Environment variables** (override YAML config):
   - `GCAL_EMBED_URL` - Google Calendar embed URL
   - `LUMA_CALENDAR_API_ID` - Luma calendar API ID
   - `COVER_URL` - Cover image URL for events
   - `TINT_COLOR` - Color tint for events (hex format)
   - `FONT_TITLE` - Font family for event titles
   - `TIMEZONE_NAME` - Timezone for event processing (default: America/New_York)
   - `LIMIT` - Maximum number of events to process (default: 5)
   - `OUT_DIR` - Output directory for JSON files (default: luma_payloads)
  - `PORT` - API server port (default: 5000)
  - `HOST` - API server host (default: 0.0.0.0)
  - `DEPLOYMENT_PROFILE` - Deployment profile (default: dev, used to load `application-{profile}.yaml`)
  - `OTEL_TRACING_ENABLED` - Enable OpenTelemetry tracing (default: false)
  - `OTEL_EXPORTER_OTLP_ENDPOINT` - OTLP endpoint (e.g. http://localhost:4318 or grpc://localhost:4317)
  - `OTEL_EXPORTER_OTLP_PROTOCOL` - OTLP protocol (`http/protobuf` or `grpc`)
  - `OTEL_SERVICE_NAME` - Service name reported in traces (default: googlecalendartoluma-api)
  - `OTEL_EXCLUDED_URLS` - Regex for excluded URLs (default: /health|/health/)

### Spring Cloud Config

The API supports loading configuration from Spring Cloud Config Server. Configure in `resources/application.yaml` or `resources/application-prod.yaml`:

```yaml
app:
  enable_spring_config: true  # Set to true to enable Spring Cloud Config
  spring_cloud_config_name: "api-google-calendar-to-luma"
  spring_cloud_config_auth_type: "jwt"  # Options: "jwt" or "basic"
  spring_cloud_config_service_url: "http://spring-cloud-config-generic-api:8888/backend/spring-cloud-config-server"
```

**For JWT authentication**, set these environment variables:
- `SPRING_TENANT` - Azure AD tenant ID
- `SPRING_CLIENT_ID` - Azure AD client ID
- `SPRING_CLIENT_SECRET` - Azure AD client secret
- `SPRING_SCOPE` - OAuth2 scope

**For Basic authentication**, set these environment variables:
- `SPRING_CONFIG_USERNAME` - Basic auth username
- `SPRING_CONFIG_PASSWORD` - Basic auth password

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

### OpenTelemetry Tracing

Enable tracing to send spans to Grafana Tempo (or any OTLP collector):

```bash
export OTEL_TRACING_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_SERVICE_NAME=googlecalendartoluma-api
```

3. Run the API:
```bash
python api.py
```

4. Access the API:
- **Swagger UI (Interactive API docs)**: `http://localhost:5000/docs`
- **ReDoc (Alternative API docs)**: `http://localhost:5000/redoc`
- Health check: `http://localhost:5000/health`
- All events: `http://localhost:5000/events`
- Specific event: `http://localhost:5000/events/1`

## Running Tests

The project includes unit tests with coverage reporting. Tests are automatically run in CI and will fail if coverage drops below 80%.

### Prerequisites

Tests require the same dependencies as the application. Make sure you've installed them:
```bash
pip install -r requirements.txt
```

### Running Tests Locally

**Run all tests:**
```bash
cd api
pytest
```

**Run tests with verbose output:**
```bash
pytest -v
```

**Run tests for a specific file:**
```bash
pytest tests/test_payloadbuilder.py
```

**Run a specific test:**
```bash
pytest tests/test_payloadbuilder.py::TestToDt::test_datetime_with_timezone
```

### Coverage Reports

**View coverage report in terminal:**
```bash
pytest
# Coverage summary is displayed at the end
```

**Generate HTML coverage report:**
```bash
pytest
# HTML report is generated in htmlcov/
# Open htmlcov/index.html in your browser
```

**Generate XML coverage report (for CI):**
```bash
pytest
# XML report is generated as coverage.xml
```

**View coverage with missing lines:**
```bash
pytest --cov-report=term-missing
```

### Test Configuration

- Test files are located in `tests/` directory
- Coverage threshold: **80% minimum** (configured in `pytest.ini`)
- Coverage reports: HTML (`htmlcov/`), XML (`coverage.xml`), and terminal output
- Test results: JUnit XML (`junit.xml`) for CI integration

### CI Integration

Tests run automatically in GitHub Actions on every workflow run:
- Tests must pass
- Coverage must be ≥ 80% or the build fails
- Coverage reports are uploaded to Codecov
- Test results are published as artifacts

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

**For Production/Default** - Edit `values/values.yaml`:
```yaml
config:
  gcalEmbedUrl: "your_google_calendar_embed_url"
  lumaCalendarApiId: "your_luma_calendar_api_id"
  timezoneName: "America/New_York"
  limit: 5
```

**For Production** - Edit `values/values-prod.yaml`:
```yaml
config:
  gcalEmbedUrl: "your_google_calendar_embed_url"
  lumaCalendarApiId: "your_luma_calendar_api_id"
  timezoneName: "America/New_York"
  limit: 5
```

4. **Install with Helm**:

The Helm chart is maintained in a separate repository: [Reusable_Helm_Chart](https://github.com/jrainer12/Reusable_Helm_Chart)

**For Production** (uses `values/values-prod.yaml`):
```bash
# Clone or reference the helm chart repo
helm install googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml \
  -f ./values/values-prod.yaml
```

**For Development** (uses `values/values.yaml`):
```bash
helm install googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml
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
- `GET /events/{id}` - Get a specific event by ID (1-indexed)
- `GET /docs` - Swagger UI interactive documentation
- `GET /redoc` - ReDoc alternative documentation

**Note:** FastAPI automatically generates interactive API documentation. Visit `/docs` to explore and test all endpoints directly from your browser!

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

**Or use the Swagger UI:**
- Open `http://localhost:8080/docs` in your browser
- Click on any endpoint to expand it
- Click "Try it out" to test the endpoint directly
- View request/response schemas and examples

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

**For Production:**
```bash
# Edit values/values.yaml and values/values-prod.yaml, then upgrade
helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml \
  -f ./values/values-prod.yaml

# Or override values directly
helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml \
  -f ./values/values-prod.yaml \
  --set config.limit=10 \
  --set config.timezoneName="America/Los_Angeles"
```

**For Development:**
```bash
# Edit values/values.yaml, then upgrade
helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml

# Or override values directly
helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml \
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

**For Production** - Edit `values/values-prod.yaml`:
```yaml
autoscaling:
  enabled: true  # Set to true to enable HPA
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80
```

Then upgrade:
```bash
helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml \
  -f ./values/values-prod.yaml
```

**For Development** - Edit `values/values.yaml` (autoscaling can be disabled):
```yaml
autoscaling:
  enabled: false  # Disabled in dev
```

Then upgrade:
```bash
helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml
```

**Or enable via command line:**
```bash
# Production
helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml \
  -f ./values/values-prod.yaml \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=5

# Development
helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml \
  --set autoscaling.enabled=true
```

**Check HPA status:**
```bash
kubectl get hpa
kubectl describe hpa googlecalendartoluma-api
```

## Enable Ingress (for external access)

**For Production** - Edit `values/values-prod.yaml`:
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
helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml \
  -f ./values/values-prod.yaml
```

**For Development** - Edit `values/values.yaml`:
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
helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml
```

## Environment-Specific Values

The Helm chart supports environment-specific configuration:

- **`values/values.yaml`** - Base/default values
- **`values/values-prod.yaml`** - Production environment overrides

**Always specify the environment when installing or upgrading:**

```bash
# Production (uses values.yaml + values-prod.yaml)
helm install googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml \
  -f ./values/values-prod.yaml

helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml \
  -f ./values/values-prod.yaml

# Development (uses values.yaml only)
helm install googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml

helm upgrade googlecalendartoluma ./path-to-helm-chart \
  -f ./values/values.yaml
```

**The `values-prod.yaml` file typically overrides:**
- Image pull secrets for GHCR
- Autoscaling settings
- Gateway/Ingress configuration
- Environment-specific config values

**Note:** `values-prod.yaml` only contains differences from `values.yaml`. Helm merges them, so you only need to specify what's different for your environment.

## Project Structure

```
api/
├── api.py                    # FastAPI application entry point
├── app/                      # Application code
│   ├── models/              # Data models
│   ├── services/            # Business logic services
│   └── util/                # Utilities (config, setup)
├── resources/                # Application configuration YAML files
│   ├── application.yaml     # Base configuration
│   └── application-prod.yaml # Production overrides
├── values/                   # Helm values files
│   ├── values.yaml          # Base Helm values
│   └── values-prod.yaml     # Production Helm values
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Local development setup
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

**Note:** The Helm chart is maintained in a separate repository: [Reusable_Helm_Chart](https://github.com/jrainer12/Reusable_Helm_Chart)

## For Production

- Push the image to a container registry (GHCR, Docker Hub, etc.)
- Update `values/values.yaml` to use the registry image
- Change `image.pullPolicy` to `Always` or `IfNotPresent`
- Configure `imagePullSecrets` in `values/values-prod.yaml` for private registries
- Consider using Secrets for sensitive configuration
- Enable Gateway/Ingress for external access
- Configure HPA for automatic scaling
- Set appropriate resource limits and requests
- Configure Spring Cloud Config if needed (see Configuration section)

## Cleanup

```bash
# Uninstall the Helm release
helm uninstall googlecalendartoluma

# Verify it's removed
helm list
kubectl get pods -l app.kubernetes.io/name=googlecalendartoluma-api
```

