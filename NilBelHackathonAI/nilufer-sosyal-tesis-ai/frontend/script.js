// API base URL - development için localhost
const API_BASE = 'http://localhost:8000';

// Sayfa yüklendiğinde
document.addEventListener('DOMContentLoaded', function() {
    console.log('Nilüfer Sosyal Tesis AI Frontend yüklendi');
    // Sayfa yüklendiğinde tesisleri yükle
    loadTesisler();
});

// Tesisleri yükle
async function loadTesisler() {
    try {
        const response = await fetch(`${API_BASE}/tesisler`);
        if (!response.ok) {
            throw new Error('Tesisler yüklenemedi');
        }
        const data = await response.json();
        console.log(`${data.count} tesis yüklendi`);
    } catch (error) {
        console.error('Tesis yükleme hatası:', error);
    }
}

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
            throw new Error(`API Hatası: ${response.status} - ${response.statusText}`);
        }

        const data = await response.json();
        displayResults(data.tahminler);

    } catch (error) {
        console.error('Tahmin hatası:', error);
        document.getElementById('results-container').innerHTML =
            '<div class="tesis-card" style="color: red; text-align: center; border: 2px solid #dc3545;">' +
            '<h3>❌ Bağlantı Hatası</h3>' +
            '<p>Backend API\'ye bağlanılamadı. Lütfen backend\'in çalıştığından emin olun.</p>' +
            '<p><strong>Kullanım:</strong> <code>cd backend && python app.py</code></p>' +
            '<p><small>Hata: ' + error.message + '</small></p>' +
            '</div>';
    } finally {
        // Loading gizle
        document.getElementById('loading').style.display = 'none';
    }
}

// Tek tesis için tahmin al
async function getTesisTahmin(tesisId) {
    const rezervasyon = document.getElementById('rezervasyon').value;
    const sinav = document.getElementById('sinav').checked ? 1 : 0;

    try {
        const response = await fetch(`${API_BASE}/tahmin/${tesisId}?rezervasyon=${rezervasyon}&sinav_vakti=${sinav}`);

        if (!response.ok) {
            throw new Error(`API Hatası: ${response.status}`);
        }

        const data = await response.json();

        // Sonucu göster
        const container = document.getElementById('results-container');
        container.innerHTML = '';

        const dolulukYuzde = parseFloat(data.doluluk_orani.replace('%', ''));
        let dolulukClass = 'doluluk-dusuk';

        if (dolulukYuzde >= 80) {
            dolulukClass = 'doluluk-yuksek';
        } else if (dolulukYuzde >= 60) {
            dolulukClass = 'doluluk-orta';
        }

        const card = document.createElement('div');
        card.className = `tesis-card ${dolulukClass}`;

        card.innerHTML = `
            <h3>${data.tesis_adi}</h3>
            <p><strong>Doluluk Oranı:</strong> ${data.doluluk_orani}</p>
            <p><strong>Hava Sıcaklığı:</strong> ${data.hava_sicakligi}</p>
            <p><small>Rezervasyon: ${data.parametreler.rezervasyon_sayisi}, Sınav Haftası: ${data.parametreler.sinav_haftasi ? 'Evet' : 'Hayır'}</small></p>
        `;

        container.appendChild(card);

    } catch (error) {
        console.error('Tek tesis tahmin hatası:', error);
        alert('Tahmin alınamadı: ' + error.message);
    }
}

// Sonuçları göster
function displayResults(tahminler) {
    const container = document.getElementById('results-container');

    tahminler.forEach(tahmin => {
        const dolulukYuzde = parseFloat(tahmin.doluluk_orani.replace('%', ''));
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
            <p><strong>Doluluk:</strong> ${tahmin.doluluk_orani}</p>
            <p><strong>Hava Sıcaklığı:</strong> ${tahmin.hava_sicakligi}</p>
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

// Input validasyonları
document.getElementById('rezervasyon').addEventListener('input', function(e) {
    const value = parseInt(e.target.value);
    if (value < 0) e.target.value = 0;
    if (value > 100) e.target.value = 100;
});
