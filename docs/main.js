// Global variable to store all fetched data
let allData = [];
const SITE_DATA_URL = 'site_data.json'; // Or directly 'site_data.json' if in the same folder

// DOMContentLoaded listener
document.addEventListener('DOMContentLoaded', init);

// Init function
async function init() {
    await fetchData(); // Wait for data to be fetched and parsed
    if (allData.length > 0) {
        populateFilters(allData);
        renderVorschlaege(allData);
        calculateAndDisplayStats(allData);
        setupEventListeners();
        updateDataGeneratedDate(); // If you have a date in your data
    } else {
        document.getElementById('vorschlaege-container').innerHTML = '<p>Keine Daten geladen oder Daten sind leer.</p>';
        document.getElementById('stats-container').innerHTML = '<p>Keine Statistiken verfügbar.</p>';
    }
}

// Fetch data function
async function fetchData() {
    try {
        const response = await fetch(SITE_DATA_URL);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        allData = data; // Assign to global variable
        console.log("Daten erfolgreich geladen:", allData);
    } catch (error) {
        console.error("Fehler beim Laden der Daten:", error);
        allData = []; // Ensure allData is empty on error
    }
}

// Render Vorschlaege function
function renderVorschlaege(vorschlaegeArray) {
    const container = document.getElementById('vorschlaege-container');
    container.innerHTML = ''; // Clear current content

    if (!vorschlaegeArray || vorschlaegeArray.length === 0) {
        container.innerHTML = '<p>Keine Ergebnisse gefunden.</p>';
        return;
    }

    vorschlaegeArray.forEach(item => {
        const article = document.createElement('article');
        
        // Basic info
        let htmlContent = `
            <h3>${item.vorschlag || 'Unbekannter Vorschlag'}</h3>
            <p><strong>Vorgeschlagen von:</strong> ${item.vorschlagender || 'N/A'} 
               ${item.ist_hoerer ? ` (Hörer: ${item.hoerer_name || 'N/A'})` : ''}
            </p>
            <p><strong>Punkt erhalten:</strong> ${item.punkt_erhalten ? 'Ja' : 'Nein'} 
               (von: ${item.punkt_von || 'N/A'})
            </p>
            <p><strong>Begründung:</strong> ${item.begruendung || 'Keine'}</p>
            <p><strong>Tags:</strong> ${item.tags && item.tags.length > 0 ? item.tags.join(', ') : 'Keine'}</p>
            <p><strong>Diskussion ab Sekunde:</strong> ${item.start_zeit_sekunden !== null ? item.start_zeit_sekunden : 'N/A'}</p>
            <p><strong>Episode:</strong> ${item.episode_title || 'Unbekannter Titel'} 
               (${item.episode_date || 'Unbekanntes Datum'})
            </p>
        `;

        // Episode Links
        if (item.episode_apple_url) {
            htmlContent += `<p><a href="${item.episode_apple_url}" target="_blank">Auf Apple Podcasts anhören</a></p>`;
        }
        // The key 'url' from combined_episodes.json was Spotify URL
        if (item.episode_spotify_url) { 
            htmlContent += `<p><a href="${item.episode_spotify_url}" target="_blank">Auf Spotify anhören</a></p>`;
        }
        
        article.innerHTML = htmlContent;
        container.appendChild(article);
    });
}

// Populate filters function
function populateFilters(data) {
    const proposers = new Set();
    const tags = new Set();

    data.forEach(item => {
        if (item.vorschlagender) {
            proposers.add(item.vorschlagender);
        }
        if (item.tags && Array.isArray(item.tags)) {
            item.tags.forEach(tag => tags.add(tag));
        }
    });

    const proposerSelect = document.getElementById('filter-proposer');
    Array.from(proposers).sort().forEach(proposer => {
        const option = document.createElement('option');
        option.value = proposer;
        option.textContent = proposer;
        proposerSelect.appendChild(option);
    });

    const tagSelect = document.getElementById('filter-tag');
    Array.from(tags).sort().forEach(tag => {
        const option = document.createElement('option');
        option.value = tag;
        option.textContent = tag;
        tagSelect.appendChild(option);
    });
}

