import re
from multiprocessing.pool import ThreadPool
import multiprocessing as mp
import time
import socket
import json
import os
from jsonschema import validate, ValidationError


# opciones configurables del servidor
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

# tipos mime
mime_types = None

# respustas posibles
respuesta_http = {'200': 'HTTP/1.1 200 OK\r\n',
                  '403': 'HTTP/1.1 403 Forbidden\r\n',
                  '404': 'HTTP/1.1 404 Not Found\r\n',
                  '406': 'HTTP/1.1 406 Not Acceptable\r\n',
                  '500': 'HTTP/1.1 500 Internal Server Error\r\n',
                  '501': 'HTTP/1.1 501 Not Implemented\r\n'
                  }


def procesar_cabeceras(diccionario, cadena_texto):
    """
    :param diccionario: un diccionario en el que se ingresaran los datos del header
    :param cadena_texto: cadena que contiene los datos de la cabecera
    :return: no devuelve nada
    """
    print('/*******************************************************************/')
    # divide el encabezado en cadenas de texto correspondiente a cada línea
    dividido = cadena_texto.split('\r\n')
    # la primer línea del encabezado contiene el recurso al cual se accede y la version de http
    (recurso, version_http) = dividido.pop(0).split(' ')
    # separa el recurso solicitado, en el nombre del recurso y los parametros de url (si los tiene)
    (diccionario['recurso_solicitado'], discard, diccionario['parametros_url']) = recurso.partition('?')
    # obtiene la extension del archivo que se solicita (obtiene desde el ultimo punto)
    diccionario['recurso_solicitado_extension'] = diccionario['recurso_solicitado'].rsplit('/', 1)[1]
    (discard_prove, discard, diccionario['recurso_solicitado_extension']) = diccionario[
        'recurso_solicitado_extension'].rpartition('.')
    if discard_prove == '':
        diccionario['recurso_solicitado_extension'] = ''
    diccionario['version_http'] = version_http
    # para todas las otras lineas del encabezado se guarda su parte derecha e izquieda, separadas así por los dos puntos
    for h in dividido:
        x, y = h.split(': ')
        diccionario[x] = y
    print(repr(diccionario))
    print('/*******************************************************************/')


def obtener_datos_archivo(filename, extension):
    """
    :param filename: nombre del archivo
    :param extension: extension del archivo

    :return:    > archivo:      :-  File:   en caso de encontrarse el archivo
                                :-  None:   en caso de no existir el el archivo
                                :-  -1      en caso de que se trate de obtener un archivo de un folder superior

                > mime_type     :- String:  contiene el mime type

                > read_as_text  :- Boolean: indica si el archivo fue o no leido como texto
    """
    print('/*******************************************************************/')
    # concatena al nombre del archivo la ruta de donde se toman lops archvos
    filename = settings['htdocs_folder'] + filename
    print('param: filename=' + filename + ' extension=' + extension)
    # verifica si se solicita un archivo o una carpeta verficando su ultimo caracter
    if filename == '' or filename[-1] == '/':
        # en caso de ser una carpeta verfica si existe algún archivo de índice
        for filename_index in settings['default_index']:
            print(filename + filename_index)
            # verifica el primero de los archivos que exista
            if os.path.isfile(filename + filename_index):
                filename += filename_index
                (discard, discard, extension) = filename_index.rpartition('.')
                break
    # verifica si la extension está registrada en la lista de MIME-TYPES
    if extension not in mime_types:
        # en caso de no estarlo lo toma como si fuera del tipo default
        extension = 'default'
    # por defecto se lee como un archivo de texto
    type_file_read = 'r'
    # verifica si está indicado que se lea como un archivo binario
    if 'binary' in mime_types[extension] and mime_types[extension]['binary'] == True:
        type_file_read = 'rb'
    mime_type_file = ''
    print('filename: ' + filename + ' | htdocs_folder: ' + settings['htdocs_folder'])
    # verifica que la solicitud no sea de un folder superior al de htdocs (seguridad)
    if '..' not in os.path.relpath(filename, settings['htdocs_folder']):
        try:
            print("voy a ver")
            print("type_file_read->", type_file_read)
            print("filename", filename)
            # abre el archivo
            archivo = open(filename, type_file_read)
            # obtiene el content type correspondiente
            mime_type_file = mime_types[extension]['content-type']
        except OSError:
            archivo = None
    else:
        archivo = -1
    print(repr(archivo), mime_types[extension]['content-type'], sep='   |||  ')
    print('/*******************************************************************/')
    return archivo, mime_type_file, type_file_read == 'r'


