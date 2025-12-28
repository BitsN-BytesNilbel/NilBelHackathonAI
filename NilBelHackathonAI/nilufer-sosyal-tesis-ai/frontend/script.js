const API_BASE = 'http://localhost:8000';
let userEmail = null;
let userRole = null;
let html5QrScanner = null;
let map = null;
let userLocationMarker = null;
let allMarkers = [];
let currentFilter = '';

// 1. GİRİŞ SİSTEMİ - BACKEND İLE ENTEGRASYON
async function handleLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');

    if (!email || !password) {
        errorDiv.textContent = "Lütfen e-posta ve şifre girin!";
        errorDiv.style.display = 'block';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            // Giriş başarılı
            userEmail = email;
            userRole = data.role;

            // Giriş panelini gizle
            document.getElementById('auth-panel').style.display = 'none';
            document.getElementById('main-app').style.display = 'block';

            // Kullanıcı bilgilerini göster
            document.getElementById('display-name').textContent = email.split('@')[0];

            // Rol tabanlı sekme gösterimi
            setupRoleBasedUI();

            // Uygulama başlayınca verileri çek
            loadTesisler();
            getTumTesislerTahmin();

            console.log(`Giriş başarılı: ${userRole} rolü`);

        } else {
            // Giriş hatası
            errorDiv.textContent = data.detail || "Giriş bilgileri hatalı!";
            errorDiv.style.display = 'block';
        }

    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = "Sunucuya bağlanılamadı. Lütfen backend'in çalıştığından emin olun.";
        errorDiv.style.display = 'block';
    }
}

// 2. ROL TABANLI UI AYARLARI
function setupRoleBasedUI() {
    const navTabs = document.querySelector('.nav-tabs');

    if (userRole === 'admin') {
        // Belediye personeli için yönetim sekmesi ekle
        const adminTab = document.createElement('button');
        adminTab.className = 'tab-btn';
        adminTab.textContent = 'Belediye Paneli';
        adminTab.onclick = () => showTab('belediye-paneli');

        navTabs.appendChild(adminTab);

        // Belediye paneli içeriğini oluştur
        createAdminPanel();
    }
}

// 3. BELEDİYE YÖNETİM PANELİ OLUŞTUR
function createAdminPanel() {
    const adminSection = document.createElement('section');
    adminSection.id = 'belediye-paneli';
    adminSection.className = 'tab-content';

    adminSection.innerHTML = `
        <div class="controls">
            <h3>🏛️ Belediye Yönetim Paneli</h3>
            <div class="admin-controls">
                <button onclick="getLoadBalancing()">⚖️ Yük Dengeleme Analizi</button>
                <button onclick="getPerformanceReport()">📈 Performans Raporu</button>
                <button onclick="triggerRetraining()">🔄 Model Yeniden Eğitimi</button>
                <button onclick="getDailyStats()">📊 Günlük İstatistikler</button>
            </div>
        </div>

        <div class="results">
            <h2>📋 Yönetim Raporları</h2>
            <div id="admin-results" class="results-container">
                <div class="tesis-card">
                    <h3>Belediye Yönetim Paneli</h3>
                    <p>Yukarıdaki butonları kullanarak sistem analizi yapabilirsiniz.</p>
                </div>
            </div>
        </div>
    `;

    document.querySelector('main').appendChild(adminSection);
}

// 4. BELEDİYE PANEL FONKSİYONLARI
async function getLoadBalancing() {
    const container = document.getElementById('admin-results');

    try {
        const response = await fetch(`${API_BASE}/belediye/yuk-dengeleme`);
        const data = await response.json();

        container.innerHTML = '<h3>⚖️ Yük Dengeleme Önerileri</h3>';

        if (data.oneriler && data.oneriler.length > 0) {
            data.oneriler.forEach(oneri => {
                container.innerHTML += `
                    <div class="tesis-card ${oneri.type === 'warning' ? 'doluluk-yuksek' : 'doluluk-dusuk'}">
                        <h4>${oneri.tesis}</h4>
                        <p>${oneri.message}</p>
                        <small><strong>Öneri:</strong> ${oneri.action}</small>
                    </div>
                `;
            });
        } else {
            container.innerHTML += '<p>Yük dengeleme önerisi bulunmuyor.</p>';
        }

    } catch (error) {
        container.innerHTML = '<p style="color:red;">Yük dengeleme verisi alınamadı.</p>';
    }
}

