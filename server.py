import json
import multiprocessing as mp
import os
import re
import socket
import time
from multiprocessing.pool import ThreadPool
from pprint import pprint
import subprocess
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
# soporte CGI
soporte_cgi = False

# tipos mime
mime_types = None

# opciones cgi
opciones_cgi = None

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
    print(cadena_texto)
    # divide el encabezado en cadenas de texto correspondiente a cada línea
    dividido = cadena_texto.split('\r\n')
    # la primer línea del encabezado contiene el recurso al cual se accede y la version de http
    (diccionario['REQUEST_URI'], diccionario['SERVER_PROTOCOL']) = dividido.pop(0).split(' ')
    # separa el recurso solicitado, en el nombre del recurso y los parametros de url (si los tiene)
    (diccionario['recurso_solicitado'], discard, diccionario['QUERY_STRING']) = diccionario['REQUEST_URI'].partition('?')
    # obtiene la extension del archivo que se solicita (obtiene desde el ultimo punto)
    discard = diccionario['recurso_solicitado'].rsplit('/', 1)
    diccionario['PATH_INFO'] = discard[0] + '/'
    (discard_prove, discard, diccionario['recurso_solicitado_extension']) = discard[1].rpartition('.')
    if discard_prove == '':
        diccionario['recurso_solicitado_extension'] = ''
    # para todas las otras lineas del encabezado se guarda su parte derecha e izquieda, separadas así por los dos puntos
    for h in dividido:
        x, y = h.split(': ')
        diccionario[x] = y
    print(diccionario)
    print('/*******************************************************************/')


def procesar_cabeceras_cgi(diccionario):
    if diccionario["REQUEST_METHOD"] == "POST":
        print("NOSE")
        if 'Content-Type' in diccionario:
            diccionario["CONTENT_TYPE"] = diccionario['Content-Type']
        else:
            diccionario["CONTENT_TYPE"] = ""
        if 'Content-Length' in diccionario:
            diccionario['CONTENT_LENGTH'] = diccionario['Content-Length']
        else:
            diccionario['CONTENT_LENGTH'] = "0"
    if 'Accept' in diccionario:
        diccionario['HTTP_ACCEPT'] = diccionario['Accept']
    diccionario["SCRIPT_NAME"] = diccionario['recurso_solicitado']
    # Otras
    diccionario['GATEWAY_INTERFACE'] = "CGI/1.1"
    diccionario['PATH_TRANSLATED'] = os.path.realpath(diccionario['PATH_INFO'])
    diccionario['SERVER_SOFTWARE'] = settings['server_name']
    # SERVER PROTOCOL VARIABLES
    diccionario['HTTP_HOST'] = diccionario['Host']
    diccionario['SERVER_NAME'] = diccionario['HTTP_HOST'].split(':')[0]
    # PHP
    diccionario["REDIRECT_STATUS"] = "200"
    diccionario["SCRIPT_FILENAME"] = os.path.realpath(settings['htdocs_folder']+diccionario['recurso_solicitado'])
    pprint(diccionario)
    print('/*******************************************************************/')


