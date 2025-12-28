// 1. Backend adresimizi en başa yazıyoruz
const API_URL = "http://127.0.0.1:8001";
const API_BASE = API_URL;
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
