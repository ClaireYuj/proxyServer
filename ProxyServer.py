# -*- coding = utf-8 -*-
# @Time : 2021/10/21 16:58
# @Author:Yu
# @File: ProxyServer.py
# @Software: PyCharm

import socket
import re
import _thread
from multiprocessing import Process
from threading import Thread

TIMEOUT = 60
HOST = '127.0.0.1'
PORT = 8080


class Header:
    """
    To get the header info
    """
    def __init__(self,tcpSocket):
        """
        :param tcpSocket:
        """
        _header = b''
        try:
            while True:
                data = tcpSocket.recv(4096)
                _header = b"%s%s" % (_header, data)
                if _header.endswith(b'\r\n\r\n') or (not data):
                    break
        except:
            print("Error on initial")
        self.method = None
        self.header = _header
        self.header_list = _header.split(b'\r\n')
        self.requestStart = self.header_list[0]
        self.request_obj = None
        self.host = None
        self.port = None

    def getMethod(self):
        '''
        get the method--connect/get/post
        :return:
        '''
        if self.method is None:
            self.method = self.header[:self.header.index(b' ')]
        return self.method

    def getHost(self):
        '''
        get the host and port information
        :return:
        '''
        if self.host is None:
            method = self.getMethod()

            # get the host if the request is CONNECT https
            line = self.header_list[0].decode('utf-8')
            if method == b'CONNECT':
                host = line.split(' ')[1]
                if ':' in host:
                    host, port = host.split(':')
                else:
                    port = 443 #!! must be 443, then can be catched

            # get the host if the request is POST, PUT, GET, DELETE, HEAD http
            else:
                for otherLine in self.header_list:
                    if otherLine.startswith(b"Host:"):
                        host = otherLine.split(b' ')
                        if len(host) < 2:
                            continue
                        host = host[1].decode('utf-8')
                        break
                else:
                    host = line.split('/')[2]
                if ':' in host:
                    host, port = host.split(':')
                else:
                    port = 80 #the default port -- 80
            self.host = host
            self.port = int(port)
        return self.host, self.port

    def getData(self):
        '''
        return the header
        :return:
        '''
        return self.header

    def isConnect(self):
        '''
        determine is the protocal is https
        :return:
        '''
        if self.getMethod() == b'CONNECT':
            return True
        return False


def socketCommunication(sendSocket, recvSocket):
    '''
    A data communicatin between sendsocket and recv socket
    :param sendSocket:
    :param recvSocket:
    :return:
    '''
    try:
        while True:
            data = sendSocket.recv(1024)
            if not data:
                return
            recvSocket.sendall(data)
    except:
        pass

def handleRequest(client):
    '''
    handle the request of connected client for server
    :param client:
    :return:
    '''
    client.settimeout(TIMEOUT) # if it exceed the timoeout, socket will stop
    header = Header(client)
    if not header.getData():
        client.close()
        return
    print(*header.getHost(), header.getMethod())
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # try to connect
    try:
        server.connect(header.getHost())
        server.settimeout(TIMEOUT)

        # if the request is connect, the proxy will receive the data from client and send the data to server
        if header.isConnect():
            data = b"HTTP/1.0 200 Connection Established\r\n\r\n"
            print(data)
            client.sendall(data)
            proxy = Thread(target=socketCommunication, args=(client, server)) # client send message and server receive message
            proxy.start()

        # if the request is POST, PUT. GET, HEAD, DELETE
        else:
            # server send header information
            server.sendall(header.getData())
            print(header.getData())

        # the server send the data to client and client receive data from server
        socketCommunication(server, client)
    except Exception as e:
        client.close()
        server.close()
        print(e)

def startProxy(host, port):
    '''
    start proxy and use the multi-thread module
    :param host:
    :param port:
    :return:
    '''
    # create a proxy socket
    sevSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sevSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sevSocket.bind((host, port))
    try:
        sevSocket.listen(128)
        print("start listen to ", host, port)
    except socket.error:
        print("cannot listen to ", host)
        exit()
    print("Start Proxy")

    while True:
        clntSocket, ip = sevSocket.accept()
        print("connection established...")

        proxyThread = Thread(target=handleRequest, args=(clntSocket, ))
        proxyThread.start()
        #clientProcesss = Process(target=handleRequest, args=(clntSocket,))
        #clientProcesss.start()


if __name__ =="__main__":
    startProxy(HOST, PORT)