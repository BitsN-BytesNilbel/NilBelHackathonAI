// API base URL - development için localhost
const API_BASE = 'http://localhost:8000';

// Sayfa yüklendiğinde
document.addEventListener('DOMContentLoaded', function() {
    console.log('Nilüfer Sosyal Tesis AI Frontend yüklendi');
});

// Tüm tesisler için tahmin al
async function getTumTesislerTahmin() {
    const rezervasyon = document.getElementById('rezervasyon').value;
    const sinav = document.getElementById('sinav').checked ? 1 : 0;

    // Loading göster
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results-container').innerHTML = '';

    try {
        const response = await fetch(`${API_BASE}/tum-tesisler-tahmin?rezervasyon=${rezervasyon}&sinav_vakti=${sinav}`);
        
        if (!response.ok) {
            throw new Error(`API Hatası: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data.tahminler);

    } catch (error) {
        console.error('Tahmin hatası:', error);
        document.getElementById('results-container').innerHTML = 
            '<div class="tesis-card" style="color: red; text-align: center;">' +
            '<h3>❌ Bağlantı Hatası</h3>' +
            '<p>Backend API\'ye bağlanılamadı. Lütfen backend\'in çalıştığından emin olun.</p>' +
            '<p>Kullanım: python backend/app.py</p>' +
            '</div>';
    } finally {
        // Loading gizle
        document.getElementById('loading').style.display = 'none';
    }
}

// Sonuçları göster
function displayResults(tahminler) {
    const container = document.getElementById('results-container');
    
    tahminler.forEach(tahmin => {
        const dolulukYuzde = parseFloat(tahmin.doluluk.replace('%', ''));
        let dolulukClass = 'doluluk-dusuk';
        
        if (dolulukYuzde >= 80) {
            dolulukClass = 'doluluk-yuksek';
        } else if (dolulukYuzde >= 60) {
            dolulukClass = 'doluluk-orta';
        }

        const card = document.createElement('div');
        card.className = `tesis-card ${dolulukClass}`;
        
        card.innerHTML = `
            <h3>${tahmin.tesis_adi}</h3>
            <p><strong>Doluluk:</strong> ${tahmin.doluluk}</p>
            <p><strong>Hava Sıcaklığı:</strong> ${tahmin.sicaklik}</p>
        `;
        
        container.appendChild(card);
    });
}

// Klavye kısayolları
document.addEventListener('keydown', function(event) {
    // Enter tuşu ile tahmin al
    if (event.key === 'Enter') {
        getTumTesislerTahmin();
    }
});
