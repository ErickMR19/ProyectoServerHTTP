
# Análisis de los resultados de las pruebas

1-) Se reciben los encabezados esperados, además el contenido del *index.html* cuyo nombre a pesar de no estar presente en la petición se encuentra entre los nombres definidos como índice al solicitar una carpeta (en este caso la raíz).
En la bitácora se registra la solicitud de la manera esperada.

2-) Se fuerza a un error 406. Se solicita un archivo html pero se indica que únicamente se acepta un archivo de MIME-type *image/png*. El servidor retorna el esperado código de estado 406.

3-) La solicitud es similar al caso 1, pero en este caso se utiliza el método HEAD. El resultado es el esperado, ya que envía los mismos encabezados, pero no así el cuerpo del mensaje.

4-) Se fuerza a un error 404. Se solicita un archivo no existente. El servidor lo maneja bien, devolviendo al cliente un código de estado 404.

5-) Muy similar al caso 1. En este caso se realiza una solicitud con el método POST. Se reciben los mismos encabezados y cuerpo del mensaje. Esto es lo esperado, dado que lo que se envía no genera ningún cambio. Sin embargo se verifica que se recibe el cuerpo de la solicitud de manera correcta, verificando el texto de la bitácora.

6-) Igual que el caso 6, solo que en este caso el método es GET, y por ello los datos se envían en la URL. De la misma manera, se verifica esto en el texto de la bitácora.

7-) Se verifica que el servidor comprende correctamente la solicitud proveniente desde un navegador. Además al recuperar una imagen incrustada, se puede verificar en la bitácora el campo *Referer* de la cabecera.


8-) Se verifica que el CGI de PHP trabaje correctamente. Se recupera un archivo que llama a la función ```phpinfo()``` la cual despliega la información de configuración y estado de PHP. Al recibirse estos datos de manera correcta, se llega a que funciona de manera correcta.

9-) Se accede a un formulario básico HTML, el cual envía los datos ingresados a un archivo PHP. Este muestra todas las variables asignadas que tiene tanto por GET como por POST. El formulario permite escoger el método de envío. Se realizó una prueba con cada uno. Se obtienen los resultados esperados, mostrando el valor de las variables recibidas según el método seleccionado. 