// Apply filters and search function
function applyFiltersAndSearch() {
    const searchText = document.getElementById('search-input').value.toLowerCase();
    const selectedProposer = document.getElementById('filter-proposer').value;
    const selectedTag = document.getElementById('filter-tag').value;

    const filteredData = allData.filter(item => {
        const matchesSearchText = (
            (item.vorschlag && item.vorschlag.toLowerCase().includes(searchText)) ||
            (item.begruendung && item.begruendung.toLowerCase().includes(searchText)) ||
            (item.episode_title && item.episode_title.toLowerCase().includes(searchText)) ||
            (item.tags && Array.isArray(item.tags) && item.tags.some(tag => tag.toLowerCase().includes(searchText)))
        );
        const matchesProposer = !selectedProposer || (item.vorschlagender === selectedProposer);
        const matchesTag = !selectedTag || (item.tags && Array.isArray(item.tags) && item.tags.includes(selectedTag));

        return matchesSearchText && matchesProposer && matchesTag;
    });

    renderVorschlaege(filteredData);
    calculateAndDisplayStats(filteredData);
}

// Calculate and display stats function
function calculateAndDisplayStats(data) {
    const statsContainer = document.getElementById('stats-container');
    statsContainer.innerHTML = ''; // Clear current stats

    if (!data || data.length === 0) {
        statsContainer.innerHTML = "<p>Keine Daten für Statistiken vorhanden.</p>";
        return;
    }

    // Total suggestions
    const totalSuggestions = data.length;
    statsContainer.innerHTML += `<p><strong>Angezeigte Vorschläge:</strong> ${totalSuggestions}</p>`;

    // Suggestions per proposer
    const suggestionsPerProposer = {};
    const pointsPerProposer = {};
    data.forEach(item => {
        if (item.vorschlagender) {
            suggestionsPerProposer[item.vorschlagender] = (suggestionsPerProposer[item.vorschlagender] || 0) + 1;
            if (item.punkt_erhalten) {
                pointsPerProposer[item.vorschlagender] = (pointsPerProposer[item.vorschlagender] || 0) + 1;
            }
        }
    });

    let proposerStatsHtml = '<h4>Vorschläge pro Person:</h4><ul>';
    for (const [proposer, count] of Object.entries(suggestionsPerProposer).sort((a,b) => b[1] - a[1])) {
        const points = pointsPerProposer[proposer] || 0;
        const successRate = count > 0 ? ((points / count) * 100).toFixed(1) : 0;
        proposerStatsHtml += `<li>${proposer}: ${count} (Erfolgsrate: ${successRate}%)</li>`;
    }
    proposerStatsHtml += '</ul>';
    statsContainer.innerHTML += proposerStatsHtml;

    // Tag frequency
    const tagFrequency = {};
    data.forEach(item => {
        if (item.tags && Array.isArray(item.tags)) {
            item.tags.forEach(tag => {
                tagFrequency[tag] = (tagFrequency[tag] || 0) + 1;
            });
        }
    });

    let tagStatsHtml = '<h4>Tag Häufigkeit:</h4><ul>';
    for (const [tag, count] of Object.entries(tagFrequency).sort((a,b) => b[1] - a[1]).slice(0, 15)) { // Display top 15 tags
        tagStatsHtml += `<li>${tag}: ${count}</li>`;
    }
    tagStatsHtml += '</ul>';
    statsContainer.innerHTML += tagStatsHtml;
}

// Setup event listeners function
function setupEventListeners() {
    document.getElementById('search-input').addEventListener('input', applyFiltersAndSearch);
    document.getElementById('filter-proposer').addEventListener('change', applyFiltersAndSearch);
    document.getElementById('filter-tag').addEventListener('change', applyFiltersAndSearch);
}

// Update data generated date (Placeholder)
function updateDataGeneratedDate() {
    // This function can be expanded if your site_data.json includes a generation timestamp.
    // For now, let's assume we don't have it, or set a static date.
    const dateSpan = document.getElementById('data-generated-date');
    if (dateSpan) {
        // Example: If allData has a root-level property like "generated_at"
        // if (allData.length > 0 && allData[0].data_generation_date_iso) { // Assuming date is on first item or metadata
        //    dateSpan.textContent = new Date(allData[0].data_generation_date_iso).toLocaleString('de-DE');
        // } else {
        dateSpan.textContent = new Date().toLocaleDateString('de-DE', { year: 'numeric', month: 'long', day: 'numeric' });
        // }
    }
}
console.log("main.js geladen.");
