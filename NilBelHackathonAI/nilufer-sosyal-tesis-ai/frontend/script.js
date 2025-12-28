// 1. Backend adresimizi en başa yazıyoruz
const API_URL = "http://127.0.0.1:8001";
const API_BASE = API_URL; // İsim karmaşasını önlemek için eşitledik
let userNickname = null;
let html5QrScanner = null;

// Sayfa yüklendiğinde hiçbir şey yapma, giriş sonrası veri çekilecek

// 1. GİRİŞ SİSTEMİ
async function handleLogin() {
    const email = document.getElementById('email').value;
    const pass = document.getElementById('password').value;
    const errorEl = document.getElementById('login-error');

    if (!email || !pass) {
        errorEl.textContent = "Lütfen tüm alanları doldurun!";
        errorEl.style.display = 'block';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: email, password: pass })
        });
        const data = await response.json();

        if (data.status === 'success') {
            userNickname = email;
            document.getElementById('auth-panel').style.display = 'none';
            document.getElementById('main-app').style.display = 'block';
            document.getElementById('display-name').textContent = email;

            // Admin için belediye panelini göster
            if (email === 'admin@nilufer.bel.tr') {
                document.getElementById('belediye-tab').style.display = 'inline-block';
            }

            loadUserReservations();
            loadTesisler();
            getTumTesislerTahmin();
        } else {
            errorEl.textContent = "Giriş başarısız: " + data.message;
            errorEl.style.display = 'block';
        }
    } catch (error) {
        errorEl.textContent = "Backend'e bağlanılamadı: " + error.message;
        errorEl.style.display = 'block';
    }
}

// 2. TESİS LİSTESİ (Dropdown Düzeltmesi)
async function loadTesisler() {
    const select = document.getElementById('rez-tesis-id');
    try {
        const res = await fetch(`${API_BASE}/tesisler`);
        const data = await res.json();

        select.innerHTML = '<option value="">Seçim yapınız...</option>';
        // Backend liste döndürdüğü için data.tesisler yerine direkt data kullanıyoruz
        data.forEach(t => {
            let opt = document.createElement('option');
            opt.value = t.tesis_id; // Backend'den gelen anahtar ismiyle eşlendi
            opt.textContent = t.isim;
            select.appendChild(opt);
        });
    } catch (e) {
        select.innerHTML = '<option value="">Hata: Veri alınamadı</option>';
    }
}

// 3. QR OKUYUCU (Frontend Entegrasyonu)
function startScanner() {
    if (html5QrScanner) return; 

    html5QrScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });

    html5QrScanner.render((decodedText) => {
        document.getElementById('qr-status-text').textContent = "⏳ İşleniyor...";

        fetch(`${API_BASE}/qr/entry`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userNickname,
                tesis_id: parseInt(decodedText)
            })
        })
        .then(r => r.json())
        .then(data => {
            alert(data.status === "success" ? "✅ " + data.message : "❌ " + data.message);
            document.getElementById('qr-status-text').textContent = data.status === "success" ? "✅ Giriş Yapıldı!" : "❌ Giriş Reddedildi";
        })
        .catch(err => alert("Hata: Backend'e ulaşılamadı."));
    });
}

// 4. TAB SİSTEMİ
function showTab(tabId, event) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');
    if(event) event.currentTarget.classList.add('active');

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

        // data.tahminler yerine direkt data kullanıyoruz, eksik nokta düzeltildi
        data.forEach(t => {
            const dolulukYuzde = (t.doluluk_orani * 100).toFixed(0);
            container.innerHTML += `
                <div class="result-item" style="border-left: 5px solid ${t.doluluk_orani > 0.7 ? '#ff4b2b' : '#28a745'}">
                    <h3>🏛️ ${t.isim}</h3>
                    <p><strong>Tahmini Doluluk:</strong> %${dolulukYuzde}</p>
                    <p><strong>Durum:</strong> ${t.durum} | 🌡️ ${t.sicaklik}°C</p>
                </div>`;
        });
    } catch (e) {
        container.innerHTML = '<p style="color:red;">Veriler backendden çekilemedi.</p>';
    }
}

// 6. Konum alma
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(p => {
            document.getElementById('location-btn').textContent = "✅ Konum Alındı";
            document.getElementById('location-btn').style.background = "#28a745";
        });
    }
}

