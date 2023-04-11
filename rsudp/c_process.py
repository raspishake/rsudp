import sys, os
from datetime import timedelta
import rsudp.raspberryshake as rs
from obspy.signal.trigger import recursive_sta_lta
from rsudp import printM, printW, printE, helpers
from rsudp.test import TEST

class Processor(rs.ConsumerThread):
    
    
    
    def __init__(self, q, data_dir, testing=False, cha='all',lta=30,deconv="False"):
        """
		Initialize the process
		"""
        super().__init__()
        self.sender = 'Processor'
        self.alive = True
        self.testing = testing
        # debug = debug
        if self.testing:
            self.debug = True

        self.fmt = '%Y-%m-%d %H:%M:%S.%f'

        self.queue = q
        self.master_queue = None
        
        self.chans = []
        helpers.set_channels(self, cha)

        self.stream = rs.Stream()
        self.raw = rs.Stream()
        self.outdir = os.path.join(data_dir, 'data')
        self.outfiles = []
        self.lta = lta
        self.sps = rs.sps
        self.inv = rs.inv
        # self.stalta = np.ndarray(1)
        self.maxstalta = 0
        self.units = 'counts'
        
        # self._set_deconv(self, deconv)
        
        # self.max_pga = 0
        # self.max_pgd = 0
        

        self.chans = []
        helpers.set_channels(self, cha)

        # printM('Writing channels: %s' % self.chans, self.sender)
        # self.numchns = rs.numchns
        # self.stime = 1/rs.sps
        # self.inv = rs.inv

        printM('Starting.', self.sender)
        
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
        return intensity    
        
    def intensity_to_int(self,intensity): # Convert string to number for text-to-voice
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
    
    def getq(self):
        '''
        Reads data from the queue and updates the stream.

		:rtype: bool
		:return: Returns ``True`` if stream is updated, otherwise ``False``.
		'''         
            
        d = self.queue.get()
        self.queue.task_done()
        
        if 'TERM' in str(d):
            self.alive = False
            printM('Exiting.', self.sender)
            sys.exit()
        elif 'ALARM' in str(d):
            return d
        else:
            if rs.getCHN(d) in self.chans:
                self.raw = rs.update_stream(
                    stream=self.raw, d=d, fill_value=None)
                return True
            else:
                return False
            


    def _deconvolve(self):
        '''
		Deconvolves the stream associated with this class.
		'''
		# if self.deconv:
        helpers.deconvolve(self)

#     def _subloop(self):
#         '''
# 		Gets the queue and figures out whether or not the specified channel is in the packet.
# 		'''
#         while True:
#             if self.queue.qsize() > 0:
#                 self.getq()			# get recent packets
#             else:
#                 if self.getq():		# is this the specified channel? if so break
#                     break


    def _filter(self):
        '''
		Filters the stream associated with this class.
		'''
        if self.filt:
            if self.filt in 'bandpass':
                self.stalta = recursive_sta_lta(
							self.stream[0].copy().filter(type=self.filt,
							freqmin=self.freqmin, freqmax=self.freqmax),
							int(self.sta * self.sps), int(self.lta * self.sps))
            else:
                self.stalta = recursive_sta_lta(
							self.stream[0].copy().filter(type=self.filt,
							freq=self.freq),
							int(self.sta * self.sps), int(self.lta * self.sps))
        else:
            self.stalta = recursive_sta_lta(self.stream[0],
					int(self.sta * self.sps), int(self.lta * self.sps))
                    
                    
    def _when_alarm(self,d):
        
        n = 0
        while n > 3:
            self.getq()
            n += 1
        
        n = 0
        
        
        while True:
            # self._subloop()
            
            self.raw = rs.copy(self.raw)
            self.stream = self.raw.copy()
            self.deconv ="ACC"
            self.units = "Acceleration"
            self._deconvolve()
            
            ### get max acceleration
            
            # get max PGA, max intensity, and which channel
            max_pga = 0
            max_intensity_int = 0
            max_intensity_str = ""
            max_pga_channel = "" # channel with max PGA
            
            
            for acc_tr in self.stream:
                if acc_tr.stats.channel == "EHZ":
                    pass
                else:
                    peakAcc = max(abs(acc_tr.data))
                    if peakAcc > max_pga:
                        max_pga = peakAcc
                        max_intensity_str = self.g_to_intensity(max_pga/9.81)
                        max_intensity_int = self.intensity_to_int(max_intensity_str)
                        max_pga_channel = acc_tr.stats.channel
                
            
            ## get displacement
            self.deconv = "DISP"
            self._deconvolve
            # obstart = self.stream[0].stats.endtime - timedelta(seconds=self.lta)
            # self.stream = self.stream.slice(starttime=obstart)
            # self._filter
            
            max_pgd = 0
            
            for dis_tr in self.stream:
                if dis_tr.stats.channel == "EHZ":
                    pass
                else:
                    peakDis = max(abs(acc_tr.data))
                    if peakDis > max_pgd:
                        max_pgd = peakDis
                        max_pgd_channel = dis_tr.stats.channel
            
            # self.max_pga = max_pga
            # self.max_pgd = max_pgd
            
            # printM("Peak displacement is %.2f centimeters along " + max_pgd_channel 
                   # +", and peak acceleration is %.2f centimeters-per-second-squared along " + max_pga_channel % (max_pgd*100, max_pga*100),self.sender)
            
            self.process = [max_pga,max_pgd]
            # self.process = [max_pga,max_pgd,max_pga_channel,max_pgd_channel,helpers.fsec(self.stream[0].stats.endtime)]
            
            printM("Intensity: {0}".format(max_intensity_str),self.sender)
            printM("Peak displacement is {0:.3g} centimeters along ".format(max_pgd*100) + max_pgd_channel 
                   +", and peak acceleration is {0:.3g} centimeters-per-second-squared along ".format(max_pga*100)
                   + max_pga_channel,self.sender)
            sys.stdout.flush()
            
            if self.testing:
                TEST['c_process'][1] = True
            
            break

        
    def run(self):
        """
		Reads data from the queue and sends a message if it sees an ALARM or IMGPATH message
		"""
        printM("process module ongoing",self.sender)
        while True:
            d = self.getq()

            if 'ALARM' in str(d):
                printM("process module triggered",self.sender)
                self._when_alarm(d)