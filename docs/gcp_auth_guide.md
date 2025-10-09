Absolutely ✅ — here’s a clean and professional **Markdown (`.md`) documentation** you can add to your project (e.g., `GCP_Auth_Setup.md`):

---

# 🔐 GCP Authentication & Project Setup Guide

This guide explains how to properly authenticate and configure your environment to use **Google Cloud services** (e.g., BigQuery, Vertex AI) in your Python project.

---

## 🧩 1. Prerequisites

Make sure you have:

* A **Google Cloud Project** (e.g., `gen-lang-client-0939972341`)
* A **Service Account** with appropriate roles (e.g., `BigQuery Admin`, `Vertex AI Administrator`)
* The **Service Account Key File** (e.g., `aqi-service-account.json`)
* **Google Cloud CLI** installed
  👉 [Install Guide](https://cloud.google.com/sdk/docs/install)

---

## ⚙️ 2. Authenticate with Google Cloud

Run the following command in your terminal to authenticate using your service account:

```bash
gcloud auth activate-service-account --key-file="C:\path\to\aqi-service-account.json"
```

✅ Expected Output:

```
Activated service account credentials for: [your-service-account@project-id.iam.gserviceaccount.com]
```

---

## 🏗️ 3. Set the Active Project

Tell Google Cloud which project to use for all operations:

```bash
gcloud config set project gen-lang-client-0939972341
```

✅ Expected Output:

```
Updated property [core/project].
```

---

## 🧾 4. Verify Authentication

Check that your service account is active:

```bash
gcloud auth list
```

✅ Example Output:

```
Credentialed Accounts
ACTIVE  ACCOUNT
*       github-actions-aqi@gen-lang-client-0939972341.iam.gserviceaccount.com
        qudratullah0708@gmail.com
```

---

## 🗄️ 5. Verify BigQuery Access

Check if the dataset or table exists and is accessible:

```bash
bq show gen-lang-client-0939972341:aqi_dataset.aqi_features
```

If you see the schema output (columns listed), access is correctly configured.

If you get a permission error:

* Ensure your service account has the **BigQuery Admin** role
  → You can add it via the [Google Cloud Console → IAM](https://console.cloud.google.com/iam-admin/iam).

---

## 🧠 6. Using Authentication in Python Code

In your Python script (e.g., `setup_feature_store.py`), ensure you use the service account key:

```python
from google.cloud import bigquery, aiplatform

# Initialize clients
aiplatform.init(
    project="gen-lang-client-0939972341",
    location="us-central1",
    credentials_path="aqi-service-account.json"
)

bq_client = bigquery.Client.from_service_account_json("aqi-service-account.json")
print("✅ BigQuery and Vertex AI authenticated successfully!")
```

---

## 🤖 7. (Optional) Setup for GitHub Actions / CI

If you’re automating deployments:

1. Save the contents of `aqi-service-account.json` as a **GitHub Secret** (e.g., `GCP_KEY`).
2. In your workflow, write it to a file and authenticate:

```yaml
- name: Set up GCP auth
  run: |
    echo "$GCP_KEY" > key.json
    gcloud auth activate-service-account --key-file=key.json
    gcloud config set project gen-lang-client-0939972341
```

---

## ✅ Summary

| Step           | Purpose                 | Command                                                 |
| -------------- | ----------------------- | ------------------------------------------------------- |
| Authenticate   | Verify identity         | `gcloud auth activate-service-account --key-file="..."` |
| Set Project    | Choose where to operate | `gcloud config set project PROJECT_ID`                  |
| Verify Auth    | Confirm login           | `gcloud auth list`                                      |
| Check BigQuery | Confirm dataset access  | `bq show PROJECT:DATASET.TABLE`                         |

---

Would you like me to add a short section explaining **how to securely store the service account key** (for local dev + GitHub Actions)?