// 6. AKILLI SIRALAMA (Vatandaş Konumuna Göre)
async function getAkıllıSiralama() {
    const resultsContainer = document.getElementById('akilli-results');
    resultsContainer.innerHTML = "⏳ En uygun tesisler hesaplanıyor...";

    navigator.geolocation.getCurrentPosition(async (position) => {
        const { latitude, longitude } = position.coords;
        try {
            const res = await fetch(`${API_BASE}/akilli-siralama?lat=${latitude}&lon=${longitude}`);
            const data = await res.json();
            resultsContainer.innerHTML = '';
            data.oneriler.forEach(o => {
                resultsContainer.innerHTML += `
                    <div class="result-item">
                        <strong>${o.sira}. ${o.tesis_adi}</strong>
                        <p>💡 ${o.siralama_nedeni}</p>
                    </div>`;
            });
        } catch (e) {
            resultsContainer.innerHTML = '<p style="color:red;">Sıralama verisi alınamadı.</p>';
        }
    });
}

// 7. REZERVASYON OLUŞTURMA
async function createReservation() {
    const tesisId = document.getElementById('rez-tesis-id').value;
    const tarih = document.getElementById('rez-tarih').value;
    const saat = document.getElementById('rez-saat').value;

    if (!tesisId || !tarih || !saat) return alert("Alanları doldurun!");

    try {
        const res = await fetch(`${API_BASE}/rezervasyon-olustur`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userNickname, tesis_id: parseInt(tesisId), tarih, saat })
        });
        if (res.ok) { alert("✅ Başarılı!"); loadUserReservations(); }
    } catch (e) { alert("Hata!"); }
}

// 8. KULLANICI REZERVASYONLARINI YÜKLEME
async function loadUserReservations() {
    const container = document.getElementById('rezervasyon-results');
    try {
        const res = await fetch(`${API_BASE}/rezervasyonlarim/${userNickname}`);
        const data = await res.json();
        container.innerHTML = '';
        if (data.rezervasyonlar.length === 0) {
            container.innerHTML = '<p>Henüz rezervasyonunuz yok.</p>';
            return;
        }
        data.rezervasyonlar.forEach(r => {
            container.innerHTML += `<div class="result-item"><strong>${r.tesis_adi}</strong><br>${r.tarih} - Saat: ${r.saat}:00</div>`;
        });
    } catch (e) { container.innerHTML = 'Yüklenemedi.'; }
}

// 9. BELEDİYE FONKSİYONLARI
async function loadAllReservations() {
    const container = document.getElementById('belediye-results');
    try {
        const res = await fetch(`${API_BASE}/belediye/tum-rezervasyonlar`);
        const data = await res.json();
        container.innerHTML = '<h3>Tüm Rezervasyonlar</h3>';
        if (data.tum_rezervasyonlar.length === 0) {
            container.innerHTML += '<p>Henüz rezervasyon yok.</p>';
            return;
        }
        data.tum_rezervasyonlar.forEach(r => {
            container.innerHTML += `<div class="result-item"><strong>${r.tesis_adi}</strong><br>Kullanıcı: ${r.user_id}<br>${r.tarih} - Saat: ${r.saat}:00<br>Durum: ${r.durum}</div>`;
        });
    } catch (e) { container.innerHTML = 'Yüklenemedi.'; }
}

async function loadReservationStats() {
    const container = document.getElementById('belediye-results');
    try {
        const res = await fetch(`${API_BASE}/belediye/istatistikler`);
        const data = await res.json();
        container.innerHTML = '<h3>Rezervasyon İstatistikleri</h3>';
        const stats = data.istatistikler;
        container.innerHTML += `
            <div class="result-item">
                <strong>Toplam Rezervasyon:</strong> ${stats.toplam_rezervasyon}<br>
                <strong>Aktif Rezervasyon:</strong> ${stats.aktif_rezervasyon}<br>
                <strong>İptal Rezervasyon:</strong> ${stats.iptal_rezervasyon}
            </div>
        `;
        // Tesis bazlı istatistikler
        container.innerHTML += '<h4>Tesis Bazlı İstatistikler</h4>';
        for (const [tesisId, count] of Object.entries(stats.tesis_bazli)) {
            container.innerHTML += `<div class="result-item"><strong>Tesis ${tesisId}:</strong> ${count} rezervasyon</div>`;
        }
    } catch (e) { container.innerHTML = 'Yüklenemedi.'; }
}

