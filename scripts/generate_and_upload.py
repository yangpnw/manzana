#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import datetime
import re
import urllib.request
import urllib.parse

BUCKET_NAME = "manzana-facts-493603"
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS_DIR = os.path.join(WORKSPACE_DIR, "docs", "facts")
IMAGES_DIR = os.path.join(FACTS_DIR, "images")

PROMPT = (
    "Act as a master storyteller for curious school-age kids. Find today's news and identify 10 "
    "kid-friendly topic themes (e.g., Space Robotics, Weird Nature, Tech Toys, Ancient Mysteries). "
    "For each of these 10 themes, generate a factual, super obscure, and little-known fun fact. "
    "Avoid all common knowledge (e.g., do NOT mention that octopuses have three hearts, or that "
    "honey never spoils). Format exactly these 10 facts into a JSON array, where each fact has these "
    "exact keys: 'headline', 'narrative', and 'search_query'. The 'search_query' should be 1-3 keywords "
    "suitable for a Wikipedia image search. Output ONLY the raw JSON array. Do not wrap it in markdown "
    "code blocks. Do not output any other text or explanation."
)

def extract_json_array(text):
    text = text.strip()
    
    # Remove markdown code block if present
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        
    # Find the outermost JSON array brackets
    start_idx = text.find('[')
    end_idx = text.rfind(']')
    
    if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
        raise ValueError("Could not find JSON array brackets in the output.")
        
    json_str = text[start_idx:end_idx + 1]
    return json.loads(json_str)

def get_real_image_url(query):
    if not query:
        return None
    headers = {
        "User-Agent": "FunFactsBot/1.0 (https://github.com/yangpnw/manzana; yangpnw@gmail.com)"
    }
    try:
        # 1. Search for the Wikipedia page title
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1
        }
        search_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(search_params)
        req1 = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req1, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            
        search_results = data.get("query", {}).get("search", [])
        if not search_results:
            return None
        page_title = search_results[0]["title"]
        
        # 2. Query page image (thumbnail)
        img_params = {
            "action": "query",
            "titles": page_title,
            "prop": "pageimages",
            "format": "json",
            "pithumbsize": 800
        }
        img_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(img_params)
        req2 = urllib.request.Request(img_url, headers=headers)
        with urllib.request.urlopen(req2, timeout=5) as response:
            img_data = json.loads(response.read().decode("utf-8"))
            
        pages = img_data.get("query", {}).get("pages", {})
        for page_id in pages:
            thumbnail = pages[page_id].get("thumbnail", {}).get("source")
            if thumbnail:
                return thumbnail
    except Exception as e:
        print(f"⚠️ Image search error for '{query}': {e}", file=sys.stderr)
    return None

def download_and_save_image(url, output_dir, filename_prefix):
    if not url:
        return None
    
    headers = {
        "User-Agent": "FunFactsBot/1.0 (https://github.com/yangpnw/manzana; yangpnw@gmail.com)"
    }
    
    try:
        # Determine extension from url
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path
        ext = os.path.splitext(path)[1]
        if not ext or len(ext) > 5:
            ext = ".jpg"  # Default fallback
            
        safe_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', filename_prefix).lower()
        filename = f"{safe_prefix}{ext}"
        filepath = os.path.join(output_dir, filename)
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            with open(filepath, "wb") as f:
                f.write(response.read())
        return filename
    except Exception as e:
        print(f"⚠️ Failed to download image from {url}: {e}", file=sys.stderr)
    return None

