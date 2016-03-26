import re
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
import multiprocessing as mp
import time
import socket
import json
import os
from jsonschema import validate, ValidationError

settings = dict()
# nombre del servidor
settings['server_name'] = 'ErickMRServer/0.5'
# nombre del archivo de bitacora
settings['log_requests_file_name'] = 'serverhttp_requests.log'
settings['log_server_file_name'] = 'serverhttp_events.log'
# carpeta de donde se encuentran los documentos
settings['htdocs_folder'] = 'htdocs'
# numero de puerto para escuchar
settings['port_listening'] = 8080
# direccion ip donde escuchar
settings['ip_listening'] = ''
# indices por default
settings['default_index'] = ['index.html']

# Recursos
mime_types = None

# respustas
respuesta_http = {'200': 'HTTP/1.1 200 OK\r\n',
                  '403': 'HTTP/1.1 403 Forbidden\r\n',
                  '404': 'HTTP/1.1 404 Not Found\r\n',
                  '406': 'HTTP/1.1 406 Not Acceptable\r\n',
                  '500': 'HTTP/1.1 500 Internal Server Error\r\n',
                  '501': 'HTTP/1.1 501 Not Implemented\r\n'
                  }


def procesar_cabeceras(diccionario, cadena_texto):
    print('/*******************************************************************/')
    dividido = cadena_texto.split('\r\n')
    (recurso, version_http) = dividido.pop(0).split(' ')
    (diccionario['recurso_solicitado'], discard, diccionario['parametros_url']) = recurso.partition('?')
    diccionario['recurso_solicitado_extension'] = diccionario['recurso_solicitado'].rsplit('/', 1)[1]
    (discard_prove, discard, diccionario['recurso_solicitado_extension']) = diccionario[
        'recurso_solicitado_extension'].rpartition('.')
    if discard_prove == '':
        diccionario['recurso_solicitado_extension'] = ''
    diccionario['version_http'] = version_http
    for h in dividido:
        x, y = h.split(': ')
        diccionario[x] = y
    print(repr(diccionario))
    print('/*******************************************************************/')


def obtener_datos_archivo(filename, extension):
    print('/*******************************************************************/')
    filename = settings['htdocs_folder'] + filename
    print('param: filename=' + filename + ' extension=' + extension)
    if filename == '' or filename[-1] == '/':
        for filename_index in settings['default_index']:
            print(filename + filename_index)
            if os.path.isfile(filename + filename_index):
                filename += filename_index
                (discard, discard, extension) = filename_index.rpartition('.')
                break
    if extension not in mime_types:
        extension = 'default'
    type_file_read = 'r'
    if 'binary' in mime_types[extension] and mime_types[extension]['binary'] == True:
        type_file_read = 'rb'
    mime_type_file = ''
    archivo = None
    if filename != '':
        print('filename: ' + filename + ' | htdocs_folder: ' + settings['htdocs_folder'])
        if '..' not in os.path.relpath(filename, settings['htdocs_folder']):
            try:
                print("voy a ver")
                print("type_file_read->", type_file_read)
                print("filename", filename)
                archivo = open(filename, type_file_read)
                mime_type_file = mime_types[extension]['content-type']
            except OSError:
                archivo = None
        else:
            archivo = -1
    print(repr(archivo), mime_types[extension]['content-type'], sep='   |||  ')
    print('/*******************************************************************/')
    return archivo, mime_type_file, type_file_read == 'r'


