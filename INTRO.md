
# Introducción
El objetivo de este trabajo es mejorar la comprensión del protocolo HTTP, creando un servidor el cual provee un subconjunto de la funcionalidad propuesta en el [RFC 2616](https://www.w3.org/Protocols/rfc2616/rfc2616.html).


---
## Descripción del problema

Conforme la accesibilidad al Internet y su uso aumentó, nació también la necesidad de poder crear protocolos para facilitar la comunicación y el acceso a los recursos. Particularmente importante fue y es  HTTP, hasta el punto de convertirse en indispensable para el desarrollo de aplicaciones para Internet.

Por ello para poder utilizarlo correctamente, es de suma importancia comprender de forma profunda su funcionamiento, centrándonos en algunas de sus funciones, pero abarcando lo suficiente para poder incorporar su uso en nuestras actividades cotidianas como profesionales en computación e informática.

Pero no solo es importante conocer el funcionamiento del  protocolo HTTP. Aunque este demostró ser muy importante sobre todo para el uso de sitios web estáticos, con el avance del Internet se quedo un poco corto a la hora de trabajar con contenido altamente dinámico. Por ello surge, no como alternativa sino como complemento, un estándar que permite comunicar datos entre un programa y el servidor HTTP, lo cual permite que algunos archivos puedan ser procesados antes de ser devueltos al cliente.


---
## Descripción de la metodología

Para la resolución el problema se realiza un servidor web reducido, con el fin de lograr entender mejor su funcionamiento. Debido a su naturaleza de protocolo, no está definida su implementación, sino su funcionalidad, indicando la forma en que deben de realizarse las peticiones y la forma en que deben ser respondidas.

Por ello va a ser de vital importancia consultar el RFC 2616, el cual define el estándar HTTP 1.1, comprenderlo tanto para realizar solicitudes como para completarlas. No se plantea que el servidor por realizar cumpla con todas las funciones y respuestas de este estándar, ni que considere todos sus parámetros.

Se plantea desarrollarlo con una funcionalidad menor, pero que garantice una correcta comprensión del protocolo, centrándonos en los aspecto más importante de las solicitudes y sus correspondiente respuestas. Es necesario también una vez realizado, aplicar una serie de pruebas y evaluar sus resultados, de manera que pueda evaluarse su correcto funcionamiento, y sobre todo su correcta comprensión.
