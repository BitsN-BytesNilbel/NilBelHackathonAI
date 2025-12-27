// API base URL - development için localhost
const API_BASE = 'http://localhost:8000';

// Global değişkenler
let userLocation = null;
let tesisListesi = [];

// Sayfa yüklendiğinde
document.addEventListener('DOMContentLoaded', function() {
    console.log('Nilüfer Sosyal Tesis AI Vatandaş Platformu yüklendi');
    // Sayfa yüklendiğinde tesisleri yükle
    loadTesisler();
});

// Tab sistemi
function showTab(tabId) {
    // Tüm tab content'leri gizle
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Tüm tab button'larını normal yap
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Seçilen tab'ı göster ve button'u aktif yap
    document.getElementById(tabId).classList.add('active');
    event.target.classList.add('active');
}

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

// ========== AKILLI SIRALAMA ==========

// Konum alma
function getLocation() {
    const btn = document.getElementById('location-btn');
    btn.textContent = '⏳ Konum alınıyor...';
    btn.disabled = true;

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                userLocation = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
                };
                btn.textContent = '✅ Konum alındı';
                console.log('Konum alındı:', userLocation);
            },
            function(error) {
                console.error('Konum hatası:', error);
                btn.textContent = '❌ Konum alınamadı';
                alert('Konum alınamadı. Lütfen konum iznini kontrol edin.');
            }
        );
    } else {
        alert('Tarayıcınız konum özelliğini desteklemiyor.');
        btn.textContent = '📍 Konum Al';
        btn.disabled = false;
    }

    setTimeout(() => {
        btn.disabled = false;
        if (userLocation) {
            btn.textContent = '✅ Konum alındı';
        } else {
            btn.textContent = '📍 Konum Al';
        }
    }, 2000);
}

