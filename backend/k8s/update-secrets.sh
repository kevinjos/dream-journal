#!/bin/bash
# Script to add SendGrid API key and Django admin password to existing Kubernetes secret

set -e

echo "Updating Kubernetes secrets with SendGrid and Admin password..."

# Get the current GCP project
PROJECT_ID=$(gcloud config get-value project)
echo "Using project: $PROJECT_ID"

# Ensure we're in the right cluster context
gcloud container clusters get-credentials dream-journal-autopilot --region=us-central1 --project=$PROJECT_ID

# Fetch the new secrets from Google Secret Manager
echo "Fetching secrets from Google Secret Manager..."
SENDGRID_API_KEY=$(gcloud secrets versions access latest --secret="sendgrid-api-key" --project=$PROJECT_ID)
DJANGO_ADMIN_PASSWORD=$(gcloud secrets versions access latest --secret="django-admin-password" --project=$PROJECT_ID)

# Get the existing secret data
echo "Fetching existing django-secrets..."
EXISTING_SECRET_KEY=$(kubectl get secret django-secrets -n dream-journal -o jsonpath='{.data.secret-key}' | base64 -d)
EXISTING_DATABASE_URL=$(kubectl get secret django-secrets -n dream-journal -o jsonpath='{.data.database-url}' | base64 -d)

# Recreate the secret with all values
echo "Updating django-secrets with SendGrid and admin password..."
kubectl create secret generic django-secrets \
  --from-literal=secret-key="$EXISTING_SECRET_KEY" \
  --from-literal=database-url="$EXISTING_DATABASE_URL" \
  --from-literal=sendgrid-api-key="$SENDGRID_API_KEY" \
  --from-literal=django-admin-password="$DJANGO_ADMIN_PASSWORD" \
  --namespace=dream-journal \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secrets successfully updated!"
echo ""
echo "Admin credentials:"
echo "  Username: admin"
echo "  Email: admin@sensorium.dev"
echo "  Password: [stored in secret]"
echo ""
echo "To retrieve admin password:"
echo "  gcloud secrets versions access latest --secret='django-admin-password'"
