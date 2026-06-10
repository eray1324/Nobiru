import os
import random
from datetime import datetime
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'nobiru_secret_key_super_secreta'
DATABASE = 'nobiru.db'

FRASES = [
    "El esfuerzo de hoy es el éxito de mañana.",
    "Cada pregunta resuelta te acerca a tu meta.",
    "Aprender es avanzar.",
    "La constancia supera al talento.",
    "Nunca subestimes una hora de estudio.",
    "Tu futuro comienza con lo que haces hoy.",
    "La disciplina vence a la motivación."
]

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea la base de datos con TODAS las tablas necesarias del ecosistema Nobiru."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            insignia TEXT DEFAULT 'Bronce',
            puntos INTEGER DEFAULT 0
        )
    ''')
    
    # 2. Cuestionarios y Preguntas
    cursor.execute('CREATE TABLE IF NOT EXISTS quizes (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, descripcion TEXT)')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, quiz_id INTEGER, pregunta TEXT NOT NULL,
            opcion_a TEXT NOT NULL, opcion_b TEXT NOT NULL, opcion_c TEXT NOT NULL, opcion_d TEXT NOT NULL,
            correcta TEXT NOT NULL, FOREIGN KEY (quiz_id) REFERENCES quizes(id)
        )
    ''')
    
    # 3. TABLA NUEVA: Comunidad (Foro de preguntas y respuestas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comunidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autor TEXT NOT NULL,
            contenido TEXT NOT NULL,
            tipo TEXT NOT NULL, -- 'pregunta' o 'consejo'
            fecha TEXT NOT NULL
        )
    ''')
    
    # 4. TABLA NUEVA: Biblioteca (Archivos PDF, Libros)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biblioteca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            autor TEXT NOT NULL,
            fecha TEXT NOT NULL,
            archivo_url TEXT DEFAULT '#'
        )
    ''')

    # 5. TABLA NUEVA: Reels (Videos educativos por categorías)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            categoria TEXT NOT NULL, -- 'Matemáticas', 'Historia', etc.
            video_url TEXT NOT NULL
        )
    ''')
    
    # Insertar Quiz demo si está vacío
    cursor.execute("SELECT COUNT(*) FROM quizes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO quizes (titulo, descripcion) VALUES ('Quiz de Demostración General', 'Demuestra tus conocimientos')")
        quiz_id = cursor.lastrowid
        preguntas_demo = [
            ("¿Cuánto es 7 x 8?", "54", "56", "62", "64", "B"),
            ("¿Cuál es el símbolo del agua?", "Ag", "H2O", "O2", "HO", "B"),
            ("¿En qué año se descubrió América?", "1492", "1592", "1392", "1500", "A")
        ]
        for p in preguntas_demo:
            cursor.execute('INSERT INTO preguntas (quiz_id, pregunta, opcion_a, opcion_b, opcion_c, opcion_d, correcta) VALUES (?,?,?,?,?,?,?)',
                           (quiz_id, p[0], p[1], p[2], p[3], p[4], p[5]))
            
    conn.commit()
    conn.close()

init_db()

def obtener_frase_del_dia():
    dia_del_ano = datetime.now().timetuple().tm_yday
    return FRASES[dia_del_ano % len(FRASES)]

# --- RUTAS ---

@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('index.html', frase=obtener_frase_del_dia(), usuario=usuario)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        if not user:
            try:
                conn.execute('INSERT INTO usuarios (email, username) VALUES (?, ?)', (email, username))
                conn.commit()
                user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
            except sqlite3.IntegrityError:
                conn.close()
                return "Error: Datos duplicados"
        session['user_id'] = user['id']
        session['username'] = user['username']
        conn.close()
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/quiz')
def quiz():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    preguntas = conn.execute('SELECT * FROM preguntas WHERE quiz_id = 1').fetchall()
    conn.close()
    return render_template('quiz.html', preguntas=preguntas)

@app.route('/calificar-quiz', methods=['POST'])
def calificar_quiz():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    preguntas = conn.execute('SELECT * FROM preguntas WHERE quiz_id = 1').fetchall()
    aciertos, errores = 0, 0
    for p in preguntas:
        if request.form.get(f"pregunta_{p['id']}") == p['correcta']: aciertos += 1
        else: errores += 1
    puntuacion = aciertos * 10
    
    user_actual = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    nuevos_puntos = user_actual['puntos'] + puntuacion
    
    insignia = 'Bronce'
    if nuevos_puntos >= 30: insignia = 'Oro'
    elif nuevos_puntos >= 10: insignia = 'Plata'
    
    conn.execute('UPDATE usuarios SET puntos = ?, insignia = ? WHERE id = ?', (nuevos_puntos, insignia, session['user_id']))
    conn.commit()
    conn.close()
    
    return render_template('resultado.html', aciertos=aciertos, errores=errores, puntos=puntuacion, insignia=insignia)

# --- RUTAS DE LAS NUEVAS SECCIONES ---

@app.route('/comunidad', methods=['GET', 'POST'])
def comunidad():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    if request.method == 'POST':
        contenido = request.form['contenido']
        tipo = request.form['tipo']
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        conn.execute('INSERT INTO comunidad (autor, contenido, tipo, fecha) VALUES (?, ?, ?, ?)',
                     (session['username'], contenido, tipo, fecha))
        conn.commit()
    posts = conn.execute('SELECT * FROM comunidad ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('comunidad.html', posts=posts)

@app.route('/biblioteca', methods=['GET', 'POST'])
def biblioteca():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        autor = request.form['autor']
        fecha = datetime.now().strftime("%d/%m/%Y")
        conn.execute('INSERT INTO biblioteca (titulo, descripcion, autor, fecha) VALUES (?, ?, ?, ?)',
                     (titulo, descripcion, autor, fecha))
        conn.commit()
    archivos = conn.execute('SELECT * FROM biblioteca ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('biblioteca.html', archivos=archivos)

@app.route('/reels', methods=['GET', 'POST'])
def reels():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    if request.method == 'POST':
        titulo = request.form['titulo']
        categoria = request.form['categoria']
        # En la web, simulamos la subida apuntando a un video demo local o de red
        video_url = "/static/videos/demo.mp4" 
        conn.execute('INSERT INTO reels (titulo, categoria, video_url) VALUES (?, ?, ?)', (titulo, categoria, video_url))
        conn.commit()
    videos = conn.execute('SELECT * FROM reels ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('reels.html', videos=videos)

if __name__ == '__main__':
    app.run(debug=True)
