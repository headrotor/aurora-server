#!/usr/bin/python

PORT = 80
server_address = ("",PORT)

#import threading
import BaseHTTPServer
import SimpleHTTPServer
import json
import webbrowser
import sys
import os
from urlparse import urlparse, parse_qs
from multiprocessing import Process, Pipe

import signal
import time
import atexit
import logging

logger = logging.getLogger(__name__)

class AuroraHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """Handler for aurora control"""

    # If someone went to "http://something.somewhere.net/foo/bar/",
    # then s.path equals "/foo/bar/".

    def do_GET(self):
        print "request for " + self.path
        logger.info("request for " + self.path)
        if self.path=="/":
            self.path="/index.html"
            
        try:
	#Check the file extension required and
	#set the right mime type
	#NOTE Added the same for js as to serve them locally

            sendReply = False
            if self.path.endswith(".html"):
                mimetype='text/html'
                sendReply = True
            if self.path.endswith(".css"):
                mimetype='text/css'
                sendReply = True
            elif self.path.endswith(".png"):
                mimetype='image/png'
                sendReply = True
            elif self.path.endswith(".jpg"):
                mimetype='image/jpg'
                sendReply = True
            elif self.path.endswith(".js"):
                mimetype='text/javascript'
                sendReply = True
            elif self.path.endswith(".woff"):
                mimetype='font/woff'
                sendReply = True
            elif self.path.endswith(".map"):
                mimetype='text/plain'
                sendReply = True

            if sendReply == True:
                #Open the static file requested and send it
                #f = open(curdir + sep + self.path) 
                path = "." + self.path
                print "serving " + path
                logger.info("serving %s", path)
                f = open(path) 
                self.send_response(200)
                self.send_header('Content-type',mimetype)
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            else:
                #self.send_error(404,'File Not Found: %s' % self.path)
                #logger.info("404 wrong file type '%s'", self.path)
                f = open("./redirect.html") 
                self.send_response(200)
                mimetype='text/html'
                self.send_header('Content-type',mimetype)
                self.end_headers()
                self.wfile.write(f.read())
                f.close()

        except IOError:
            #self.send_error(404,'File Not Found: %s' % self.path)
            #logger.info("404 file not found '%s'", self.path)
            f = open("./redirect.html") 
            self.send_response(200)
            mimetype='text/html'
            self.send_header('Content-type',mimetype)
            self.end_headers()
            self.wfile.write(f.read())
            f.close()

    def do_POST(self):
        """Handle a post request by returning the square of the number."""
        length = int(self.headers.getheader('content-length'))        
        data_string = self.rfile.read(length)
        #print repr(self.headers)
        print 'Recieved "%s" from page %s' % (str(data_string), self.path)
        logger.info('Received "%s" from page %s', str(data_string), self.path)
        # now parse post things and deal with them


#        try:
        params = parse_qs(data_string)
        handler_response = self.server.handler(params)
        if handler_response is not None:
            logging.info("Handler response: " + handler_response)
            result = [handler_response, 99]

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            # send AJAX response back to requesting page
            self.wfile.write(json.dumps([{"response":result}]))


class MyHTTPServer(BaseHTTPServer.HTTPServer):
    """Subclass BaseHTTPSServer so we can pass custom request handler
       method into the RequestHandlerClass"""
    def __init__(self, server_address, RequestHandlerClass, handler):
        BaseHTTPServer.HTTPServer.__init__(self, 
                                           server_address, 
                                           RequestHandlerClass)
        self.handler = handler
        #self.handler.server_parent = self

def server_handler(request):
    """ dispatch a command to the DMX generator process """
    global ParentP # pipe end to send commands to 
    # send command, try to keep running crash if receiver does

    try:
        parentP.send(request)
    except:
        print "server_handler(%s) exited with '%s' " % (request, sys.exc_info())

                                                        
        #logger.info("server_handler(%s) exited with '%s' " % (request, sys.exc_info()))
    time.sleep(0.01)
    if parentP.poll():
        try:
            msg = parentP.recv()
        except EOFError: # happens when generator crashes, 
            #self.server_parent.shutdown()
            logger.info("Child crash detected")
        else:
            print 'hander receieved ack "%s"' % msg
            return msg
    else:
        return "null response :/"

def restart_child():
    """Start/restart the child process that generates DMX events"""
    global parentP
    global p
    import DMXgenerator
    if parentP is not None:
        try:
            parentP.close()
        except:
            print sys.exc_info()
    parentP, childP = Pipe()
    p = Process(target=DMXgenerator.listener, args=(childP,"foo"))
    #p.daemon = True
    p.start()
    childP.close() # don't need child end, only parent
    return p

def start_server():
    """Start the server."""
    import os
    global p

    logging.basicConfig(filename='logs/aurora.log', 
                        filemode='w', 
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    proc = restart_child()
    #server = BaseHTTPServer.HTTPServer(server_address, AuroraHandler)
    server = MyHTTPServer(server_address, AuroraHandler,server_handler)
    print "aurora server pid %d listening on port %d" % (os.getpid(),PORT)
    logging.info('aurora server pid %d listening on port %d' % (os.getpid(),PORT))
    keep_running = True
   
    while True:
        #server.serve_forever()
        #print "child proc " + repr(p.is_alive())
        if p.is_alive() is not True:
            proc = restart_child()
            logger.info('DMX process restarted as ' + repr(proc))
        server.handle_request()


def handler(signum, frame):
    """ Kill DMXgenerator child on TERM signal"""
    global p
    p.terminate()
    print 'Signal handler called with signal', signum


if __name__ == "__main__":
    #open_browser()
    global p
    global parentP
    signal.signal(signal.SIGTERM, handler)
    parentP = None
    p = None
    start_server()
    p.terminate()



