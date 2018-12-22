import socket as s

port = 8888								# Port to bind to

hostipF = "/opt/settings/sys/ip.txt"
file = open(hostipF, 'r')
host = file.read().strip()
file.close()

HP = host + ":" + str(port)
print("  Opening socket on (HOST:PORT)", HP)

sock = s.socket(s.AF_INET, s.SOCK_DGRAM | s.SO_REUSEADDR)
sock.bind((host, port))

print("Waiting for data on (HOST:PORT) ", HP)

while 1:								# loop forever
    data, addr = sock.recvfrom(1024)	# wait to receive data
    print(data)							
