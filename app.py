import os
import random
from datetime import datetime
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'nobiru_secret_key_super_secreta' # Llave para encriptar las sesiones de usuario

DATABASE = 'nobiru.db'

# Lista de frases motivacionales (se selecciona una según el día del año)
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
    """Establece conexión con SQLite y devuelve filas accesibles por nombre de columna."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea la base de datos y sus tablas de forma automática al iniciar."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            insignia TEXT DEFAULT 'Bronce',
            puntos INTEGER DEFAULT 0
        )
    ''')
    
    # 2. Tabla de Cuestionarios (Quiz)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT
        )
    ''')
    
    # 3. Tabla de Preguntas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            pregunta TEXT NOT NULL,
            opcion_a TEXT NOT NULL,
            opcion_b TEXT NOT NULL,
            opcion_c TEXT NOT NULL,
            opcion_d TEXT NOT NULL,
            correcta TEXT NOT NULL,
            FOREIGN KEY (quiz_id) REFERENCES quizes(id)
        )
    ''')
    
    # Insertar Quiz de demostración si no existe
    cursor.execute("SELECT COUNT(*) FROM quizes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO quizes (titulo, descripcion) VALUES ('Quiz de Demostración General', 'Demuestra tus conocimientos básicos')")
        quiz_id = cursor.lastrowid
        
        preguntas_demo = [
            ("¿Cuál es el océano más grande del mundo?", "Atlántico", "Índico", "Pacífico", "Ártico", "C"),
            ("¿Qué país tiene forma de bota?", "España", "Italia", "Francia", "Portugal", "B"),
            ("¿Cuánto es 7 x 8?", "54", "56", "62", "64", "B"),
            ("¿Cuál es el planeta más cercano al Sol?", "Venus", "Marte", "Mercurio", "Tierra", "C"),
            ("¿Qué gas respiramos principalmente de forma vital?", "Oxígeno", "Nitrógeno", "Dióxido de Carbono", "Argón", "A"),
            ("¿Quién escribió 'Don Quijote de la Mancha'?", "Gabriel García Márquez", "Miguel de Cervantes", "Federico García Lorca", "Pablo Neruda", "B"),
            ("¿Cuál es el símbolo químico del agua?", "Ag", "H2O", "O2", "HO", "B"),
            ("¿En qué año descubrió Colón América?", "1492", "1592", "1392", "1500", "A"),
            ("¿Cuál es el animal terrestre más rápido?", "León", "Guepardo", "Tigre", "Antílope", "B"),
            ("¿Qué continente se encuentra en el Polo Sur?", "África", "Asia", "Antártida", "Europa", "C")
        ]
        for p in preguntas_demo:
            cursor.execute('''
                INSERT INTO preguntas (quiz_id, pregunta, opcion_a, opcion_b, opcion_c, opcion_d, correcta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (quiz_id, p[0], p[1], p[2], p[3], p[4], p[5]))
            
    conn.commit()
    conn.close()

# Inicializamos la Base de Datos automáticamente
init_db()

def obtener_frase_del_dia():
    """Selecciona una frase única usando el día del año como índice."""
    dia_del_ano = datetime.now().timetuple().tm_yday
    indice = dia_del_ano % len(FRASES)
    return FRASES[indice]

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    frase = obtener_frase_del_dia()
    
    # Consultar datos frescos del usuario
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    return render_template('index.html', frase=frase, usuario=usuario)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        
        if not user:
            # Registro automático ultra sencillo
            try:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO usuarios (email, username) VALUES (?, ?)', (email, username))
                conn.commit()
                user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
            except sqlite3.IntegrityError:
                flash('El nombre de usuario o correo ya está en uso.')
                conn.close()
                return redirect(url_for('login'))
                
        conn.close()
        
        # Iniciar sesión guardando datos en la cookie del navegador
        session['user_id'] = user['id']
        session['username'] = user['username']
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
    
    aciertos = 0
    errores = 0
    
    for p in preguntas:
        respuesta_usuario = request.form.get(f"pregunta_{p['id']}")
        if respuesta_usuario == p['correcta']:
            aciertos += 1
        else:
            errores += 1
            
    puntuacion = aciertos * 10
    
    # Sistema de actualización de Insignias según puntaje acumulado
    usuario_id = session['user_id']
    user_actual = conn.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    nuevos_puntos = user_actual['puntos'] + puntuacion
    
    # Escala de insignias
    insignia = 'Bronce'
    if nuevos_puntos >= 90: insignia = 'Diamante'
    elif nuevos_puntos >= 70: insignia = 'Platino'
    elif nuevos_puntos >= 50: insignia = 'Oro'
    elif nuevos_puntos >= 30: insignia = 'Plata'
    
    mensaje_insignia = None
    if insignia != user_actual['insignia']:
        mensaje_insignia = f"¡Felicidades! Has alcanzado la insignia de {insignia}."
        # Si baja (ejemplo simplificado) se gestionaría comparando rangos.
        
    conn.execute('UPDATE usuarios SET puntos = ?, insignia = ? WHERE id = ?', (nuevos_puntos, insignia, usuario_id))
    conn.commit()
    conn.close()
    
    return f"<h2>Resultado: {aciertos} Aciertos, {errores} Errores. Puntos ganados: {puntuacion}. Insignia: {insignia}</h2><br><a href='/'>Volver al Inicio</a>"

if __name__ == '__main__':
    app.run(debug=True)
