#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import socket
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XmlHandler(ContentHandler):

    def __init__(self):

        self.tags = {}

    def startElement(self, name, attrs):

        posibatts = ['username', 'passwd', 'ip', 'puerto', 'path']
        posibtags = ['account', 'uaserver', 'regproxy', 'rtpaudio',
                     'log', 'audio']
        for tag in posibtags:
            if name == tag:
                attdicc = {}
                for att in posibatts:
                    if str(attrs.get(str(att))) != 'None':
                        attdicc[str(att)] = attrs.get(str(att), "")
                self.tags[str(name)] = attdicc

    def get_tags(self):
        return self.tags


class SIPServerHandler(socketserver.DatagramRequestHandler):

    def handle(self):
        line = self.rfile.read().decode('utf-8').split()
        #print(line[0])
        my_methods = ['INVITE', 'ACK', 'BYE']
        if line[0] not in my_methods:
            self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')
        #elif len(line) = 3:
         #   self.wfile.write(b'SIP/2.0 400 Bad Request\r\n\r\n')
        else:
            if line[0] == 'INVITE':
                print('llegaaaaa:', line)
                templateSIP = ('SIP/2.0 100 Trying\r\n\r\n'
                               'SIP/2.0 180 Ring\r\n\r\n'
                               'SIP/2.0 200 OK\r\n\r\n')
                #self.wfile.write(bytes(templateSIP, 'utf-8'))
                templateSDP = "Content-Type: application/sdp\r\n\r\n" + "v=0\r\n" \
                    + "o=" + str(config_data['account']['username']) + \
                    " " + str(config_data['uaserver']['ip']) + \
                    "\r\ns=LaMesa\r\n" + "t=0\r\nm=audio " + \
                    str(config_data['rtpaudio']['puerto']) + " RTP\r\n\r\n"
                self.wfile.write(bytes(templateSIP + templateSDP, 'utf-8'))
            elif line[0] == 'ACK':
                print('hola')
                #os.system('./mp32rtp -i 127.0.0.1 -p 23032 < ' +
                 #         archivo_audio)
            elif line[0] == 'BYE':
                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')

if __name__ == "__main__":

    try:
        CONFIG = sys.argv[1]
    except:
        sys.exit("Usage: python3 uaserver.py config")

    parser = make_parser()
    xHandler = XmlHandler()
    parser.setContentHandler(xHandler)
    parser.parse(open(CONFIG))
    config_data = xHandler.get_tags()
    serv = socketserver.UDPServer(('', int(config_data['uaserver']['puerto'])), SIPServerHandler)
    print("Listening...\n")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("\nFinalizado servidor")
