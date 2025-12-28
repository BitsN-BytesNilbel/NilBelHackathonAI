const API_BASE = 'http://localhost:8000';
let userNickname = null;
let html5QrScanner = null;

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

    // Uygulama başlayınca verileri çek
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