"""
Etkinlik Yönetimi - Nilüfer'deki Etkinliklerin Sistem Üzerinde Gösterilmesi

Bu modül:
- Nilüfer ilçesindeki etkinlikleri yönetir
- Etkinlik bilgilerini AI modeline girdi olarak kullanır
- Vatandaşlara etkinlik takvimi sunar
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class EventManager:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.events_file = os.path.join(self.data_dir, "etkinlikler.json")

        # Etkinlik dosyası yoksa oluştur
        if not os.path.exists(self.events_file):
            self._create_sample_events()

        self.events = self._load_events()

    def _create_sample_events(self):
        """Örnek etkinlikler oluştur"""
        sample_events = [
            {
                "id": 1,
                "baslik": "Nilüfer Kültür Festivali",
                "aciklama": "İlçemizdeki kültür mirasını tanıtmak için düzenlediğimiz festival",
                "tarih": "2025-12-25",
                "saat": "14:00",
                "yer": "Nilüfer Kent Müzesi",
                "tesis_id": 3,
                "etki_orani": 0.3,  # Doluluk artış etkisi (%30)
                "katilimci_sayisi": 500,
                "aktif": True
            },
            {
                "id": 2,
                "baslik": "Gençlik Buluşması",
                "aciklama": "Gençlerimizin bir araya geldiği sosyal etkinlik",
                "tarih": "2025-12-26",
                "saat": "16:00",
                "yer": "Beşevler Gençlik Merkezi",
                "tesis_id": 10,
                "etki_orani": 0.4,
                "katilimci_sayisi": 200,
                "aktif": True
            },
            {
                "id": 3,
                "baslik": "Kitap Fuarı",
                "aciklama": "Yerel yazarların katılımıyla kitap fuarı",
                "tarih": "2025-12-27",
                "saat": "10:00",
                "yer": "Nilbel Koza Kütüphanesi",
                "tesis_id": 1,
                "etki_orani": 0.25,
                "katilimci_sayisi": 300,
                "aktif": True
            }
        ]

        with open(self.events_file, 'w', encoding='utf-8') as f:
            json.dump(sample_events, f, indent=2, ensure_ascii=False)

    def _load_events(self) -> List[Dict]:
        """Etkinlikleri dosyadan yükle"""
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _save_events(self):
        """Etkinlikleri dosyaya kaydet"""
        with open(self.events_file, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)

    def get_active_events(self, date: Optional[str] = None) -> List[Dict]:
        """Belirtilen tarihteki aktif etkinlikleri döndür"""
        active_events = [e for e in self.events if e.get("aktif", True)]

        if date:
            active_events = [e for e in active_events if e["tarih"] == date]

        return active_events

    def get_events_by_tesis(self, tesis_id: int) -> List[Dict]:
        """Belirli bir tesisteki etkinlikleri döndür"""
        return [e for e in self.events if e.get("tesis_id") == tesis_id and e.get("aktif", True)]

    def add_event(self, event_data: Dict) -> Dict:
        """Yeni etkinlik ekle"""
        # ID'yi otomatik belirle
        max_id = max([e.get("id", 0) for e in self.events], default=0)
        event_data["id"] = max_id + 1
        event_data["aktif"] = True

        self.events.append(event_data)
        self._save_events()

        return {"status": "success", "event_id": event_data["id"]}

    def get_event_impact(self, tesis_id: int, date: str) -> float:
        """
        Belirli tarih ve tesisteki etkinliklerin doluluk etkisi
        AI modelinde kullanılmak üzere
        """
        events = self.get_events_by_tesis(tesis_id)
        date_events = [e for e in events if e["tarih"] == date]

        if not date_events:
            return 0.0

        # Etkinliklerin toplam etkisi (ortalama)
        total_impact = sum(e.get("etki_orani", 0.1) for e in date_events)
        return min(total_impact, 1.0)  # Max %100 etki

    def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """Yaklaşan etkinlikleri döndür"""
        today = datetime.now().date()
        end_date = today + timedelta(days=days)

        upcoming = []
        for event in self.events:
            if event.get("aktif", True):
                event_date = datetime.strptime(event["tarih"], "%Y-%m-%d").date()
                if today <= event_date <= end_date:
                    upcoming.append(event)

        return sorted(upcoming, key=lambda x: x["tarih"])

# Global instance
event_manager = EventManager()

if __name__ == "__main__":
    print("Etkinlik Yönetimi Test")
    print(f"Aktif etkinlik sayısı: {len(event_manager.get_active_events())}")
    print(f"Yaklaşan etkinlikler: {len(event_manager.get_upcoming_events())}")

    # Etkinlik etkisi testi
    impact = event_manager.get_event_impact(1, "2025-12-27")
    print(f"Kitap fuarı etkisi: {impact}")