async function getPerformanceReport() {
    const container = document.getElementById('admin-results');

    try {
        const response = await fetch(`${API_BASE}/performance`);
        const data = await response.json();

        container.innerHTML = `
            <h3>📈 AI Model Performansı</h3>
            <div class="tesis-card">
                <h4>Genel İstatistikler</h4>
                <p><strong>Toplam Tahmin:</strong> ${data.total_predictions || 0}</p>
                <p><strong>Ortalama Hata:</strong> ${data.overall_stats?.average_error || 'N/A'}%</p>
                <p><strong>Doğruluk:</strong> ${data.recent_performance?.accuracy_assessment || 'N/A'}</p>
            </div>
        `;

    } catch (error) {
        container.innerHTML = '<p style="color:red;">Performans raporu alınamadı.</p>';
    }
}

async function triggerRetraining() {
    const container = document.getElementById('admin-results');

    if (!confirm('Model yeniden eğitimi başlatılsın mı? Bu işlem zaman alabilir.')) {
        return;
    }

    container.innerHTML = '<div class="tesis-card">⏳ Model yeniden eğitiliyor...</div>';

    try {
        const response = await fetch(`${API_BASE}/retrain`);
        const data = await response.json();

        container.innerHTML = `
            <div class="tesis-card doluluk-dusuk">
                <h4>✅ Model Güncellendi</h4>
                <p>${data.message || 'Model başarıyla yeniden eğitildi.'}</p>
            </div>
        `;

    } catch (error) {
        container.innerHTML = '<p style="color:red;">Model eğitimi başlatılamadı.</p>';
    }
}

async function getDailyStats() {
    const container = document.getElementById('admin-results');

    try {
        const response = await fetch(`${API_BASE}/daily-stats`);
        const data = await response.json();

        container.innerHTML = `
            <h3>📊 Günlük Giriş İstatistikleri</h3>
            <div class="tesis-card">
                <h4>Bugünkü Özet</h4>
                <p><strong>Toplam Giriş:</strong> ${data.total_entries}</p>
                <p><strong>En Popüler Tesis:</strong> ${data.most_popular_facility || 'Yok'}</p>
                <p><strong>Tarih:</strong> ${data.date}</p>
            </div>
        `;

        // Tesis bazlı istatistikler
        for (const [tesisId, count] of Object.entries(data.facility_breakdown || {})) {
            if (count > 0) {
                container.innerHTML += `
                    <div class="tesis-card">
                        <h4>Tesis ${tesisId}</h4>
                        <p><strong>Giriş Sayısı:</strong> ${count}</p>
                    </div>
                `;
            }
        }

    } catch (error) {
        container.innerHTML = '<p style="color:red;">Günlük istatistikler alınamadı.</p>';
    }
}

// 2. TESİS LİSTESİ (Dropdown Düzeltmesi)
async function loadTesisler() {
    const select = document.getElementById('rez-tesis-id');
    try {
        const res = await fetch(`${API_BASE}/tesisler`);
        const data = await res.json();

        select.innerHTML = '<option value="">Seçim yapınız...</option>';
        data.tesisler.forEach(t => {
            let opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.isim;
            select.appendChild(opt);
        });
    } catch (e) {
        select.innerHTML = '<option value="">Hata: Veri alınamadı</option>';
    }
}

