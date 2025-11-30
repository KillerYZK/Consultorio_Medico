from flask import Flask
from flask_mysqldb import MySQL
from flask import jsonify 
from flask_jwt_extended import JWTManager

from config import config

from pacientes import pacientes_bp  
from servicios.doctores import doctores_bp
from servicios.citas import citas_bp
from servicios.login import login_bp

app = Flask(__name__)

# Asegurar claves (solo fallback; no usar claves hardcodeadas en producción)
app.config.setdefault('SECRET_KEY', 'cambiar_esta_clave_secreta')
app.config.setdefault('JWT_SECRET_KEY', 'cambiar_esta_clave_jwt')

jwt = JWTManager(app)
conexion = MySQL(app)

# Pasar la conexión al Blueprint
import pacientes
pacientes.conexion = conexion
import servicios.doctores as doctores
doctores.conexion = conexion
import servicios.citas as citas
citas.conexion = conexion
import servicios.login as login_mod
login_mod.conexion = conexion

# Registrar el Blueprint
app.register_blueprint(pacientes_bp)
app.register_blueprint(doctores_bp)
app.register_blueprint(citas.citas_bp)
app.register_blueprint(login_bp)


def pagina_no_encontrada(error):
    return "La página que intentas buscar no existe.."


if __name__ == '__main__':
    app.config.from_object(config['development']) #se carga desde un objeto from_object
    app.register_error_handler(404,pagina_no_encontrada)
    app.run()