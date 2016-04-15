# Bitácoras

Se utilizan dos archivos de bitácora. Una de eventos donde se registra la hora en la que el servidor inició, el número de procesadores con los que cuenta y en que dirección y puerto está escuchando peticiones. Si se produce algún error en la inicialización del servidor quedá registrado aquí.

La otra bitácora es de todas las solicitudes que se han realizado. El formato que utiliza es de una fila por solicitud, y separado por columnas los siguientes valores en el orden presentado.

<table>
  <tr>
    <th>Método</th>
    <th>Estampilla de Tiempo</th>
    <th>Servidor</th>
    <th>Solicitante</th>
    <th>Refiere</th>
    <th>URL</th>
    <th>Datos</th>
  </tr>
</table>

Este archivo no incluye los encabezados, está pensado para poder *parsearse* en caso de que ser necesario, para un mejor análisis de las misma. 