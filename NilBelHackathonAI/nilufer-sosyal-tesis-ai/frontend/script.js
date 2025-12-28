// 1. Backend adresimizi en başa yazıyoruz
const API_URL = "http://127.0.0.1:8001";
const API_BASE = API_URL; // İsim karmaşasını önlemek için eşitledik
let userNickname = null;
let html5QrScanner = null;

// TESİS TÜRÜ -> ÖNCELİKLİ MEKAN HARİTASI (SADECE EK)
const TESIS_TUR_HARITA = {
    "kütüphane": [
        "Nilbel Koza Kütüphanesi",
        "Şiir Kütüphanesi",
        "Akkılıç Kütüphanesi"
    ],
    "kafe": [
        "29 Ekim Kafe",
        "Kafe Pancar",
        "Nilüfer Kent Lokantası"
    ],
    "müze": [
        "Nilüfer Fotoğraf Müzesi",
        "Sağlık Müzesi",
        "Edebiyat Müzesi"
    ],
    "gençlik merkezi": [
        "Beşevler Gençlik Merkezi",
        "Altınşehir Gençlik Merkezi",
        "Cumhuriyet Gençlik Merkezi"
    ]
};

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
                showTab('belediye-yonetimi');
            } else {
                // Vatandaş için normal akış
                loadUserReservations();
                loadTesisler();
                getTumTesislerTahmin();
            }
        } else {
            errorEl.textContent = "Giriş başarısız: " + data.message;
            errorEl.style.display = 'block';
        }
    } catch (error) {
        errorEl.textContent = "Backend'e bağlanılamadı: " + error.message;
        errorEl.style.display = 'block';
    }
}

// 6. AKILLI SIRALAMA (SADECE EK YAPILDI)
async function getAkıllıSiralama() {
    const resultsContainer = document.getElementById('akilli-results');
    const secilenTur = document.getElementById('tesis-tercih').value;
    resultsContainer.innerHTML = "⏳ En uygun tesisler hesaplanıyor...";

    navigator.geolocation.getCurrentPosition(async (position) => {
        const { latitude, longitude } = position.coords;
        try {
            // Eğer bir tesis türü seçildiyse, sadece o türü iste
            let url = `${API_BASE}/akilli-siralama?lat=${latitude}&lon=${longitude}`;
            if (secilenTur) {
                url += `&tercih_edilen_tur=${encodeURIComponent(secilenTur)}`;
            }

            const res = await fetch(url);
            const data = await res.json();

            let oneriler = data.oneriler;

            // 🔥 EKLENEN AKILLI ÖNCELİKLENDİRME - GELİŞTİRİLMİŞ
            if (secilenTur && TESIS_TUR_HARITA[secilenTur]) {
                const oncelikliListe = TESIS_TUR_HARITA[secilenTur];

                // Öncelikli tesisleri bul ve sırala
                const oncelikliTesisler = [];
                oncelikliListe.forEach(priorityTesis => {
                    const found = oneriler.find(o => o.tesis_adi === priorityTesis);
                    if (found) {
                        oncelikliTesisler.push(found);
                    }
                });

                // Geri kalan tesisleri bul
                const digerTesisler = oneriler.filter(o => !oncelikliListe.includes(o.tesis_adi));

                // Birleştir: önce öncelikli tesisler, sonra diğerleri
                oneriler = [...oncelikliTesisler, ...digerTesisler];
            }

            // SIRALAYARAK YAZDIR
            resultsContainer.innerHTML = "";
            oneriler.forEach((o, index) => {
                resultsContainer.innerHTML += `
                    <div class="result-item">
                        <strong>${index + 1}. ${o.tesis_adi}</strong>
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

// TESİS QR YÖNETİMİ - Tıklama Özelliği Eklendi
async function manageFacilityQRs() {
    const container = document.getElementById('belediye-results');
    try {
        const res = await fetch(`${API_BASE}/belediye/tesis-qr-yonetimi`);
        const data = await res.json();
        container.innerHTML = '<h3>Tesis QR Yönetimi</h3><p style="font-size:12px; color:#666;">QR kodunu görmek için tesis adına tıklayın.</p>';
        data.tesis_qr_yonetimi.forEach(qr => {
            // TIKLAMA ÖZELLİĞİ: onclick="openFacilityQR(...)" eklendi
            container.innerHTML += `
                <div class="result-item" onclick="openFacilityQR(${qr.tesis_id}, '${qr.tesis_adi}')" style="cursor:pointer; transition: 0.3s; border: 2px solid #eee;">
                    <strong>${qr.tesis_adi}</strong><br>
                    QR Kod: ${qr.qr_kod}<br>
                    Durum: ${qr.aktif ? 'Aktif' : 'Pasif'}
                </div>
            `;
        });
    } catch (e) { container.innerHTML = 'Yüklenemedi.'; }
}

// --- EKSTRA EKLENEN QR MODAL FONKSİYONLARI ---

function openFacilityQR(id, isim) {
    const modal = document.getElementById('qr-modal');
    const canvas = document.getElementById('qrcode-canvas');
    
    // Eski QR'ı temizle
    canvas.innerHTML = "";
    document.getElementById('modal-tesis-adi').innerText = isim;
    document.getElementById('modal-tesis-id-text').innerText = "Tesis ID: " + id;

    // QR Kütüphanesini kullanarak yeni QR Üret
    new QRCode(canvas, {
        text: id.toString(), // QR içine sadece Tesis ID yazılır
        width: 200,
        height: 200,
        colorDark : "#000000",
        colorLight : "#ffffff",
        correctLevel : QRCode.CorrectLevel.H
    });

    modal.style.display = "flex";
}

function closeQR() {
    document.getElementById('qr-modal').style.display = "none";
}
