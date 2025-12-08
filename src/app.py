from flask import Flask
from flask_mysqldb import MySQL
from flask import jsonify 
from flask_jwt_extended import JWTManager

from config import config

from pacientes import pacientes_bp  
from servicios.doctores import doctores_bp
from servicios.citas import citas_bp
from servicios.login import login_bp
from servicios.usuario import usuarios_bp

app = Flask(__name__)

# Cargar configuración ANTES de inicializar extensiones
app.config.from_object(config['development'])

# Asegurar claves (solo fallback)
app.config.setdefault('SECRET_KEY', 'cambiar_esta_clave_secreta')
app.config.setdefault('JWT_SECRET_KEY', 'cambiar_esta_clave_jwt')

jwt = JWTManager(app)
conexion = MySQL(app)   

# Pasar la conexión a todos los módulos
import pacientes
pacientes.conexion = conexion
import servicios.doctores as doctores
doctores.conexion = conexion
import servicios.citas as citas_mod
citas_mod.conexion = conexion
import servicios.login as login_mod
login_mod.conexion = conexion
import servicios.usuario as usuarios_mod
usuarios_mod.conexion = conexion
import Decoradores.decoradores as decoradores
decoradores.conexion = conexion

# Registrar blueprints
app.register_blueprint(pacientes_bp)
app.register_blueprint(doctores_bp)
app.register_blueprint(citas_bp)
app.register_blueprint(login_bp)
app.register_blueprint(usuarios_bp)
app.url_map.strict_slashes = False


def pagina_no_encontrada(error):
    return jsonify({
        'mensaje': "La página que intentas buscar no existe",
        'exito': False
    }), 404

if __name__ == '__main__':
    app.register_error_handler(404, pagina_no_encontrada)
    app.run(debug=True)