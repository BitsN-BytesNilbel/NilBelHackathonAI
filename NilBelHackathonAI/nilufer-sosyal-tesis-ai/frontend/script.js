// 1. Backend adresimizi en başa yazıyoruz
const API_URL = "http://127.0.0.1:8001";
const API_BASE = API_URL; // İsim karmaşasını önlemek için eşitledik
let userNickname = null;
let html5QrScanner = null;

// --- 2. ADIM: TÜM TESİSLERİ YÜKLEME FONKSİYONU ---
async function tumTesisleriYukle() {
    const container = document.getElementById("tesis-listesi"); 
    if (!container) return; 

    try {
        const response = await fetch(`${API_URL}/tum-tesisler-tahmin`);
        const data = await response.json();
        
        container.innerHTML = ""; 
        
        // Backend direkt liste [] döndürdüğü için direkt data üzerinden dönüyoruz
        data.forEach(tesis => {
            const dolulukYuzde = (tesis.doluluk_orani * 100).toFixed(0);
            container.innerHTML += `
                <div class="tesis-kart">
                    <h3>${tesis.isim}</h3>
                    <div class="doluluk-bari">
                        <div class="doluluk-dolgu" style="width: ${dolulukYuzde}%"></div>
                    </div>
                    <p>Doluluk: %${dolulukYuzde}</p>
                    <span class="durum-badge ${tesis.durum.toLowerCase()}">${tesis.durum}</span>
                    <p class="hava-durumu">🌡️ ${tesis.sicaklik}°C</p>
                </div>`;
        });
    } catch (error) {
        console.error("Backend hatası:", error);
        container.innerHTML = "<p style='color:red;'>Veriler backendden çekilemedi.</p>";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    tumTesisleriYukle();
});

// 1. GİRİŞ SİSTEMİ
function handleLogin() {
    const nick = document.getElementById('username').value;
    const pass = document.getElementById('password').value;

    if (!nick || !pass) {
        alert("Lütfen tüm alanları doldurun!");
        return;
    }

    userNickname = nick;
    document.getElementById('auth-panel').style.display = 'none';
    document.getElementById('main-app').style.display = 'block';
    document.getElementById('display-name').textContent = nick;

    // Fonksiyonun içine düzgünce yerleştirildi
    loadUserReservations();
    loadTesisler();
    getTumTesislerTahmin();
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