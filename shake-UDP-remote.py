import socket as s

host = ""				# when running not on the Shake Pi: blank = localhost 
port = 18005				# Port to bind to

HP = host + ":" + str(port)
print("  Opening socket on (HOST:PORT)", HP)

sock = s.socket(s.AF_INET, s.SOCK_DGRAM | s.SO_REUSEADDR)
sock.bind((host, port))

print("Waiting for data on (HOST:PORT) ", HP)

while 1:								# loop forever
    data, addr = sock.recvfrom(1024)	# wait to receive data
    print(data)							