// YÜK DENGELEME ANALİZİ
async function loadBalancingAnalysis() {
    const container = document.getElementById('belediye-results');
    try {
        const res = await fetch(`${API_BASE}/belediye/yuk-dengeleme`);
        const data = await res.json();
        container.innerHTML = '<h3>Yük Dengeleme Analizi</h3>';
        data.yuk_dengeleme_analizi.forEach(item => {
            const color = item.doluluk_orani > 0.8 ? '#ff4b2b' : item.doluluk_orani > 0.6 ? '#ffc107' : '#28a745';
            container.innerHTML += `
                <div class="result-item" style="border-left: 5px solid ${color}">
                    <strong>${item.tesis_adi}</strong><br>
                    Doluluk: %${(item.doluluk_orani * 100).toFixed(0)}<br>
                    Durum: ${item.durum}<br>
                    Öneri: ${item.oneri}
                </div>
            `;
        });
    } catch (e) { container.innerHTML = 'Yüklenemedi.'; }
}

// PERFORMANS RAPORU
async function loadPerformanceReport() {
    const container = document.getElementById('belediye-results');
    try {
        const res = await fetch(`${API_BASE}/belediye/performans-raporu`);
        const data = await res.json();
        container.innerHTML = '<h3>Performans Raporu</h3>';
        const report = data.performans_raporu;
        container.innerHTML += `
            <div class="result-item">
                <strong>Toplam Tesis:</strong> ${report.toplam_tesis}<br>
                <strong>Toplam Rezervasyon:</strong> ${report.toplam_rezervasyon}<br>
                <strong>Aktif Rezervasyon:</strong> ${report.aktif_rezervasyon}<br>
                <strong>Sistem Durumu:</strong> ${report.sistem_durumu}<br>
                <strong>Son Güncelleme:</strong> ${new Date(report.son_guncelleme).toLocaleString('tr-TR')}
            </div>
        `;
    } catch (e) { container.innerHTML = 'Yüklenemedi.'; }
}

// MODEL YENİDEN EĞİTİMİ
async function retrainModel() {
    const container = document.getElementById('belediye-results');
    container.innerHTML = '<h3>Model Yeniden Eğitimi</h3><p>Model eğitimi başlatılıyor...</p>';
    try {
        const res = await fetch(`${API_BASE}/belediye/model-egitim`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            container.innerHTML += '<div class="result-item" style="color: #28a745;">✅ Model başarıyla yeniden eğitildi!</div>';
        } else {
            container.innerHTML += '<div class="result-item" style="color: #dc3545;">❌ Model eğitimi başarısız.</div>';
        }
    } catch (e) {
        container.innerHTML += '<div class="result-item" style="color: #dc3545;">Hata: ' + e.message + '</div>';
    }
}

// GÜNLÜK İSTATİSTİKLER
async function loadDailyStats() {
    const container = document.getElementById('belediye-results');
    try {
        const res = await fetch(`${API_BASE}/belediye/gunluk-istatistikler`);
        const data = await res.json();
        container.innerHTML = '<h3>Günlük İstatistikler</h3>';
        const stats = data.gunluk_istatistikler;
        container.innerHTML += `
            <div class="result-item">
                <strong>Tarih:</strong> ${stats.tarih}<br>
                <strong>Günlük Rezervasyon:</strong> ${stats.gunluk_rezervasyon}<br>
                <strong>Günlük Giriş:</strong> ${stats.gunluk_giris}<br>
                <strong>En Popüler Tesis:</strong> ${stats.en_populer_tesis}
            </div>
        `;
    } catch (e) { container.innerHTML = 'Yüklenemedi.'; }
}

// TESİS QR YÖNETİMİ
async function manageFacilityQRs() {
    const container = document.getElementById('belediye-results');
    try {
        const res = await fetch(`${API_BASE}/belediye/tesis-qr-yonetimi`);
        const data = await res.json();
        container.innerHTML = '<h3>Tesis QR Yönetimi</h3>';
        data.tesis_qr_yonetimi.forEach(qr => {
            container.innerHTML += `
                <div class="result-item">
                    <strong>${qr.tesis_adi}</strong><br>
                    QR Kod: ${qr.qr_kod}<br>
                    Durum: ${qr.aktif ? 'Aktif' : 'Pasif'}
                </div>
            `;
        });
    } catch (e) { container.innerHTML = 'Yüklenemedi.'; }
}
