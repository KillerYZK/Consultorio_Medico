# Archivo: config.py
from datetime import timedelta #definimos el tiempo de uso

# Primero paso se hace la clase de configuración
class DevelopmentConfig():
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'consultorio_user'
    MYSQL_PASSWORD = "killerisaac1234567"
    MYSQL_DB = 'bd_consultorio_tpoa'

    JWT_SECRET_KEY = '0s1409k8674i124b432id04i'
    JWT_ACCESS_TOCKEN_EXPIRES = timedelta (hours=2)
# Luego creamos el diccionario de configuración
config = {
    'development': DevelopmentConfig
}


