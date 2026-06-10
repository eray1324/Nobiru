import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuración de Base de Datos simple (SQLite)
# Nota: En Render Free, la DB se reinicia al desplegar. Para algo permanente se usa Postgres, 
# pero para empezar, SQLite es lo más sencillo.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comunidad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

# --- MODELOS (Base de datos) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)
    level = db.Column(db.String(20), default="Bronce")

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(200))
    filename = db.Column(db.String(100))
    file_type = db.Column(db.String(10)) # pdf o video

# --- RUTAS ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/quiz-data')
def get_quiz():
    # Aquí cargamos las 10 preguntas que pediste
    questions = [
        {"q": "¿2 + 2?", "a": "4", "options": ["3","4","5","6"]},
        {"q": "¿Capital de México?", "a": "CDMX", "options": ["Guadalajara","Monterrey","CDMX","Puebla"]},
        {"q": "¿Días de la semana?", "a": "7", "options": ["5","6","7","8"]},
        {"q": "¿Planeta donde vivimos?", "a": "Tierra", "options": ["Marte","Venus","Júpiter","Tierra"]},
        {"q": "¿10 ÷ 2?", "a": "5", "options": ["2","4","5","8"]},
        {"q": "¿Cuál es un ser vivo?", "a": "Árbol", "options": ["Piedra","Árbol","Mesa","Lápiz"]},
        {"q": "¿Horas de un día?", "a": "24", "options": ["12","18","24","30"]},
        {"q": "¿Azul + Amarillo?", "a": "Verde", "options": ["Verde","Rojo","Morado","Negro"]},
        {"q": "¿Símbolo del agua?", "a": "H2O", "options": ["CO2","O2","H2O","NaCl"]},
        {"q": "¿5 × 3?", "a": "15", "options": ["8","10","15","20"]}
    ]
    return jsonify(questions)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
