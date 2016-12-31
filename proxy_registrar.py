#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa servidor proxy SIP-SDP
"""

import socketserver
import sys
import time
import json
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

def get_psswd(user):
    try:
        file = open("passwords", "r")
        lines = file.readlines()
        password = ""
        for line in lines:
            user_file = line.split()[0].split(":")[1]
            if user == user_file:
                password = line.split()[1].split(":")[1]
    except FileNotFoundError:
        os.exit('ERROR: passwords file not found')
    return password

class ProxyHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    clients = {}
    no_file = False

    def caducity_check(self, line):
        """
        Compara la fecha de caducidad de los clientes del diccionario,
        y si han caducado los añade a la lista caduced para borrarlos
        """
        caduced = []
        for client in self.clients:
            now = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
            if now >= self.clients[client][1] and line[4] != 0:
                caduced.append(client)
        for client in caduced:
            del self.clients[client]

    def register2json(self):
        """
        Imprime el diccionario de clientes en un fichero json
        """
        if self.no_file:
            fichero = open('registered.json', 'w')
        else:
            fichero = open('registered.json', 'r+')
        json.dump(self.clients, fichero, indent='\t')

    def json2register(self):
        """
        Comprueba si hay un fichero de json y si lo hay importa los clientes,
        si no cambia el valor de no_file a True
        """
        try:
            with open('registered.json') as data_file:
                self.clients = json.load(data_file)
        except:
            self.no_file = True

    def handle(self):
        self.json2register()
        line = self.rfile.read().decode('utf-8').split()
        self.caducity_check(line)
        if line[0] == 'REGISTER':
            data = []
            
            data.append(self.client_address[0])
            data.append(line[1].split(':')[2])
            self.clients[line[1].split(':')[1]] = data
            if line[3] == 'Expires:' and line[4] == '0':
                del self.clients[line[1].split(':')[1]]
            elif line[3] == 'Expires:' and line[4] != '0':
                caduc_time = time.gmtime(time.time()+int(line[4]))
                data.append(time.strftime('%Y-%m-%d %H:%M:%S', caduc_time))
                self.clients[line[1].split(':')[1]] = data
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            self.register2json()
            
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
    serv = socketserver.UDPServer(('', int(config_data['server']['puerto'])), ProxyHandler)
    print('>> ' + config_data['server']['name'] + ' listening...\n')
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("\nFinalizado servidor")
