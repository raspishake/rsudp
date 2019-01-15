import raspberryShake as RS
import sys, getopt


def run(port):
	RS.initRSlib(dport=port)
	RS.openSOCK()

	while 1:								# loop forever
		print(RS.getDATA())


hlp_txt = '''
This program prints UDP data sent to a specific local port.
The following command will print data from port 18001:

python shake-UDP-remote.py -p 18001

Use -h to display this message.
'''

if __name__ == '__main__':
	prt = 8888
	opts, args = getopt.getopt(sys.argv[1:], 'hp:', ['help', 'port='])
	for o, a in opts:
		if o in ('-h, --help'):
			print(hlp_txt)
			exit(0)
		try:
			if o in ('-p', 'port='):
				prt = int(a)
		except Exception as e:
			RS.printM('ERROR: Port value must be integer.')
			RS.printM('Error details: %s' % e)
			exit(2)
	try:
		run(prt)
	except KeyboardInterrupt:
		print('')
		RS.printM('Quitting...')
		exit(0)