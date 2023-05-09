# Trabajo practico I - File-Transfer - Introduccion a los Sistemas Distribuidos (1C-2023)


---


<p align="center">
<br>
<br>
  <img src="https://www.estudiaradistancia.com.ar/logos/original/logo-universidad-de-buenos-aires.webp" height=150 />
  <img  src="https://confedi.org.ar/wp-content/uploads/2020/09/fiuba_logo.jpg" height="150">
<br>
<br>
</p>

---


## Grupo 2

### Integrantes

| Nombre                                                              | Padrón |
| ------------------------------------------------------------------- | ------ |
| [Luciano Martin Gamberale](https://github.com/lucianogamberale)     | 105892 |
| [Erick Martinez Quintero](https://github.com/erick12m)              | 103745 |
| [Facundo Monpelat](https://github.com/fmonpelat)                    |  92716 |
| [Lionel Guglielmone](https://github.com/lionelguglielmone)          |  96963 |
| [Miguel Vasquez](https://github.com/MiguelV5)                       | 107378 |

---

## Introducción

El presente trabajo práctico tiene como objetivo la creación de una aplicación de red que implemente transferencia de archivos
entre cliente y servidor (multiples clientes).
Para tal finalidad, será necesario comprender cómo se comunican los procesos a través de la red, y cuál es el modelo de servicio que la capa de transporte le ofrece a la capa de aplicación. Además se aprenderá el uso de la interfaz de
sockets y los principios básicos de la transferencia de datos confiable (RDT).

## Para correr la topología:
```bash
sudo mn --custom ./src/topologia.py --topo customTopo,num_clients=4,loss_percent=10 --mac -x
```


## Ejecución start-server

```
$ python3 src/start-server.py -h
usage: start-server.py [-h] [-v | -q] [-H ADDR] [-p PORT] [-saw | -sr] [-s STORAGE]

Start the server

options:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -q, --quiet           decrease output verbosity
  -H ADDR, --host ADDR  the server's listening IP address
  -p PORT, --port PORT  the server's listening port
  -saw, --stop_and_wait
                        choose Stop and Wait transference
  -sr, --selective_repeat
                        choose Selective Repeat transference
  -s STORAGE, --storage STORAGE
                        specify the server's storage path
```

Inicia el server.

***Nota***:
Si no se indica el `STORAGE` se guardará en `./misc/sv_storage/` .
Si no se indica el protocolo de manejo de errores, se elige Stop And Wait por defecto.

## Ejecución download

```
$ python3 src/download_file.py -h
usage: download.py [-h] [-v | -q] [-H ADDR] [-p PORT] [-saw | -sr] -n FILENAME [-d FILEPATH]

Download a file from the server

options:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -q, --quiet           decrease output verbosity
  -H ADDR, --host ADDR  the server's listening IP address
  -p PORT, --port PORT  the server's listening port
  -saw, --stop_and_wait
                        choose Stop and Wait transference
  -sr, --selective_repeat
                        choose Selective Repeat transference
  -n FILENAME, --name FILENAME
                        name of the file to request to the server
  -d FILEPATH, --dst FILEPATH
                        destination file path
```

Descargar un archivo del server. 

***Nota***:
Es necesario indicar el nombre del archivo (`FILENAME`).
Si no se brinda `FILEPATH`: por defecto se almacena en `./misc/downloads/`.
Si no se indica el protocolo de manejo de errores, se elige Stop And Wait por defecto.

## Ejecución upload

```
$ python3 src/upload.py -h

usage: upload.py [-h] [-v | -q] [-H ADDR] [-p PORT] [-saw | -sr] -n FILENAME -s FILEPATH

Upload a file to the server

options:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -q, --quiet           decrease output verbosity
  -H ADDR, --host ADDR  the server's listening IP address
  -p PORT, --port PORT  the server's listening port
  -saw, --stop_and_wait
                        choose Stop and Wait transference
  -sr, --selective_repeat
                        choose Selective Repeat transference
  -n FILENAME, --name FILENAME
                        name of the file to request to the server
  -s FILEPATH, --src FILEPATH
                        path to the file to upload
```


Este programa permite al usuario subir un nuevo archivo al servidor, en caso de que ya exista será remplazado.

***Nota***:
Es necesario indicar el nombre del archivo (`FILENAME`).
Si no se brinda `FILEPATH`: por defecto se busca en `./misc/files_to_upload`.
Si no se indica el protocolo de manejo de errores, se elige Stop And Wait por defecto

