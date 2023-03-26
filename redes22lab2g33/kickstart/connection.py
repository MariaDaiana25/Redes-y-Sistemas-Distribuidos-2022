# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import os
import socket
from base64 import b64encode

from constants import *


class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, socket, directory):
        # Inicializar atributos de Connection
        self.socket = socket
        self.directory = directory
        self.buffer_in = ""
        self.buffer_out = ""
        self.connected = True
        self.timeout = 5 * 60  # 5 minutos

    def get_file_listing(self, args):
        """
        Envía la lista de archivos que están actualmente disponibles.
        """
        if len(args) != 1:
            self.get_error_msg(INVALID_ARGUMENTS)
            return
        try:
            files = os.listdir(self.directory)
        except OSError:
            self.get_error_msg(INTERNAL_ERROR)
            return

        self.get_error_msg(CODE_OK)
        for file in files:
            self.buffer_out += file + EOL
        self.buffer_out += EOL
        self.send_buffer_out()

    def get_metadata(self, args):
        """
        Envía el tamaño del archivo 'filename' en bytes.
        """
        if len(args) != 2:
            self.get_error_msg(INVALID_ARGUMENTS)
            return
        try:
            filename = str(args[1])
        except ValueError:
            self.get_error_msg(INVALID_ARGUMENTS)
            return
        # al nombre del archivo lo transforma en un conjunto
        # es subconjunto de el conjunto de valid char
        if not set(filename).issubset(VALID_CHARS):
            self.get_error_msg(INVALID_ARGUMENTS)
            return

        try:
            filepath = os.path.join(self.directory, filename)
            if not os.path.exists(filepath):
                self.get_error_msg(FILE_NOT_FOUND)
                return
        except OSError:
            self.get_error_msg(INTERNAL_ERROR)
            return

        self.get_error_msg(CODE_OK)
        self.buffer_out = str(os.path.getsize(filepath)) + EOL
        self.send_buffer_out()

    def get_slice(self, args):
        """
        Envía un fragmento o slice del archivo 'filename', codificado en
        base64, de tamaño 'size' (en bytes) y comenzando desde 'offset'.
        """
        if len(args) != 4:
            self.get_error_msg(INVALID_ARGUMENTS)
            return
        try:
            filename = str(args[1])
            offset = int(args[2])
            size = int(args[3])
        except ValueError:
            self.get_error_msg(INVALID_ARGUMENTS)
            return

        if not set(filename).issubset(VALID_CHARS):
            self.get_error_msg(INVALID_ARGUMENTS)
            return

        try:
            filepath = os.path.join(self.directory, filename)
            if not os.path.exists(filepath):
                self.get_error_msg(FILE_NOT_FOUND)
                return
        except OSError:
            self.get_error_msg(INTERNAL_ERROR)
            return

        file_size = os.path.getsize(filepath)
        if size > file_size or size < 0:
            self.get_error_msg(INVALID_ARGUMENTS)
            return
        if offset + size > file_size or offset > file_size or offset < 0:
            self.get_error_msg(BAD_OFFSET)
            return

        try:
            file = open(filepath, 'rb')
        except OSError:
            self.get_error_msg(INTERNAL_ERROR)
            return

        file.seek(offset)
        self.get_error_msg(CODE_OK)
        file_read = b64encode(file.read(size))
        self.buffer_out = file_read.decode("ascii") + EOL
        self.send_buffer_out()
        file.close()

    def quit(self, args):
        """
        Termina la conexión.
        """
        if len(args) != 1:
            self.get_error_msg(INVALID_ARGUMENTS)
            return
        self.get_error_msg(CODE_OK)
        self.connected = False

    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        while self.connected:
            self.recv_buffer_in()
            while EOL in self.buffer_in and self.connected:
                request, self.buffer_in = self.buffer_in.split(EOL, 1)
                if not '\n' in request:
                    print("Request:", request)
                    self.parse_request(request)
                else:
                    self.get_error_msg(BAD_EOL)

        self.socket.close()

    def recv_buffer_in(self):
        """
        Recibe datos del cliente. Cierra la conexión si ocurre un error, para
        mantener en funcionamiento el servidor.
        """
        try:
            self.buffer_in += self.socket.recv(4096).decode("ascii")
            if self.buffer_in:
                # Evita que haya un timeout antes de que el cliente termine de
                # enviar el pedido, o antes de enviar la respuesta
                self.socket.settimeout(None)
            else:
                self.socket.settimeout(self.timeout)
        except UnicodeDecodeError:  # Pedido malformado
            self.get_error_msg(BAD_REQUEST)
        except TimeoutError:
            print("Connection timed out.")
            self.connected = False
        except ConnectionError as e:
            print("Connection Error.")
            self.connected = False

    def send_buffer_out(self):
        """
        Envía datos al cliente. Cierra la conexión si ocurre un error, para
        mantener en funcionamiento el servidor.
        """
        try:
            self.socket.send(self.buffer_out.encode("ascii"))
        except TimeoutError:
            print("Connection timed out.")
            self.connected = False
        except ConnectionError as e:
            print("Connection Error.")
            self.connected = False
        self.buffer_out = ""

    def parse_request(self, args):
        """
        Separa el pedido en una lista con el comando y sus argumentos.
        Llama al método correspondiente.
        """
        if not len(args):  # Es un "pedido vacío"
            return
        args = args.split(None)
        if args[0] == 'quit':
            self.quit(args)
        elif args[0] == 'get_file_listing':
            self.get_file_listing(args)
        elif args[0] == 'get_metadata':
            self.get_metadata(args)
        elif args[0] == 'get_slice':
            self.get_slice(args)
        else:
            self.get_error_msg(INVALID_COMMAND)

    def get_error_msg(self, code):
        """
        Envía un código de respuesta y su texto descriptivo.
        En caso de error fatal, cierra la conexión.
        """
        self.buffer_out = str(code) + ' ' + error_messages[code] + ' ' + EOL
        self.send_buffer_out()
        if fatal_status(code):
            self.connected = False
