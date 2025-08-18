# Dream Journal Infrastructure

This directory contains the OpenTofu/Terraform configuration for deploying the Dream Journal application to Google Cloud Platform.

## Prerequisites

1. **Install OpenTofu** (or Terraform):
   ```bash
   # On macOS with Homebrew
   brew install opentofu
   
   # Or download from https://opentofu.org/
   ```

2. **Install Google Cloud SDK**:
   ```bash
   # On macOS
   brew install --cask google-cloud-sdk
   
   # Or follow: https://cloud.google.com/sdk/docs/install
   ```

3. **Authenticate with GCP**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

4. **Create a GCP Organization** (if not already created):
   - This typically requires a Google Workspace or Cloud Identity account
   - See: https://cloud.google.com/resource-manager/docs/creating-managing-organization

5. **Set up Billing**:
   - Create or identify a billing account
   - Get the billing account ID: `gcloud billing accounts list`

## Initial Setup

1. **Create the Terraform state bucket** (one-time setup):
   ```bash
   # Create a project to hold the Terraform state
   gcloud projects create dream-journal-terraform --name="Dream Journal Terraform"
   
   # Link billing account
   gcloud billing projects link dream-journal-terraform \
     --billing-account=YOUR_BILLING_ACCOUNT_ID
   
   # Enable required APIs
   gcloud services enable storage.googleapis.com \
     --project=dream-journal-terraform
   
   # Create the state bucket
   gsutil mb -p dream-journal-terraform \
     -l us-central1 \
     gs://dream-journal-terraform-state-prod/
   
   # Enable versioning on the bucket
   gsutil versioning set on gs://dream-journal-terraform-state-prod/
   ```

2. **Configure terraform.tfvars**:
   ```bash
   cd infrastructure/environments/prod
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your actual values
   ```

## Deployment

1. **Initialize OpenTofu/Terraform**:
   ```bash
   cd infrastructure/environments/prod
   tofu init  # or 'terraform init'
   ```

2. **Review the plan**:
   ```bash
   tofu plan
   ```

3. **Apply the configuration**:
   ```bash
   tofu apply
   ```

## Architecture

The infrastructure creates:

- **GCP Project**: Isolated project for the Dream Journal application
- **VPC Network**: Custom network with subnets for the application
- **Cloud NAT**: For outbound internet access from private resources
- **Firewall Rules**: Security rules for internal communication and health checks
- **Enabled APIs**: All necessary GCP APIs for running the application

## Next Steps

After the base infrastructure is created, you can add:

1. **Cloud SQL**: PostgreSQL database for the Django backend
2. **Cloud Run**: Serverless hosting for the Django API
3. **Cloud Storage**: Static file hosting for the Quasar frontend
4. **Cloud Load Balancing**: Global load balancer with SSL certificates
5. **Cloud Armor**: WAF and DDoS protection
6. **Secret Manager**: Secure storage for API keys and secrets

## Module Structure

```
infrastructure/
├── modules/
│   └── gcp-project/        # Reusable GCP project module
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    └── prod/               # Production environment
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── terraform.tfvars.example
```

## Security & CI/CD

### 🔒 Security Model
- **Sensitive values** (project IDs, credentials) are **NOT stored in git**
- **CI/CD** uses Cloud Build substitutions to inject sensitive values  
- **Local development** uses `.tfvars` files (gitignored)
- **Never commit** `terraform.tfvars` to version control
- Use Secret Manager for application secrets
- Enable audit logging for compliance

### 🚀 Cloud Build CI/CD Setup

Due to Terraform provider limitations with 2nd generation repository connections, Cloud Build triggers must be created manually:

#### Required Cloud Build Trigger Substitutions:
```
# For all triggers:
PROJECT_ID = your-project-id
GITHUB_OWNER = your-github-username  
GITHUB_REPO = your-repo-name
```

#### Steps to create triggers:
1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click "Create Trigger"
3. Select "Cloud Build GitHub App" (2nd gen)
4. Choose your GitHub repository
5. Configure each trigger:

**Infrastructure Trigger:**
   - **Name**: `infrastructure-update`
   - **Branch pattern**: `^main$` 
   - **Build configuration**: `infrastructure/cloudbuild.yaml`
   - **File filter**: `infrastructure/**`
   - **Substitution variables**:
     - `PROJECT_ID` = `your-project-id`
     - `GITHUB_OWNER` = `your-github-username`
     - `GITHUB_REPO` = `your-repo-name`

**Backend Trigger:**
   - **Name**: `backend-build-deploy`
   - **Branch pattern**: `^main$`
   - **Build configuration**: `backend/cloudbuild.yaml` 
   - **File filter**: `backend/**`
   - **Substitution variables**:
     - `PROJECT_ID` = `your-project-id`

**Frontend Trigger:**
   - **Name**: `frontend-build-deploy`
   - **Branch pattern**: `^main$`
   - **Build configuration**: `frontend/cloudbuild.yaml`
   - **File filter**: `frontend/**` 
   - **Substitution variables**:
     - `PROJECT_ID` = `your-project-id`

The CI/CD pipeline will:
- ✅ **Plan** infrastructure changes on all branches
- ✅ **Apply** changes automatically on `main` branch only
- ✅ Use substitutions to inject sensitive values securely