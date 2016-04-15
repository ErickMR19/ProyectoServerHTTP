
# Configuración de CGI

Si en las opciones de configuración está indicado un valor para **cgi_file**, se tomará como un archivo de tipo json. Este tiene una estructura similar al archivo de MIME-TYPES. Se incluye una clave que indica una extensión, y una cadena que indica la ruta hasta el programa CGI que procesará los archivos de esa extensión.

Está probado y se asegura su funcionamiento únicamente con PHP. Debe comprobarse que la ruta al archivo sea correcta, de  lo contrario el servidor se verá afectado.