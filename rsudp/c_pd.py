import os, sys
import time
import rsudp.raspberryshake as rs
from rsudp import printM, printW, printE, helpers
from rsudp.test import TEST

class Pd(rs.ConsumerThread):
	"""
	.. versionadded:: 1.1.1

	A consumer class that calculates peak amplitude of displacement P(d) when a trigger is set off.
    """
