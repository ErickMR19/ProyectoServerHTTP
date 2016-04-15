

# Análisis del problema

En el problema se identifican 3 grandes secciones.

En primer lugar la comunicación. El protocolo HTTP está pensado para utilizarse en Internet. Esto hace necesario el uso de una dirección de red, un número de puerto, y un protocolo de transporte. Típicamente, el más extendido e implementado para HTTP es TCP.

En segundo lugar, la parte más importante del problema es entender la solicitud. En HTTP 1.1 la solicitud incluye las cabeceras en texto plano y en algunos métodos también incluye un cuerpo. Por ello el problema implica tener identificado tanto el cuerpo como las cabeceras, e identificar en la cabecera aquellos campos que sean importantes para poder comprender la solicitud. Ello va a implicar encontrar el archivo solicitado, y leerlo o procesarlo según sea el caso.

La parte tercera consiste en dar una respuesta adecuada y coherente al cliente. Debe consistir de algún código de estado, indicando si el archivo no existiese, si no fuera del tipo solicitado, y en el caso de ser válido el contenido del mismo, o la respuesta que generara el programa que lo proceso si fuera el caso.

Además de esto, surge un asunto externo al problema. Si la cantidad de solicitudes fuera muy elevada, el rendimiento podría no ser el deseado. También debe tomarse en cuenta que la solución debe ser ejecutable en ambientes Windows y Unix. 
