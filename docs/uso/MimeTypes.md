
# MimeTypes

Es el archivo que indica el Content-Type y el modo de lectura de algún archivo basado en su extensión. Es de tipo json. Se puede visualizar como un arreglo asociativo, donde la clave es la extensión, y el valor un objeto, que contiene la propiedad *content-type*y puede o no contener la propiedad *binary* que indica si el archivo debe leerse en modo binario o no (en caso de no estar presente se lee en modo texto).

Este archivo es indispensable, en caso de no estar presente, o ser inválido, el servidor no iniciará. Es también necesario que exista al menos la clave *default* que se utilizará cuando algún archivo no tenga la extensión registrada. 
