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
import hashlib



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

if __name__ == "__main__":
   
    parser = make_parser()
    xHandler = XmlHandler()
    parser.setContentHandler(xHandler)
    parser.parse(open('ua1.xml'))
    config_data = xHandler.get_tags()
    print(config_data['account']['username'])
    
