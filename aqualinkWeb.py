#!/usr/bin/python
# coding=utf-8

import threading
import socket
import select

from debugUtils import *
from webUtils import *
from aqualinkConf import *

########################################################################################################
# web UI
########################################################################################################
class WebUI:
    # constructor
    def __init__(self, theName, theState, thePool):
        self.name = theName
        self.state = theState
        self.pool = thePool
        webThread = WebThread("Web:     ", theState, httpPort, thePool)
        webThread.start()

########################################################################################################
# web server thread
########################################################################################################
class WebThread(threading.Thread):
    # constructor
    def __init__(self, theName, state, httpPort, thePool):
        threading.Thread.__init__(self, target=self.webServer)
        self.name = theName
        self.state = state
        self.httpPort = httpPort
        self.pool = thePool

    # web server loop
    def webServer(self):
        if debug: log(self.name, "starting web thread")
        # open the socket and listen for connections
        if debug: log(self.name, "opening port", self.httpPort)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#        try:
        self.socket.bind(("", self.httpPort))
        if debug: log(self.name, "waiting for connections")
        self.socket.listen(5)
        # handle connections
        try:
            while self.state.running:
                inputs, outputs, excepts = select.select([self.socket], [], [], 1)
                if self.socket in inputs:
                    (ns, addr) = self.socket.accept()
                    name = addr[0]+":"+str(addr[1])+" -"
                    if debug: log(self.name, name, "connected")
                    self.handleRequest(ns, addr)
        finally:
            self.socket.close()
#        except:
#            if debug: log(self.name, "unable to open port", httpPort)
        if debug: log(self.name, "terminating web thread")

    # parse and handle a request            
    def handleRequest(self, ns, addr):
        # got a request, parse it
        request = ns.recv(8192)
        if not request: return
        if debugHttp: log(self.name, "request:\n", request)
        (verb, path, params) = parseRequest(request)
        if debugHttp: log(self.name, "parsed verb:", verb, "path:", path, "params:", params)
        try:
            if verb == "GET":
                if path == "/":
                    html  = htmlDocument(displayPage([[self.pool.printState("<br>")]]), 
                                          [self.pool.title], 
                                          refreshScript(10))
                    response = httpHeader(self.pool.title, len(html)) + html
                else:
                    if path == "/spaon":
                        self.pool.spaOn()
                        response = httpHeader(self.pool.title)
                    elif path == "/spaoff":
                        self.pool.spaOff()
                        response = httpHeader(self.pool.title)
                    elif path == "/lightson":
                        self.pool.lightsOn()
                        response = httpHeader(self.pool.title)
                    elif path == "/lightsoff":
                        self.pool.lightsOff()
                        response = httpHeader(self.pool.title)
                    else:
                        response = httpHeader(self.pool.title, "404 Not Found")                    
                ns.sendall(response)
        finally:
            ns.close()
            if debug: log(self.name, "disconnected")

