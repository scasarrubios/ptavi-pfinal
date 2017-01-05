#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import socket
import sys
import os
import time
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


def event2log(event, ip, port, flag):
    now = time.strftime('%Y%m%d%H%M%S ', time.localtime(time.time()))
    log_file = open(config_data['log']['path'], 'a')
    if flag == 'r':
        flag = 'Received from '
    elif flag == 's':
        flag = 'Sent to '
    if flag == 'Received from ' or flag == 'Sent to ':
        event = event.replace('\r\n', ' ')
        event = event.replace('\r\n ', ' ')
        log_file.write(now + flag + ip + ':' + str(port) + ': ' + event + '\n')
        log_file.close()
    else:
        log_file.write(now + event + '\n')
        log_file.close()


class SIPServerHandler(socketserver.DatagramRequestHandler):

    rtp_data = []

    def handle(self):
        literal = self.rfile.read().decode('utf-8')
        line = literal.split()
        ip = self.client_address[0]
        port = self.client_address[1]
        event2log(literal, ip, port, 'r')
        print('>>Recibido:\n' + literal)
        if line[0] == 'INVITE':
            self.rtp_data.append(line[6][2:])
            self.rtp_data.append(line[7])  # Guardamos la info de RTP
            self.rtp_data.append(line[11])  # para el envío
            templateSIP = ('SIP/2.0 100 Trying\r\n\r\n'
                           'SIP/2.0 180 Ring\r\n\r\n'
                           'SIP/2.0 200 OK\r\n\r\n')
            templateSDP = "Content-Type: application/sdp\r\n\r\n" + \
                "v=0\r\n" + "o=" + str(config_data['account']['username']) + \
                " " + str(config_data['uaserver']['ip']) + \
                "\r\ns=LaMesa\r\n" + "t=0\r\nm=audio " + \
                str(config_data['rtpaudio']['puerto']) + " RTP\r\n\r\n"
            self.wfile.write(bytes(templateSIP + templateSDP, 'utf-8'))
            event2log(templateSIP + templateSDP, ip, port, 's')
        elif line[0] == 'ACK':
            event2log(literal, ip, port, 'r')
            os.system("./mp32rtp -i " + self.rtp_data[1] + " -p " +
                      self.rtp_data[2] + " < " +
                      config_data['audio']['path'])
            event2log(config_data['audio']['path'], self.rtp_data[1],
                      self.rtp_data[2], 's')
            cmd = 'cvlc rtp://@' + config_data['uaserver']['ip'] + \
                  ':' + config_data['rtpaudio']['puerto']
            os.system(cmd)
            event2log('audio', self.rtp_data[1], self.rtp_data[2], 'r')
            self.rtp_data = []
        elif line[0] == 'BYE':
            to_send = 'SIP/2.0 200 OK\r\n\r\n'
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
        sys.exit("Usage: python3 uaserver.py config")

    parser = make_parser()
    xHandler = XmlHandler()
    parser.setContentHandler(xHandler)
    parser.parse(open(CONFIG))
    config_data = xHandler.get_tags()
    port = int(config_data['uaserver']['puerto'])
    serv = socketserver.UDPServer(('', port), SIPServerHandler)
    event2log('Starting UAServer...', '1', 1, 'f')
    print("Listening...\n")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("\nFinalizado servidor")
        event2log('Finishing UAServer...', '1', 1, 'f')