def process_petition(socket_cliente, log_queue):
    # bandera de error
    error_solicitud = False
    # obtiene los datos del servidor
    (ip_servidor, puerto_servidor) = socket_cliente.getsockname()
    # obtiene los datos del cliente
    (ip_cliente, puerto_cliente) = socket_cliente.getpeername()
    # información a guardar en la bitácora
    texto_bitacora = ''
    # información que se devolverá al cliente 
    cabeceras_respuesta = ''
    # fecha actual para HTTP
    fecha = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    # estampilla tiempo bitacora
    tiempo = str(int(time.time()))
    # recibe el nombre del método
    metodo_http = socket_cliente.recv(4)
    # variables de cabecera
    cabecera_content_type = ''
    if metodo_http == b'':
        socket_cliente.shutdown(socket.SHUT_RDWR)
        socket_cliente.close()
        return
    elif metodo_http == b'GET ':
        texto_bitacora += 'GET, '
    elif metodo_http == b'POST':
        texto_bitacora += 'POST, '
        socket_cliente.recv(1)
    elif metodo_http == b'HEAD':
        texto_bitacora += 'HEAD, '
        socket_cliente.recv(1)
    else:
        texto_bitacora += 'ERROR, '
        error_solicitud = True
        cabeceras_respuesta += respuesta_http['501']
    texto_bitacora += tiempo + ', '
    texto_bitacora += ip_servidor + ', '
    texto_bitacora += ip_cliente + ', '
    cuerpo_respuesta = b''
    solicitud = ''
    if not error_solicitud:
        buffer = socket_cliente.recv(4)
        cabeceras = dict()
        cuerpo = b''
        while 1:
            solicitud += buffer.decode()
            if solicitud.find("\r\n\r\n") != -1:
                (texto_cabeceras, cuerpo) = solicitud.split("\r\n\r\n")
                procesar_cabeceras(cabeceras, texto_cabeceras)
                break
            buffer = socket_cliente.recv(4)
        texto_bitacora += cabeceras['recurso_solicitado'] + ', '
        texto_bitacora += cabeceras['parametros_url']

        if metodo_http == b'POST':
            if 'Content-Length' not in cabeceras:
                cabeceras['Content-Length'] = '0'
            while str(len(cuerpo)) != cabeceras['Content-Length']:
                buffer = socket_cliente.recv(4)
                cuerpo += buffer.decode()
            str(cuerpo).replace('\n', '\\n')
            texto_bitacora += ' || POST-> |' + cuerpo

        # verificar MIME
        (archivo, content_type, codificar) = obtener_datos_archivo(
            cabeceras['recurso_solicitado'],
            cabeceras['recurso_solicitado_extension']
        )

        # verificar tipo compatible
        tipo_aceptado = True
        if 'Accept' in cabeceras and content_type != '':
            if cabeceras['Accept'].find('*/*') == -1:
                tipo_aceptado = False
                print('no existe */*')
                print('cabecera accept | ' + cabeceras['Accept'])
                separadas = re.sub(';q.+?(,|$)', ',', cabeceras['Accept'])
                print('separadas | ' + separadas)
                patrones = re.sub('/\*', '/.+', separadas).rstrip(',').split(',')
                print('patrones | ' + repr(patrones))
                for x in patrones:
                    print("X: " + repr(x) + " CT->" + repr(content_type))
                    if re.fullmatch(x, content_type):
                        tipo_aceptado = True
                        break

        if archivo == -1:
            print(-1)
            cabeceras_respuesta = respuesta_http['403']
        elif archivo:
            if tipo_aceptado:
                if archivo.readable():
                    cuerpo_respuesta = archivo.read()
                    if codificar:
                        print(cuerpo_respuesta)
                        cuerpo_respuesta = cuerpo_respuesta.encode()
                    cabeceras_respuesta = respuesta_http['200']
                else:
                    cabeceras_respuesta = respuesta_http['500']
            else:
                cabeceras_respuesta = respuesta_http['406']
            archivo.close()
        else:
            cabeceras_respuesta = respuesta_http['404']

        if content_type != '':
            cabeceras_respuesta += 'Content-Type: ' + content_type + '\r\n'
    else:
        texto_bitacora += ', '
    cabeceras_respuesta += 'Date: ' + fecha + '\r\n'
    cabeceras_respuesta += 'Server: ' + settings['server_name'] + '\r\n'
    cabeceras_respuesta += 'Content-Length: ' + str(len(cuerpo_respuesta)) + '\r\n'
    cabeceras_respuesta += '\r\n'
    respuesta = cabeceras_respuesta.encode() + cuerpo_respuesta
    # codifica los datos a enviarse
    datos = respuesta
    # escribe en la bitácora
    log_queue.put(texto_bitacora)
    # envia la respuesta
    socket_cliente.sendall(datos)
    # termina la comunicación en el socket
    socket_cliente.shutdown(socket.SHUT_RDWR)
    # cierra el socker
    socket_cliente.close()


def bitacora(cola_bitacora):
    """Lee los mensajes en la cola y lo escribe en el archivo de bitácora
    :param cola_bitacora: cola de donde se leeran los archivos
    :return: no devuelve nada
    """

    log_requests = open(settings['log_requests_file_name'], 'a')
    while True:
        m = cola_bitacora.get()
        log_requests.write(str(m) + '\n')
        log_requests.flush()
    log_requests.close()


