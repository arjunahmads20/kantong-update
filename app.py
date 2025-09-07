import os
from flask import Flask, render_template, request, jsonify # Tambahkan jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

# --- Konfigurasi Aplikasi ---
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'kantong_update.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Model Database ---
class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    context = db.Column(db.Text, nullable=False)
    aiSummarization = db.Column(db.Text, nullable=False)
    datetime_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Topic {self.title}>'
    
    # Metode baru untuk mengkonversi objek Topic ke dictionary/JSON
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'context': self.context,
            'aiSummarization': self.aiSummarization,
            'datetime_added': self.datetime_added.isoformat() # Format ISO untuk kompatibilitas JS
        }

# --- Alur Aplikasi (Routing) ---

# Rute untuk halaman utama (frontend akan mengambil data melalui API)
@app.route('/')
def index_page():
    # Cukup render template HTML dasar, tanpa mengirimkan data topik
    return render_template('index.html')

# Rute API untuk mengambil data topik (mengembalikan JSON)
@app.route('/api/topics', methods=['GET'])
def get_topics_api():
    keyword = request.args.get('keyword', '')
    
    query = Topic.query.order_by(Topic.datetime_added.desc())

    if keyword:
        search_term = f"%{keyword}%"
        query = query.filter(Topic.title.ilike(search_term))
        
    topics = query.all()
    
    # Konversi setiap objek Topic ke dictionary menggunakan metode to_dict()
    topics_data = [topic.to_dict() for topic in topics]
    
    # Mengembalikan data dalam format JSON
    return jsonify(topics_data)

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/privacy')
def privacy_page():
    return render_template('privacy.html')

@app.route('/terms')
def terms_page():
    return render_template('terms.html')


# --- Inisialisasi Database ---
@app.cli.command("init-db")
def init_db_command():
    """Membuat tabel database."""
    with app.app_context():
        db.create_all()
    print("Database telah diinisialisasi.")

if __name__ == '__main__':
    app.run(debug=True)
