// Update this URL after deploying your GCP Cloud Function
// Updated on 16-Apr
const BACKEND_URL = 'https://get-fun-facts-342362459405.us-east1.run.app';

async function fetchFacts() {
    const container = document.getElementById('facts-container');
    const loading = document.getElementById('loading');
    const errorMsg = document.getElementById('error');

    try {
        // Use a dummy response if URL is not set to show it works locally
        let data;
        if (BACKEND_URL === 'YOUR_CLOUD_FUNCTION_URL_HERE') {
            console.warn('Backend URL not set. Using local dummy data for demonstration.');
            data = [
                {
                    headline: "Placeholder Fact",
                    narrative: "This is a placeholder fact because the BACKEND_URL in script.js has not been set yet. Once you deploy your GCP Cloud Function, paste the URL into script.js.",
                    image: "https://images.unsplash.com/photo-1516733725897-1aa73b87c8e8?w=400"
                }
            ];
        } else {
            const response = await fetch(BACKEND_URL);
            if (!response.ok) throw new Error('Network response was not ok');
            data = await response.json();
        }

        loading.style.display = 'none';
        container.innerHTML = '';

        data.forEach(fact => {
            const card = document.createElement('div');
            card.className = 'fact-card';

            const headline = document.createElement('span');
            headline.className = 'fact-headline';
            headline.textContent = fact.headline;

            const narrative = document.createElement('p');
            narrative.className = 'fact-narrative';
            narrative.textContent = fact.narrative;

            card.appendChild(headline);
            card.appendChild(narrative);

            if (fact.image) {
                const img = document.createElement('img');
                img.className = 'fact-image';
                img.src = fact.image;
                img.alt = fact.headline;
                card.appendChild(img);
            }

            container.appendChild(card);
        });
    } catch (error) {
        console.error('Fetch error:', error);
        loading.style.display = 'none';
        errorMsg.style.display = 'block';
    }
}

window.onload = fetchFacts;
