FILE = 'sparkle.html'
PORT = 8080

import threading
import BaseHTTPServer
import SimpleHTTPServer
import json
import webbrowser
import sys
from urlparse import urlparse, parse_qs

class TestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """The test example handler."""

    def do_GET(self):
        print "request for " + self.path
        if self.path=="/":
            self.path="/index.html"
            
        try:
	#Check the file extension required and
	#set the right mime type

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

            if sendReply == True:
				#Open the static file requested and send it
                    #f = open(curdir + sep + self.path) 
                path = "." + self.path
                print "serving " + path
                f = open(path) 
                self.send_response(200)
                self.send_header('Content-type',mimetype)
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return


        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)


    def do_POST(self):
        """Handle a post request by returning the square of the number."""
        length = int(self.headers.getheader('content-length'))        
        data_string = self.rfile.read(length)
        #print repr(self.headers)
        print 'Recieved "%s" from page %s' % (str(data_string), self.path)


        # now parse post things and deal with them



        try:
            params = parse_qs(data_string)
            print repr(params)
            result = ['OK!', 99]
        except:
            result = 'error'


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

def open_browser():
    """Start a browser after waiting for half a second."""
    def _open_browser():
        webbrowser.open('http://localhost:%s/%s' % (PORT, FILE))
    thread = threading.Timer(0.5, _open_browser)
    thread.start()

def start_server():
    """Start the server."""
    server_address = ("", PORT)
    server = BaseHTTPServer.HTTPServer(server_address, TestHandler)
    print "aurora server listening on port " + str(PORT)
    server.serve_forever()

if __name__ == "__main__":
    #open_browser()
    start_server()
