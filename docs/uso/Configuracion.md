
# Opciones de configuración

A el servidor se le pueden proveer algunas opciones configurables en una archivo de tipo json, llamado *settings.json*. 

<table>
  <tr><th>Nombre</th><th>Descripción</th><th>Tipo Valor</th><tr>
  <tr>
    <td>server_name</td><td>Nombre del servidor mostrado en el encabezado</td><td>String</td><tr>
  </tr>
    <td>log_requests_file_name</td><td>Nombre del archivo de bitácora para las solicitudes</td><td>String</td><tr>
  <tr>
    <td>log_server_file_name</td><td>Nombre del archivo de bitácora para los eventos</td><td>String</td><tr>
  </tr>
  <tr>
    <td>htdocs_folder</td><td>Ruta de donde se tomarán los archivos que se soliciten al servidor</td><td>String</td>
  </tr>
  <tr>
    <td>port_listening</td><td>Puerto en el cual se escucharan los solicitudes</td><td>String</td><tr>
  <tr>
    <td>ip_listening</td><td>Dirección en la cual se escucharán las solicitudes (cadena vacía [""] indica que se escuche en todas las direcciones asignadas al equipo)</td><td>String</td><tr>
  </tr>
    <td>default_index</td><td>Nombres de los archivo que se usarán en caso de solicitarse una carpeta</td><td>Lista de String</td>
  </tr>
  <tr>
    <td>cgi_file</td><td>Indica el nombre del archivo donde está la configuración de <a href="Cgi.md">CGI</a></td><td>String</td>
  </tr>
</table>

En caso de no encontrarse este archivo, o alguno de estos valores, el servidor utilizará las opciones de configuración por defecto, definidas en el script*server.py*.