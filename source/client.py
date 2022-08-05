import socket
import struct
import time
import numpy as np

Buff_size = 32767

# Choose the behaviour of the program :
#  - "SLOW" : send a data request for 2 values each 2 seconds. Use for debug and verify is the data received correspond
#             to the data generated.
#  - "NORMAL" : send a data request for all 150 values each 33ms. Correspond to the normal use of the program.
#  - "FAST" : send a data request for all 150 values as fast possible. Use for test of speed.
# The behaviour is of most use when the data generation in LabView is done on the same oder of magnitude than data # request.
MODE_OF_EXECUTION = "NORMAL"


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
        self.time_total_request_reception = 0

    @staticmethod
    def client_sock(type: str, ):
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

    def connect(self):
        self.client.connect((self.server_address, self.port))

        self.time_total_request_reception = 0

    def _recv_all(self, buff_size: int = Buff_size):
        """
        Receive all data from the server and process it to return a tuple.
        Parameters
        ----------
        buff_size: int
            Size of the buffer.

        Returns
        -------
        data: tuple
            Tuple of data received.
        """

        msg_len = self.client.recv(4)

        # Unpack signed int in network standard (Big endian)
        msg_len = struct.unpack('!i', msg_len)[0]

        data = b''
        length_read = 0
        while length_read < msg_len:
            chunk = self.client.recv(buff_size)
            length_read += len(chunk)
            data += chunk

        # Unpack double in network standard (Big endian)
        frmt = '!' + str(int(msg_len)) + 'd'
        data = struct.unpack(frmt, data)
        self.time_total_request_reception = time.time() - self.time_total_request_reception
        return data

    def _send_message(self, message: list):
        """
        Convert message to bytes and send it.
        Parameters
        ----------
        message: list
            List that will be sent
        """

        # Convert message in bytes type
        b_message = b''
        for i in range(np.shape(message)[0]):
            for j in range(np.shape(message)[1]):
                # we chose unsigned char 8 (range from 0 to 511) so each x or y coordinates can be store on 1 byte
                b_message += struct.pack('!B', message[i][j])

        # Convert int in bytes type
        # The length is stored on an int by convention.
        b_size = struct.pack('!i', np.shape(message)[0] * np.shape(message)[1] * 1)

        # Send size of the message
        self.client.sendall(b_size)

        # Send message
        self.client.sendall(b_message)

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
        self.time_total_request_reception = time.time()
        self._send_message(message)
        return self._recv_all(buff)


# Correspondence table between name of the value and their coordinates
array_dictionary = {"FGx": [0, 0], "FGy": [0, 1], "FGz": [0, 2], "FDx": [0, 3], "FDy": [0, 4], "FDz": [0, 5],
                    "MGx": [2, 0], "MGy": [2, 1], "MGz": [2, 2], "MDx": [2, 3], "MDy": [2, 4], "MDz": [2, 5],
                    "TG": [4, 0], "TD": [4, 1],
                    "AG": [6, 0], "AD": [6, 1]}

# Main execution
if __name__ == '__main__':
    # index give the number of request made, is reset to 1 at 100
    index = 1
    # time_read_tcp_ip is used to measure the average time of the time needed to send a command and received the data
    time_read_tcp_ip = 0

    # Run streaming data
    host_ip = 'localhost'
    host_port = 6000

    # Set the command containing the data request that will be sent to LabView
    command = []
    if MODE_OF_EXECUTION == "SLOW":
        command = [array_dictionary["FGx"], array_dictionary["MGx"]]

    elif (MODE_OF_EXECUTION == "NORMAL") | (MODE_OF_EXECUTION == "FAST"):
        for i in range(15):
            for j in range(10):
                command.append([i, j])

    client = Client(host_ip, host_port, "TCP")
    client.connect()

    time_past = time.time()

    while True:
        if index == 100:
            print(round(time.time() - time_past, 6), time_read_tcp_ip / 100)
            time_past = time.time()
            index = 0
            time_read_tcp_ip = 0

        data = client.get_data(command)

        index += 1
        time_read_tcp_ip += client.time_total_request_reception

        if MODE_OF_EXECUTION == "SLOW":
            print(data)
            time.sleep(2 - client.time_total_request_reception)
        elif MODE_OF_EXECUTION == "NORMAL":
            if 0.033 > client.time_total_request_reception:
                time.sleep(0.033 - client.time_total_request_reception)