def load_settings():
    global mime_types
    schema_settings = {
        "type": "object",
        "properties": {
            "server_name": {
                "type": "string"
            },
            "log_requests_file_name": {
                "type": "string"
            },
            "log_server_file_name": {
                "type": "string"
            },
            "htdocs_folder": {
                "type": "string"
            },
            "port_listening": {
                "type": "integer",
                "minimum": 0
            },
            "ip_listening": {
                "type": "string"
            },
            "default_index": {
                "type": "array",
                "items": {
                    "type": "string"
                }

            }
        },
        "additionalProperties": False
    }
    schema_mime_types = {
        "type": "object",
        "patternProperties": {
            "([A-z]|[0-9]|-|_)+$": {
                "type": "object",
                "properties": {
                    "binary": {
                        "type": "boolean"
                    },
                    "content-type": {
                        "type": "string"
                    }
                },
                "required": [
                    "content-type"
                ]
            }
        },
        "additionalProperties": False,
        "required": [
            "default"
        ]
    }
    try:
        mime_types = json.load(open('mimetypes.json'))
    except json.JSONDecodeError:
        log_server.write('ERROR: el archivo mimetypes.json no es valido\n')
        return False
    except OSError:
        log_server.write('ERROR: el archivo mimetypes.json no existe o no cuenta con permisos de lectura\n')
        return False
    try:
        validate(mime_types, schema_mime_types)
    except ValidationError as e:
        log_server.write('ERROR: problema con el archivo mimetypes.json\n<-------------------\_/------------------->\n')
        log_server.write(repr(e))
        log_server.write('\n<-------------------/^\------------------->\n')
        return False

    try:
        settings_file = json.load(open('settings.json'))
    except json.JSONDecodeError:
        log_server.write('ERROR: el archivo settings.json no es valido\nUsando configuración por defecto\n')
        return True
    except OSError:
        log_server.write('ERROR: el archivo settings.json no existe o no cuenta con permisos de lectura\n')
        log_server.write('Usando configuración por defecto\n')
        return True
    try:
        validate(settings_file, schema_settings)
    except ValidationError as e:
        log_server.write('ERROR: problema con el archivo settings.json\n')
        log_server.write('<-------------------\_/------------------->\n\n')
        log_server.write(repr(e))
        log_server.write('\n<-------------------/^\------------------->\n')
        log_server.write('Usando configuración por defecto\n')
        return True

    for x in settings_file:
        settings[x] = settings_file[x]
    print(mime_types)
    print(settings_file)
    return True

if __name__ == '__main__':
    # obtiene el numero de procesadores disponibles
    numberProcessors = mp.cpu_count()
    log_server = open(settings['log_server_file_name'], 'a')
    if numberProcessors < 3:
        numberProcessors = 3
    administrador = mp.Manager()
    cola = administrador.Queue()
    fecha_servidor = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
    log_server.write('/***********************************************/\n')
    log_server.write('Inicio Servidor: ' + fecha_servidor + '\n')
    log_server.write('El numero de procesadores es: ' + str(numberProcessors) + '\n')
    log_server.flush()
    if not load_settings():
        log_server.close()
        exit(-1)
    if settings['ip_listening'] == '':
        log_server.write('escuchando en todas las direcciones del equipo en el puerto: ' + str(settings['port_listening']) + '\n')
    else:
        log_server.write('escuchando en: ' + settings['ip_listening'] + ' en el puerto: ' + str(settings['port_listening']) + '\n')
    log_server.flush()
    with ThreadPool(processes=numberProcessors - 2) as pool:
        # put listener to work first
        watcher = pool.apply_async(bitacora, (cola,))

        # create an INET, STREAMing socket
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the socket to a public host, and a well-known port
        serversocket.bind((settings['ip_listening'], settings['port_listening']))
        # become a server socket
        serversocket.listen(numberProcessors - 1)
        while True:
            # accept connections from outside
            print('esperando')
            (clientsocket, address) = serversocket.accept()
            log_server.flush()

            # now do something with the clientsocket
            # in this case, we'll pretend this is a threaded server
            pool.apply_async(process_petition, (clientsocket, cola,))

    # exiting the 'with'-block has stopped the pool
    print("Now the pool is closed and no longer available")
