<a href="https://www.gotoiot.com/">
    <img src="_doc/gotoiot-logo.png" alt="logo" title="Goto IoT" align="right" width="60" height="60" />
</a>

Service Beacons Scanner
=======================

*Ayudaría mucho si apoyaras este proyecto con una ⭐ en Github!*

`Bluetooth` es un protocolo que sirve para crear redes personales de manera inalámbrica en la banda de 2.4 Ghz. `BLE` es la version low energy del protocolo Bluetooth orientada a dispositivos de bajo consumo. Las comunicaciones dentro de BLE pueden realizarse bajo el esquema de `Advertising` o bien a través de `Connections`.

Dentro de las comunicaciones mediante el mecanismo de Advertising de Bluetooth Low Energy existe una implementación denominada `Beacons`, en la que dispositivos emiten periódicamente una señal que contiene información propia que otros dispositivos dentro del rango de cobertura pueden leer y actuar en consecuencia. Dentro de los beacons existen distintos protocolos, los más conocidos son `iBeacon` desarrollado por Apple y `Eddystone` desarrollado por Google, aunque también existen otras implementaciones.`Bluetooth` es un protocolo que sirve para crear redes personales de manera inalámbrica en la banda de 2.4 Ghz. `BLE` es la version low energy del protocolo Bluetooth orientada a dispositivos de bajo consumo. Las comunicaciones dentro de BLE pueden realizarse bajo el esquema `central-peripheral` o bien `broadcaster-observer`.

Dentro del tipo broadcaster-observer existe un subtipo de dispositivos que se comunican a través de paquetes `beacons`, emitiendo información periódica que otros dispositivos pueden capturar y reaccionar en consecuencia (observers). Dentro de los beacons existen distintos protocolos de comunicación. Los protocolos `iBeacon` desarrollado por Apple y `Eddystone` desarrollado por Google, son los más dominantes.

Este proyecto es un scanner (observer) de distintas tramas beacons que lee los beacons cercanos y aloja las lecturas en una memoria interna. Tiene además una `HTTP REST API` como interfaz que te permite controlar el scanner y obtener los datos de los beacons leidos. Está desarrollado en `Python` y se ejecuta sobre un contenedor de `Docker`. 

> Para que este servicio funcione deberías contar con un host que tenga Bluetooth LE 4.0+.

> El soporte actual es únicamente para tramas iBeacon.

## Instalar las dependencias 🔩

Para correr este proyecto es necesario que instales `Docker` y `Docker Compose`. 

<details><summary><b>Mira cómo instalar las dependencias</b></summary><br>

