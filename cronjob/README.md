# CronJob Module

Standalone script that fetches Google Calendar events and generates Luma-compatible JSON payloads. Designed to run as a scheduled task (cronjob) or one-time job.

## Features

- Fetches upcoming events from a Google Calendar ICS feed
- Converts events to Luma-compatible JSON payloads
- Generates files named after event summaries (slugified)
- Configurable via environment variables
- Dockerized for easy deployment
- Kubernetes CronJob support for scheduled execution
- Can run as a one-time job or scheduled task

## Prerequisites

- **Container runtime** (choose one):
  - **Podman** (recommended - free, open-source)
  - **Docker** (requires Docker Desktop on Windows/Mac)
- **Kubernetes** (minikube for local, or any K8s cluster for production)
- OR **Python 3.13+** (for local development)

## Configuration

The script can be configured using environment variables:

- `GCAL_EMBED_URL` - Google Calendar embed URL (required)
- `LUMA_CALENDAR_API_ID` - Luma calendar API ID (required)
- `COVER_URL` - Cover image URL for events
- `TINT_COLOR` - Color tint for events (hex format)
- `FONT_TITLE` - Font family for event titles
- `TIMEZONE_NAME` - Timezone for event processing (default: America/New_York)
- `LIMIT` - Maximum number of events to process (default: 5)
- `OUT_DIR` - Output directory for JSON files (default: luma_payloads)

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
- Files are named based on event summaries (slugified)
- Example: `club-meeting.json`, `holiday-party.json`
- If duplicate names exist, a numeric suffix is added: `event-name-1.json`

Each file contains a Luma-compatible event payload that can be sent to the Luma API.

## Container Deployment

### Using Podman (Recommended)

**Prerequisites:** See main README for Podman installation instructions.

1. Create a `.env` file with your configuration:
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
podman build -t googlecalendartoluma-cron .
```

2. Run the container:
```bash
podman run --rm \
  -v $(pwd)/luma_payloads:/app/luma_payloads \
  -e GCAL_EMBED_URL="your_embed_url" \
  -e LUMA_CALENDAR_API_ID="your_api_id" \
  googlecalendartoluma-cron
```

### Using Docker Compose

1. Create a `.env` file with your configuration (same as Podman)

2. Run with Docker Compose:
```bash
docker-compose up
```

3. Generated JSON files will be saved in the `luma_payloads/` directory on your host machine.

### Using Docker directly

1. Build the image:
```bash
docker build -t googlecalendartoluma-cron .
```

2. Run the container:
```bash
docker run --rm \
  -v $(pwd)/luma_payloads:/app/luma_payloads \
  -e GCAL_EMBED_URL="your_embed_url" \
  -e LUMA_CALENDAR_API_ID="your_api_id" \
  googlecalendartoluma-cron
```

**Note:** On Windows, replace `$(pwd)` with `%cd%` in PowerShell or use the full path.

## Kubernetes Deployment

Deploy the script as a Kubernetes CronJob for scheduled execution.

**Prerequisites:**
- [Minikube](https://minikube.sigs.k8s.io/docs/start/) installed and running
- `kubectl` configured to use minikube

**Setup Steps:**

1. **Start minikube** (if not already running):
```bash
minikube start
```

2. **Build the image and load it into minikube**:

**Using Podman:**
```bash
# Build the cronjob image with Podman
podman build -t googlecalendartoluma-cron:latest .

# Save the image to a tar file
podman save googlecalendartoluma-cron:latest -o googlecalendartoluma-cron.tar

# Load the image into minikube
minikube image load googlecalendartoluma-cron.tar

# Optional: Verify image is available
minikube image ls | grep googlecalendartoluma-cron
```

**Alternative: Using Docker:**
```bash
# Set Docker environment to use minikube's Docker daemon
eval $(minikube docker-env)

# Build the cronjob image
docker build -t googlecalendartoluma-cron:latest .

# Optional: Verify image is available
minikube image ls | grep googlecalendartoluma-cron
```

3. **Update configuration** in `deployment/configmap.yaml`:
```yaml
data:
  GCAL_EMBED_URL: "your_google_calendar_embed_url"
  LUMA_CALENDAR_API_ID: "your_luma_calendar_api_id"
  TIMEZONE_NAME: "America/New_York"
  LIMIT: "5"
```

4. **Apply the ConfigMap**:
```bash
kubectl apply -f deployment/configmap.yaml
```

5. **Apply the CronJob**:
```bash
kubectl apply -f deployment/cronjob.yaml
```

6. **Check CronJob status**:
```bash
# View the CronJob
kubectl get cronjob googlecalendartoluma-cron

# View scheduled jobs
kubectl get jobs

# View job pods
kubectl get pods -l app=googlecalendartoluma-cron

# View logs from the most recent job
kubectl logs -l app=googlecalendartoluma-cron --tail=50
```

## CronJob Schedule

The default schedule in `deployment/cronjob.yaml` is set to run daily at 2 AM:
```yaml
schedule: "0 2 * * *"  # Cron format: minute hour day month weekday
```

**Common Cron Schedule Examples:**
- `"0 2 * * *"` - Daily at 2 AM
- `"0 */6 * * *"` - Every 6 hours
- `"0 9 * * 1"` - Every Monday at 9 AM
- `"*/30 * * * *"` - Every 30 minutes

To change the schedule, edit `deployment/cronjob.yaml` and reapply:
```bash
kubectl apply -f deployment/cronjob.yaml
```

## Running a One-Time Job

You can manually trigger a job from the CronJob:

```bash
# Create a one-time job from the CronJob
kubectl create job --from=cronjob/googlecalendartoluma-cron manual-run-$(date +%s)

# Check the job status
kubectl get jobs

# View logs
kubectl logs -l app=googlecalendartoluma-cron --tail=50
```

## Accessing Output Files

The CronJob writes output files to a volume. By default, it uses a hostPath volume at `/tmp/luma_payloads` on the minikube node.

**To access files from minikube:**

1. SSH into the minikube node:
```bash
minikube ssh
```

2. Navigate to the output directory:
```bash
cd /tmp/luma_payloads
ls -la
```

**To use a PersistentVolume instead:**

1. Create a PersistentVolumeClaim and update `deployment/cronjob.yaml` to use it instead of hostPath.

## Updating Configuration

1. Edit `deployment/configmap.yaml` with new values
2. Apply the updated ConfigMap:
```bash
kubectl apply -f deployment/configmap.yaml
```
3. The next scheduled run will use the new configuration

## Managing the CronJob

```bash
# View CronJob details
kubectl describe cronjob googlecalendartoluma-cron

# Suspend the CronJob (stops scheduling new jobs)
kubectl patch cronjob googlecalendartoluma-cron -p '{"spec":{"suspend":true}}'

# Resume the CronJob
kubectl patch cronjob googlecalendartoluma-cron -p '{"spec":{"suspend":false}}'

# Delete the CronJob (does not delete completed jobs)
kubectl delete cronjob googlecalendartoluma-cron

# Delete the ConfigMap
kubectl delete configmap googlecalendartoluma-cron-config
```

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
  --data-binary '@luma_payloads/event-name.json'
```

## Cleanup

```bash
# Delete the CronJob
kubectl delete cronjob googlecalendartoluma-cron

# Delete the ConfigMap
kubectl delete configmap googlecalendartoluma-cron-config

# Delete completed jobs (optional)
kubectl delete jobs -l app=googlecalendartoluma-cron
```

