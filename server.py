from multiprocessing import Pool
import multiprocessing as mp
import time
import socket

# nombre del servidor
server_name = 'ErickMRServer/0.5'
# nombre del archivo de bitacora
log_requests_file_name = 'serverhttp_requests.log'
log_server_file_name = 'serverhttp_events.log'
# carpeta de donde se encuentran los documentos
htdocs_folder = 'htdocs/'
# numero de puerto
port_number = 8080


def procesar_cabeceras(diccionario, cadena_texto):
    print('/*******************************************************************/')
    dividido = cadena_texto.split('\r\n')
    (recurso, version_http) = dividido.pop(0).split(' ')
    diccionario['recurso solicitado'] = recurso
    diccionario['version http'] = version_http
    for h in dividido:
        x, y = h.split(': ')
        diccionario[x] = y
    print(repr(diccionario))
    print('/*******************************************************************/')


def process_petition(socket_cliente, log_queue):
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
    cabecera_content_length = '0'
    if metodo_http == b'':
        socket_cliente.shutdown(socket.SHUT_RDWR)
        socket_cliente.close()
        return
    elif metodo_http == b'GET ':
        texto_bitacora += 'GET, '
        cabeceras_respuesta += 'HTTP/1.1 200 OK\r\n'
    elif metodo_http == b'POST':
        texto_bitacora += 'POST, '
        socket_cliente.recv(1)
        cabeceras_respuesta += 'HTTP/1.1 404 Not Found\r\n'
    elif metodo_http == b'HEAD':
        texto_bitacora += 'HEAD, '
        socket_cliente.recv(1)
        cabeceras_respuesta += 'HTTP/1.1 406 Not Acceptable\r\n'
    else:
        texto_bitacora += 'ERROR, '
        cabeceras_respuesta += 'HTTP/1.1 501 Not Implemented\r\n'
    texto_bitacora += tiempo + ', '
    texto_bitacora += ip_servidor + ', '
    texto_bitacora += ip_cliente + ', '
    cabeceras_respuesta += 'Date: '+fecha+'\r\n'
    cabeceras_respuesta += 'Server: '+server_name+'\r\n'
    cuerpo_respuesta = ''
    solicitud = ''
    buffer = socket_cliente.recv(4)
    cabeceras = dict()
    cuerpo = b''
    while 1:
            solicitud += buffer.decode()
            if solicitud.find("\r\n\r\n") != -1:
                print('solicitud: ' + solicitud)
                (texto_cabeceras, cuerpo) = solicitud.split("\r\n\r\n")
                print('cabeceras: '+texto_cabeceras)
                print('cuerpo: '+cuerpo)
                print('length cuerpo: '+str(len(cuerpo)))
                procesar_cabeceras(cabeceras, texto_cabeceras)
                break
            buffer = socket_cliente.recv(4)
    if metodo_http == b'POST':
        print('POST primer IF')
        if 'Content-Length' not in cabeceras:
            cabeceras['Content-Length'] = '0'
        print('en el cuerpo hay: ' + str(len(cuerpo)))
        while str(len(cuerpo)) != cabeceras['Content-Length']:
            buffer = socket_cliente.recv(4)
            cuerpo += buffer.decode()
    if cabecera_content_type != '':
        cabeceras_respuesta += 'Content-Type: ' + cabecera_content_type + '\r\n'
    cabeceras_respuesta += 'Content-Length: ' + cabecera_content_length + '\r\n'
    cabeceras_respuesta += '\r\n'
    respuesta = cabeceras_respuesta + cuerpo_respuesta
    # escribe en la bitácora
    log_queue.put(texto_bitacora)
    # codifica los datos a enviarse
    datos = str.encode(respuesta)
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
    with Pool(processes=numberProcessors-2) as pool:
        # put listener to work first
        watcher = pool.apply_async(bitacora, (cola,))

        # create an INET, STREAMing socket
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the socket to a public host, and a well-known port
        serversocket.bind(('', port_number))
        # become a server socket
        serversocket.listen(numberProcessors-1)
        log_server.write('/***********************************************/\n')
        log_server.write('Inicio Servidor: '+fecha_servidor + '\n')
        log_server.write('escuchando en el puerto: '+str(port_number) + '\n')
        log_server.write('El numero de procesadores es: ' + str(numberProcessors) + '\n')
        log_server.flush()
        while True:
            # accept connections from outside
            print('esperando')
            (clientsocket, address) = serversocket.accept()
            print('coneecion recibidida desde: '+str(address))
            log_server.flush()

            # now do something with the clientsocket
            # in this case, we'll pretend this is a threaded server
            pool.apply_async(process_petition, (clientsocket, cola,))

    # exiting the 'with'-block has stopped the pool
    print("Now the pool is closed and no longer available")
