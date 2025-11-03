### Configure GCP Artifact Registry

```bash
# Configure Docker to use GCP Artifact Registry
gcloud auth configure-docker northamerica-northeast1-docker.pkg.dev

# Build the image
docker build -t northamerica-northeast1-docker.pkg.dev/c4hnrd-dev/job-repo/iam-idir-scanner:latest .

# Push to Artifact Registry
docker push northamerica-northeast1-docker.pkg.dev/c4hnrd-dev/job-repo/iam-idir-scanner:latest
