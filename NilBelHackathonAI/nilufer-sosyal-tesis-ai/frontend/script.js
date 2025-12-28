const API_BASE = 'http://localhost:8000';
let userEmail = null;
let userRole = null;
let html5QrScanner = null;

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

// 3. QR OKUYUCU (Frontend Entegrasyonu)
function startScanner() {
    if (html5QrScanner) return; // Zaten çalışıyorsa tekrar başlatma

    html5QrScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });

    html5QrScanner.render((decodedText) => {
        // QR okunduğunda backend'e yolla
        document.getElementById('qr-status-text').textContent = "⏳ İşleniyor...";

        fetch(`${API_BASE}/qr-scan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tesis_id: parseInt(decodedText),
                qr_data: `QR_SCAN_${Date.now()}`
            })
        })
            .then(r => r.json())
            .then(data => {
                alert("Giriş Başarılı: " + (data.message || "Tesis girişi yapıldı."));
                document.getElementById('qr-status-text').textContent = "✅ Giriş Yapıldı!";
            })
            .catch(err => alert("Hata: Backend'e ulaşılamadı."));
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

// Konum alma
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(p => {
            document.getElementById('location-btn').textContent = "✅ Konum Alındı";
        });
    }
}