def main():
    # Ensure common installation paths (like ~/.local/bin and /usr/local/bin) are in PATH for cron execution
    user_bin = os.path.expanduser("~/.local/bin")
    current_path = os.environ.get("PATH", "")
    additional_paths = [user_bin, "/usr/local/bin", "/opt/homebrew/bin"]
    for path in additional_paths:
        if path not in current_path.split(":"):
            current_path = f"{path}:{current_path}"
    os.environ["PATH"] = current_path

    print("🤖 Starting fun facts generation using agy CLI...")
    
    # Run agy command
    try:
        # We call the agy binary. It should be available in PATH.
        # We add --dangerously-skip-permissions to auto-approve tool usage in non-interactive mode.
        result = subprocess.run(
            ["agy", "--dangerously-skip-permissions", "--print", PROMPT],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
        if result.stderr:
            print(f"⚠️ Warning (stderr from agy):\n{result.stderr}", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running agy: {e}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: 'agy' command not found in PATH.", file=sys.stderr)
        sys.exit(1)
        
    try:
        facts = extract_json_array(output)
        print(f"✅ Successfully generated and parsed {len(facts)} facts.")
    except Exception as e:
        print(f"❌ Error parsing generated output as JSON: {e}", file=sys.stderr)
        print(f"Raw output was:\n{output}", file=sys.stderr)
        sys.exit(1)
        
    if not isinstance(facts, list) or len(facts) == 0:
        print("❌ Error: Output is not a non-empty list.", file=sys.stderr)
        sys.exit(1)
        
    # Ensure images directory exists
    os.makedirs(IMAGES_DIR, exist_ok=True)
        
    # Fetch real image URLs for each fact using Wikipedia API
    print("📸 Querying Wikipedia and downloading images...")
    for idx, fact in enumerate(facts):
        query = fact.get("search_query", "")
        # Set default empty string
        fact["image"] = ""
        if query:
            image_url = get_real_image_url(query)
            if image_url:
                print(f"   [{idx + 1}/10] Found external image for '{query}': {image_url}")
                # Download image locally
                local_filename = download_and_save_image(image_url, IMAGES_DIR, query)
                if local_filename:
                    # Point to GCS path
                    fact["image"] = f"https://storage.googleapis.com/{BUCKET_NAME}/images/{local_filename}"
                    print(f"   [{idx + 1}/10] Downloaded and mapped to GCS: {fact['image']}")
                else:
                    # Fallback to direct external URL if download fails
                    fact["image"] = image_url
            else:
                print(f"   [{idx + 1}/10] No image found for '{query}'")
            # Clean up key
            if "search_query" in fact:
                del fact["search_query"]
        
    # Validate structure
    for idx, fact in enumerate(facts):
        for key in ["headline", "narrative", "image"]:
            if key not in fact:
                print(f"⚠️ Warning: Fact at index {idx} is missing key '{key}'. Setting default.", file=sys.stderr)
                fact[key] = ""
                
    # Create facts directory
    os.makedirs(FACTS_DIR, exist_ok=True)
    
    # Save dated and latest facts
    today = datetime.date.today().isoformat()
    dated_filename = f"facts_{today}.json"
    
    dated_path = os.path.join(FACTS_DIR, dated_filename)
    latest_path = os.path.join(FACTS_DIR, "latest.json")
    
    with open(dated_path, "w", encoding="utf-8") as f:
        json.dump(facts, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved locally to {dated_path}")
        
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(facts, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved locally to {latest_path}")
    
    # Upload to GCS
    print(f"☁️ Uploading to GCS bucket: gs://{BUCKET_NAME}...")
    try:
        # Upload images directory
        subprocess.run(
            ["gcloud", "storage", "cp", "-r", IMAGES_DIR, f"gs://{BUCKET_NAME}/"],
            check=True
        )
        # Upload dated file
        subprocess.run(
            ["gcloud", "storage", "cp", "--cache-control=no-cache, no-store, must-revalidate", dated_path, f"gs://{BUCKET_NAME}/{dated_filename}"],
            check=True
        )
        # Upload latest file
        subprocess.run(
            ["gcloud", "storage", "cp", "--cache-control=no-cache, no-store, must-revalidate", latest_path, f"gs://{BUCKET_NAME}/latest.json"],
            check=True
        )
        print("🎉 Successfully uploaded all files and images to GCS!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error uploading to GCS: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
