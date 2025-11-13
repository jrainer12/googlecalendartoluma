# GitHub Actions Workflows

This directory contains GitHub Actions workflows for building and deploying the Google Calendar to Luma Sync project.

## Workflows

### `build-and-deploy.yml`

Main workflow for building Docker images and deploying to Kubernetes environments.

**Features:**
- Multi-module support (api, cronjob)
- Multi-environment deployment (dev, prod, etc.)
- Docker image building with caching
- Helm deployment for API module
- Kubernetes CronJob deployment for cronjob module
- Optional unit test execution
- Deployment summary

**Usage:**

1. **Manual Trigger:**
   - Go to Actions → Build and Deploy All Environments → Run workflow
   - Configure inputs:
     - **modules**: Comma-separated list (e.g., `api,cronjob`)
     - **environments**: Comma-separated list (e.g., `dev,prod`)
     - **releaseBuild**: Boolean for release builds
     - **runUnitTests**: Boolean to run unit tests
     - **imageRegistry**: Container registry (default: `ghcr.io`)
     - **imageNamespace**: Image namespace (default: repository owner)

2. **Required Secrets:**
   - `GITHUB_TOKEN` (automatically provided for GHCR)
   - `KUBECONFIG`: Base64-encoded kubeconfig file for Kubernetes access
   - For Azure ACR: `ACR_USERNAME`, `ACR_PASSWORD`
   - For Azure AKS: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AKS_RG`, `AKS_CLUSTER`

3. **Optional Secrets (for advanced features):**
   - `SONAR_TOKEN`: For SonarQube scanning
   - Azure credentials for AKS deployment

**Workflow Steps:**

1. **Prepare_Data**: Creates matrix JSON for modules and environments
2. **Docker_Build**: Builds Docker images for each module
3. **Deploy_To_Kubernetes**: Deploys to Kubernetes using Helm (API) or kubectl (CronJob)
4. **Summary**: Prints deployment summary

**Module-Specific Behavior:**

- **API Module**: Deploys using Helm chart from `api/helm/googlecalendartoluma/`
  - Uses `values-dev.yaml` for `dev` environment
  - Uses `values.yaml` for other environments
  - Sets image repository and tag dynamically

- **CronJob Module**: Deploys using kubectl apply
  - Updates image in `cronjob/deployment/cronjob.yaml`
  - Applies ConfigMap and CronJob manifests

**Customization:**

To add Azure AKS deployment, uncomment the Azure login steps in the `Deploy_To_Kubernetes` job and configure the secrets.

To add security scanning, uncomment the Trivy or other scanner steps in the `Docker_Build` job.

## Environment Setup

### GitHub Container Registry (GHCR)

Default registry. No additional setup needed - uses `GITHUB_TOKEN` automatically.

### Azure Container Registry (ACR)

1. Add secrets: `ACR_USERNAME`, `ACR_PASSWORD`
2. Uncomment Azure login step in workflow
3. Update `imageRegistry` input to your ACR URL

### Kubernetes Cluster

**For Cloud Clusters (Azure AKS, GKE, EKS, etc.):**
1. Export your kubeconfig: `cat ~/.kube/config | base64`
2. Add as secret: `KUBECONFIG` (base64-encoded)
3. Or use Azure AKS credentials (uncomment Azure steps)

**For Local Minikube:**
⚠️ **GitHub Actions cannot directly deploy to local minikube** because it runs on cloud runners that can't access your local machine.

**Options for local deployment:**

1. **Use Self-Hosted Runner** (Recommended for local testing):
   ```bash
   # Install GitHub Actions runner on your local machine
   mkdir actions-runner && cd actions-runner
   curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
   tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
   ./config.sh --url https://github.com/YOUR_USERNAME/YOUR_REPO --token YOUR_TOKEN
   ./run.sh
   ```
   Then update workflow to use `runs-on: self-hosted` for the deployment job.

2. **Use `act` to run workflows locally**:
   ```bash
   # Install act: https://github.com/nektos/act
   brew install act  # macOS
   # or download from releases
   
   # Run the workflow locally
   act workflow_dispatch
   ```

3. **Manual deployment** (simpler for local):
   - Use the manual commands in the module READMEs
   - Build images locally and load into minikube
   - Deploy with Helm/kubectl manually

For production, use a cloud Kubernetes cluster (AKS, GKE, EKS) that GitHub Actions can access.

## Example Workflow Runs

**Build and deploy both modules to dev:**
```
modules: api,cronjob
environments: dev
runUnitTests: false
imageRegistry: ghcr.io
```

**Build only API for production:**
```
modules: api
environments: prod
releaseBuild: true
runUnitTests: true
imageRegistry: ghcr.io
```

