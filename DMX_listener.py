

#!/usr/bin/python

import socket
import time

HOST = ''                 # Symbolic name meaning the local host
PORT = 50007              # Arbitrary non-privileged port


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print 'Connected by', addr
while 1:
    data = conn.recv(1)
    print str(data)
    if not data: 
        print "wait"
        time.sleep(0.01)

conn.close()

