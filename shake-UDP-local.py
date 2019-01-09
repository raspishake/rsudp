import raspberryShake as RS

port = 8888								# Port to bind to

hostipF = "/opt/settings/sys/ip.txt"
file = open(hostipF, 'r')
host = file.read().strip()
file.close()

RS.initRSlib(dport=port)
RS.openSOCK()

while 1:								# loop forever
	print(RS.getDATA())