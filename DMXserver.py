#!/usr/bin/python

FILE = 'sparkle.html'
PORT = 8080

import threading
import BaseHTTPServer
import SimpleHTTPServer
import json
import webbrowser
import sys
from urlparse import urlparse, parse_qs
from multiprocessing import Process, Pipe
import time

import logging
logger = logging.getLogger(__name__)


PORT = 8080
server_address = ("",PORT)

class AuroraHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """Handler for aurora control"""

    # If someone went to "http://something.somewhere.net/foo/bar/",
    # then s.path equals "/foo/bar/".

    def do_GET(self):
        print "request for " + self.path
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

        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)
            logger.info("404 file not found '%s'", self.path)


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
        logging.info("Handler response: " + handler_response)

        result = [handler_response, 99]

        

#        except:
#            result = 'error'


        # now parse post things and deal with them


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

def server_handler(request):
    """ dispatch a command to the DMX generator process """
    global ParentP # pipe end to send commands to 
    # send command, try to keep running crash if receiver does
    try:
        parentP.send(request)
    except:
        print "server_handler(%s) exited with '%s' " % (request, sys.exc_info())
    time.sleep(0.01)
    if parentP.poll():
        msg = parentP.recv()
        print 'hander receieved ack "%s"' % msg
        sys.stdout.flush()
        return msg
    else:
        return "null response :/"

def start_child():
    """Start the child process that generates DMX events"""
    global parentP
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


def start_server():
    """Start the server."""

    logging.basicConfig(filename='logs/aurora.log', 
                        filemode='w', 
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    start_child()
    #server = BaseHTTPServer.HTTPServer(server_address, AuroraHandler)
    server = MyHTTPServer(server_address, AuroraHandler,server_handler)
    print "aurora server listening on port " + str(PORT)
    logging.info('aurora server listening on port %s', str(PORT))
    server.serve_forever()
    p.join() # won't get here, but clean up nicely anyway

if __name__ == "__main__":
    #open_browser()
    global parentP
    parentP = None
    start_server()


