# Manzana - Top 10 Daily Fun Facts

A simple web application that displays 10 random fun facts daily.

## Structure
- `frontend/`: Static HTML/JS website.
- `backend/`: Python Cloud Function (GCP).

## Setup & Deployment

### 1. Backend (GCP Cloud Function)
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Enable the **Cloud Functions** and **Cloud Build** APIs.
3.  Navigate to **Cloud Functions** and click **Create Function**.
4.  **Configuration**:
    *   **Environment**: 2nd gen
    *   **Function name**: `get-fun-facts`
    *   **Trigger**: HTTPS (Allow unauthenticated invocations for public access)
5.  **Code**:
    *   **Runtime**: Python 3.10+
    *   **Entry point**: `get_fun_facts`
    *   Upload/Paste the contents of `backend/main.py` and `backend/requirements.txt`.
6.  Deploy the function.
7.  Copy the **URL** provided after deployment.

### 2. Frontend Configuration
1.  Open `frontend/script.js`.
2.  Replace `'YOUR_CLOUD_FUNCTION_URL_HERE'` with the URL you copied from GCP.

### 3. Deployment (GitHub Pages)
1.  Push this repository to GitHub.
2.  Go to **Settings** > **Pages** in your GitHub repository.
3.  Under **Build and deployment** > **Source**, select **Deploy from a branch**.
4.  Select your branch (e.g., `main`) and the folder `/frontend`.
5.  Click **Save**. Your site will be live at `https://<username>.github.io/<repo-name>/`.

## Local Development
To test the frontend locally:
1.  Open `frontend/index.html` in your browser.
2.  By default, it uses placeholder data if the URL is not set.
