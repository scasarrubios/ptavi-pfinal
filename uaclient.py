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
    ip = config_data['regproxy']['ip']
    port = int(config_data['regproxy']['puerto'])
    try:
        my_socket.connect((ip, port))
        event2log('Opening socket...', ip, port, 'f')
        if METHOD == 'REGISTER':
            user = str(config_data['account']['username'])
            line = METHOD + ' sip:' + user + \
                ':' + str(config_data['uaserver']['puerto']) + \
                ' SIP/2.0\r\nExpires: ' + OPTION
            print(">>Enviando:\n" + line)
            my_socket.send(bytes(line, 'utf-8') + b'\r\n\r\n')
            event2log(line, ip, port, 's')
            answer = my_socket.recv(1024).decode('utf-8')
            event2log(answer, ip, port, 'r')

            # Realizamos la autenticación
            if answer.split()[1] == '401':
                nonce = answer.split('"')[1]
                psswd = config_data['account']['passwd']
                response = hashlib.sha1()
                response.update(bytes(psswd, 'utf-8'))
                response.update(bytes(nonce, 'utf-8'))
                response = response.hexdigest()
                authorization = 'Authorization: Digest response="' + response
                line += '\r\n' + authorization
                my_socket.send(bytes(line, 'utf-8') + b'"\r\n\r\n')
                event2log(line, ip, port, 's')
                answer = my_socket.recv(1024).decode('utf-8')
                event2log(answer, ip, port, 'r')
                print('>>Recibido:\n' + answer)
        elif METHOD == 'INVITE':
            templateSDP = "Content-Type: application/sdp\r\n\r\n" + "v=0\r\n" \
                        + "o=" + str(config_data['account']['username']) + \
                        " " + str(config_data['uaserver']['ip']) + \
                        "\r\ns=LaMesa\r\n" + "t=0\r\nm=audio " + \
                        str(config_data['rtpaudio']['puerto']) + " RTP\r\n\r\n"
            line = METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n' + templateSDP
            print('>>Enviando:\n' + line)
            my_socket.send(bytes(line, 'utf-8'))
            event2log(line, ip, port, 's')
            answer = my_socket.recv(1024).decode('utf-8')
            event2log(answer, ip, port, 'r')
            print('>>Recibido:\n' + answer)
            sliced = answer.split()
            if '200' in answer:
                rtp_ip = sliced[13]
                rtp_port = sliced[17]
                line = 'ACK sip:' + OPTION + ' SIP/2.0\r\n'
                my_socket.send(bytes(line, 'utf-8'))
                event2log(line, ip, port, 's')
                cmd = 'cvlc rtp://@' + config_data['uaserver']['ip'] + \
                      ':' + config_data['rtpaudio']['puerto']
                os.system(cmd)
                event2log('audio', rtp_ip, rtp_port, 'r')
                os.system("./mp32rtp -i " + rtp_ip + " -p " +
                          rtp_port + " < " + config_data['audio']['path'])
                event2log(config_data['audio']['path'], rtp_ip,
                          rtp_port, 's')
        elif METHOD == 'BYE':
            line = 'BYE sip:' + OPTION + ' SIP/2.0\r\n'
            print("Enviando:\n" + line)
            my_socket.send(bytes(line, 'utf-8'))
            event2log(line, ip, port, 's')
            answer = my_socket.recv(1024).decode('utf-8')
            event2log(answer, ip, port, 'r')
            print('>>Recibido:\n' + answer)
        print("Cerrando socket")
        event2log('Closing socket...', ip, port, 'f')
        my_socket.close()
    except ConnectionRefusedError:
        event = 'Error: No server listening at ' + ip + ' port ' + str(port)
        event2log(event, ip, port, 'f')
        sys.exit(event)
