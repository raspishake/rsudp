import rsudp.raspberryshake as RS

port = 8888								# Port to bind to

with open('/opt/settings/sys/ip.txt', 'r') as file:
    host = file.read().strip()

RS.initRSlib(dport=port)
RS.openSOCK(host)

def main():
	'''
	Simple function to print data to the command line until CTRL+C is pressed.
	'''
	try:
		while 1:								# loop forever
			print(RS.getDATA())
	except KeyboardInterrupt:
		print('')
		RS.printM('Quitting...')
		exit(0)

if __name__ == '__main__':
	main()
