FILE = 'sparkle.html'
PORT = 8080

import threading
import BaseHTTPServer
import SimpleHTTPServer
import json
import webbrowser
import sys
from urlparse import urlparse, parse_qs

import logging
logger = logging.getLogger(__name__)

# Echo client program
import socket

SOCKHOST = '127.0.0.1'    # Send the data
SOCKPORT = 50007          # The same port as used by the server


class TestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """The test example handler."""

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
        """Handle a post request-- send the data to the chid proc"""
        length = int(self.headers.getheader('content-length'))        
        data_string = self.rfile.read(length)
        #print repr(self.headers)
        print 'Recieved "%s" from page %s' % (str(data_string), self.path)
        logger.info('Received "%s" from page %s', str(data_string), self.path)

        try:
            self.s.write(str(data_str))
        except AttributeError as e:
            print "error writing DMX process "
            raise e

        # now parse post things and deal with them
        # try:
        #     params = parse_qs(data_string)
        #     print repr(params)
        #     result = ['OK!', 99]
        # except:
        #     result = 'error'


        # now parse post things and deal with them

        self.send_response(200)
        #self.send_header("Content-type", "text/html")
        self.send_header("Content-type", "application/json")
        self.end_headers()
        # send AJAX response back to requesting page
        self.wfile.write(json.dumps([{"response":result}]))
        #self.wfile.write("<html><head><title>Title goes here.</title></head>")
        #self.wfile.write("<body><p>This is a test.</p>")
                # If someone went to "http://something.somewhere.net/foo/bar/",
                # then s.path equals "/foo/bar/".


    def attach_socket(self,socket):
        self.s = socket


def start_server():
    """Start the server."""
    logging.basicConfig(filename='logs/aurora.log', 
                        filemode='w', 
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    logging.info('server started')

    server_address = ("", PORT)
    server = BaseHTTPServer.HTTPServer(server_address, TestHandler)
    print "aurora server listening on port " + str(PORT)
    logging.info('aurora server listening on port %s', str(PORT))

    server.serve_forever()

if __name__ == "__main__":
    #open_browser()
    start_server()
    while True:
        print "Still have control..."
        time.sleep(0.5)
