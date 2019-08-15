import rsudp.rs2obspy as rso

'''
A small example program that uses rs2obspy to build a stream, then
plots the result when the user interrupts the program using CTRL+C.

Requires obspy, numpy, rs2obspy, and raspberryShake.
'''

def construct_stream():
	'''
	Main function. Designed to run until user cancels with CTRL+C,
	at which point it will create a simple trace plot.
	'''
	s = rso.init_stream()
	try:
		rso.RS.printM('Updating stream continuously. Will run unitl Ctrl+C is pressed.')
		while True:
			s = rso.update_stream(s)
	except KeyboardInterrupt:
		print('')
		rso.RS.printM('Plotting...')
		s.plot()


def main():
	rso.init(port=18003, sta='Z0000')

	construct_stream()

if __name__ == '__main__':
	main()
