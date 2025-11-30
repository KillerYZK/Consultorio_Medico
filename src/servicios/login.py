from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from passlib.hash import pbkdf2_sha256 as sha256
from flask_jwt_extended import jwt_required
import datetime

login_bp = Blueprint('login_bp', __name__)
conexion = None

@login_bp.route('/login', methods=['POST'])
def login():
    try:

        datos = request.get_json()
        if not datos or 'username' not in datos or 'password' not in datos:
            return jsonify({'mensaje': 'username y password requeridos', 'exito': False}), 400

        cursor = conexion.connection.cursor()
        # traemos todas las columnas para mapear por nombre
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", (datos['username'],))
        fila = cursor.fetchone()
        columnas = [d[0] for d in cursor.description] if cursor.description else []
        cursor.close()

        if fila is None:
            return jsonify({'mensaje': 'Usuario no encontrado', 'exito': False}), 404

        row = dict(zip(columnas, fila))

        # Determinar campos posibles
        id_field = next((k for k in ('id', 'id_usuario', 'user_id', 'usuario_id') if k in row), None)
        password_field = next((k for k in ('password_hash', 'password', 'passwd') if k in row), None)
        username_field = next((k for k in ('username', 'user', 'usuario') if k in row), None)

        if password_field is None:
            return jsonify({'mensaje': 'Columna de contraseña no encontrada en la tabla usuarios', 'exito': False}), 500
        stored_hash = row[password_field]
        if not stored_hash:
            return jsonify({'mensaje': 'Hash de contraseña vacío', 'exito': False}), 500

        if sha256.verify(datos['password'], stored_hash):
            identidad = row[id_field] if id_field is not None else row.get(username_field)
            token = create_access_token(identity=str(identidad), expires_delta=datetime.timedelta(hours=2))
            return jsonify({'mensaje': 'Login exitoso', 'token': token, 'exito': True}), 200

        return jsonify({'mensaje': 'Contraseña incorrecta', 'exito': False}), 401

    except Exception as ex:
        return jsonify({'mensaje': f"Error en el login: {str(ex)}", 'exito': False}), 500
    
@login_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    return jsonify({'mensaje': 'Acceso autorizado a ruta protegida', 'exito': True}), 200