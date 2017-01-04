#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa servidor proxy SIP-SDP
"""

import socketserver
import socket
import sys
import os
import time
import json
import hashlib
import random
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class ProxyXmlHandler(ContentHandler):

    def __init__(self):

        self.tags = {}

    def startElement(self, name, attrs):

        posibatts = ['name', 'passwdpath', 'ip', 'puerto', 'path']
        posibtags = ['server', 'database', 'log']
        for tag in posibtags:
            if name == tag:
                attdicc = {}
                for att in posibatts:
                    if str(attrs.get(str(att))) != 'None':
                        attdicc[str(att)] = attrs.get(str(att), "")
                self.tags[str(name)] = attdicc

    def get_tags(self):
        return self.tags

def event2log(event, ip, port, flag):
    now = time.strftime('%Y%m%d%H%M%S ', time.localtime(time.time()))
    if not os.path.isfile(config_data['log']['path']):
        log_file = open(config_data['log']['path'], 'a')
        log_file.write(now + 'Starting...\n')
        log_file.close()
    log_file = open(config_data['log']['path'], 'a')
    if flag == 'r':
        flag = 'Received from '
    elif flag == 's':
        flag = 'Sent to '
    event = event.replace('\r\n', ' ')
    event = event.replace('\r\n ', ' ')
    log_file.write(now + flag + ip + ':' + str(port) + ': ' + event + '\n')
    log_file.close()

class ProxyHandler(socketserver.DatagramRequestHandler):
    """
    Register server class
    """
    clients = {}
    user = []
    dest = []
    no_file = False
    nonce = str(random.randint(000000000000000000000,
                               99999999999999999999))

    def caducity_check(self):
        """
        Compara la fecha de caducidad de los clientes del diccionario,
        y si han caducado los añade a la lista caduced para borrarlos
        """
        caduced = []
        for client in self.clients:
            now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            if now >= self.clients[client][2]:
                caduced.append(client)
        for client in caduced:
            del self.clients[client]
    
    def get_psswd(self, user):
        try:
            file = open(str(config_data['database']['passwdpath']), "r")
            lines = file.readlines()
            password = ""
            for line in lines:
                user_file = line.split()[0].split(":")[0]
                if user == user_file:
                    password = line.split()[0].split(":")[1]
        except FileNotFoundError:
            os.exit('ERROR: passwords file not found')
        return password

    def register_check(self, user):
        """
        Comprueba si la petición recibida es de un usuario registrado
        """
        registered = False
        for client in self.clients:
            if user == client:
                registered = True
        return registered

    def register2json(self):
        """
        Imprime el diccionario de clientes en un fichero json
        """
        if self.no_file:
            fichero = open(str(config_data['database']['path']), 'w')
        else:
            fichero = open(str(config_data['database']['path']), 'r+')
        json.dump(self.clients, fichero, indent='\t')

    def json2register(self):
        """
        Comprueba si hay un fichero de json y si lo hay importa los clientes,
        si no cambia el valor de no_file a True
        """
        try:
            with open(str(config_data['database']['path'])) as data_file:
                self.clients = json.load(data_file)
        except:
            self.no_file = True

    def handle(self):
        self.json2register()
        literal = self.rfile.read().decode('utf-8')
        line = literal.split()
        print(line)
        print('PRIMERA')
        print(self.clients)
        ip = self.client_address[0]
        port = self.client_address[1]
        self.caducity_check()
        self.register2json()
        if line[0] == 'REGISTER' and len(line) < 6:  # Si falta autenticación
            to_send = 'SIP/2.0 401 Unauthorized\r\n' + \
                      'WWW Authenticate: Digest nonce="' + \
                      self.nonce + '"\r\n\r\n'
            self.wfile.write(bytes(to_send, 'utf-8'))
            event2log(literal, ip, port, 'r')
            event2log(to_send, ip, port, 's')
        elif line[0] == 'REGISTER' and len(line) >= 6:  # Autenticación recibida
            user = line[1].split(':')[1]
            authenticate = hashlib.sha1()
            authenticate.update(bytes(self.get_psswd(user), 'utf-8'))
            authenticate.update(bytes(self.nonce, 'utf-8'))
            authenticate = authenticate.hexdigest()
            if authenticate == line[7].split('"')[1]:
                print("PERFE")
                data = []
                data.append(self.client_address[0])  # Añade la IP
                data.append(line[1].split(':')[2])  # Añade el puerto
                if line[3] == 'Expires:' and line[4] == '0':
                    del self.clients[user]
                elif line[3] == 'Expires:' and line[4] != '0':
                    caduc_time = time.localtime(time.time()+int(line[4]))
                    data.append(time.strftime('%Y-%m-%d %H:%M:%S', caduc_time))
                    self.clients[user] = data
                to_send = "SIP/2.0 200 OK\r\n\r\n"
                self.wfile.write(bytes(to_send, 'utf-8'))
                event2log(literal, ip, port, 'r')
                event2log(to_send, ip, port, 's')
                self.register2json()
                print('SEGUNDA')
                print(self.clients)
        elif line[0] == 'INVITE':
            self.user.append(line[6][2:])
            self.dest.append(line[1].split(':')[1])
            registered = self.register_check(self.user[0])
            user_found = self.register_check(self.dest[0])
            event2log(literal, ip, port, 'r')
            if registered and user_found:
                ip_sock = self.clients[self.dest[0]][0]
                port_sock = int(self.clients[self.dest[0]][1])
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) \
                as my_socket:  # Abrimos un socket con el cliente solicitado
                    my_socket.connect((ip_sock, port_sock))
                    my_socket.send(bytes(literal, 'utf-8'))
                    event2log(literal, ip_sock, port_sock, 's')
                    answer = my_socket.recv(1024).decode('utf-8')
                    event2log(answer, ip_sock, port_sock, 'r')
                    self.wfile.write(bytes(answer, 'utf-8'))
                    event2log(answer, ip, port, 's')
            elif not registered:
                to_send = 'SIP/2.0 401 Unauthorized\r\n\r\n'
                self.wfile.write(bytes(to_send, 'utf-8'))
                event2log(to_send, ip, port, 's')
            elif not user_found:
                to_send = 'SIP/2.0 404 User Not Found\r\n\r\n'
                self.wfile.write(bytes(to_send, 'utf-8'))
                event2log(to_send, ip, port, 's')
        elif line[0] == 'ACK':
            registered = self.register_check(self.user[0])
            event2log(literal, ip, port, 'r')
            if registered:
                ip_sock = self.clients[self.dest[0]][0]
                port_sock = int(self.clients[self.dest[0]][1])
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) \
                as my_socket:  # Abrimos un socket con el cliente solicitado
                    my_socket.connect((ip_sock, port_sock))
                    my_socket.send(bytes(literal, 'utf-8'))
                    event2log(literal, ip_sock, port_sock, 's')
                self.user = []
                self.dest = []
        elif line[0] == 'BYE':
            dest = line[1][4:]
            user_found = self.register_check(dest)
            event2log(literal, ip, port, 'r')
            if user_found:
                ip_sock = self.clients[self.dest[0]][0]
                port_sock = int(self.clients[self.dest[0]][1])
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) \
                as my_socket:  # Abrimos un socket con el cliente solicitado
                    my_socket.connect((ip_sock, port_sock))
                    my_socket.send(bytes(literal, 'utf-8'))
                    event2log(literal, ip_sock, port_sock, 's')
                    answer = my_socket.recv(1024).decode('utf-8')
                    event2log(answer, ip_sock, port_sock, 'r')
                    self.wfile.write(bytes(answer, 'utf-8'))
                    event2log(answer, ip, port, 's')
            elif not user_found:
                to_send = 'SIP/2.0 404 User Not Found\r\n\r\n'
                self.wfile.write(bytes(to_send, 'utf-8'))
                event2log(to_send, ip, port, 's')
        elif line[0] not in ['INVITE', 'ACK', 'BYE']:
            to_send = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
            self.wfile.write(bytes(to_send, 'utf-8'))
            event2log(to_send, ip, port, 's')
        else:
            to_send = 'SIP/2.0 400 Bad Request\r\n\r\n'
            self.wfile.write(bytes(to_send, 'utf-8'))
            event2log(to_send, ip, port, 's')
if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except:
        sys.exit("Usage: python3 proxy_registrar.py config")

    parser = make_parser()
    pxHandler = ProxyXmlHandler()
    parser.setContentHandler(pxHandler)
    parser.parse(open(CONFIG))
    config_data = pxHandler.get_tags()
    serv = socketserver.UDPServer(('', int(config_data['server']['puerto'])),
                                  ProxyHandler)
    print('>> ' + config_data['server']['name'] + ' listening...\n')
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("\nFinalizado servidor")
        now = time.strftime('%Y%m%d%H%M%S ', time.localtime(time.time()))
        log_file = open(config_data['log']['path'], 'a')
        log_file.write(now + 'Finishing...\n')
        log_file.close() 
