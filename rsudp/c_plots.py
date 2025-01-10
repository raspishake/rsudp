import os
import math
from datetime import datetime
import numpy as np
import pkg_resources as pr
from rsudp import printM, printW, printE, get_scap_dir, helpers


sender = 'plots.py'


try:
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.ticker import EngFormatter
    MPL = True
except Exception as e:
    printE('Could not import matplotlib, plotting will not be available.', sender)
    printE('detail: %s' % e, sender, spaces=True)
    MPL = False


class BasePlot():
    ICON = 'icon.ico'
    ICON2 = 'icon.png'

    def __init__(self, controller, alert=True, spectrogram=True):
        self._controller = controller

        self.sps = self._controller.sps
        self.fig = None # Figure https://matplotlib.org/stable/api/_as_gen/matplotlib.figure.Figure.html#matplotlib.figure.Figure

        self.alert = alert
        self.seconds = self._controller.seconds
        self.spectrogram = spectrogram

        self.net = self._controller.net
        self.stn = self._controller.stn
        self.bgcolor = self._controller.bgcolor
        self.fgcolor = self._controller.fgcolor
        self.linecolor = self._controller.linecolor
        self.unit = self._controller.unit
        self.num_chans = len(self._controller.chans)
        self.event_text = ' - detected events: 0' if alert else ''
        self.sender = "BasePlot"

        self.ax = []
        self.lines = []

    @staticmethod
    def is_event_title():
        return False

    @staticmethod
    def nearest_pow_2(x):
        """
        Find power of two nearest to x

        :type x: float
        :param x: Number
        :rtype: Int
        :return: Nearest power of 2 to x

        Adapted from the `obspy <https://obspy.org>`_ library
        """
        a = math.pow(2, math.ceil(np.log2(x)))
        b = math.pow(2, math.floor(np.log2(x)))
        if abs(a - x) < abs(b - x):
            return a
        else:
            return b

    def handle_close(self, evt):
        '''
        Handles a plot close event.
        This will trigger a full shutdown of all other processes related to rsudp.
        '''
        self._controller.master_queue.put(helpers.msg_term())

    def handle_resize(self, evt=False):
        '''
        Handles a plot window resize event.
        This will allow the plot to resize dynamically.
        '''
        if evt:
            h = evt.height
        else:
            h = self.fig.get_size_inches()[1] * self.fig.dpi
        plt.tight_layout(pad=0, h_pad=0.1, w_pad=0,
                         rect=[0.02, 0.01, 0.98, 0.90 + 0.045 * (h / 1080)])  # [left, bottom, right, top]

    def set_icon(self):
        return self._controller.set_icon()

    def set_fig_manager(self, qt=None):
        '''
        Setting up figure manager and
        '''
        # update canvas and draw
        figManager = plt.get_current_fig_manager()
        if self._controller.kiosk:
            figManager.full_screen_toggle()
        else:
            if self._controller.fullscreen:  # set fullscreen
                if qt:  # maximizing in Qt
                    figManager.window.showMaximized()
                else:  # maximizing in Tk
                    figManager.resize(*figManager.window.maxsize())


    def init_plot(self, qt=None):
        '''
        Initialize plot elements and calculate parameters.
        '''
        self.fig = plt.figure(figsize=(11, 3 * self.num_chans))
        self.fig.canvas.mpl_connect('close_event', self.handle_close)
        self.fig.canvas.mpl_connect('resize_event', self.handle_resize)

        if qt:
            self.fig.canvas.window().statusBar().setVisible(False)  # remove bottom bar
        self.fig.canvas.manager.set_window_title('%s.%s - Raspberry Shake Monitor' % (self.net, self.stn))
        self.fig.patch.set_facecolor(self.bgcolor)  # background color
        self.fig.suptitle('%s.%s live output%s'  # title
                          % (self.net, self.stn, self.event_text),
                          fontsize=14, color=self.fgcolor, x=0.52)
        self.ax, self.lines = [], []  # list for subplot axes and lines artists
        self.mult = 1  # spectrogram selection multiplier
        if self.spectrogram:
            self.mult = 2  # 2 if user wants a spectrogram else 1
            if self.seconds > 60:
                self.per_lap = 0.9  # if axis is long, spectrogram overlap can be shorter
            else:
                self.per_lap = 0.975  # if axis is short, increase resolution
            # set spectrogram parameters
            self.nfft1 = self.nearest_pow_2(self.sps)
            self.nlap1 = self.nfft1 * self.per_lap

    def init_axes(self, i):
        '''
        Initialize plot axes.
        '''
        if i == 0:
            # set up first axes (axes added later will share these x axis limits)
            self.ax.append(self.fig.add_subplot(self.num_chans * self.mult,
                                                1, 1, label=str(1)))
            self.ax[0].set_facecolor(self.bgcolor)
            self.ax[0].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)
            self.ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self.ax[0].yaxis.set_major_formatter(EngFormatter(unit='%s' % self.unit.lower()))
            if self.spectrogram:
                self.ax.append(self.fig.add_subplot(self.num_chans * self.mult,
                                                    1, 2, label=str(2)))  # , sharex=ax[0]))
                self.ax[1].set_facecolor(self.bgcolor)
                self.ax[1].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)
        else:
            # add axes that share either lines or spectrogram axis limits
            s = i * self.mult  # plot selector
            # add a subplot then set colors
            self.ax.append(self.fig.add_subplot(self.num_chans * self.mult,
                                                1, s + 1, sharex=self.ax[0], label=str(s + 1)))
            self.ax[s].set_facecolor(self.bgcolor)
            self.ax[s].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)
            self.ax[s].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self.ax[s].yaxis.set_major_formatter(EngFormatter(unit='%s' % self.unit.lower()))
            if self.spectrogram:
                # add a spectrogram and set colors
                self.ax.append(self.fig.add_subplot(self.num_chans * self.mult,
                                                    1, s + 2, sharex=self.ax[1], label=str(s + 2)))
                self.ax[s + 1].set_facecolor(self.bgcolor)
                self.ax[s + 1].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)


    def _format_axes(self):
        '''
        Setting up axes and artists.
        '''
        # calculate times
        start = np.datetime64(self._controller.stream[0].stats.endtime
                              ) - np.timedelta64(self.seconds, 's')  # numpy time
        end = np.datetime64(self._controller.stream[0].stats.endtime)  # numpy time

        im = mpimg.imread(pr.resource_filename('rsudp', os.path.join('img', 'version1-01-small.png')))
        self.imax = self.fig.add_axes([0.015, 0.944, 0.2, 0.056], anchor='NW')  # [left, bottom, right, top]
        self.imax.imshow(im, aspect='equal', interpolation='sinc')
        self.imax.axis('off')
        # set up axes and artists
        for i in range(self.num_chans):  # create lines objects and modify axes
            if len(self._controller.stream[i].data) < int(self.sps * (1 / self.per_lap)):
                comp = 0  # spectrogram offset compensation factor
            else:
                comp = (1 / self.per_lap) ** 2  # spectrogram offset compensation factor
            r = np.arange(start, end, np.timedelta64(int(1000 / self.sps), 'ms'))[-len(
                self._controller.stream[i].data[int(-self.sps * (self.seconds - (comp / 2))):-int(self.sps * (comp / 2))]):]
            mean = int(round(np.mean(self._controller.stream[i].data)))
            # add artist to lines list
            self.lines.append(self.ax[i * self.mult].plot(r,
                                                          np.nan * (np.zeros(len(r))),
                                                          label=self._controller.stream[i].stats.channel, color=self.linecolor,
                                                          lw=0.45)[0])
            # set axis limits
            self.ax[i * self.mult].set_xlim(left=start.astype(datetime),
                                            right=end.astype(datetime))
            self.ax[i * self.mult].set_ylim(bottom=np.min(self._controller.stream[i].data - mean)
                                                   - np.ptp(self._controller.stream[i].data - mean) * 0.1,
                                            top=np.max(self._controller.stream[i].data - mean)
                                                + np.ptp(self._controller.stream[i].data - mean) * 0.1)
            # we can set line plot labels here, but not imshow labels
            ylabel = self._controller.stream[i].stats.units.strip().capitalize() if (' ' in self._controller.stream[i].stats.units) else \
            self._controller.stream[i].stats.units
            self.ax[i * self.mult].set_ylabel(ylabel, color=self.fgcolor)
            self.ax[i * self.mult].legend(loc='upper left')  # legend and location
            if self.spectrogram:  # if the user wants a spectrogram, plot it
                # add spectrogram to axes list
                sg = self.ax[1].specgram(self._controller.stream[i].data, NFFT=8, pad_to=8,
                                         Fs=self.sps, noverlap=7, cmap='inferno',
                                         xextent=(self.seconds - 0.5, self.seconds))[0]
                self.ax[1].set_xlim(0, self.seconds)
                self.ax[i * self.mult + 1].set_ylim(0, int(self.sps / 2))
                self.ax[i * self.mult + 1].imshow(np.flipud(sg ** (1 / float(10))), cmap='inferno',
                                                  extent=(self.seconds - (1 / (self.sps / float(len(self._controller.stream[i].data)))),
                                                          self.seconds, 0, self.sps / 2), aspect='auto')

