import requests
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash # Seguridad avanzada

app = Flask(__name__)

# --- CONFIGURACIÓN ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:dangel232@localhost/base_pasantia_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'pomaray_2026_gst'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

IMGBB_API_KEY = "0e6901cb0c02a5f295b89eff4e86a61e"

# --- MEJORA: Control de Navegación (Evita volver atrás) ---
@app.after_request
def add_header(response):
    """Indica al navegador que no guarde copias locales de las páginas protegidas"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# --- MODELOS DE DATOS ---
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # Longitud para el hash

class Pasante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    empresa = db.Column(db.String(100), nullable=False)
    horas_completadas = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(20), default='Activo')
    dir_foto = db.Column(db.String(500))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

# Inicialización automática del sistema
with app.app_context():
    db.create_all()
    # Crear admin por defecto con contraseña segura si no existe
    if not Usuario.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('123')
        db.session.add(Usuario(username='admin', password=hashed_pw))
        db.session.commit()

def subir_a_imgbb(archivo):
    url = "https://api.imgbb.com/1/upload"
    payload = {"key": IMGBB_API_KEY}
    files = {"image": archivo.read()}
    try:
        response = requests.post(url, payload, files=files)
        if response.status_code == 200:
            return response.json()['data']['url']
    except Exception as e:
        print(f"Error en ImgBB: {e}")
    return None

# --- RUTAS DE SESIÓN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('bienvenida')) # No permite ver login si ya entró
        
    if request.method == 'POST':
        user = Usuario.query.filter_by(username=request.form.get('username')).first()
        # Verificación segura contra el Hash
        if user and check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('bienvenida'))
        flash('Credenciales incorrectas.', 'danger')
    return render_template('login.html')

@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if Usuario.query.filter_by(username=u).first():
            flash('Este usuario ya existe.', 'danger')
            return redirect(url_for('crear_usuario'))
            
        hashed_pw = generate_password_hash(p)
        db.session.add(Usuario(username=u, password=hashed_pw))
        db.session.commit()
        flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('crear_usuario.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- RUTAS PRINCIPALES ---

@app.route('/')
def home(): 
    # Redirección de seguridad: siempre a bienvenida si hay sesión
    return redirect(url_for('bienvenida'))

@app.route('/bienvenida')
@login_required
def bienvenida():
    # Panel con el video de introducción
    return render_template('bienvenida.html')

@app.route('/panel')
@login_required
def index():
    search = request.args.get('search')
    if search:
        estudiantes = Pasante.query.filter(Pasante.nombre.contains(search)).all()
    else:
        estudiantes = Pasante.query.all()
    return render_template('index.html', estudiantes=estudiantes)

@app.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar():
    if request.method == 'POST':
        foto = request.files.get('foto')
        url_foto = "https://via.placeholder.com/300x200?text=Sin+Foto"
        if foto and foto.filename != '':
            res = subir_a_imgbb(foto)
            if res: url_foto = res

        nuevo = Pasante(
            nombre=request.form.get('nombre'),
            empresa=request.form.get('empresa'),
            horas_completadas=int(request.form.get('horas') or 0),
            dir_foto=url_foto
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('registro.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    p = db.get_or_404(Pasante, id)
    if request.method == 'POST':
        p.nombre = request.form.get('nombre')
        p.empresa = request.form.get('empresa')
        p.horas_completadas = int(request.form.get('horas') or 0)
        nueva_foto = request.files.get('foto')
        if nueva_foto and nueva_foto.filename != '':
            res = subir_a_imgbb(nueva_foto)
            if res: p.dir_foto = res
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('editar.html', p=p)

@app.route('/reporte')
@login_required
def reporte():
    total = Pasante.query.count()
    suma = db.session.query(func.sum(Pasante.horas_completadas)).scalar() or 0
    listos = Pasante.query.filter(Pasante.horas_completadas >= 360).count()
    return render_template('reporte.html', total_e=total, horas=suma, listos=listos)

@app.route('/eliminar/<int:id>')
@login_required
def eliminar(id):
    p = db.session.get(Pasante, id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)