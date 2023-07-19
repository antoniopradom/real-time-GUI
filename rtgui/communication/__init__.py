import socket
import select
import queue
import threading
import time
import struct


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


class UDPreceiveProto(object):

    def __init__(self, console, portN=12345, bufferedData=None, useThread=False, maxQSize=4):
        """
        :param console: tkInter text to be used as "console"
        :param portN: port number for receiving
        """

        self.data = ""
        self.dataRead = False
        self.t1 = None
        self.t2 = None
        self.rec = True
        self.rec1 = None
        self.console = console
        self.portN = portN
        self.useThread = useThread
        self.q = queue.Queue()
        self.useQ = True
        self.maxQSize = maxQSize
        if bufferedData is None:
            self.bufferedData = []
        else:
            self.bufferedData = bufferedData

    def reOpenSocket(self):
        self.sock = socket.socket(socket.AF_INET,  # Internet
                                  socket.SOCK_DGRAM)  # UDP
        self.sock.bind(("", self.portN))

    def _parseData(self, unparsed, qSize=None):
        """
        Parses network data and process it accordingly
        :param unparsed:
        :return:
        """
        # print(unparsed)
        self.console.set(unparsed.decode("utf-8", "ignore"))

    def __receiveData(self, e):
        """
        Main function for receiving, this is usually on a different thread
        :param e:
        :return:
        """
        while e.is_set():
            readable = [self.sock]
            # q = queue.Queue()
            while len(readable) > 0:
                readable, _, _, = select.select([self.sock], [], [], 1. / 500.)
                if self.sock in readable:
                    data, addr = self.sock.recvfrom(1024)
                    if self.useQ:
                        self.q.put(data)
                    else:
                        th = threading.Thread(target=self._parseData, args=(data, 1))
                        th.start()
                        th.join()
        print("Thread ended")

    def parseQueue(self):
        for j in range(self.q.qsize()):
            data = self.q.get()
            self._parseData(data, qSize=self.q.qsize())
            self.q.task_done()
            if j > self.maxQSize:
                # flush the queue
                print('Flushing Q')
                with self.q.mutex:
                    self.q.queue.clear()

    def clearBuffer(self):
        self.bufferedData = []

    def startThread(self):
        """
        Starts the receiving thread
        :return:
        """
        self.rec = True
        self.reOpenSocket()
        self.rec1 = threading.Event()
        self.rec1.set()
        self.t1 = threading.Thread(target=self.__receiveData, args=[self.rec1])
        self.t1.daemon = True
        self.t1.start()

    def stopThread(self):
        self.rec = False
        self.rec1.clear()
        time.sleep(0.5)
        self.closeSocket()

    def closeSocket(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


