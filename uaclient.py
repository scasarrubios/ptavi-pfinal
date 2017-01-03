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
    #my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((config_data['regproxy']['ip'],
                       int(config_data['regproxy']['puerto'])))
    if METHOD == 'REGISTER':
        line = METHOD + ' sip:' + str(config_data['account']['username']) + \
            ':' + str(config_data['uaserver']['puerto']) + \
            ' SIP/2.0 Expires: ' + OPTION
        print("Enviando: " + line)
        my_socket.send(bytes(line, 'utf-8') + b'\r\n\r\n')
        answer = my_socket.recv(1024).decode('utf-8')

        # Realizamos la autenticación
        if answer.split()[1] == '401':
            nonce = answer.split('"')[1]
            response = hashlib.sha1()
            response.update(bytes(config_data['account']['passwd'], 'utf-8'))
            response.update(bytes(nonce, 'utf-8'))
            response = response.hexdigest()
            authorization = 'Authorization: Digest response="' + response
            line += '\r\n' + authorization
            my_socket.send(bytes(line, 'utf-8') + b'\r\n\r\n')
            answer = my_socket.recv(1024).decode('utf-8')

    elif METHOD == 'INVITE':
        templateSDP = "Content-Type: application/sdp\r\n\r\n" + "v=0\r\n" \
                    + "o=" + str(config_data['account']['username']) + \
                    " " + str(config_data['uaserver']['ip']) + \
                    "\r\ns=LaMesa\r\n" + "t=0\r\nm=audio " + \
                    str(config_data['rtpaudio']['puerto']) + " RTP\r\n\r\n"
        line = METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n' + templateSDP
        my_socket.send(bytes(line, 'utf-8'))
        answer = my_socket.recv(1024).decode('utf-8')
        if '200' in answer:
            line = 'ACK sip:' + OPTION + ' SIP/2.0\r\n'
            my_socket.send(bytes(line, 'utf-8'))
    print("Fin.")
