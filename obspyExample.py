import obspy
import raspberryShake as RS

'''
1. open socket
2. create empty obspy stream
3. get a data packet and analyze inherent values
4. create trace(s) and assign inherent values
5. gather & parse data (may be for more than one trace)
6. append data to obspy trace(s)
7. repeat 4 + 5
'''

def init_stream():
	RS.openSOCK()
	nchan = RS.getTTLCHN()
	d = RS.getDATA()
	tr = RS.getTR(RS.getCHN(d))
	sps = RS.getSR(RS.getTR(RS.getCHN(d)))

def parse_stream():
	d = RS.getDATA()
	ch = RS.getCHN(d)
	t = RS.getTIME(d)
	rst = RS.getSTREAM(d)

