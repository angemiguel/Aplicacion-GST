import os
import requests
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, make_response, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash 

app = Flask(__name__)

# --- CONFIGURACIÓN ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:dangel232@localhost/base_pasantia_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'pomaray_2026_gst'
app.config['UPLOAD_FOLDER_PDF'] = os.path.join('static', 'uploads', 'reportes')
db = SQLAlchemy(app)

# Asegurar que la carpeta de reportes exista
os.makedirs(app.config['UPLOAD_FOLDER_PDF'], exist_ok=True)

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

@app.context_processor
def inject_now():
    return {'datetime': datetime}

from functools import wraps

# ... (configuración previa)

# --- MEJORA: Control de Roles ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('No tienes permisos para realizar esta acción.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

from datetime import datetime

# --- MODELOS DE DATOS ---
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='estudiante') # admin, docente, estudiante
    notificaciones_enviadas = db.relationship('Notificacion', backref='remitente', lazy=True)

class Notificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mensaje = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    leida = db.Column(db.Boolean, default=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

class ReporteExterno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Pasante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    empresa = db.Column(db.String(100), nullable=False)
    horas_completadas = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(20), default='Activo')
    descripcion = db.Column(db.String(255))
    dir_foto = db.Column(db.String(500))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    mapa_url = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

# Inicialización automática del sistema
with app.app_context():
    db.create_all()
    # Crear admin por defecto con rol admin si no existe
    if not Usuario.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('123')
        db.session.add(Usuario(username='admin', password=hashed_pw, rol='admin'))
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
        r = request.form.get('rol', 'estudiante')
        if Usuario.query.filter_by(username=u).first():
            flash('Este usuario ya existe.', 'danger')
            return redirect(url_for('crear_usuario'))
            
        hashed_pw = generate_password_hash(p)
        db.session.add(Usuario(username=u, password=hashed_pw, rol=r))
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
    search = request.args.get('search', '')
    if search:
        estudiantes = Pasante.query.filter(
            or_(
                Pasante.nombre.contains(search),
                Pasante.empresa.contains(search),
                Pasante.descripcion.contains(search)
            )
        ).all()
    else:
        estudiantes = Pasante.query.all()
    return render_template('index.html', estudiantes=estudiantes, search=search)

@app.route('/registrar', methods=['GET', 'POST'])
@login_required
@admin_required
def registrar():
    if request.method == 'POST':
        foto = request.files.get('foto')
        url_foto = "https://via.placeholder.com/300x200?text=Sin+Foto"
        if foto and foto.filename != '':
            res = subir_a_imgbb(foto)
            if res: url_foto = res

        m_url = request.form.get('mapa_url')
        if m_url and '<iframe' in m_url:
            import re
            match = re.search(r'src="([^"]+)"', m_url)
            if match: m_url = match.group(1)

        nuevo = Pasante(
            nombre=request.form.get('nombre'),
            empresa=request.form.get('empresa'),
            horas_completadas=int(request.form.get('horas') or 0),
            descripcion=request.form.get('descripcion'),
            dir_foto=url_foto,
            mapa_url=m_url
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('registro.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    p = db.get_or_404(Pasante, id)
    if request.method == 'POST':
        p.nombre = request.form.get('nombre')
        p.empresa = request.form.get('empresa')
        p.horas_completadas = int(request.form.get('horas') or 0)
        p.descripcion = request.form.get('descripcion')
        
        m_url = request.form.get('mapa_url')
        if m_url and '<iframe' in m_url:
            import re
            match = re.search(r'src="([^"]+)"', m_url)
            if match: m_url = match.group(1)
        p.mapa_url = m_url

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
    if current_user.rol not in ['admin', 'docente']:
        flash('No tienes permiso para ver los reportes.', 'danger')
        return redirect(url_for('index'))
        
    total = Pasante.query.count()
    suma = db.session.query(func.sum(Pasante.horas_completadas)).scalar() or 0
    listos = Pasante.query.filter(Pasante.horas_completadas >= 360).count()
    return render_template('reporte.html', total_e=total, horas=suma, listos=listos)

from flask import Flask, render_template, request, redirect, url_for, flash, make_response, jsonify

# ... (otras rutas)

@app.route('/enviar_notificacion', methods=['POST'])
@login_required
def enviar_notificacion():
    mensaje = request.form.get('mensaje')
    if mensaje:
        nueva = Notificacion(mensaje=mensaje, usuario_id=current_user.id)
        db.session.add(nueva)
        db.session.commit()
        flash('Mensaje enviado al administrador correctamente.', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/notificaciones')
@login_required
@admin_required
def ver_notificaciones():
    notis = Notificacion.query.order_by(Notificacion.fecha.desc()).all()
    return render_template('notificaciones.html', notificaciones=notis)

@app.route('/notificaciones/leer/<int:id>', methods=['POST'])
@login_required
@admin_required
def leer_notificacion(id):
    noti = db.get_or_404(Notificacion, id)
    noti.leida = True
    db.session.commit()
    return redirect(url_for('ver_notificaciones'))

@app.route('/api/notificaciones/nuevas')
@login_required
def api_notificaciones_nuevas():
    if current_user.rol != 'admin':
        return jsonify([])
    
    nuevas = Notificacion.query.filter_by(leida=False).all()
    res = [{
        'id': n.id,
        'mensaje': n.mensaje,
        'remitente': n.remitente.username,
        'fecha': n.fecha.strftime('%H:%M')
    } for n in nuevas]
    return jsonify(res)

@app.route('/reportes_externos')
@login_required
@admin_required
def reportes_externos():
    reportes = ReporteExterno.query.order_by(ReporteExterno.fecha.desc()).all()
    return render_template('reportes_externos.html', reportes=reportes)

@app.route('/subir_reporte_pdf', methods=['POST'])
@login_required
@admin_required
def subir_reporte_pdf():
    archivo = request.files.get('archivo')
    titulo = request.form.get('titulo')
    
    if archivo and archivo.filename.endswith('.pdf'):
        filename = secure_filename(archivo.filename)
        # Añadir timestamp para evitar colisiones
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        archivo.save(os.path.join(app.config['UPLOAD_FOLDER_PDF'], unique_filename))
        
        nuevo = ReporteExterno(titulo=titulo, nombre_archivo=unique_filename)
        db.session.add(nuevo)
        db.session.commit()
        flash('Reporte PDF subido correctamente.', 'success')
    else:
        flash('Por favor selecciona un archivo PDF válido.', 'danger')
    
    return redirect(url_for('reportes_externos'))

@app.route('/eliminar_reporte_pdf/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_reporte_pdf(id):
    reporte = db.get_or_404(ReporteExterno, id)
    try:
        ruta = os.path.join(app.config['UPLOAD_FOLDER_PDF'], reporte.nombre_archivo)
        if os.path.exists(ruta):
            os.remove(ruta)
        db.session.delete(reporte)
        db.session.commit()
        flash('Reporte eliminado.', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {e}', 'danger')
    return redirect(url_for('reportes_externos'))

@app.route('/eliminar/<int:id>')
@login_required
@admin_required
def eliminar(id):
    p = db.session.get(Pasante, id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)