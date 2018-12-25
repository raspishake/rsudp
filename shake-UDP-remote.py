import raspberryShake as RS

host = ""				# when running not on the Shake Pi: blank = localhost
port = 18005				# Port to bind to

RS.openSOCK(host=host, port=port)

while 1:								# loop forever
	print(RS.getDATA())