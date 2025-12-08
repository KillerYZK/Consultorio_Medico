from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from passlib.hash import pbkdf2_sha256 as sha256
from flask_jwt_extended import jwt_required, get_jwt
from Decoradores.decoradores import role_required

usuarios_bp = Blueprint('usuarios_bp', __name__)
conexion = None

# Obtener todos los usuarios (SOLO ADMIN)
@usuarios_bp.route('/usuarios', methods=['GET'])
@jwt_required()
@role_required('admin')
def lista_de_usuarios():
    try:
        cursor = conexion.connection.cursor()
        
        rol_filtro = request.args.get('rol', 'todos')
        
        sql = "CALL sp_usuarios_get_by_rol(%s)"
        cursor.execute(sql, (rol_filtro,))
        datos = cursor.fetchall()
        
        # OBTENER COLUMNAS ANTES de nextset()
        columnas = [desc[0] for desc in cursor.description]
        cursor.nextset()
        
        if not datos:
            return jsonify({
                'datos': [],
                'mensaje': f"No hay usuarios con rol: {rol_filtro}",
                'exito': False
            }), 404
        
        arr_usuarios = [dict(zip(columnas, fila)) for fila in datos]
        
        # No exponer contraseñas
        for u in arr_usuarios:
            u.pop('password_hash', None)
            u.pop('password', None)
            u.pop('passwd', None)

        return jsonify({
            'datos': arr_usuarios,
            'total': len(arr_usuarios),
            'mensaje': f"Usuarios con rol '{rol_filtro}'",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500

# Obtener mi información (cualquier usuario autenticado)
@usuarios_bp.route('/usuarios/me', methods=['GET'])
@jwt_required()
def mi_informacion():
    try:
        claims = get_jwt()
        
        cursor = conexion.connection.cursor()
        # Remover fecha_creacion si no existe
        sql = "SELECT id_usuario, username, rol, id_paciente, id_doctor FROM usuarios WHERE id_usuario = %s"
        cursor.execute(sql, (claims.get('id_usuario'),))
        resultado = cursor.fetchone()
        
        if not resultado:
            return jsonify({
                'mensaje': "Usuario no encontrado",
                'exito': False
            }), 404
        
        columnas = [desc[0] for desc in cursor.description]
        usuario_dict = dict(zip(columnas, resultado))
        
        return jsonify({
            'datos': usuario_dict,
            'mensaje': "Información del usuario autenticado",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500

# Crear usuario (SOLO ADMIN)
@usuarios_bp.route('/usuarios', methods=['POST'])
@jwt_required()
@role_required('admin')
def agregar_usuario():
    try:
        datos = request.json
        
        campos_requeridos = ['username', 'password', 'rol']
        for campo in campos_requeridos:
            if campo not in datos:
                return jsonify({
                    'mensaje': f"El campo {campo} es requerido",
                    'exito': False
                }), 400
        
        roles_validos = ['admin', 'doctor', 'paciente', 'staff']
        if datos['rol'] not in roles_validos:
            return jsonify({
                'mensaje': f"Rol inválido. Roles válidos: {', '.join(roles_validos)}",
                'exito': False
            }), 400
        
        if datos['rol'] == 'doctor' and not datos.get('id_doctor'):
            return jsonify({
                'mensaje': "Para rol 'doctor' es obligatorio id_doctor",
                'exito': False
            }), 400
        
        if datos['rol'] == 'paciente' and not datos.get('id_paciente'):
            return jsonify({
                'mensaje': "Para rol 'paciente' es obligatorio id_paciente",
                'exito': False
            }), 400

        hashed_pw = sha256.hash(datos['password'])

        cursor = conexion.connection.cursor()
        sql = "CALL sp_usuarios_add(%s, %s, %s, %s, %s)"
        
        cursor.execute(sql, (
            datos['username'],
            hashed_pw,
            datos['rol'],
            datos.get('id_paciente'),
            datos.get('id_doctor')
        ))
        
        resultado = cursor.fetchone()
        cursor.nextset()
        conexion.connection.commit()
        
        return jsonify({
            'mensaje': resultado[0] if resultado else "Usuario creado",
            'exito': resultado[1] if resultado else True
        }), 201

    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500

# Editar usuario
@usuarios_bp.route('/usuarios/<int:id_usuario>', methods=['PUT'])
@jwt_required()
def editar_usuario(id_usuario):
    try:
        claims = get_jwt()
        user_id = claims.get('id_usuario')
        user_rol = claims.get('rol')
        
        if user_id != id_usuario and user_rol != 'admin':
            return jsonify({
                'mensaje': "No tienes permiso para editar otros usuarios",
                'exito': False
            }), 403
        
        datos = request.json
        
        cursor = conexion.connection.cursor()
        sql = "CALL sp_usuarios_update(%s, %s, %s, %s, %s, %s)"
        
        cursor.execute(sql, (
            id_usuario,
            datos.get('nombre'),
            datos.get('username'),
            datos.get('rol'),
            datos.get('id_paciente'),
            datos.get('id_doctor')
        ))
        
        resultado = cursor.fetchone()
        cursor.nextset()
        conexion.connection.commit()
        
        return jsonify({
            'mensaje': resultado[0] if resultado else "Usuario actualizado",
            'exito': resultado[1] if resultado else True
        }), 200

    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500

# Eliminar usuario (SOLO ADMIN)
@usuarios_bp.route('/usuarios/<int:id_usuario>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def eliminar_usuario(id_usuario):
    try:
        cursor = conexion.connection.cursor()
        sql = "CALL sp_usuarios_delete(%s)"
        cursor.execute(sql, (id_usuario,))
        
        resultado = cursor.fetchone()
        cursor.nextset()
        conexion.connection.commit()

        return jsonify({
            'mensaje': resultado[0] if resultado else "Usuario eliminado",
            'exito': resultado[1] if resultado else True
        }), 200

    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500

# Obtener usuarios por rol (SOLO ADMIN)
@usuarios_bp.route('/usuarios/rol/<rol>', methods=['GET'])
@jwt_required()
@role_required('admin')
def usuarios_por_rol(rol):
    try:
        roles_validos = ['admin', 'doctor', 'paciente', 'staff']
        if rol not in roles_validos:
            return jsonify({
                'mensaje': f"Rol inválido. Roles válidos: {', '.join(roles_validos)}",
                'exito': False
            }), 400
        
        cursor = conexion.connection.cursor()
        sql = "CALL sp_usuarios_get_by_rol(%s)"
        cursor.execute(sql, (rol,))
        datos = cursor.fetchall()
        
        # OBTENER COLUMNAS ANTES de nextset()
        columnas = [desc[0] for desc in cursor.description]
        cursor.nextset()
        
        if not datos:
            return jsonify({
                'datos': [],
                'mensaje': f"No hay usuarios con rol '{rol}'",
                'exito': False
            }), 404
        
        arr_usuarios = [dict(zip(columnas, fila)) for fila in datos]
        
        for u in arr_usuarios:
            u.pop('password_hash', None)

        return jsonify({
            'datos': arr_usuarios,
            'total': len(arr_usuarios),
            'rol': rol,
            'mensaje': f"Usuarios con rol '{rol}'",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500