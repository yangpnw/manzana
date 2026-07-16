const GCS_BUCKET_URL = 'https://storage.googleapis.com/manzana-facts-493603';

function getDatedUrl(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${GCS_BUCKET_URL}/facts_${year}-${month}-${day}.json`;
}

let phraseInterval;
let spinnerInterval;


function startLoadingAnimations() {
    const spinnerEmojis = ['🌟', '✨', '🔥', '💫', '🌈', '🛸'];
    const phrases = [
        "Herding stray electrons...",
        "Bribing the algorithm with tacos...",
        "Peeling digital bananas...",
        "Consulting the ancient scrolls...",
        "Brewing hot fresh facts...",
        "Untangling the space-time continuum...",
        "Asking the neighbors for Wi-Fi...",
        "Polishing the crystal ball...",
        "Calibrating the curiosity sensors...",
        "Wait, is this thing on?..."
    ];
    
    const phraseElement = document.getElementById('loading-phrase');
    const spinnerElement = document.querySelector('.emoji-spinner');
    
    let phraseIndex = 0;
    phraseInterval = setInterval(() => {
        phraseIndex = (phraseIndex + 1) % phrases.length;
        phraseElement.textContent = phrases[phraseIndex];
    }, 1500);

    spinnerInterval = setInterval(() => {
        spinnerElement.textContent = spinnerEmojis[Math.floor(Math.random() * spinnerEmojis.length)];
    }, 1000);
}

function stopLoadingAnimations() {
    clearInterval(phraseInterval);
    clearInterval(spinnerInterval);
}

async function fetchFacts() {
    const container = document.getElementById('facts-container');
    const loading = document.getElementById('loading');
    const errorMsg = document.getElementById('error');

    startLoadingAnimations();

    try {
        let data;
        const today = new Date();
        const todayUrl = getDatedUrl(today);
        let response;
        
        console.log(`Attempting to fetch today's facts from GCS: ${todayUrl}`);
        response = await fetch(todayUrl);
        
        if (!response.ok) {
            console.warn(`Today's facts not found (status ${response.status}). Falling back to yesterday...`);
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            const yesterdayUrl = getDatedUrl(yesterday);
            response = await fetch(yesterdayUrl);
        }
        
        if (!response.ok) {
            console.warn(`Yesterday's facts not found. Falling back to latest.json...`);
            response = await fetch(`${GCS_BUCKET_URL}/latest.json`);
        }
        
        if (!response.ok) {
            throw new Error(`Failed to fetch facts from GCS (status ${response.status})`);
        }
        
        data = await response.json();

        stopLoadingAnimations();
        loading.style.display = 'none';
        container.innerHTML = '';

        data.forEach((fact, idx) => {
            const card = document.createElement('div');
            card.className = 'fact-card';

            const headline = document.createElement('span');
            headline.className = 'fact-headline';
            headline.textContent = `${idx + 1}. ${fact.headline}`;

            const narrative = document.createElement('p');
            narrative.className = 'fact-narrative';
            narrative.textContent = fact.narrative;

            card.appendChild(headline);
            card.appendChild(narrative);

            if (fact.image) {
                const imgContainer = document.createElement('div');
                imgContainer.className = 'fact-image-container';
                
                const img = document.createElement('img');
                img.className = 'fact-image';
                img.src = fact.image;
                img.alt = fact.headline;
                
                imgContainer.appendChild(img);
                card.appendChild(imgContainer);
            }

            container.appendChild(card);
        });
    } catch (error) {
        console.error('Fetch error:', error);
        stopLoadingAnimations();
        loading.style.display = 'none';
        errorMsg.style.display = 'block';
    }
}

window.onload = fetchFacts;
