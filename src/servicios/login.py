from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from passlib.hash import pbkdf2_sha256 as sha256
import datetime

login_bp = Blueprint('login_bp', __name__)
conexion = None

@login_bp.route('/login', methods=['POST'])
def login():
    try:
        datos = request.get_json()
        
        if not datos or 'username' not in datos or 'password' not in datos:
            return jsonify({
                'mensaje': 'Username y password son requeridos',
                'exito': False
            }), 400

        cursor = conexion.connection.cursor()
        sql = "SELECT id_usuario, username, password_hash, rol FROM usuarios WHERE username = %s"
        cursor.execute(sql, (datos['username'],))
        resultado = cursor.fetchone()

        if resultado is None:
            return jsonify({
                'mensaje': 'Usuario no encontrado',
                'exito': False
            }), 404

        id_usuario, username, password_hash, rol = resultado

        if not sha256.verify(datos['password'], password_hash):
            return jsonify({
                'mensaje': 'Contraseña incorrecta',
                'exito': False
            }), 401

        token = create_access_token(
            identity=username,
            additional_claims={'id_usuario': id_usuario, 'rol': rol},
            expires_delta=datetime.timedelta(hours=3)
        )
        
        return jsonify({
            'mensaje': 'Login exitoso',
            'token': token,
            'usuario': username,
            'rol': rol,
            'exito': True
        }), 200

    except Exception as ex:
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500
