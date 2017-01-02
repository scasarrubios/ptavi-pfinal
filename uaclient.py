#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import hashlib
import time
import os
from uaserver import XmlHandler
from xml.sax import make_parser

if __name__ == "__main__":

    try:
        CONFIG = sys.argv[1]
        METHOD = sys.argv[2].upper()
        OPTION = sys.argv[3]
    except:
        sys.exit("Usage: python3 uaclient.py config method option")

    parser = make_parser()
    xHandler = XmlHandler()
    parser.setContentHandler(xHandler)
    parser.parse(open(CONFIG))
    config_data = xHandler.get_tags()

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((config_data['regproxy']['ip'],
                       int(config_data['regproxy']['puerto'])))
    if METHOD == 'REGISTER':
        line = METHOD + ' sip:' + str(config_data['account']['username']) + ':' + \
         str(config_data['uaserver']['puerto']) + ' SIP/2.0 Expires: ' + OPTION
    print("Enviando: " + line)
    my_socket.send(bytes(line, 'utf-8') + b'\r\n\r\n')
    answer = my_socket.recv(1024).decode('utf-8')
    if answer.split()[1] == '401':
        nonce = answer.split('"')[1]
        response = hashlib.sha1()
        response.update(bytes(config_data['account']['passwd'],'utf-8'))
        response.update(bytes(nonce,'utf-8'))
        response = response.hexdigest()
        authorization = 'Authorization: Digest response="' + response \
                        + '"\r\n\r\n'
        line += '\r\n' + authorization
        my_socket.send(bytes(line, 'utf-8'))
        answer = my_socket.recv(1024).decode('utf-8')
    print("Fin.")
