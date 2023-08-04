import socket
import select
import queue
import threading
import time
import struct
import warnings

import serial


class UDPsend(object):
    """
    Object for sending data through UDP
    """

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET,  # Internet
                                  socket.SOCK_DGRAM)  # UDP

    def send(self, msg, addr=('192.168.42.1', 12354)):
        """
        :param msg: message to send
        :param addr: tuple of length 2, (ip address, port number)
        :return:
        """
        self.sock.sendto(msg, addr)

    def closeSocket(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def reOpenSocket(self):
        self.sock = socket.socket(socket.AF_INET,  # Internet
                                  socket.SOCK_DGRAM)  # UDP


class receiveProto(object):

    def __init__(self, console, parseFunction=None, useThread=False, maxQSize=4, useQ=False,
                 parseArgs=(), **kwargs):
        """
        :param console: rtgui console
        :type console: ConsoleFrame
        :param parseFunction: Function used to parse the data
        :type parseFunction: Function
        :param parseArgs: positional arguments for parse function
        :param parseKwargs: keyword arguments for parse function
        """

        self.data = ""
        self.dataRead = False
        self.t1 = None
        self.t2 = None
        self.rec = True
        self.rec1 = None
        self.q_var = None
        self.console = console
        self.useThread = useThread
        self.q = queue.Queue()
        self.useQ = useQ
        self.maxQSize = maxQSize
        self._parseFunction = parseFunction
        self._parseArgs = parseArgs
        self._parseKwargs = kwargs

    def _parseData(self, unparsed):
        """
        Parses network data and process it accordingly
        :param unparsed:
        :return:
        """
        # print(unparsed)
        if self._parseFunction:
            self._parseFunction(unparsed, *self._parseArgs, **self._parseKwargs)
        else:
            self.console.set(unparsed.decode("utf-8", "ignore"))

    def _comReceive(self):
        warnings.warn("_comReceive function not declared")
        return None

    def __receiveData(self, e):
        """
        Main function for receiving, this is usually on a different thread
        :param e:
        :return:
        """
        while e.is_set():
            data = self._comReceive()
            if not data:
                continue
            if self.useQ:
                self.q.put(data)
            else:
                if self.useThread:
                    th = threading.Thread(target=self._parseData, args=(data,))
                    th.start()
                    th.join()
                else:
                    self._parseData(data)
        print("Thread ended")

    def parseQueue(self, e):
        while e.is_set():
            for j in range(self.q.qsize()):
                data = self.q.get()
                self._parseData(data)
                self.q.task_done()
                if j > self.maxQSize:
                    # flush the queue
                    print('Flushing Q')
                    with self.q.mutex:
                        self.q.queue.clear()

    def startThread(self):
        """
        Starts the receiving thread
        :return:
        """
        self.rec = True
        # self.reOpenSocket()
        self.rec1 = threading.Event()
        self.rec1.set()
        self.t1 = threading.Thread(target=self.__receiveData, args=[self.rec1], daemon=True)
        self.t1.start()
        # start queue thread
        if self.useQ:
            self.q_var = threading.Event()
            self.q_var.set()
            self.t2 = threading.Thread(target=self.parseQueue, args=[self.q_var], daemon=True)
            self.t2.start()

    def stopThread(self):
        self.rec = False
        self.rec1.clear()
        if self.useQ:
            self.q_var.clear()
        time.sleep(0.5)


class serialReceive(receiveProto):
    def __init__(self, console, serialConnection, **kwargs):
        """
        Serial communication
        :param console: rtgui console
        :type console: ConsoleFrame
        :param serialConnection: serial object to use for receiving
        :type serialConnection: serial.Serial
        """
        super(serialReceive, self).__init__(console, **kwargs)
        self._serial = serialConnection

    def _comReceive(self):
        data = self._serial.readline()
        return data


class UDPreceiveProto(receiveProto):

    def __init__(self, console, portN=12345, bufferedData=None, **kwargs):
        """
        :param console: rtgui console
        :type console: ConsoleFrame
        :param portN: port number for receiving
        """
        super(UDPreceiveProto, self).__init__(console, **kwargs)
        self.portN = portN
        if bufferedData is None:
            self.bufferedData = []
        else:
            self.bufferedData = bufferedData

    def reOpenSocket(self):
        self.sock = socket.socket(socket.AF_INET,  # Internet
                                  socket.SOCK_DGRAM)  # UDP
        self.sock.bind(("", self.portN))

    def _comReceive(self):
        """
        Main function for receiving, this is usually on a different thread
        :return: data from the UDP port
        """
        readable = [self.sock]
        # q = queue.Queue()
        while len(readable) > 0:
            readable, _, _, = select.select([self.sock], [], [], 1. / 500.)
            if self.sock in readable:
                data, addr = self.sock.recvfrom(1024)
                return data

    def clearBuffer(self):
        self.bufferedData = []

    def stopThread(self):
        self.rec = False
        self.rec1.clear()
        if self.useQ:
            self.q_var.clear()
        time.sleep(0.5)
        self.closeSocket()

    def closeSocket(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
