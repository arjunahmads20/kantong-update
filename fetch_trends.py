import os
import requests
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from trendspy import Trends

from app import app, db, Topic  # Mengimpor konteks aplikasi dan model

from dotenv import load_dotenv

load_dotenv()
-
AI_API_URL = "https://openrouter.ai/api/v1/chat/completions" 
AI_API_KEY = os.getenv("AI_API_KEY")
AI_MODEL = "deepseek/deepseek-chat-v3.1:free" 
AI_MODEL = "openai/gpt-oss-20b:free"

def get_ai_summary(title: str, context: str) -> str:
    """
    Mengirim judul ke AI untuk mendapatkan ringkasan.
    2. Teruskan data trend/topik/judul ke AI.
    3. Terima response dari deepseek.
    """
    datetime_date_now_str = datetime.now(ZoneInfo('Asia/Jakarta')).strftime("%d %B %Y")
    prompt = f"Buat ringkasan artikel/berita update, akurat dan terpercaya untuk hari ini, {datetime_date_now_str} dalam Bahasa Indonesia mengenai '{title}', konteksnya: [{context}]'. Buat dalam 1-2 paragraf singkat atau jika tidak memungkinkan, maka buat dalam beberapa kalimat."
    
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful news summarizer."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(AI_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        summary = data['choices'][0]['message']['content']
        return summary.strip()
        
    except requests.exceptions.RequestException as e:
        print(f"Error saat menghubungi AI API: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Struktur response dari AI tidak sesuai: {e}")
        return None



def fetch_and_save_trends():
    """
    Fungsi utama untuk mengambil tren, meringkas, dan menyimpan ke database.
    """
    with app.app_context(): # Butuh konteks aplikasi untuk akses database
        print("Memulai pengambilan data tren...")
        
        # 1. Ambil data trend (topik) menggunakan trendspy
        tr = Trends()
        try:
            trending_list = tr.trending_now(geo='ID')[:10]
            print(f"Berhasil mendapatkan {len(trending_list)} tren dari Google Trends.")
        except Exception as e:
            print(f"Gagal mengambil data dari Google Trends: {e}")
            return

        today = date.today()
        start_of_today = datetime.combine(today, datetime.min.time()) # Midnight of today
        tomorrow = today + timedelta(days=1)
        start_of_tomorrow = datetime.combine(tomorrow, datetime.min.time())

        new_topics_count = 0
        for trending in trending_list:
            keyword = trending.keyword
            topic_names = trending.topic_names
            r_keywords = trending.trend_keywords # related keywords
            if len(r_keywords) > 10:
                r_keywords = r_keywords[:10]

            title = f"{keyword} - {topic_names[0]}"
            # Cek apakah topik sudah ada di database
            exists = db.session.query(Topic.title).filter(
                Topic.title==title, 
                Topic.datetime_added >= start_of_today, 
                Topic.datetime_added < start_of_tomorrow
            ).first() is not None
            if exists:
                print(f"Topik '{title}' sudah ada, dilewati.")
                continue

            context = ", ".join(r_keywords)

            print(f"Memproses topik baru: '{title}'...")
            summary = get_ai_summary(title, context)

            if summary:
                # 3. Simpan datanya ke database
                new_topic = Topic(
                    title=title,
                    context=context,
                    aiSummarization=summary
                )
                db.session.add(new_topic)
                new_topics_count += 1
                print(f"Berhasil mendapatkan ringkasan untuk '{title}'.")
        
        if new_topics_count > 0:
            db.session.commit()
            print(f"Berhasil menyimpan {new_topics_count} topik baru ke database.")
        else:
            print("Tidak ada topik baru untuk ditambahkan.")

if __name__ == '__main__':
    fetch_and_save_trends()
