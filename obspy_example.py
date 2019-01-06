import rs2obspy as rso

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
		while True:
			s = rso.update_stream(s)
	except KeyboardInterrupt:
		s.plot()


rso.init(port=18003, sta='R4989', net='AM')

construct_stream()
