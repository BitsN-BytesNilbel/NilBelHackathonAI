import sqlite3
from datetime import datetime, timedelta
import os

# Veritabanı dosya yolu
DB_PATH = os.path.join(os.path.dirname(__file__), "nilufer_tesis.db")

def init_db():
    """Veritabanını ve gerekli tabloları oluşturur."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Giriş kayıtları tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS giris_kayitlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id TEXT NOT NULL,
            tesis_id INTEGER NOT NULL,
            giris_zamani DATETIME NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def check_and_log_entry(user_id: str, tesis_id: int):
    """
    1.5 saat (90 dk) kuralını kontrol eder ve giriş başarılıysa kaydeder.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Kullanıcının son girişini sorgula
    doksan_dakika_once = datetime.now() - timedelta(minutes=90)
    
    cursor.execute('''
        SELECT giris_zamani FROM giris_kayitlari 
        WHERE kullanici_id = ? AND giris_zamani > ?
        ORDER BY giris_zamani DESC LIMIT 1
    ''', (user_id, doksan_dakika_once.strftime('%Y-%m-%d %H:%M:%S')))
    
    last_entry = cursor.fetchone()
    
    if last_entry:
        conn.close()
        return False, "1.5 saat içinde tekrar giriş yapamazsınız."
    
    # 2. Giriş uygunsa kaydet
    simdi = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO giris_kayitlari (kullanici_id, tesis_id, giris_zamani)
        VALUES (?, ?, ?)
    ''', (user_id, tesis_id, simdi))
    
    conn.commit()
    conn.close()
    return True, "Giriş başarılı! Keyifli vakit geçirmenizi dileriz."

# İlk çalıştırmada tabloyu oluştur
if __name__ == "__main__":
    init_db()
    print("Veritabanı hazır!")