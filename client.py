"""
This file is part of biosiglive. It allows connecting to a biosiglive server and to receive data from it.
"""

import socket
import struct
import time
from typing import Union
import numpy as np

Buff_size = 32767


class Message:
    def __init__(self,
                 command: list = (),
                 read_frequency: float = 100,
                 nb_frame_to_get: int = 1,
                 get_names: bool = None,
                 mvc_list: list = None,
                 kalman: bool = None,
                 get_raw_data: bool = False,
                 **kwargs):
        """
        Message class
        """

        self.command = command
        self.emg_windows = 2000
        self.get_names = False
        self.nb_frames_to_get = 1
        self.get_names = get_names
        self.mvc_list = mvc_list
        self.kalman = kalman
        self.read_frequency = read_frequency
        self.nb_frames_to_get = nb_frame_to_get
        self.raw_data = get_raw_data
        for key in kwargs.keys():
            self.__setattr__(key, kwargs[key])

    def update_command(self, name: Union[str, list], value: Union[bool, int, float, list, str]):
        """
        Update the command.

        Parameters
        ----------
        name: str
            Name of the command to update.
        value: bool, int, float, list, str
            Value of the command to update.
        """
        names = [name] if not isinstance(name, list) else value
        values = [value] if not isinstance(value, list) else value
        values = [values] if name == "command" else values

        for i, name in enumerate(names):
            self.__setattr__(name, values[i])

    def get_command(self):
        """
        Get the command.

        Returns
        -------
        message: Message.dic
            Message containing the command.
        """
        return self.command

    def add_command(self, name: str, value: Union[bool, int, float, list, str]):
        """
        Add a command.

        Parameters
        ----------
        name: str
            Name of the command to add.
        value: bool, int, float, list, str
            Value of the command to add.
        """
        new_value = None
        old_value = self.get_command()[name]
        if isinstance(old_value, list):
            old_value.append(value)
            new_value = old_value
        elif isinstance(old_value, (bool, int, float, str)):
            new_value = value
        return self.update_command(name, new_value)


class Client:
    def __init__(self, server_ip: str, port: int, type: str = "TCP", name: str = None):
        """
        Create a client main.
        Parameters
        ----------
        server_ip: str
            Server address.
        port: int
            Server port.
        type: str
            Type of the main.
        name: str
            Name of the client.
        """

        self.name = name if name is not None else "Client"
        self.type = type
        self.address = f"{server_ip}:{port}"
        self.server_address = server_ip
        self.port = port
        self.client = self.client_sock(self.type)

    def _connect(self):
        self.client.connect((self.server_address, self.port))

        self.time_total = 0

    @staticmethod
    def client_sock(type: str,):
        """
        Create a client main.
        Parameters
        ----------
        type: str
            Type of the main.

        Returns
        -------
        client: socket.socket
            Client main.
        """
        if type == "TCP" or type is None:
            return socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif type == "UDP":
            return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            raise RuntimeError(f"Invalid type of connexion ({type}). Type must be 'TCP' or 'UDP'.")

    def _recv_all(self, buff_size: int = Buff_size):
        """
        Receive all data from the server.
        Parameters
        ----------
        buff_size: int
            Size of the buffer.

        Returns
        -------
        data: list
            List of data received.
        """

        msg_len = self.client.recv(4)

        # Unpack signed int in network standard (Big endian)
        msg_len = struct.unpack('!i', msg_len)[0]

        data = b''
        l = 0
        while l < msg_len:
            chunk = self.client.recv(buff_size)
            l += len(chunk)
            data += chunk

        # Unpack double in network standard (Big endian)
        frmt = '!' + str(int(msg_len)) + 'd'
        data = struct.unpack(frmt, data)
        self.time_total = time.time() - self.time_total
        return data

    def get_data(self, message, buff: int = Buff_size):
        """
        Get the data from server using the command.

        Parameters
        ----------
        message
        buff: int
            Size of the buffer.

        Returns
        -------
        data: dict
            Data from server.
        """
        self.time_total = time.time()
        if isinstance(message, Message):
            message = message.__dict__

        # Send text in byte form
        b_message = b''
        for i in range(np.shape(message)[0]):
            for j in range(np.shape(message)[1]):
                b_message += struct.pack('!B', message[i][j])

        # Send int in byte form
        # TODO: Change in order to correspond to an array
        # we chose unsigned int 8 (range from 0 to 511) so each x or y coordinates can be store on 1 byte
        b_size = struct.pack('!i', np.shape(message)[0] * np.shape(message)[1] * 1)

        # Send size of the message
        self.client.sendall(b_size)

        # Send message
        self.client.sendall(b_message)
        return self._recv_all(buff)


array_dictionary = {"FGx": [0, 0], "FGy": [0, 1], "FGz": [0, 2], "MGx": [2,0]}

if __name__ == '__main__':
    # Set program variables
    type_of_data = ["force_gauche"]


    # Run streaming data
    host_ip = 'localhost'
    host_port = 6000
    command = []
    # for i in range(15):
    #     for j in range(10):
    #         command.append([i, j])
    command = [array_dictionary["FGx"], array_dictionary["MGx"]]
    client = Client(host_ip, host_port, "TCP")
    client._connect()
    i = 1
    time_past = time.time()
    time_read_tcp_ip = 0

    while True:
        if i == 100:
            print(round(time.time() - time_past, 6), time_read_tcp_ip/100)
            time_past = time.time()
            i = 0
            time_read_tcp_ip = 0

        data = client.get_data(command)
        print(data)
        i += 1
        time_read_tcp_ip += client.time_total
        time.sleep(2)
