
# Resultados de los casos de prueba

1) 
<pre>HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Date: Fri, 15 Apr 2016 10:05:09 GMT
Server: ErickMRServer/0.5
Content-Length: 201
&nbsp;
&nbsp;
<html>
    <head>
        <title>Server Funcionando</title>
    </head>
    <body>
        <h2>Hola Mundo!</h2>
        <hr />
        <img alt="LOGO" src="img/logo.png" />
    </body>
</html>
</pre>


2) 
<pre>HTTP/1.1 406 Not Acceptable
Content-Type: text/html; charset=utf-8
Date: Fri, 15 Apr 2016 10:06:37 GMT
Server: ErickMRServer/0.5
Content-Length: 0
&nbsp;
&nbsp;
</pre>

3. ```Warning: Setting custom HTTP method to HEAD may not work the way you want.
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Date: Fri, 15 Apr 2016 10:07:38 GMT
Server: ErickMRServer/0.5
Content-Length: 201

curl: (18) transfer closed with 201 bytes remaining to read
```

4. ```HTTP/1.1 404 Not Found
Date: Fri, 15 Apr 2016 10:08:15 GMT
Server: ErickMRServer/0.5
Content-Length: 0

```

5. ```HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Date: Fri, 15 Apr 2016 10:05:09 GMT
Server: ErickMRServer/0.5
Content-Length: 201

<html>
    <head>
        <title>Server Funcionando</title>
    </head>
    <body>
        <h2>Hola Mundo!</h2>
        <hr />
        <img alt="LOGO" src="img/logo.png" />
    </body>
</html>```

6. ```HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Date: Fri, 15 Apr 2016 10:05:09 GMT
Server: ErickMRServer/0.5
Content-Length: 201

<html>
    <head>
        <title>Server Funcionando</title>
    </head>
    <body>
        <h2>Hola Mundo!</h2>
        <hr />
        <img alt="LOGO" src="img/logo.png" />
    </body>
</html>```