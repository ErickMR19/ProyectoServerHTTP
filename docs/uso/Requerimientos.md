
#  Requerimientos

El servidor es multiplataforma. Lo único que necesita es una versión del intérptrete de Python 3 (el proyecto fue desarrollado y probado en Python 3.5.1)

Se puede hacer uso de alguna aplicación compatible con CGI (probado con PHP 5.5 y 5.6), se requiere que la misma esté lista para su ejecución, y que el usuario que ejecuta el servidor tenga permisos de acceso a la misma.

En el caso de los sistema UNIX posiblemente se requieran privilegios si se quiere ejecutar al servidor escuchando en el puerto 80 o alguno cuyo número sea inferior a 1000.