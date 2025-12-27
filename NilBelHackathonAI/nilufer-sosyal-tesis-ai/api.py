import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, request, jsonify
from flask_cors import CORS
# 'model' yerine klasörün gerçek adı olan 'ai' yazıyoruz
from ai.predict import predict_occupancy
import os

app = Flask(__name__)
CORS(app) # Web sitesinden gelen isteklere izin ver

@app.route('/tahmin', methods=['GET'])
def get_tahmin():
    """
    Web sitesinden gelen Tesis ID'sine göre doluluk tahmini döner.
    Örnek kullanım: http://localhost:5001/tahmin?id=1
    """
    tesis_id = request.args.get('id', default=1, type=int)
    
    try:
        # Mevcut predict.py dosyasındaki fonksiyonu çağırıyoruz
        sonuc = predict_occupancy(tesis_id=tesis_id)
        
        if "HATA" in sonuc:
            return jsonify({"status": "error", "message": sonuc}), 500
            
        return jsonify({
            "status": "success",
            "data": sonuc
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Flask sunucusunu 5001 portunda başlat
    print("--- Nilüfer Belediyesi AI Tahmin API Başlatıldı ---")
    app.run(host='0.0.0.0', port=5001, debug=True)