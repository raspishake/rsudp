import os, sys, platform
import pkg_resources as pr
import time
import math
import numpy as np
from datetime import datetime, timedelta
import rsudp.raspberryshake as rs
from rsudp import printM, printW, printE, get_scap_dir, helpers
from rsudp.test import TEST
import linecache
sender = 'controller.py'
QT = False
QtGui = False
PhotoImage = False
ICON = 'icon.ico'
ICON2 = 'icon.png'

try:		# test for matplotlib and exit if import fails
    from matplotlib import use
    try:	# no way to know what machines can handle what software, but Tk is more universal
        use('Qt5Agg')	# try for Qt because it's better and has less threatening errors
        from PyQt5 import QtGui
        QT = True
    except Exception as e:
        printW('Qt import failed. Trying Tk...')
        printW('detail: %s' % e, spaces=True)
        try:	# fail over to the more reliable Tk
            use('TkAgg')
            from tkinter import PhotoImage
        except Exception as e:
            printE('Could not import either Qt or Tk, and the plot module requires at least one of them to run.', sender)
            printE('Please make sure either PyQt5 or Tkinter is installed.', sender, spaces=True)
            printE('detail: %s'% e, sender, spaces=True)
            raise ImportError('Could not import either Qt or Tk, and the plot module requires at least one of them to run')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.image as mpimg
    from matplotlib import rcParams
    from matplotlib.ticker import EngFormatter
    rcParams['toolbar'] = 'None'
    plt.ion()
    MPL = True

    # avoiding a matplotlib user warning
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='rsudp')

except Exception as e:
    printE('Could not import matplotlib, plotting will not be available.', sender)
    printE('detail: %s' % e, sender, spaces=True)
    MPL = False


