import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)

# CONFIGURACIÓN
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:dangel232@localhost/base_pasantia_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'pomaray_2026_gst' 
db = SQLAlchemy(app)

IMGBB_API_KEY = "0e6901cb0c02a5f295b89eff4e86a61e"

# MODELO DE DATOS
class pasante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    empresa = db.Column(db.String(100), nullable=False)
    horas_completadas = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(20), default='Activo')
    dir_foto = db.Column(db.String(500))

with app.app_context():
    db.create_all()

def subir_a_imgbb(archivo):
    url = "https://api.imgbb.com/1/upload"
    payload = {"key": IMGBB_API_KEY}
    files = {"image": (archivo.filename, archivo.read())}
    try:
        response = requests.post(url, payload, files=files)
        if response.status_code == 200:
            return response.json()['data']['url']
    except Exception as e:
        print(f"Error en ImgBB: {e}")
    return None

# --- RUTAS ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/panel')
def index():
    search = request.args.get('search')
    if search:
        estudiantes = pasante.query.filter(pasante.nombre.contains(search)).all()
    else:
        estudiantes = pasante.query.all()
    return render_template('index.html', estudiantes=estudiantes)

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        foto_subida = request.files.get('foto')
        enlace_foto = "https://via.placeholder.com/300x200?text=Sin+Foto"
        if foto_subida and foto_subida.filename != '':
            res = subir_a_imgbb(foto_subida)
            if res: enlace_foto = res

        nuevo = pasante(
            nombre=request.form['nombre'],
            empresa=request.form['empresa'],
            horas_completadas=request.form.get('horas', 0),
            dir_foto=enlace_foto
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('¡Pasante registrado con éxito!', 'success')
        return redirect(url_for('index'))
    return render_template('registro.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    p = pasante.query.get_or_404(id)
    if request.method == 'POST':
        p.nombre = request.form['nombre']
        p.empresa = request.form['empresa']
        p.horas_completadas = request.form['horas']
        
        nueva_foto = request.files.get('foto')
        if nueva_foto and nueva_foto.filename != '':
            res = subir_a_imgbb(nueva_foto)
            if res: p.dir_foto = res
            
        db.session.commit()
        flash(f'Datos de {p.nombre} actualizados correctamente.', 'success')
        return redirect(url_for('index'))
    return render_template('editar.html', p=p)

@app.route('/reporte')
def reporte():
    total_e = pasante.query.count()
    suma_h = db.session.query(func.sum(pasante.horas_completadas)).scalar() or 0
    listos = pasante.query.filter(pasante.horas_completadas >= 360).count()
    return render_template('reporte.html', total_e=total_e, horas=suma_h, listos=listos)

@app.route('/eliminar/<int:id>')
def eliminar(id):
    p = pasante.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
        flash('Registro eliminado del sistema.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)