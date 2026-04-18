// Update this URL after deploying your GCP Cloud Function
// Updated on 16-Apr
const BACKEND_URL = 'https://get-fun-facts-342362459405.us-east1.run.app';

let rainInterval;
let phraseInterval;
let spinnerInterval;

function startLoadingAnimations() {
    const rainEmojis = ['🍌', '🌮', '🍍', '🍕', '🍉', '🍔'];
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
    
    const emojiContainer = document.getElementById('emoji-container');
    const phraseElement = document.getElementById('loading-phrase');
    const spinnerElement = document.querySelector('.emoji-spinner');
    
    // 1. Start Emoji Rain
    rainInterval = setInterval(() => {
        const emoji = document.createElement('div');
        emoji.className = 'falling-emoji';
        emoji.textContent = rainEmojis[Math.floor(Math.random() * rainEmojis.length)];
        emoji.style.left = Math.random() * 100 + 'vw';
        emoji.style.animationDuration = (Math.random() * 2 + 2) + 's';
        emojiContainer.appendChild(emoji);
        setTimeout(() => emoji.remove(), 4000);
    }, 150);

    // 2. Start Phrase Cycle
    let phraseIndex = 0;
    phraseInterval = setInterval(() => {
        phraseIndex = (phraseIndex + 1) % phrases.length;
        phraseElement.textContent = phrases[phraseIndex];
    }, 1500);

    // 3. Update Spinner Emoji
    spinnerInterval = setInterval(() => {
        spinnerElement.textContent = spinnerEmojis[Math.floor(Math.random() * spinnerEmojis.length)];
    }, 1000);
}

function stopLoadingAnimations() {
    clearInterval(rainInterval);
    clearInterval(phraseInterval);
    clearInterval(spinnerInterval);
    const container = document.getElementById('emoji-container');
    setTimeout(() => {
        container.innerHTML = '';
    }, 2000);
}

async function fetchFacts() {
    const container = document.getElementById('facts-container');
    const loading = document.getElementById('loading');
    const errorMsg = document.getElementById('error');

    startLoadingAnimations();

    try {
        // Use a dummy response if URL is not set to show it works locally
        let data;
        if (BACKEND_URL === 'YOUR_CLOUD_FUNCTION_URL_HERE') {
            console.warn('Backend URL not set. Using local dummy data for demonstration.');
            await new Promise(r => setTimeout(r, 2000)); // Simulate delay
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

        stopLoadingAnimations();
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
