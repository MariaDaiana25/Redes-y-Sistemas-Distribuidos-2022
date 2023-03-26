# Informe

## Laboratorio 2: _Home-made File Transfer Protocol_

### Integrantes:

Grupo 33

- Coria Maria Daiana
- Garcia Fernandez Florencia Andrea
- Giuliano Maximiliano Gabriel

## Estructura del servidor

El servidor que se implementó usa como medio un sistema de sockets programados que permiten la comunicación cliente/servidor que fue realizado en el lenguaje Python y se usa como protocolo de transferencia de datos HFTP (Home-made File Transfer Protocol).

- **server.py**: Inicialización y lanzamiento del servidor.

   - `__init__`: Se crea y configura su socket, se establece el directorio donde están (o estarán) los archivos a compartir, y se lo habilita para aceptar solicitudes de conexiones por parte de los clientes.
   - `serve`: Se acepta una conexión de un cliente, creándose un nuevo socket dedicado a la comunicación entre el cliente y el servidor. Cuando se desconecta el cliente, el servidor estará disponible para una nueva solicitud de un cliente.

- **connection.py**: Inicialización de la conexión y atención de pedidos del cliente.

   - `__init__`: Se especifica el socket a utilizar, el directorio compartido del server, y otras variables útiles para la ejecución.
   - `handle`: Atiende eventos de la conexión hasta que termina. Recibe datos del cliente, los separa en strings correspondientes a un comando y sus argumentos, y los ejecuta.
   - Comandos aceptados: Se comprueba la cantidad de argumentos y su validez, en base a lo especificado en el protcolo HFTP. De ser correctos, se ejecuta el comando y se envía la respuesta al cliente. Se manejan los errores con una función auxiliar.
      - `get_file_listing`: Envía la lista de archivos que están actualmente disponibles en el directorio compartido.
      - `get_metadata`: Envía el tamaño del archivo pedido.
      - `get_slice`: Envía un fragmento o slice del archivo pedido, codificado en base64, de un cierto tamaño y comenzando desde un punto en particular.
      - `quit`: Termina la conexión.

## Decisiones de diseño

En **server.py** se decidió asegurarse de que exista el directorio compartido (se lo crea si aún no existe), para evitar que el comando `get_file_listing` genere un INTERNAL ERROR y desconecte al cliente.

En **connection.py** se implementaron funciones auxiliares para simplificar el manejo de erores y facilitar la comprensión del código.

- `recv_buffer_in` y `send_buffer_out`: Reciben o envían datos al cliente, codificados en ASCII, y si se detecta un error terminan la conexión para evitar que se caiga el servidor.
- `get_error_msg`: Genera el string con el código de respuesta y su texto descriptivo, y lo envía al cliente. Si el código corresponde a un error fatal, termina la conexión.
- `parse_request`: Se separa el pedido en el comando y sus argumentos. De ser comandos válidos, se llama al método correspondiente.

También se estableció un "timeout" de 5 minutos, para evitar que un cliente bloquee la conexión si pasa mucho tiempo sin enviar nada al servidor.

El timeout, `recv_buffer_in` y `send_buffer_out` fueron implementados para que el servidor nunca se caiga o bloquee a causa de un cliente, es decir, que sea más robusto.

## Dificultades y Resoluciones

Al principio las dificultades estuvieron en acostumbrarse al estilo de código de Python y el funcionamiento de los módulos, y en la comprensión de la lógica organizativa de un socket y el protocolo utilizado. Para esto ayudó mucho leer el material de la cátedra, la documentación de Python, y los tutoriales disponibles en Internet.

Luego, hubo que asegurarse de entender lo que se pedía de cada comando, del manejo de errores, y la robustez del servidor necesaria para tolerar comandos malformados y malintencionados. Aquí investigamos sobre las funciones de Python necesarias para obtener la información que se debe transmitir al cliente (librería os, manejo de archivos).

También se investigó sobre los problemas y errores que pueden ocurrir, y cómo manejarlos como excepciones para que el servidor no se caiga.

## PREGUNTAS

1. ¿Qué estrategias existen para poder implementar este mismo servidor pero con capacidad de atender múltiples clientes simultáneamente? Investigue y responda brevemente qué cambios serían necesario en el diseño del código.

  Por lo que se investigó existen varias formas de un servidor con múltiples clientes simultáneamente.

    - Multiprocesssing: Paralelismo basado en procesos. Cada cliente es un nuevo proceso.

    - Threading: Paralelismo basado en hilos. Cada cliente es un nuevo hilo.

  Para su implementación, en ambos casos solo hace falta modificar el archivo **server.py**, importando la librería correspondiente, y creando un nuevo proceso o hilo para cada llamada a `Connection.handle`. También se pueden agregar un conteo y condiciones para que solo se conecten una cierta cantidad de clientes al mismo tiempo.

2. Pruebe ejecutar el servidor en una máquina del laboratorio, mientras utiliza el cliente desde otra, hacia la IP de la máquina servidor. ¿Qué diferencia hay si se corre el servidor desde la IP “localhost”, “127.0.0.1” o la IP “0.0.0.0”?

  La diferencia entre localhost o 127.0.0.1 y 0.0.0.0 es que localhost es la dirección de loopback, mientras que 0.0.0.0 es una meta-dirección no enrutable que se usa para designar un objeto no válido o desconocido (lo que sería un marcador de posición sin dirección en particular).

  En el contexto de una entrada de ruta 0.0.0.0 generalmente es la ruta predeterminada. En el contexto de los servidores significa todas las direcciones IPv4 en la máquina local.
  
  127.0.0.1 es la dirección IP de bucle invertido que se utiliza para establecer una conexión a la misma máquina o computadora que utiliza el usuario final.