// 3. QR OKUYUCU (Frontend Entegrasyonu) - GERÇEK VERİ LOGLAMA İLE
function startScanner() {
    if (html5QrScanner) return; // Zaten çalışıyorsa tekrar başlatma

    html5QrScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });

    html5QrScanner.render((decodedText) => {
        // QR kod içeriği: "TESIS_{tesis_id}_{doluluk_orani}" formatında olmalı
        // Örnek: "TESIS_1_75.5"
        document.getElementById('qr-status-text').textContent = "⏳ QR kod işleniyor...";

        try {
            const parts = decodedText.split('_');
            if (parts.length >= 3 && parts[0] === 'TESIS') {
                const tesis_id = parseInt(parts[1]);
                const doluluk_orani = parseFloat(parts[2]);

                if (isNaN(tesis_id) || isNaN(doluluk_orani)) {
                    throw new Error('Geçersiz QR kod formatı');
                }

                // Gerçek veri loglama endpoint'ini kullan
                fetch(`${API_BASE}/log-real-data`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tesis_id: tesis_id,
                        doluluk_orani: doluluk_orani
                    })
                })
                    .then(r => r.json())
                    .then(data => {
                        if (data.status === 'success') {
                            document.getElementById('qr-status-text').textContent = `✅ ${data.tesis} - Veri kaydedildi!`;
                            // 2 saniye sonra mesajı temizle
                            setTimeout(() => {
                                document.getElementById('qr-status-text').textContent = "📷 QR kod bekleniyor...";
                            }, 2000);
                        } else {
                            document.getElementById('qr-status-text').textContent = `❌ Hata: ${data.message}`;
                        }
                    })
                    .catch(err => {
                        console.error('QR log error:', err);
                        document.getElementById('qr-status-text').textContent = "❌ Backend bağlantı hatası!";
                    });

            } else {
                document.getElementById('qr-status-text').textContent = "❌ Geçersiz QR kod formatı!";
            }

        } catch (error) {
            console.error('QR parse error:', error);
            document.getElementById('qr-status-text').textContent = "❌ QR kod okunamadı!";
        }
    });
}

// 4. TAB SİSTEMİ
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');

    // Eğer QR sekmesine tıklandıysa kamerayı aç
    if (tabId === 'qr-giris') {
        startScanner();
    }
}

// 5. TÜM TESİS TAHMİNLERİ (Sadeleştirilmiş)
async function getTumTesislerTahmin() {
    const container = document.getElementById('tum-tesis-results');
    try {
        const res = await fetch(`${API_BASE}/tum-tesisler-tahmin`);
        const data = await res.json();
        container.innerHTML = '';

        data.tahminler.forEach(t => {
            container.innerHTML += `
                <div class="tesis-card doluluk-dusuk">
                    <h3>${t.tesis_adi}</h3>
                    <p><strong>Tahmini Doluluk:</strong> ${t.doluluk_orani}</p>
                    <p><strong>Sıcaklık:</strong> ${t.hava_sicakligi}</p>
                </div>`;
        });
    } catch (e) {
        container.innerHTML = '<p style="color:red;">Veriler backendden çekilemedi.</p>';
    }
}

// ========== HARİTA SİSTEMİ ==========

// Harita renkleri (tesis türlerine göre)
const markerColors = {
    'kütüphane': 'blue',
    'müze': 'red',
    'kafe': 'green',
    'lokanta': 'purple',
    'gençlik merkezi': 'orange'
};

// Harita başlatma
function initializeMap() {
    if (map) return; // Zaten başlatılmışsa

    // Bursa merkezli harita oluştur
    map = L.map('map-container').setView([40.1821, 29.0677], 12); // Bursa koordinatları

    // OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Tesis işaretlerini ekle
    loadTesisMarkers();
}