def obtener_datos_archivo(filename, extension, headers):
    """
    :param filename: nombre del archivo
    :param extension: extension del archivo
    :param headers: todos los encabezados

    :return:    > archivo:      :-  File:   en caso de encontrarse el archivo
                                :-  None:   en caso de no existir el el archivo
                                :-  -1      en caso de que se trate de obtener un archivo de un folder superior

                > mime_type     :- String:  contiene el mime type

                > read_as_text  :- Boolean: indica si el archivo fue o no leido como texto
    """
    print('/*******************************************************************/')
    # concatena al nombre del archivo la ruta de donde se toman los archvos
    filename = settings['htdocs_folder'] + filename

    print('param: filename=' + filename + ' extension=' + extension)
    mime_type_file = ""
    type_file_read = "r"
    archivo = -1
    # verifica que la solicitud no sea de un folder superior al de htdocs (seguridad)
    if '..' not in os.path.relpath(filename, settings['htdocs_folder']):
        # verifica si se solicita un archivo o una carpeta verficando su ultimo caracter
        if os.path.isdir(filename):
            if filename[-1] != '/':
                filename += '/'
                headers['recurso_solicitado'] += '/'
            # en caso de ser una carpeta verfica si existe algún archivo de índice
            for filename_index in settings['default_index']:
                print(filename + filename_index)
                # verifica el primero de los archivos que exista
                if os.path.isfile(filename + filename_index):
                    filename += filename_index
                    headers['recurso_solicitado'] += filename_index
                    (discard, discard, extension) = filename_index.rpartition('.')
                    break
        if soporte_cgi and extension in opciones_cgi:
            procesar_cabeceras_cgi(headers)
            p = subprocess.Popen(opciones_cgi[extension], env=headers, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            respuesta = p.communicate(input=b'nombre=ERICKMR19')[0]
            header, cuerpo = respuesta.split(b'\r\n\r\n', 1)
            header = header.decode()
            if 'Status' in header:
                header = header.replace('Status:', 'HTTP/1.1', 1)
            else:
                header = respuesta_http["200"]+header
            content_type = re.search('Content-Type: (.*)(,|$)', header)
            print(content_type)
            if content_type:
                print("/*asdasd*/")
                content_type = content_type.group(1)
            else:
                content_type = "text/plain"
            print(header)
            print("/**/")
            print(cuerpo)
            print(content_type)
            return [header, cuerpo], content_type, -1
        else:
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
    # print(repr(archivo), mime_types[extension]['content-type'], sep='   |||  ')
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
    cabeceras = dict()
    # obtiene los datos del servidor
    (ip_servidor, cabeceras['SERVER_PORT']) = socket_cliente.getsockname()
    cabeceras['SERVER_PORT'] = str(cabeceras['SERVER_PORT'])
    # obtiene los datos del cliente
    (cabeceras['REMOTE_ADDR'], puerto_cliente) = socket_cliente.getpeername()
    print(cabeceras['REMOTE_ADDR'], puerto_cliente, sep=" | ")
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
        cabeceras['REQUEST_METHOD'] = "GET"
        texto_bitacora += 'GET, '
    elif metodo_http == b'POST':
        cabeceras['REQUEST_METHOD'] = "POST"
        texto_bitacora += 'POST, '
        socket_cliente.recv(1)
    elif metodo_http == b'HEAD':
        cabeceras['REQUEST_METHOD'] = "HEAD"
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
    texto_bitacora += cabeceras['REMOTE_ADDR'] + ', '
    cuerpo_respuesta = b''
    solicitud = ''
    # si el método de la solicitud es aceptado
    if not error_solicitud:
        # recibe contendido solicitud
        buffer = socket_cliente.recv(512)
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
        texto_bitacora += cabeceras['QUERY_STRING']

        # si el método es POST
        if metodo_http == b'POST':
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
            cabeceras['recurso_solicitado_extension'],
            cabeceras
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
                    if re.match(x, content_type):
                        tipo_aceptado = True
                        break

        # si el archivo que se solicitó es un recurso prohibido (folder superior a la raiz de htdocs)
        if archivo == -1:
            # error Forbidden
            cabeceras_respuesta = respuesta_http['403']
        # el archivo fue procesado por CGI
        elif codificar == -1:
            print(archivo)
            if tipo_aceptado:
                cuerpo_respuesta = archivo[1]
                cabeceras_respuesta = archivo[0] + '\r\n'
            else:
                # si no es aceptado se retorna un error 406
                cabeceras_respuesta = respuesta_http['406']
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
        if codificar != -1 and content_type != '':
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
    global opciones_cgi
    global soporte_cgi
    schema_settings = {
        "type": "object",
        "properties": {
            "server_name": {
                "type": "string",
                "minLength": 1
            },
            "log_requests_file_name": {
                "type": "string",
                "minLength": 1
            },
            "log_server_file_name": {
                "type": "string",
                "minLength": 1
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
                    "type": "string",
                    "minLength": 1
                }

            },
            "cgi_file": {
                "type": "string",
                "minLength": 1
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
                        "type": "string",
                        "minLength": 1
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
    schema_cgi_types = {
        "type": "object",
        "patternProperties": {
            "([A-z]|[0-9]|-|_)+$": {
                "type": "string",
                "minLength": 1
            }
        },
        "additionalProperties": False
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

    if 'cgi_file' in settings:
        soporte_cgi = True
        try:
            opciones_cgi = json.load(open(settings['cgi_file']))
        except json.JSONDecodeError:
            log_server.write('ERROR: el archivo '+settings['cgi_file']+' no es valido\n')
            log_server.write('No se utilizará CGI\n')
            soporte_cgi = False
        except OSError:
            log_server.write('ERROR: el archivo '+settings['cgi_file']+' no existe o no cuenta con permisos de lectura')
            log_server.write('\nNo se utilizará CGI\n')
            soporte_cgi = False
        if soporte_cgi:
            try:
                validate(opciones_cgi, schema_cgi_types)
            except ValidationError as e:
                log_server.write('ERROR: problema con el archivo '+settings['cgi_file']+'\n')
                log_server.write('<-------------------\_/------------------->\n\n')
                log_server.write(repr(e))
                log_server.write('\n<-------------------/^\------------------->\n')
                log_server.write('No se utilizará CGI\n')
                soporte_cgi = False
    print(mime_types)
    print(settings_file)
    print(soporte_cgi)
    print(opciones_cgi)
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
