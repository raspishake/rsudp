# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 16:28:38 2022

@author: jermz
"""

import sys, os
from datetime import timedelta
import rsudp.raspberryshake as rs
from obspy.signal.trigger import recursive_sta_lta
from rsudp import printM, printW, printE, helpers
from rsudp.test import TEST
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import time
import tkinter as tk
from tkinter import messagebox as mb
import threading

class Dialog(rs.ConsumerThread):


    def g_to_intensity(self,g): # Gets intensity from PGA
        intensity_scale = {
            (0,0.00170): 'I',
            (0.00170,0.01400): 'II-III',
            (0.01400,0.03900): 'IV',
            (0.03900,0.09200): 'V',
            (0.09200,0.18000): 'VI',
            (0.18000,0.34000): 'VII',
            (0.34000,0.65000): 'VIII',
            (0.65000,1.24000): 'IX',
            (1.24000,5): 'X+'
        }
        for i in intensity_scale:
            if i[0] < g < i[1]:
                intensity = intensity_scale[i]
            # else:
            #     intensity = 'X+'
        return intensity

    def threadSound(self): #thread for playing alert sound
        for _ in range(1):
            # play(AudioSegment.from_mp3("alarm.mp3"))
            play(AudioSegment.from_mp3("eq_intensity.mp3"))
            play(AudioSegment.from_mp3("eq_displacement.mp3"))
            time.sleep(1)

    def threadDialog(self,intensity,pgd,pga): # thread for displaying alert box

        root = tk.Tk()
        root.withdraw()
        mb.showwarning('! EARTHQUAKE ALERT !',
                        ('Intensity: %s\nDisplacement: %.2f m, '+'\nAcceleration: %.2f m/s2') % (intensity,pgd,pga))

        # mb.showwarning('! EARTHQUAKE ALERT !',
        #        ('Intensity: %s\nDisplacement: %.2f cm, ' + pgd_cha
        #         +'\nAcceleration: %.2f cm/s2, '+ pga_cha) % (intensity,pgd,pga))

        root.destroy()



    def intensity_to_int(self,intensity): #convert string to number for text-to-voice
        if intensity == "I":
            intensityNum = 1
        elif intensity == "II-III":
            intensityNum = 2
        elif intensity == "IV":
            intensityNum = 4
        elif intensity == "V":
            intensityNum = 5
        elif intensity == "VI":
            intensityNum = 6
        elif intensity == "VII":
            intensityNum = 7
        elif intensity == "VIII":
            intensityNum = 8
        elif intensity == "IX":
            intensityNum = 9
        elif intensity == "X+":
            intensityNum = 10
        else:
            intensityNum = 0

        return intensityNum

    def channel_to_axis(self,channel):
        if "HZ" in channel:
            return "Vertical axis" # geophone, should we indicate?
        elif "NZ" in channel:
            return "Vertical axis" # MEMS.
        elif "NN" in channel:
            return "North-South axis"# MEMS.
        elif "NE" in channel:
            return "East-West axis"# MEMS.

    def getq(self):
        '''
        Reads data from the queue and updates the stream.

        :rtype: bool
        :return: Returns ``True`` if stream is updated, otherwise ``False``.
        '''
        d = self.queue.get(True, timeout=None)
        self.queue.task_done()

        if 'PROCESS' in str(d):
            return d
        elif 'TERM' in str(d):
            self.alive = False
            printM('Exiting.', self.sender)
            sys.exit()
        else:
            return False

    def __init__(self, q, testing=False):
        """
        Initialize the process
        """
        super().__init__()
        self.sender = 'Dialog'
        self.alive = True
        self.testing = testing
        # debug = debug
        if self.testing:
            self.debug = True

        self.fmt = '%Y-%m-%d %H:%M:%S.%f'

        self.queue = q
        self.master_queue = None

        self.chans = []

        self.stream = rs.Stream()
        self.raw = rs.Stream()
        self.outfiles = []
        self.sps = rs.sps
        self.inv = rs.inv
        self.maxstalta = 0
        self.units = 'counts'


        printM('Starting.', self.sender)

    def _when_process(self,d):

        while True:
            pga, pgd = helpers.get_msg_process_values(d)
            pga = float(pga)
            pgd = float(pgd)

            # pga_cha, pgd_cha = helpers.get_msg_process_channels(d)

            # event_time = helpers.get_msg_process_time(d)

            max_intensity_str = self.g_to_intensity(pga/9.81)
            max_intensity_int = self.intensity_to_int(max_intensity_str)

            if max_intensity_str == "II-III":
                myobj = gTTS(text="Attention! Earthquake detected at intensity two or three", lang="en", slow=False)
            else:
                myobj = gTTS(text="Attention! Earthquake detected at intensity %.0f" % max_intensity_int, lang="en", slow=False)
            myobj.save("./eq_intensity.mp3")

            myobj = gTTS(text=("Peak displacement is %.2f meters" \
                                + " and peak acceleration is %.2f meters-per-second-squared ") % (pgd, pga), lang="en", slow=False)

            # myobj = gTTS(text=("Peak displacement is %.2f centimeters along " + self.channel_to_axis(pgd_cha) \
            #             + ", and peak acceleration is %.2f centimeters-per-second-squared along " \
            #             + self.channel_to_axis(pga_cha)) % (pgd, pga), lang="en", slow=False)

            myobj.save("./eq_displacement.mp3")

            alertThread1 = threading.Thread(target=self.threadSound)
            alertThread1.start()
            alertThread2 = threading.Thread(target=self.threadDialog, args=(max_intensity_str,pgd,pga))
            alertThread2.start()

            if self.testing:
                TEST['c_dialog'][1] = True

            break


    def run(self):
        """
        Reads data from the queue and sends a message if it sees an ALARM or IMGPATH message
        """
        while True:
            d = self.getq()

            if 'PROCESS' in str(d):
                self._when_process(d)