// Tesis işaretlerini yükle
async function loadTesisMarkers() {
    try {
        const response = await fetch(`${API_BASE}/tesisler`);
        const data = await response.json();

        data.tesisler.forEach(tesis => {
            if (tesis.koordinat) {
                const markerColor = markerColors[tesis.tesis_tipi] || 'blue';

                // Özel marker icon'u oluştur
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: `<div style="background-color: ${markerColor}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>`,
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                });

                const marker = L.marker([tesis.koordinat.lat, tesis.koordinat.lng], { icon: icon })
                    .addTo(map)
                    .bindPopup(`
                        <div style="font-family: Arial, sans-serif; max-width: 200px;">
                            <h4 style="margin: 0 0 8px 0; color: #333;">${tesis.isim}</h4>
                            <p style="margin: 0 0 4px 0;"><strong>Tür:</strong> ${tesis.tesis_tipi}</p>
                            <p style="margin: 0 0 4px 0;"><strong>Kapasite:</strong> ${tesis.kapasite} kişi</p>
                            <p style="margin: 0 0 8px 0;"><strong>Adres:</strong> ${tesis.adres}</p>
                            <p style="margin: 0; font-size: 12px; color: #666;">${tesis.aciklama}</p>
                        </div>
                    `);

                // Marker'ı listeye ekle (filtreleme için)
                marker.tesisType = tesis.tesis_tipi;
                allMarkers.push(marker);
            }
        });

    } catch (error) {
        console.error('Tesis marker yükleme hatası:', error);
    }
}

// Kullanıcı konumunu göster
function showUserLocation() {
    const btn = document.getElementById('user-location-btn');

    if (!navigator.geolocation) {
        alert('Tarayıcınız konum özelliğini desteklemiyor.');
        return;
    }

    btn.textContent = '⏳ Konum alınıyor...';
    btn.disabled = true;

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            // Önceki marker'ı kaldır
            if (userLocationMarker) {
                map.removeLayer(userLocationMarker);
            }

            // Yeni marker ekle
            const userIcon = L.divIcon({
                className: 'user-marker',
                html: `<div style="background-color: #ff6b6b; width: 25px; height: 25px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.4); position: relative;">
                          <div style="position: absolute; top: -8px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 5px solid transparent; border-right: 5px solid transparent; border-bottom: 8px solid #ff6b6b;"></div>
                       </div>`,
                iconSize: [25, 25],
                iconAnchor: [12.5, 25]
            });

            userLocationMarker = L.marker([lat, lng], {
                icon: userIcon,
                title: 'Konumunuz'
            })
                .addTo(map)
                .bindPopup('<div style="text-align: center;"><strong>📍 Siz buradasınız!</strong></div>');

            // Haritayı konumunuza odakla
            map.setView([lat, lng], 15);

            btn.textContent = '✅ Konumunuz gösteriliyor';
            btn.disabled = false;

            // 5 saniye sonra buton metnini geri döndür
            setTimeout(() => {
                btn.textContent = '📍 Konumumu Göster';
            }, 5000);

        },
        (error) => {
            console.error('Konum alma hatası:', error);
            alert('Konum alınamadı: ' + error.message);
            btn.textContent = '❌ Konum alınamadı';
            btn.disabled = false;
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        }
    );
}

// Harita filtreleme
function filterMapMarkers() {
    const filterValue = document.getElementById('map-filter').value;
    currentFilter = filterValue;

    allMarkers.forEach(marker => {
        if (filterValue === '' || marker.tesisType === filterValue) {
            if (!map.hasLayer(marker)) {
                marker.addTo(map);
            }
        } else {
            if (map.hasLayer(marker)) {
                map.removeLayer(marker);
            }
        }
    });
}

// TAB SİSTEMİ GÜNCELLEME - Harita sekmesi için
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');

    // Eğer QR sekmesine tıklandıysa kamerayı aç
    if (tabId === 'qr-giris') {
        startScanner();
    }

    // Eğer harita sekmesine tıklandıysa haritayı başlat
    if (tabId === 'harita') {
        setTimeout(() => {
            initializeMap();
        }, 100);
    }
}

// Konum alma (güncellenmiş)
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(p => {
            document.getElementById('location-btn').textContent = "✅ Konum Alındı";
            // Harita varsa konum göster
            if (map) {
                showUserLocation();
            }
        });
    }
}
