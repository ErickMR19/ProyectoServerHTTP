import re
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
import multiprocessing as mp
import time
import socket
import json
import os

# nombre del servidor
server_name = 'ErickMRServer/0.5'
# nombre del archivo de bitacora
log_requests_file_name = 'serverhttp_requests.log'
log_server_file_name = 'serverhttp_events.log'
# carpeta de donde se encuentran los documentos
htdocs_folder = 'htdocs'
# numero de puerto para escuchar
port_listening = 8080
# direccion ip donde escuchar
ip_listening = ''
# indices por default
default_index = ('index.html', 'home.html')

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
    (discard_prove, discard, diccionario['recurso_solicitado_extension']) = diccionario['recurso_solicitado_extension'].rpartition('.')
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
    filename = htdocs_folder+filename
    print('param: filename='+filename+' extension='+extension)
    if filename == '' or filename[-1] == '/':
        for filename_index in default_index:
            print(filename + filename_index)
            if os.path.isfile(filename + filename_index):
                filename += filename_index
                (discard, discard, extension) = filename_index.rpartition('.')
                break
    if extension not in mime_types or 'content-type' not in mime_types[extension]:
        extension = 'default'
    type_file_read = 'r'
    if 'binary' in mime_types[extension] and mime_types[extension]['binary'] == True:
        type_file_read = 'rb'
    mime_type_file = ''
    archivo = None
    if filename != '':
        print('filename: '+filename+' | htdocs_folder: '+htdocs_folder)
        if '..' not in os.path.relpath(filename, htdocs_folder):
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
        cabeceras_respuesta += respuesta_http['200']
    elif metodo_http == b'POST':
        texto_bitacora += 'POST, '
        socket_cliente.recv(1)
        cabeceras_respuesta += respuesta_http['404']
    elif metodo_http == b'HEAD':
        texto_bitacora += 'HEAD, '
        socket_cliente.recv(1)
        cabeceras_respuesta += respuesta_http['406']
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
    cabeceras_respuesta += 'Server: ' + server_name + '\r\n'
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

    log_requests = open(log_requests_file_name, 'a')
    while True:
        m = cola_bitacora.get()
        log_requests.write(str(m) + '\n')
        log_requests.flush()
    log_requests.close()


if __name__ == '__main__':
    # obtiene el numero de procesadores disponibles
    numberProcessors = mp.cpu_count()
    log_server = open(log_server_file_name, 'a')
    if numberProcessors < 3:
        numberProcessors = 3
    administrador = mp.Manager()
    cola = administrador.Queue()
    fecha_servidor = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
    log_server.write('/***********************************************/\n')
    log_server.write('Inicio Servidor: ' + fecha_servidor + '\n')
    log_server.write('escuchando en el puerto: ' + str(port_listening) + '\n')
    log_server.write('El numero de procesadores es: ' + str(numberProcessors) + '\n')
    log_server.flush()

    try:
        mime_types = json.load(open('mimetypes.json'))
    except json.JSONDecodeError:
        log_server.write('ERROR: el archivo mimetypes.json no es valido\n')
        exit(-1)
    except OSError:
        log_server.write('ERROR: el archivo mimetypes.json no existe o no cuenta con permisos de lectura\n')
        exit(-1)
    if 'default' not in mime_types or 'content-type' not in mime_types['default']:
        log_server.write('ERROR: opcion default no se encuentra correctamente configurada en mimetypes.json\n')
        exit(-1)

    print(mime_types)
    with ThreadPool(processes=numberProcessors-2) as pool:
        # put listener to work first
        watcher = pool.apply_async(bitacora, (cola,))

        # create an INET, STREAMing socket
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the socket to a public host, and a well-known port
        serversocket.bind(('', port_listening))
        # become a server socket
        serversocket.listen(numberProcessors-1)
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