// Akıllı sıralama
async function getAkıllıSiralama() {
    const tercih = document.getElementById('tesis-tercih').value;
    const sayi = document.getElementById('onerilen-sayi').value;

    document.getElementById('loading').style.display = 'block';
    document.getElementById('akilli-results').innerHTML = '';

    try {
        let url = `${API_BASE}/akilli-siralama?top_n=${sayi}`;
        if (userLocation) {
            url += `&lat=${userLocation.lat}&lon=${userLocation.lon}`;
        }
        if (tercih) {
            url += `&tercih_edilen_tur=${tercih}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error(`API Hatası: ${response.status}`);

        const data = await response.json();
        displayAkıllıResults(data.oneriler);

    } catch (error) {
        console.error('Akıllı sıralama hatası:', error);
        document.getElementById('akilli-results').innerHTML =
            '<div class="tesis-card" style="color: red; text-align: center;">' +
            '<h3>❌ Akıllı Sıralama Hatası</h3>' +
            '<p>' + error.message + '</p>' +
            '</div>';
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Akıllı sonuçları göster
function displayAkıllıResults(oneriler) {
    const container = document.getElementById('akilli-results');

    oneriler.forEach(oneri => {
        const dolulukYuzde = parseFloat(oneri.doluluk_orani.replace('%', ''));
        let dolulukClass = 'doluluk-dusuk';

        if (dolulukYuzde >= 80) {
            dolulukClass = 'doluluk-yuksek';
        } else if (dolulukYuzde >= 60) {
            dolulukClass = 'doluluk-orta';
        }

        const card = document.createElement('div');
        card.className = `tesis-card ${dolulukClass}`;

        card.innerHTML = `
            <div class="rank-badge">${oneri.sira}</div>
            <h3>${oneri.tesis_adi}</h3>
            <p><strong>Tür:</strong> ${oneri.tesis_tipi}</p>
            <p><strong>Doluluk:</strong> ${oneri.doluluk_orani}</p>
            <p><strong>Kapasite:</strong> ${oneri.kapasite} kişi</p>
            <p><strong>Hava:</strong> ${oneri.hava_sicakligi}</p>
            <p><small><em>${oneri.siralama_nedeni}</em></small></p>
        `;

        container.appendChild(card);
    });
}

// ========== ETKINLIKLER ==========

async function getEtkinlikler() {
    const tarih = document.getElementById('etkinlik-gun').value;

    document.getElementById('etkinlik-results').innerHTML = '<div class="tesis-card">⏳ Etkinlikler yükleniyor...</div>';

    try {
        let url = `${API_BASE}/etkinlikler`;
        if (tarih) {
            url += `?date=${tarih}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error(`API Hatası: ${response.status}`);

        const data = await response.json();
        displayEtkinlikler(data.etkinlikler);

    } catch (error) {
        console.error('Etkinlik hatası:', error);
        document.getElementById('etkinlik-results').innerHTML =
            '<div class="tesis-card" style="color: red; text-align: center;">' +
            '<h3>❌ Etkinlik Yükleme Hatası</h3>' +
            '<p>' + error.message + '</p>' +
            '</div>';
    }
}

function displayEtkinlikler(etkinlikler) {
    const container = document.getElementById('etkinlik-results');
    container.innerHTML = '';

    if (etkinlikler.length === 0) {
        container.innerHTML = '<div class="tesis-card">Bu tarih için etkinlik bulunamadı.</div>';
        return;
    }

    etkinlikler.forEach(etkinlik => {
        const card = document.createElement('div');
        card.className = 'tesis-card';

        card.innerHTML = `
            <h3>🎪 ${etkinlik.baslik}</h3>
            <p>${etkinlik.aciklama}</p>
            <p><strong>Tarih:</strong> ${etkinlik.tarih}</p>
            <p><strong>Saat:</strong> ${etkinlik.saat}</p>
            <p><strong>Yer:</strong> ${etkinlik.yer}</p>
            <p><strong>Katılımcı:</strong> ${etkinlik.katilimci_sayisi} kişi</p>
        `;

        container.appendChild(card);
    });
}

// ========== REZERVASYONLAR ==========

// Sayfa yüklendiğinde tesisleri rezervasyon dropdown'ına ekle
document.addEventListener('DOMContentLoaded', function() {
    loadTesislerForReservation();
});

async function loadTesislerForReservation() {
    try {
        const response = await fetch(`${API_BASE}/tesisler`);
        const data = await response.json();

        const select = document.getElementById('rez-tesis-id');
        select.innerHTML = '<option value="">Tesis seçin</option>';

        data.tesisler.forEach(tesis => {
            const option = document.createElement('option');
            option.value = tesis.id;
            option.textContent = `${tesis.isim} (${tesis.tip})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Tesis yükleme hatası:', error);
    }
}

async function createReservation() {
    const userId = document.getElementById('rez-user-id').value;
    const tesisId = document.getElementById('rez-tesis-id').value;
    const tarih = document.getElementById('rez-tarih').value;
    const saat = parseInt(document.getElementById('rez-saat').value);
    const sure = parseInt(document.getElementById('rez-sure').value);
    const kisi = parseInt(document.getElementById('rez-kisi').value);

    if (!userId || !tesisId || !tarih) {
        alert('Lütfen tüm alanları doldurun!');
        return;
    }

    const reservationData = {
        user_id: userId,
        tesis_id: parseInt(tesisId),
        tarih: tarih,
        saat: saat,
        sure: sure,
        kisi_sayisi: kisi
    };

    try {
        const response = await fetch(`${API_BASE}/rezervasyon-olustur`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(reservationData)
        });

        const result = await response.json();

        if (response.ok) {
            alert(`✅ Rezervasyon oluşturuldu!\nRezervasyon ID: ${result.reservation_id}`);
            // Formu temizle
            document.getElementById('rez-user-id').value = '';
            document.getElementById('rez-tarih').value = '';
        } else {
            alert(`❌ Rezervasyon hatası: ${result.detail}`);
        }

    } catch (error) {
        console.error('Rezervasyon hatası:', error);
        alert('Rezervasyon oluşturulamadı: ' + error.message);
    }
}

async function getUserReservations() {
    const userId = document.getElementById('rez-user-lookup').value;

    if (!userId) {
        alert('Lütfen kullanıcı ID girin!');
        return;
    }

    document.getElementById('rezervasyon-results').innerHTML = '<div class="tesis-card">⏳ Rezervasyonlar yükleniyor...</div>';

    try {
        const response = await fetch(`${API_BASE}/rezervasyonlarim/${userId}`);
        const data = await response.json();

        displayReservations(data.rezervasyonlar);

    } catch (error) {
        console.error('Rezervasyon listesi hatası:', error);
        document.getElementById('rezervasyon-results').innerHTML =
            '<div class="tesis-card" style="color: red; text-align: center;">' +
            '<h3>❌ Rezervasyon Yükleme Hatası</h3>' +
            '<p>' + error.message + '</p>' +
            '</div>';
    }
}

function displayReservations(rezervasyonlar) {
    const container = document.getElementById('rezervasyon-results');
    container.innerHTML = '';

    if (rezervasyonlar.length === 0) {
        container.innerHTML = '<div class="tesis-card">Rezervasyon bulunamadı.</div>';
        return;
    }

    rezervasyonlar.forEach(rez => {
        const statusClass = rez.durum === 'aktif' ? 'doluluk-dusuk' : 'doluluk-yuksek';
        const statusText = rez.durum === 'aktif' ? 'Aktif' : 'İptal Edildi';

        const card = document.createElement('div');
        card.className = `tesis-card ${statusClass}`;

        card.innerHTML = `
            <h3>${rez.tesis_adi}</h3>
            <p><strong>Tarih:</strong> ${rez.tarih}</p>
            <p><strong>Saat:</strong> ${rez.saat}:00 (${rez.sure} saat)</p>
            <p><strong>Kişi:</strong> ${rez.kisi_sayisi}</p>
            <p><strong>Durum:</strong> ${statusText}</p>
            <p><small>Oluşturulma: ${new Date(rez.olusturulma_tarihi).toLocaleString('tr-TR')}</small></p>
            ${rez.durum === 'aktif' ? `<button onclick="cancelReservation('${rez.id}', '${rez.user_id}')">İptal Et</button>` : ''}
        `;

        container.appendChild(card);
    });
}

async function cancelReservation(reservationId, userId) {
    if (!confirm('Rezervasyonu iptal etmek istediğinizden emin misiniz?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/rezervasyon-iptal/${reservationId}?user_id=${userId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            alert('✅ Rezervasyon iptal edildi!');
            getUserReservations(); // Listeyi yenile
        } else {
            alert(`❌ İptal hatası: ${result.detail}`);
        }

    } catch (error) {
        console.error('İptal hatası:', error);
        alert('Rezervasyon iptal edilemedi: ' + error.message);
    }
}

// Input validasyonları
document.getElementById('rezervasyon').addEventListener('input', function(e) {
    const value = parseInt(e.target.value);
    if (value < 0) e.target.value = 0;
    if (value > 100) e.target.value = 100;
});
