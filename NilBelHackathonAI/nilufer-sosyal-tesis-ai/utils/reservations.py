"""
Rezervasyon Sistemi - Vatandaşların Tesis Rezervasyonu

Bu modül:
- Vatandaşların tesis rezervasyonu yapmasını sağlar
- Rezervasyon verilerini AI modeline girdi olarak kullanır
- Çift rezervasyonları önler
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

class ReservationSystem:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.reservations_file = os.path.join(self.data_dir, "rezervasyonlar.json")

        # Rezervasyon dosyası yoksa oluştur
        if not os.path.exists(self.reservations_file):
            self._create_empty_reservations()

        self.reservations = self._load_reservations()

    def _create_empty_reservations(self):
        """Boş rezervasyon dosyası oluştur"""
        with open(self.reservations_file, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    def _load_reservations(self) -> List[Dict]:
        """Rezervasyonları dosyadan yükle"""
        try:
            with open(self.reservations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _save_reservations(self):
        """Rezervasyonları dosyaya kaydet"""
        with open(self.reservations_file, 'w', encoding='utf-8') as f:
            json.dump(self.reservations, f, indent=2, ensure_ascii=False)

    def create_reservation(self, user_data: Dict) -> Dict:
        """
        Yeni rezervasyon oluştur

        Args:
            user_data: {
                "user_id": "string",
                "tesis_id": int,
                "tarih": "YYYY-MM-DD",
                "saat": int,
                "sure": int (saat),  # Rezervasyon süresi
                "kisi_sayisi": int
            }

        Returns:
            Rezervasyon sonucu
        """
        try:
            # Validasyon
            required_fields = ["user_id", "tesis_id", "tarih", "saat", "sure", "kisi_sayisi"]
            for field in required_fields:
                if field not in user_data:
                    return {"status": "error", "message": f"Eksik alan: {field}"}

            # Tesis kontrolü
            from .tesisler import get_tesis_by_id
            tesis = get_tesis_by_id(user_data["tesis_id"])
            if not tesis:
                return {"status": "error", "message": f"Tesis bulunamadı: {user_data['tesis_id']}"}

            # Tarih validasyonu (bugünden itibaren 30 güne kadar)
            rezervasyon_tarihi = datetime.strptime(user_data["tarih"], "%Y-%m-%d").date()
            bugun = datetime.now().date()
            max_tarih = bugun + timedelta(days=30)

            if rezervasyon_tarihi < bugun:
                return {"status": "error", "message": "Geçmiş tarih için rezervasyon yapılamaz"}
            if rezervasyon_tarihi > max_tarih:
                return {"status": "error", "message": "30 günden fazla ileriye rezervasyon yapılamaz"}

            # Çakışma kontrolü
            if self._check_conflict(user_data):
                return {"status": "error", "message": "Bu zaman diliminde çakışma var"}

            # Kapasite kontrolü (basit yaklaşım)
            mevcut_rezervasyonlar = self._get_reservations_for_time(
                user_data["tesis_id"], user_data["tarih"], user_data["saat"]
            )
            toplam_kisi = sum(r["kisi_sayisi"] for r in mevcut_rezervasyonlar) + user_data["kisi_sayisi"]

            if toplam_kisi > tesis["kapasite"] * 0.8:  # %80 kapasite limiti
                return {"status": "error", "message": "Yetersiz kapasite"}

            # Rezervasyon oluştur
            reservation_id = str(uuid.uuid4())[:8]

            reservation = {
                "id": reservation_id,
                "user_id": user_data["user_id"],
                "tesis_id": user_data["tesis_id"],
                "tesis_adi": tesis["isim"],
                "tarih": user_data["tarih"],
                "saat": user_data["saat"],
                "sure": user_data["sure"],
                "kisi_sayisi": user_data["kisi_sayisi"],
                "durum": "aktif",
                "olusturulma_tarihi": datetime.now().isoformat(),
                "iptal_tarihi": None
            }

            self.reservations.append(reservation)
            self._save_reservations()

            return {
                "status": "success",
                "reservation_id": reservation_id,
                "message": "Rezervasyon başarıyla oluşturuldu",
                "details": reservation
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def cancel_reservation(self, reservation_id: str, user_id: str) -> Dict:
        """Rezervasyon iptali"""
        try:
            for reservation in self.reservations:
                if reservation["id"] == reservation_id and reservation["user_id"] == user_id:
                    if reservation["durum"] == "aktif":
                        reservation["durum"] = "iptal_edildi"
                        reservation["iptal_tarihi"] = datetime.now().isoformat()
                        self._save_reservations()

                        return {"status": "success", "message": "Rezervasyon iptal edildi"}

                    else:
                        return {"status": "error", "message": "Rezervasyon zaten iptal edilmiş"}

            return {"status": "error", "message": "Rezervasyon bulunamadı"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_user_reservations(self, user_id: str) -> List[Dict]:
        """Kullanıcının rezervasyonları"""
        return [r for r in self.reservations if r["user_id"] == user_id]

    def get_reservations_for_date(self, tesis_id: int, tarih: str) -> List[Dict]:
        """Belirli tarih için tesis rezervasyonları"""
        return [
            r for r in self.reservations
            if r["tesis_id"] == tesis_id and r["tarih"] == tarih and r["durum"] == "aktif"
        ]

    def _check_conflict(self, new_reservation: Dict) -> bool:
        """Rezervasyon çakışması kontrolü"""
        mevcut_rezervasyonlar = self.get_reservations_for_date(
            new_reservation["tesis_id"], new_reservation["tarih"]
        )

        new_start = new_reservation["saat"]
        new_end = new_start + new_reservation["sure"]

        for rez in mevcut_rezervasyonlar:
            if rez["user_id"] == new_reservation["user_id"]:  # Aynı kullanıcı kontrolü
                continue

            existing_start = rez["saat"]
            existing_end = existing_start + rez["sure"]

            # Zaman çakışması kontrolü
            if (new_start < existing_end and new_end > existing_start):
                return True

        return False

    def _get_reservations_for_time(self, tesis_id: int, tarih: str, saat: int) -> List[Dict]:
        """Belirli saat için rezervasyonları döndür"""
        reservations = self.get_reservations_for_date(tesis_id, tarih)
        return [r for r in reservations if r["saat"] <= saat < r["saat"] + r["sure"]]

    def get_reservation_stats(self) -> Dict:
        """Rezervasyon istatistikleri"""
        aktif = len([r for r in self.reservations if r["durum"] == "aktif"])
        iptal = len([r for r in self.reservations if r["durum"] == "iptal_edildi"])

        # Tesis bazlı istatistikler
        tesis_stats = {}
        for tesis_id in set(r["tesis_id"] for r in self.reservations):
            tesis_rez = [r for r in self.reservations if r["tesis_id"] == tesis_id and r["durum"] == "aktif"]
            tesis_stats[tesis_id] = len(tesis_rez)

        return {
            "toplam_rezervasyon": len(self.reservations),
            "aktif_rezervasyon": aktif,
            "iptal_rezervasyon": iptal,
            "tesis_bazli": tesis_stats
        }

# Global instance
reservation_system = ReservationSystem()

def create_reservation(user_data):
    """Kolay kullanım için global fonksiyon"""
    return reservation_system.create_reservation(user_data)

def cancel_reservation(reservation_id, user_id):
    """Kolay kullanım için global fonksiyon"""
    return reservation_system.cancel_reservation(reservation_id, user_id)

if __name__ == "__main__":
    print("Rezervasyon Sistemi Test")

    # Rezervasyon oluşturma testi
    test_reservation = {
        "user_id": "test_user_123",
        "tesis_id": 1,
        "tarih": "2025-12-30",
        "saat": 14,
        "sure": 2,
        "kisi_sayisi": 3
    }

    result = reservation_system.create_reservation(test_reservation)
    print(f"Rezervasyon sonucu: {result}")

    # İstatistikler
    stats = reservation_system.get_reservation_stats()
    print(f"İstatistikler: {stats}")