class PlotController():
    def __init__(self, queue, plots, seconds=30, screencap=False, alert=True, spectrogram=True):
        self._plots = plots

        self.queue = queue
        self.master_queue = None
        self.seconds = seconds
        self.screencap = screencap
        self.main_plot = self._plots["main"]

        self.sender = "PlotController"
        self.last_event_str = ""
        self.stn = rs.stn
        self.net = rs.net
        self.totchns = rs.numchns

        # Streams
        self.raw = rs.Stream()
        self.stream = rs.Stream()

        # Flags
        self.alive = False
        self.alert = alert
        self.spectrogram = spectrogram

        # Counters
        self.events = 0
        self.save_timer = 0

        # Constants
        self.save_pct = 0.7
        self.pkts_in_period = rs.tr * rs.numchns * self.seconds

        # Plot constants
        self.bgcolor = '#202530'    # background
        self.fgcolor = '0.8'        # axis and label color
        self.linecolor = '#c28285'  # seismogram color

        # Arrays
        self.save = []
        self.chans = []

        self.sps = None
        self.unit = None
        self.units = None

    def _set_deconv(self, deconv):
        '''
        This function sets the deconvolution units. Allowed values are as follows:

        .. |ms2| replace:: m/s\ :sup:`2`\

        - ``'VEL'`` - velocity (m/s)
        - ``'ACC'`` - acceleration (|ms2|)
        - ``'GRAV'`` - fraction of acceleration due to gravity (g, or 9.81 |ms2|)
        - ``'DISP'`` - displacement (m)
        - ``'CHAN'`` - channel-specific unit calculation, i.e. ``'VEL'`` for geophone channels and ``'ACC'`` for accelerometer channels

        :param str deconv: ``'VEL'``, ``'ACC'``, ``'GRAV'``, ``'DISP'``, or ``'CHAN'``
        '''
        self.deconv = deconv if (deconv in rs.UNITS) else False
        if self.deconv and rs.inv:
            deconv = deconv.upper()
            if self.deconv in rs.UNITS:
                self.units = rs.UNITS[self.deconv][0]
                self.unit = rs.UNITS[self.deconv][1]
            printM('Signal deconvolution set to %s' % (self.deconv), self.sender)
        else:
            self.units = rs.UNITS['CHAN'][0]
            self.unit = rs.UNITS['CHAN'][1]
            self.deconv = False
        printM('Seismogram units are %s' % (self.units), self.sender)

    def terminate(self):
        plt.close()
        self.alive = False
        rs.producer = False

    def event(self):
        self.events += 1  # add event to count
        self.save_timer -= 1  # don't push the save time forward if there are a large number of alarm events
        event = [self.save_timer + int(self.save_pct * self.pkts_in_period),
                 helpers.fsec(helpers.get_msg_time(d))]  # event = [save after count, datetime]
        self.last_event_str = '%s UTC' % (event[1].strftime('%Y-%m-%d %H:%M:%S.%f')[:22])
        printM('Event time: %s' % (self.last_event_str), sender=self.sender)  # show event time in the logs
        if self.screencap:
            printM('Saving png in about %i seconds' % (self.save_pct * (self.seconds)), self.sender)
            self.save.append(event)  # append
        for _, plot in self._plots:
            if plot.is_event_title:
                plot.suptitle('%s.%s live output - detected events: %s' % (self.net, self.stn, self.events),
                              fontsize=14,
                              color=self.fgcolor,
                              x=0.52)
                plot.canvas.manager.set_window_title('(%s) %s.%s - Raspberry Shake Monitor' % (self.events, self.net, self.stn))

    def get_data_from_queue(self):
        '''
        Get data from the queue and test for whether it has certain strings.
        ALARM and TERM both trigger specific behavior.
        ALARM messages cause the event counter to increment, and if
        :py:data:`screencap==True` then aplot image will be saved when the
        event is :py:data:`self.save_pct` of the way across the plot.
        '''
        d = self.queue.get()
        self.queue.task_done()
        if 'TERM' in str(d):
            if 'SELF' in str(d):
                printM('Plot has been closed, plot thread will exit.', self.sender)
            self.terminate()
        elif 'ALARM' in str(d):
            self.event()
        if rs.getCHN(d) in self.chans:
            self.raw = rs.update_stream(stream=self.raw, d=d, fill_value='latest')
            return True
        else:
            return False

    def set_sps(self):
        '''
        Get samples per second from the main library.
        '''
        self.sps = rs.sps

    def deconvolve(self):
        '''
        Send the streams to the central library deconvolve function.
        '''
        helpers.deconvolve(self)

    def set_icon(self, qt=None):
        '''
        Set RS plot icons.
        '''
        mgr = plt.get_current_fig_manager()
        ico = pr.resource_filename('rsudp', os.path.join('img', ICON))
        if qt:
            mgr.window.setWindowIcon(QtGui.QIcon(ico))
        else:
            try:
                ico = PhotoImage(file=ico)
                mgr.window.tk.call('wm', 'iconphoto', mgr.window._w, ico)
            except:
                printW('Failed to set PNG icon image, trying .ico instead', sender=self.sender)
                try:
                    ico = pr.resource_filename('rsudp', os.path.join('img', ICON2))
                    ico = PhotoImage(file=ico)
                    mgr.window.tk.call('wm', 'iconphoto', mgr.window._w, ico)
                except:
                    printE('Failed to set window icon.')
    def setup_plot(self):
        """
        Sets up the plot. Quite a lot of stuff happens in this function.
        Matplotlib backends are not threadsafe, so things are a little weird.
        See code comments for details.
        """
        # instantiate a figure and set basic params
        for _, plot in self._plots:
            plot.init_plot(qt=QT)
            for i in range(len(self.chans)):
                plot.init_axes(i)
            for axis in plot.ax:
                # set the rest of plot colors
                plt.setp(axis.spines.values(), color=plot.fgcolor)
                plt.setp([axis.get_xticklines(), axis.get_yticklines()], color=plot.fgcolor)
            # rs logos
            plot.set_icon()
            # draw axes
            plot.format_axes()
            plot.handle_resize()
            # setup figure manager
            plot.set_fig_manager()

        # draw plot, loop, and resize the plot
        plt.draw()  # draw the canvas
        for _, plot in self._plots:
            plot.fig.canvas.start_event_loop(0.005)  # wait for canvas to update
            plot.handle_resize()

    def run(self):
        self.get_data_from_queue()  # block until data is flowing from the consumer
        for i in range((self.totchns) * 2):  # fill up a stream object
            self.get_data_from_queue()
        self.set_sps()
        self.deconvolve()
        self.setup_plot()

        n = 0  # number of iterations without plotting
        i = 0  # number of plot events without clearing the linecache
        u = -1  # number of blocked queue calls (must be -1 at startup)
        while True:  # main loop
            while True:  # sub loop
                if self.alive == False:  # break if the user has closed the plot
                    break
                n += 1
                self.save_timer += 1
                if self.queue.qsize() > 0:
                    self.getq()
                    time.sleep(0.009)  # wait a ms to see if another packet will arrive
                else:
                    u = self.qu(u)
                    if n > (self.delay * rs.numchns):
                        n = 0
                        break
            if self.alive == False:  # break if the user has closed the plot
                printM('Exiting.', self.sender)
                break
            i, u = self.mainloop(i, u)
            if self.testing:
                TEST['c_plot'][1] = True
        return