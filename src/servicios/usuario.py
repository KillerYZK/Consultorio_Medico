from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from passlib.hash import pbkdf2_sha256 as sha256
from flask_jwt_extended import jwt_required

usuarios_bp = Blueprint('usuarios_bp', __name__)
conexion = None

# Ruta para obtener todos los usuarios
@usuarios_bp.route('/usuarios', methods=['GET'])
@jwt_required()
def lista_de_usuarios():
    try:
        cursor = conexion.connection.cursor()
        sql = "CALL sp_usuarios_get"
        cursor.execute(sql)
        datos = cursor.fetchall()
        
        columnas = [desc[0] for desc in cursor.description]
        arr_usuarios = [dict(zip(columnas, fila)) for fila in datos]
        
        # No exponer contraseñas
        for u in arr_usuarios:
            for key in ('password', 'password_hash', 'passwd'):
                if key in u:
                    u.pop(key, None)
                    u['has_password'] = True

        return jsonify({
            'datos': arr_usuarios,
            'mensaje': "Lista de usuarios",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al obtener usuarios: {str(ex)}",
            'exito': False
        }), 500

# Ruta para agregar un nuevo usuario
@usuarios_bp.route('/usuarios', methods=['POST'])
@jwt_required()
def agregar_usuario():
    try:
        nuevo_usuario = request.json
        
        # Validar campos requeridos
        campos_requeridos = ['username', 'password', 'rol']
        for campo in campos_requeridos:
            if campo not in nuevo_usuario:
                return jsonify({
                    'mensaje': f"El campo {campo} es requerido",
                    'exito': False
                }), 400

        raw_pw = nuevo_usuario.get('password')
        hashed_pw = sha256.hash(raw_pw)

        cursor = conexion.connection.cursor()
        # Sin id_usuario (se auto-genera en la BD)
        sql = "CALL sp_usuarios_add(%s, %s, %s, %s, %s)"
        params = (
            nuevo_usuario.get('username'),
            hashed_pw,
            nuevo_usuario.get('rol'),
            nuevo_usuario.get('id_paciente'),
            nuevo_usuario.get('id_doctor'),
        )
        
        cursor.execute(sql, params)
        result = cursor.fetchone()
        cursor.nextset()
        conexion.connection.commit()
        cursor.close()
        
        return jsonify({
            'mensaje': result[0] if result else "Usuario agregado",
            'exito': result[1] if result else True
        }), 201

    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al agregar usuario: {str(ex)}",
            'exito': False
        }), 500

# Ruta para editar un usuario
@usuarios_bp.route('/usuarios/<int:id_usuario>', methods=['PUT'])
@jwt_required()
def editar_usuario(id_usuario):
    try:
        datos_usuario = request.json
        
        cursor = conexion.connection.cursor()
        sql = "CALL sp_usuarios_update(%s, %s, %s, %s, %s, %s)"
        params = (
            id_usuario,
            datos_usuario.get('nombre'),
            datos_usuario.get('username'),
            datos_usuario.get('rol'),
            datos_usuario.get('id_paciente'),
            datos_usuario.get('id_doctor'),
        )
        
        cursor.execute(sql, params)
        result = cursor.fetchone()
        cursor.nextset()
        conexion.connection.commit()
        cursor.close()
        
        return jsonify({
            'mensaje': result[0] if result else "Usuario actualizado",
            'exito': result[1] if result else True
        }), 200

    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al actualizar usuario: {str(ex)}",
            'exito': False
        }), 500

# Ruta para eliminar un usuario
@usuarios_bp.route('/usuarios/<int:id_usuario>', methods=['DELETE'])
@jwt_required()
def eliminar_usuario(id_usuario):
    try:
        cursor = conexion.connection.cursor()
        # Usar parámetros en lugar de f-string (previene SQL Injection)
        sql = "CALL sp_usuarios_delete(%s)"
        cursor.execute(sql, (id_usuario,))
        
        result = cursor.fetchone()
        cursor.nextset()
        conexion.connection.commit()
        cursor.close()

        return jsonify({
            'mensaje': result[0] if result else "Usuario eliminado",
            'exito': result[1] if result else True
        }), 200

    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al eliminar usuario: {str(ex)}",
            'exito': False
        }), 500