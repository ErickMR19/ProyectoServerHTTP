
# Casos de prueba

Se realizan distintas pruebas. Las primeras utilizando una aplicación CLI la cual es un cliente que genera peticiones HTTP, llamada cURL. Estas se encargan de comprobar algún funcionamiento específico y de forzar ciertos errores. 
Por la configuración del servidor en todos los casos, está escuchando en el puerto 8080 en la dirección 127.0.0.1.

1-) ```curl -i http://127.0.0.1:8080/```

2-) ```curl -i -H "Accept: image/png" http://127.0.0.1:8080/form.html```

3-) ```curl -i -X HEAD http://127.0.0.1:8080/index.html```

4-) ```curl -i http://127.0.0.1:8080/archivonoexistente.html```

5-) ```curl -i -X POST -d "mensaje=Hola+Mundo" http://127.0.0.1:8080/index.html```

6-) ```curl -i http://127.0.0.1:8080/index.html?name=Erick```

Se realizan otras pruebas más funcionales, donde se evalúa su experiencia desde un navegador.

7-) Visitar ```http://127.0.0.1:8080/```

8-) Visitar ```http://127.0.0.1:8080/info.php```

9-) Visitar ```http://127.0.0.1:8080/form.html```