En [este artículo](https://www.gotoiot.com/pages/articles/docker_installation_linux/) publicado en nuestra web están los detalles para instalar Docker y Docker Compose en una máquina Linux. Si querés instalar ambas herramientas en una Raspberry Pi podés seguir [este artículo](https://www.gotoiot.com/pages/articles/rpi_docker_installation) de nuestra web que te muestra todos los pasos necesarios.

En caso que quieras instalar las herramientas en otra plataforma o tengas algún incoveniente, podes leer la documentación oficial de [Docker](https://docs.docker.com/get-docker/) y también la de [Docker Compose](https://docs.docker.com/compose/install/).

Continua con la descarga del código cuando tengas las dependencias instaladas y funcionando.

</details>

## Descargar el código 💾

Para descargar el código, lo más conveniente es que realices un `fork` de este proyecto a tu cuenta personal haciendo click en [este link](https://github.com/gotoiot/service-beacons-scanner/fork). Una vez que ya tengas el fork a tu cuenta, descargalo con este comando (acordate de poner tu usuario en el link):

```
git clone https://github.com/USER/service-beacons-scanner.git
```

> En caso que no tengas una cuenta en Github podes clonar directamente este repo.

## Ejecutar la aplicación 🚀

Cuando tengas el código descargado, desde una terminal en la raíz del proyecto ejecuta el comando `docker-compose build beacons-scanner` que se va encargar de compilar la imagen del scanner en tu máquina (este proceso puede durar unos minutos dependiento tu conexión a internet). 

Una vez que haya compilado activa el Bluetooth en el sistema y ejecutá el comando `docker-compose up` para poner en funcionamiento el servicio. En la terminal (entre un log inicial y las configuraciones) deberías ver una salida similar a la siguiente:

```
...
...
      /$$$$$$            /$$                    /$$$$$$      /$$$$$$$$
     /$$__  $$          | $$                   |_  $$_/     |__  $$__/
    | $$  \__/ /$$$$$$ /$$$$$$   /$$$$$$         | $$   /$$$$$$| $$   
    | $$ /$$$$/$$__  $|_  $$_/  /$$__  $$        | $$  /$$__  $| $$   
    | $$|_  $| $$  \ $$ | $$   | $$  \ $$        | $$ | $$  \ $| $$   
    | $$  \ $| $$  | $$ | $$ /$| $$  | $$        | $$ | $$  | $| $$   
    |  $$$$$$|  $$$$$$/ |  $$$$|  $$$$$$/       /$$$$$|  $$$$$$| $$   
     \______/ \______/   \___/  \______/       |______/\______/|__/   

                      SERVICE BEACONS SCANNER
                      -----------------------
...
...
```

Si ves esta salida significa que el servicio se encuentra corriendo adecuadamente. Podés leer la información útil para tener un mejor entendimiento de la aplicación.

## Información útil 🔍

En esta sección vas a encontrar información que te va a servir para tener un mayor contexto.

<details><summary><b>Mira todos los detalles</b></summary>

### Funcionamiento de la aplicación

El objetivo de la aplicación es leer paquetes de beacons cercanos y guardar esas lecturas en una memoria interna. A traves de su REST API HTTP podés leer los beacons y las configuraciones del scanner, y también modificar su comportamiento. Al iniciar, el dispositivo carga la configuración leyendo el archivo `_storage/settings.json`. En función de los settings inicializa el scanner y luego se queda esperando que lleguen requests HTTP.

La lectura de los beacons se realiza en un proceso aparte y cuando se produce un cambio en la lectura de beacons se publica automáticamente un evento (acción configurable) con los datos del beacon leido.

Cuando se recibe una nueva configuración para el scanner por HTTP, si los datos son correctos, la aplicación guarda los nuevos cambios en el archivo  `_storage/settings.json` y actualiza el funcionamiento.

### Configuración de la aplicación

La configuración de toda la aplicación está alojada en el archivo `_storage/settings.json`. Podés cambiarla escribiendo en este archivo directamente. Si por casualidad llegás a borrar la configuración, podés copiar y modificar esta:

```json
{
    "FAKE_SCAN": true,
    "MAX_SCAN_TICK": 20,
    "MIN_SCAN_TICK": 5,
    "RUN_FLAG": true,
    "SCAN_TICK": 10,
    "BEACONS_LIST_CAPACITY": 20,
    "UUID_FILTER": "ffffffff-bbbb-cccc-dddd-eeeeeeeeeeee",
    "EVENTS_TO_OMIT": "BaseEvent, IBeaconRead"
}
```

Los parámetros de configuración significan lo siguiente:

* **UUID_FILTER**: Filtro para solamente escanear los beacons que tengan tal UUID.
* **RUN_FLAG**: Flag que determina si se deben realizar lecturas de beacons o no.
* **SCAN_TICK**: Valor expresado en segundos que determina cada cuanto tiempo se va a realizar la lectura de beacons.
* **MAX_SCAN_TICK**: Valor máximo admisible expresado en segundos en la lectura de beacons.
* **MIN_SCAN_TICK**: Valor mínimo admisible expresado en segundos en la lectura de beacons.
* **FAKE_SCAN**: Flag que determina si las lecturas se realizan a través del Bluetooth del sistema o de manera simulada.
* **BEACONS_LIST_CAPACITY**: Capacidad maxima de lectura de beacons cercanos
* **EVENTS_TO_OMIT**: La lista de eventos que no se publicaran en caso que sucedan.

Por razones del buen funcionamiento de la aplicación, a través de la interfaz HTTP sólo se pueden modificar las configuraciones UUID_FILTER, RUN_FLAG, SCAN_TICK y FAKE_SCAN. El resto solo son configurables mediante el archivo `_storage/settings.json`.

### Variables de entorno

Si querés modificar algúna configuración como variable de entorno podés modificar el archivo `env`. Por lo general la configuración por defecto funciona sin necesidad que la modifiques.

### Interfaz HTTP

A través de la interfaz HTTP podés acceder a todos los recursos del servicio. A continuación están los detalles de cada uno de los endpoints con los métodos que acepta.

Obtener el estado del servicio
* **URL**: http://localhost:5000/status
* **METHOD**: GET

Obtener la info de los ibeacons
* **URL**: http://localhost:5000/ibeacon_scanner/beacons_data
* **METHOD**: GET

Obtener los settings del scanner de ibeacons
* **URL**: http://localhost:5000/ibeacon_scanner/settings
* **METHOD**: GET

Cambiar los settings del scanner de ibeacons
* **URL**: http://localhost:5000/ibeacon_scanner/settings
* **METHOD**: PUT
* **EXAMPLE BODY**: {"uuid_filter": "ffffffff-bbbb-cccc-dddd-eeeeeeeeeeee", "scan_tick": 3, "run_flag": true, "fake_scan": true}

Detener el scanner de ibeacons
* **URL**: http://localhost:5000/ibeacon_scanner/stop
* **METHOD**: POST

Iniciar el scanner de ibeacons
* **URL**: http://localhost:5000/ibeacon_scanner/start
* **METHOD**: POST

### Binarios

Puede haber ocasiones donde te sea útil ejecutar parte de la funcionalidad como un binario. Todas las utilidades binarias se encuentran en el directorio `bin`.

El siguiente comando te muestra un ejemplo para correr el scanner de ibeacons.

```
docker-compose run ibeacon-scanner python bin/run_ibeacon_scanner.py
```

El siguiente comando sirve para detener el scanner de ibeacons.

```
docker-compose run ibeacon-scanner python bin/stop_ibeacon_scanner.py
```

### Pruebas

La mejor forma de probar el servicio es a través de un cliente HTTP. En el directorio `test/other/requests.http` tenés un archivo para probar todas las funcionalidades provistas. Para correr estos requests es necesario que los ejecutes dentro de Visual Studio Code y que instales la extensión REST Client. Sino, podés correr los requests desde Postman, CURL o cualquier otro.

Si querés probar algunas de las funcionalidades de manera independiente podés mirar el directorio `test` donde vas a encontrar diferentes códigos de testing.

</details>

## Tecnologías utilizadas 🛠️

<details><summary><b>Mira la lista de tecnologías usadas en el proyecto</b></summary><br>

* [Docker](https://www.docker.com/) - Ecosistema que permite la ejecución de contenedores de software.
* [Docker Compose](https://docs.docker.com/compose/) - Herramienta que permite administrar múltiples contenedores de Docker.
* [Python](https://www.python.org/) - Lenguaje en el que están realizados los servicios.
* [Beacons Tools](https://pypi.org/project/beacontools/) - Biblioteca de Python para interactuar con varios tipos de beacons.

</details>

## Contribuir 🖇️

Si estás interesado en el proyecto y te gustaría sumar fuerzas para que siga creciendo y mejorando, podés abrir un hilo de discusión para charlar tus propuestas en [este link](https://github.com/gotoiot/service-beacons-scanner/issues/new). Así mismo podés leer el archivo [Contribuir.md](https://github.com/gotoiot/gotoiot-doc/wiki/Contribuir) de nuestra Wiki donde están bien explicados los pasos para que puedas enviarnos pull requests.

## Sobre Goto IoT 📖

Goto IoT es una plataforma que publica material y proyectos de código abierto bien documentados junto a una comunidad libre que colabora y promueve el conocimiento sobre IoT entre sus miembros. Acá podés ver los links más importantes:

* **[Sitio web](https://www.gotoiot.com/):** Donde se publican los artículos y proyectos sobre IoT. 
* **[Github de Goto IoT:](https://github.com/gotoiot)** Donde están alojados los proyectos para descargar y utilizar. 
* **[Comunidad de Goto IoT:](https://groups.google.com/g/gotoiot)** Donde los miembros de la comunidad intercambian información e ideas, realizan consultas, solucionan problemas y comparten novedades.
* **[Twitter de Goto IoT:](https://twitter.com/gotoiot)** Donde se publican las novedades del sitio y temas relacionados con IoT.
* **[Wiki de Goto IoT:](https://github.com/gotoiot/doc/wiki)** Donde hay información de desarrollo complementaria para ampliar el contexto.

## Muestas de agradecimiento 🎁

Si te gustó este proyecto y quisieras apoyarlo, cualquiera de estas acciones estaría más que bien para nosotros:

* Apoyar este proyecto con una ⭐ en Github para llegar a más personas.
* Sumarte a [nuestra comunidad](https://groups.google.com/g/gotoiot) abierta y dejar un feedback sobre qué te pareció el proyecto.
* [Seguirnos en twitter](https://github.com/gotoiot/doc/wiki) y dejar algún comentario o like.
* Compartir este proyecto con otras personas.

## Autores 👥

Las colaboraciones principales fueron realizadas por:

* **[Agustin Bassi](https://github.com/agustinBassi)**: Ideación, puesta en marcha y mantenimiento del proyecto.

También podés mirar todas las personas que han participado en la [lista completa de contribuyentes](https://github.com/gotoiot/service-beacons-scanner/contributors).

## Licencia 📄

Este proyecto está bajo Licencia ([MIT](https://choosealicense.com/licenses/mit/)). Podés ver el archivo [LICENSE.md](LICENSE.md) para más detalles sobre el uso de este material.

---

**Copyright © Goto IoT 2021** - [**Website**](https://www.gotoiot.com) - [**Group**](https://groups.google.com/g/gotoiot) - [**Github**](https://www.github.com/gotoiot) - [**Twitter**](https://www.twitter.com/gotoiot) - [**Wiki**](https://github.com/gotoiot/doc/wiki)