def process_petition(socket_cliente, log_queue):
    """
    Esta función atiende la peticiones, se ejecuta de manera concurrente
    :param socket_cliente: socker del cliente de donde se recibirán los datos y luego se enviará la respuesta
    :param log_queue: cola en donde se agrega lo que se debe escribir en la bitácora
    :return: no retorna nada
    """
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
    # en caso de ser una petición vacía, solo se cierra el socket
    if metodo_http == b'':
        socket_cliente.shutdown(socket.SHUT_RDWR)
        socket_cliente.close()
        return
    # verifica que sea de alguno de los métodos aceptados
    elif metodo_http == b'GET ':
        texto_bitacora += 'GET, '
    elif metodo_http == b'POST':
        texto_bitacora += 'POST, '
        socket_cliente.recv(1)
    elif metodo_http == b'HEAD':
        texto_bitacora += 'HEAD, '
        socket_cliente.recv(1)
    # en caso de contener informacion que no sea de un método aceptado retorna un error 501
    else:
        texto_bitacora += 'ERROR, '
        error_solicitud = True
        cabeceras_respuesta += respuesta_http['501']
    # agrega información básica a la bitácora
    texto_bitacora += tiempo + ', '
    texto_bitacora += ip_servidor + ', '
    texto_bitacora += ip_cliente + ', '
    cuerpo_respuesta = b''
    solicitud = ''
    # si el método de la solicitud es aceptado
    if not error_solicitud:
        # recibe contendido solicitud
        buffer = socket_cliente.recv(512)
        cabeceras = dict()
        cuerpo = b''
        while 1:
            # continua recibiendo contenido
            solicitud += buffer.decode()
            # cuando encuentra el doble cambio de línea
            if solicitud.find("\r\n\r\n") != -1:
                # separa lo que está antes del doble cambio de línea en cabeceras y cuerpo
                (texto_cabeceras, cuerpo) = solicitud.split("\r\n\r\n")
                # procesa las cabecera
                procesar_cabeceras(cabeceras, texto_cabeceras)
                # termina el ciclo donde se recibe informacion
                break
            buffer = socket_cliente.recv(512)
        # añade a la bitácora el recurso solicitado y los parámetros de url
        texto_bitacora += cabeceras['recurso_solicitado'] + ', '
        texto_bitacora += cabeceras['parametros_url']

        # si el método es POST
        if metodo_http == b'POST':
            # se debe verificar que todo el cuerpo haya sido recibido (según el Content-Length)
            if 'Content-Length' not in cabeceras:
                # si no está definido el Content-Length se toma como 0
                cabeceras['Content-Length'] = '0'
            # se continua recibiendo hasta alcanzar el Content-Length
            while str(len(cuerpo)) != cabeceras['Content-Length']:
                buffer = socket_cliente.recv(512)
                cuerpo += buffer.decode()
            str(cuerpo).replace('\n', '\\n')
            texto_bitacora += ' || POST-> |' + cuerpo

        # obtener archivo, y el tipo de contenido
        (archivo, content_type, codificar) = obtener_datos_archivo(
            cabeceras['recurso_solicitado'],
            cabeceras['recurso_solicitado_extension']
        )

        # verificar tipo compatible
        # se presume que el tipo de archivo se acepta
        tipo_aceptado = True
        # se verifica si la cabecera Accept fue enviada
        # en caso de no haber sido enviada se asume que acepta cualquier tipo de contenido
        if 'Accept' in cabeceras and content_type != '':
            # si la cadena */* se encuentra en el valor de Accept, no es necesario verificar
            if cabeceras['Accept'].find('*/*') == -1:
                tipo_aceptado = False
                print('cabecera accept | ' + cabeceras['Accept'])
                # separa los tipos aceptados por ; además el parametro q no se toma en cuenta
                separadas = re.sub(';q.+?(,|$)', ',', cabeceras['Accept'])
                print('separadas | ' + separadas)
                # convierte los * en .+ por asuntos de expresiones regulares
                patrones = re.sub('/\*', '/.+', separadas).rstrip(',').split(',')
                print('patrones | ' + repr(patrones))
                # verifica si el MIME type del archivo es compatible con lo indicado en Accept
                for x in patrones:
                    print("X: " + repr(x) + " CT->" + repr(content_type))
                    if re.fullmatch(x, content_type):
                        tipo_aceptado = True
                        break

        # si el archivo que se solicitó es un recurso prohibido (folder superior a la raiz de htdocs)
        if archivo == -1:
            # error Forbidden
            cabeceras_respuesta = respuesta_http['403']
        # el archivo pudo abrirse correctamente
        elif archivo:
            # pregunta si el archivo es aceptado
            if tipo_aceptado:
                if archivo.readable():
                    # lee el contenido del archivo
                    cuerpo_respuesta = archivo.read()
                    if codificar:
                        # si el archivo fue abierto en modo texto debe codificarse
                        cuerpo_respuesta = cuerpo_respuesta.encode()
                    # codigo OK
                    cabeceras_respuesta = respuesta_http['200']
                else:
                    # Si el archivo no puede leerse
                    # error interno
                    cabeceras_respuesta = respuesta_http['500']
            else:
                # si no es aceptado se retorna un error 406
                cabeceras_respuesta = respuesta_http['406']
            archivo.close()
        # el archivo no fue encontrado
        else:
            # error 404
            cabeceras_respuesta = respuesta_http['404']

        # Se agrega la cabecera de content_type
        if content_type != '':
            cabeceras_respuesta += 'Content-Type: ' + content_type + '\r\n'
    # en caso de ser erróneo
    else:
        # agrega el texto a la bitácora para que todas las líneas tengan la misma cantidad de líneas
        texto_bitacora += ', '
    # agrega los datos a la cabecera de respuesta
    cabeceras_respuesta += 'Date: ' + fecha + '\r\n'
    cabeceras_respuesta += 'Server: ' + settings['server_name'] + '\r\n'
    cabeceras_respuesta += 'Content-Length: ' + str(len(cuerpo_respuesta)) + '\r\n'
    cabeceras_respuesta += '\r\n'
    respuesta = cabeceras_respuesta.encode()
    if metodo_http != b'HEAD':
        respuesta += cuerpo_respuesta
    # escribe en la bitácora
    log_queue.put(texto_bitacora)
    # envia la respuesta
    socket_cliente.sendall(respuesta)
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
        log_server.write(
            'escuchando en todas las direcciones del equipo en el puerto: ' + str(settings['port_listening']) + '\n'
                        )
    else:
        log_server.write(
                            'escuchando en: ' +
                            settings['ip_listening'] +
                            ' en el puerto: ' +
                            str(settings['port_listening']) + '\n'
                        )
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
