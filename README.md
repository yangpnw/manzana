# Manzana - Top 10 Daily Fun Facts

A simple, serverless web application that displays 10 random, highly obscure fun facts daily.

## Architecture

- **Frontend**: Static HTML/JS website located in `docs/` (designed for hosting via GitHub Pages). It fetches the latest daily fun facts directly from a public Google Cloud Storage (GCS) bucket.
- **Backend Job**: A Python script in `scripts/generate_and_upload.py` that runs daily to generate fresh fun facts via the `agy` CLI, enrich them with real-world Wikipedia or Unsplash images, and upload them to the GCS bucket.

This serverless architecture ensures that the page loads instantly with zero container cold starts.

---

## Structure

- [docs/](file:///Users/yyangv/Desktop/code/manzana/docs/): Frontend files.
- [scripts/](file:///Users/yyangv/Desktop/code/manzana/scripts/): Daily automation script and GCS bucket configuration files.

---

## Daily Fact Generation & GCS Upload

The [scripts/generate_and_upload.py](file:///Users/yyangv/Desktop/code/manzana/scripts/generate_and_upload.py) script automates the daily facts cycle. It:
1. Runs the `agy` CLI agent non-interactively to research daily news and output 10 obscure fun facts in structured JSON format.
2. Performs a web search to attach real-world Wikipedia/Unsplash image URLs.
3. Saves a local archive in `docs/facts/facts_YYYY-MM-DD.json`.
4. Uploads the files to GCS: `gs://manzana-facts-493603/facts_YYYY-MM-DD.json` and `gs://manzana-facts-493603/latest.json`.

### How to Run Locally

1. Ensure the `agy` CLI is installed and authenticated:
   ```bash
   agy --version
   ```
2. Make sure you are authenticated with Google Cloud and have access to the project:
   ```bash
   gcloud auth application-default login
   ```
3. Run the script manually:
   ```bash
   ./scripts/generate_and_upload.py
   ```

### Scheduling the Job Daily (Cron Setup)

You can schedule the script to run daily at 9:00 AM on your machine using crontab:

1. Open your crontab editor:
   ```bash
   crontab -e
   ```
2. Add the following entry (adjust path to match your repository directory):
   ```cron
   0 9 * * * /Users/yyangv/Desktop/code/manzana/scripts/generate_and_upload.py >> /Users/yyangv/Desktop/code/manzana/scripts/cron.log 2>&1
   ```

---

## GCS Bucket Configuration

The bucket `gs://manzana-facts-493603` is configured to allow direct queries from the browser:
- **Public Read Access**: Granted `roles/storage.objectViewer` to `allUsers`.
- **CORS Configuration**: Configured via [scripts/cors.json](file:///Users/yyangv/Desktop/code/manzana/scripts/cors.json) to allow GET and OPTIONS requests from any origin (`*`).

To apply the CORS configuration to a new bucket:
```bash
gcloud storage buckets update gs://<your-bucket-name> --cors-file=scripts/cors.json
```

---

## Frontend Deployment (GitHub Pages)

1. Push this repository to GitHub.
2. Go to **Settings** > **Pages** in your GitHub repository.
3. Under **Build and deployment** > **Source**, select **Deploy from a branch**.
4. Select your branch (e.g., `main`) and set the folder to `/docs`.
5. Click **Save**. Your site will be live at `https://<username>.github.io/<repo-name>/`.
