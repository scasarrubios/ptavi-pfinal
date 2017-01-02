#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa servidor proxy SIP-SDP
"""

import socketserver
import sys
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

def get_psswd(user):
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

class ProxyHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    clients = {}
    no_file = False
    nonce = str(random.randint(000000000000000000000, 
                               99999999999999999999))

    def caducity_check(self, line):
        """
        Compara la fecha de caducidad de los clientes del diccionario,
        y si han caducado los añade a la lista caduced para borrarlos
        """
        caduced = []
        for client in self.clients:
            now = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
            if now >= self.clients[client][2]:
                caduced.append(client)
        for client in caduced:
            del self.clients[client]

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
        line = self.rfile.read().decode('utf-8').split()
        user = line[1].split(':')[1]
        print(line)
        passwd = get_psswd(user)
        print(passwd)
        print('PRIMERA')
        print(self.clients)
        self.caducity_check(line)
        if line[0] == 'REGISTER' and len(line) < 6:
            to_send = 'SIP/2.0 401 Unauthorized\r\n' + \
                      'WWW Authenticate: Digest nonce="' + \
                      self.nonce + '"\r\n\r\n'
            self.wfile.write(bytes(to_send, 'utf-8'))
        if line[0] == 'REGISTER' and len(line) >= 6:
            authenticate = hashlib.sha1()
            authenticate.update(bytes(passwd,'utf-8'))
            authenticate.update(bytes(self.nonce,'utf-8'))
            authenticate = authenticate.hexdigest()
            if authenticate == line[7].split('"')[1]:
                print("PERFE")
                data = []
                data.append(self.client_address[0]) #añade la IP
                data.append(line[1].split(':')[2]) #añade el puerto
                self.clients[user] = data
                if line[3] == 'Expires:' and line[4] == '0':
                    del self.clients[user] 
                elif line[3] == 'Expires:' and line[4] != '0':
                    caduc_time = time.gmtime(time.time()+int(line[4]))
                    data.append(time.strftime('%Y-%m-%d %H:%M:%S', caduc_time))
                    self.clients[user] = data
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                self.register2json()
                print('SEGUNDA')
                print(self.clients)
            
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