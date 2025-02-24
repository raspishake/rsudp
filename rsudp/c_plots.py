import os, sys, platform
import pkg_resources as pr
import time
import math
import numpy as np
from datetime import datetime, timedelta
from obspy.signal.trigger import recursive_sta_lta, trigger_onset
import rsudp.raspberryshake as rs
from rsudp import printM, printW, printE, get_scap_dir, helpers
from rsudp.test import TEST
import linecache
sender = 'plot.py'
QT = False
QtGui = False
PhotoImage = False
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

ICON = 'icon.ico'
ICON2 = 'icon.png'


class AbcPlot():
    def __init__(self, deconv=None, testing=False):
        self.sender = "PlotAbc"
        if MPL == False:
            sys.stdout.flush()
            sys.exit()
        if QT == False:
            printW(f'Running on {platform.machine()} machine, using Tk instead of Qt', self.sender)

        self.ax = None
        self.fig = None
        self.unit = None
        self.units = None
        self.lines = None
        self.deconv = None
        self.controller = None

        self.kiosk = False
        self.testing = testing
        self.fullscreen = False
        self.spectrogram = False

        self.sps = 0
        self.stn = rs.stn
        self.net = rs.net
        self.mult = 0
        self.nfft1 = 0
        self.nlap1 = 0
        self.per_lap = 1
        self.figure_num = 0

        # Plot stuff
        self.bgcolor = '#202530'    # background
        self.fgcolor = '0.8'        # axis and label color
        self.linecolor = '#c28285'  # seismogram color

        self._set_deconv(deconv)

    def _set_deconv(self, deconv):
        '''
        This function sets the deconvolution units. Allowed values are as follows:

        .. |ms2| replace:: m/s\\ :sup:`2`\\

        - ``'VEL'`` - velocity (m/s)
        - ``'ACC'`` - acceleration (|ms2|)
        - ``'GRAV'`` - fraction of acceleration due to gravity (g, or 9.81 |ms2|)
        - ``'DISP'`` - displacement (m)
        - ``'CHAN'`` - channel-specific unit calculation, i.e. ``'VEL'`` for geophone channels and ``'ACC'`` for accelerometer channels

        :param str deconv: ``'VEL'``, ``'ACC'``, ``'GRAV'``, ``'DISP'``, or ``'CHAN'``
        '''
        self.deconv = deconv if (deconv in rs.UNITS) else None
        if self.deconv and rs.inv:
            self.deconv = deconv.upper()
            if self.deconv in rs.UNITS:
                self.units = rs.UNITS[self.deconv][0]
                self.unit = rs.UNITS[self.deconv][1]
            printM('Signal deconvolution set to %s' % (self.deconv), self.sender)
        else:
            self.units = rs.UNITS['CHAN'][0]
            self.unit = rs.UNITS['CHAN'][1]
            self.deconv = None
        printM('Seismogram units are %s' % (self.units), self.sender)

    def set_sps(self):
        '''
        Get samples per second from the main library.
        '''
        self.sps = rs.sps

    def handle_close(self, evt):
        '''
        Handles a plot close event.
        This will trigger a full shutdown of all other processes related to rsudp.
        '''
        self.controller.master_queue.put(helpers.msg_term())

    def handle_resize(self, evt=None):
        '''
        Handles a plot window resize event.
        This will allow the plot to resize dynamically.
        '''
        if evt:
            h = evt.height
        else:
            h = self.fig.get_size_inches()[1] * self.fig.dpi
        plt.tight_layout(pad=0, h_pad=0.1, w_pad=0, rect=[0.02, 0.01, 0.98, 0.90 + 0.045 * (h / 1080)])  # [left, bottom, right, top]

    def deconvolve(self):
        '''
        Send the streams to the central library deconvolve function.
        '''
        helpers.deconvolve(self)

    def savefig(self, event_time=rs.UTCDateTime.now(), event_time_str=rs.UTCDateTime.now().strftime('%Y-%m-%d-%H%M%S')):
        '''
        Saves the figure and puts an IMGPATH message on the master queue.
        This message can be used to upload the image to various services.

        :param obspy.core.utcdatetime.UTCDateTime event_time: Event time as an obspy UTCDateTime object. Defaults to ``UTCDateTime.now()``.
        :param str event_time_str: Event time as a string, in the format ``'%Y-%m-%d-%H%M%S'``. This is used to set the filename.
        '''
        figname = os.path.join(get_scap_dir(), '%s-%s.png' % (self.stn, event_time_str))
        elapsed = rs.UTCDateTime.now() - event_time
        if int(elapsed) > 0:
            printM(f'Saving png {elapsed} seconds after alarm', sender=self.sender)
        plt.savefig(figname, facecolor=self.fig.get_facecolor(), edgecolor='none')
        printM(f'Saved {figname}', sender=self.sender)
        printM(f'{self.sender} thread has saved an image, sending IMGPATH message to queues', sender=self.sender)
        # imgpath requires a UTCDateTime and a string figure path
        self.controller.master_queue.put(helpers.msg_imgpath(event_time, figname))

    def figloop(self):
        """
        Let some time elapse in order for the plot canvas to draw properly.
        Must be separate from :py:func:`update_plot()` to avoid a broadcast error early in plotting.
        """
        self.fig.canvas.start_event_loop(0.005)

    def set_fig_title(self, events):
        '''
        Sets the figure title back to something that makes sense for the live viewer.
        '''
        self.fig.suptitle(f'Raspberry Shake {self.stn} Live Data - Detected Events: {events}', fontsize=14, color=self.fgcolor, x=0.52)

    def setup_fig_manager(self):
        '''
        Setting up figure manager and
        '''
        # update canvas and draw
        figManager = plt.get_current_fig_manager()
        if self.kiosk:
            figManager.full_screen_toggle()
        else:
            if self.fullscreen:  # set fullscreen
                if QT:  # maximizing in Qt
                    figManager.window.showMaximized()
                else:  # maximizing in Tk
                    figManager.resize(*figManager.window.maxsize())

    def nearest_pow_2(self, x):
        """
        Find power of two nearest to x

        >>> _nearest_pow_2(3)
        2.0
        >>> _nearest_pow_2(15)
        16.0

        :type x: float
        :param x: Number
        :rtype: Int
        :return: Nearest power of 2 to x

        Adapted from the `obspy <https://obspy.org>`_ library
        """
        a = math.pow(2, math.ceil(np.log2(x)))
        b = math.pow(2, math.floor(np.log2(x)))
        return a if abs(a - x) < abs(b - x) else b

    def getq(self, d):
        raise NotImplemented("Method getq must be implemented.")

    def setup(self, controller, *args, **kwargs):
        raise NotImplemented("Method setup must be implemented.")

    def main(self, i, u, *args, **kwargs):
        raise NotImplemented("Method main must be implemented.")


class Plot(AbcPlot):
    '''
    .. role:: json(code)
        :language: json

    GUI plotting algorithm, compatible with both Qt5 and TkAgg backends (see :py:func:`matplotlib.use`).
    This module can plot seismogram data from a list of 1-4 Shake channels, and calculate and display a spectrogram beneath each.

    By default the plotted :json:`"duration"` in seconds is :json:`30`.
    The plot will refresh at most once per second, but slower processors may take longer.
    The longer the duration, the more processor power it will take to refresh the plot,
    especially when the spectrogram is enabled.
    To disable the spectrogram, set :json:`"spectrogram"` to :json:`false` in the settings file.
    To put the plot into fullscreen window mode, set :json:`"fullscreen"` to :json:`true`.
    To put the plot into kiosk mode, set :json:`"kiosk"` to :json:`true`.

    :param cha: channels to plot. Defaults to "all" but can be passed a list of channel names as strings.
    :type cha: str or list
    :param int seconds: number of seconds to plot. Defaults to 30.
    :param int refresh_interval: number of seconds for run main loop. If set, then time will be counted. Otherwise,
    iterations without delay will be counted. Defaults to 0.
    :param bool spectrogram: whether to plot the spectrogram. Defaults to True.
    :param bool fullscreen: whether to plot in a fullscreen window. Defaults to False.
    :param bool kiosk: whether to plot in kiosk mode (true fullscreen). Defaults to False.
    :param deconv: whether to deconvolve the signal. Defaults to False.
    :type deconv: str or bool
    :param bool screencap: whether or not to save screenshots of events. Defaults to False.
    :param bool alert: whether to draw the number of events at startup. Defaults to True.
    :param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`
    :raise ImportError: if the module cannot import either of the Matplotlib Qt5 or TkAgg backends
    '''
    def __init__(self,
                 cha='all',
                 seconds=30,
                 spectrogram=True,
                 kiosk=False,
                 fullscreen=False,
                 filter_waveform=False,
                 filter_spectrogram=False,
                 filter_highpass=0,
                 filter_lowpass=45,
                 filter_corners=4,
                 logarithmic_y_axis=False,
                 spectrogram_freq_range=False,
                 upper_limit=50.0,
                 lower_limit=0.0,
                 alert=False,
                 screencap=False,
                 deconv=None,
                 testing=False):
        super().__init__(deconv=deconv, testing=testing)

        self.sender = 'Plot'
        self.alarm = False  # don't touch this
        self.alarm_reset = False  # don't touch this

        # Initialize Streams
        self.raw = rs.Stream()
        self.stream = rs.Stream()
        self.stream_uf = rs.Stream()

        # New filter variables
        self.filter_waveform = filter_waveform
        self.filter_spectrogram = filter_spectrogram
        self.filter_highpass = filter_highpass
        self.filter_lowpass = filter_lowpass
        self.filter_corners = filter_corners

        # Logarithmic y axis
        self.logarithmic_y_axis = logarithmic_y_axis

        # Spectrogram range variables
        self.spectrogram_freq_range = spectrogram_freq_range
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

        # Events
        self.save = []
        self.events = 0
        self.save_pct = 0.7
        self.save_timer = 0
        self.event_text = ' - Detected Events: 0' if alert else ''
        self.screencap = screencap

        # Channels
        self.chans = []
        helpers.set_channels(self, cha)
        printM(f'Plotting {len(self.chans)} channels: {self.chans}', self.sender)
        self.totchns = rs.numchns
        self.num_chans = len(self.chans)

        self.seconds = seconds
        self.pkts_in_period = rs.tr * rs.numchns * self.seconds  # theoretical number of packets received in self.seconds

        # Modes
        self.kiosk = kiosk
        self.fullscreen = fullscreen
        self.spectrogram = spectrogram
        printM('Starting.', self.sender)

    def _eventsave(self):
        '''
        This function takes the next event in line and pops it out of the list,
        so that it can be saved and others preserved.
        Then, it sets the title to something having to do with the event,
        then calls the save figure function, and finally resets the title.
        '''
        self.save.reverse()
        event = self.save.pop()
        self.save.reverse()

        event_time_str = event[1].strftime('%Y-%m-%d-%H%M%S')  # event time for filename
        title_time_str = event[1].strftime('%Y-%m-%d %H:%M:%S.%f')[:22]  # pretty event time for plot

        # change title (just for a moment)
        self.fig.suptitle('%s Detected Event - %s UTC'  # title
                          % (self.stn, title_time_str),
                          fontsize=14, color=self.fgcolor, x=0.52)

        # save figure
        self.savefig(event_time=event[1], event_time_str=event_time_str)

        # reset title
        self.set_fig_title(self.events)

    def _init_plot(self):
        '''
        Initialize plot elements and calculate parameters.
        '''
        self.fig = plt.figure(self.figure_num, figsize=(11, 3 * self.num_chans))
        self.fig.canvas.mpl_connect('close_event', self.handle_close)
        self.fig.canvas.mpl_connect('resize_event', self.handle_resize)

        if QT:
            self.fig.canvas.window().statusBar().setVisible(False)  # remove bottom bar
        self.fig.canvas.manager.set_window_title('%s - Raspberry Shake Monitor' % (self.stn))
        self.fig.patch.set_facecolor(self.bgcolor)  # background color
        self.fig.suptitle('Raspberry Shake %s Live Data%s'  # title
                          % (self.stn, self.event_text),
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

    def _init_axes(self, i):
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
        start = np.datetime64(self.stream[0].stats.endtime
                              ) - np.timedelta64(self.seconds, 's')  # numpy time
        end = np.datetime64(self.stream[0].stats.endtime)  # numpy time

        im = mpimg.imread(pr.resource_filename('rsudp', os.path.join('img', 'version1-01-small.png')))
        self.imax = self.fig.add_axes([0.015, 0.944, 0.2, 0.056], anchor='NW')  # [left, bottom, right, top]
        self.imax.imshow(im, aspect='equal', interpolation='sinc')
        self.imax.axis('off')
        # set up axes and artists
        for i in range(self.num_chans):  # create lines objects and modify axes
            if len(self.stream[i].data) < int(self.sps * (1 / self.per_lap)):
                comp = 0  # spectrogram offset compensation factor
            else:
                comp = (1 / self.per_lap) ** 2  # spectrogram offset compensation factor
            r = np.arange(start, end, np.timedelta64(int(1000 / self.sps), 'ms'))[-len(
                self.stream[i].data[int(-self.sps * (self.seconds - (comp / 2))):-int(self.sps * (comp / 2))]):]
            mean = int(round(np.mean(self.stream[i].data)))
            # add artist to lines list
            self.lines.append(self.ax[i * self.mult].plot(r,
                                                          np.nan * (np.zeros(len(r))),
                                                          label=self.stream[i].stats.channel, color=self.linecolor,
                                                          lw=0.45)[0])
            # set axis limits
            self.ax[i * self.mult].set_xlim(left=start.astype(datetime),
                                            right=end.astype(datetime))
            self.ax[i * self.mult].set_ylim(bottom=np.min(self.stream[i].data - mean)
                                                   - np.ptp(self.stream[i].data - mean) * 0.1,
                                            top=np.max(self.stream[i].data - mean)
                                                + np.ptp(self.stream[i].data - mean) * 0.1)
            # we can set line plot labels here, but not imshow labels
            ylabel = self.stream[i].stats.units.strip().capitalize() if (' ' in self.stream[i].stats.units) else \
            self.stream[i].stats.units
            self.ax[i * self.mult].set_ylabel(ylabel, color=self.fgcolor)
            self.ax[i * self.mult].legend(loc='upper left')  # legend and location
            if self.filter_waveform:  # Display filter info text if filter for the waveform is enabled
                self.ax[i * self.mult].text(0.005, .05, 'Bandpass (' + str(self.filter_highpass) + ' - ' + str(
                    self.filter_lowpass) + ' Hz)',
                                            fontsize=8, color=self.fgcolor, horizontalalignment='left',
                                            verticalalignment='center',
                                            transform=self.ax[i * self.mult].transAxes)
            if self.spectrogram:  # if the user wants a spectrogram, plot it
                # add spectrogram to axes list
                sg = self.ax[1].specgram(self.stream[i].data, NFFT=8, pad_to=8,
                                         Fs=self.sps, noverlap=7, cmap='inferno',
                                         xextent=(self.seconds - 0.5, self.seconds))[0]
                self.ax[1].set_xlim(0, self.seconds)
                # spectrogram frequency range option
                if self.spectrogram_freq_range:
                    try:
                        # validate upper_limit
                        if self.upper_limit > 50:
                            raise ValueError("Upper limit cannot be greater than 50.")
                        if self.upper_limit < self.lower_limit:
                            raise ValueError("Upper limit cannot be less than the lower limit.")

                        # validate lower_limit
                        if self.lower_limit == 0:
                            y_min = 0
                        else:
                            # validate lower_limit for negative values
                            if self.lower_limit < 0:
                                raise ValueError("Lower limit cannot be negative.")
                            y_min = self.sps / (100 / self.lower_limit)
                        y_max = self.sps / (100 / self.upper_limit)
                    except ValueError as e:
                        print(f"Error: {e} Reverting to fallback values.")
                        # provide fallback values in case of error (optional)
                        y_max = int(self.sps / 2)
                        y_min = 0
                else:
                    y_max = int(self.sps / 2)
                    y_min = 0
                self.ax[i * self.mult + 1].set_ylim(y_min, y_max)
                self.ax[i * self.mult + 1].imshow(np.flipud(sg ** (1 / float(10))), cmap='inferno',
                                                  extent=(
                                                  self.seconds - (1 / (self.sps / float(len(self.stream[i].data)))),
                                                  self.seconds, y_min, y_max), aspect='auto')
                if self.logarithmic_y_axis:
                    custom_ticks = [0.5, 1, 2, 3, 5, 10, 20, 30, 50]
                    custom_labels = ['0.5', '1', '2', '3', '5', '10', '20', '30', '50']
                    self.ax[i * self.mult + 1].set_yscale('log')  # Apply logarithmic scale
                    self.ax[i * self.mult + 1].set_yticks(custom_ticks)
                    self.ax[i * self.mult + 1].set_yticklabels(custom_labels)
                    self.ax[i * self.mult + 1].tick_params(which='minor', color=self.bgcolor)
                    self.ax[i * self.mult + 1].set_ylim(10 ** (-0.25), (self.sps / 2))  # Avoid log(0)

    def _set_icon(self):
        '''
        Set RS plot icons.
        '''
        mgr = plt.get_current_fig_manager()
        ico = pr.resource_filename('rsudp', os.path.join('img', ICON))
        if QT:
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

    def _set_ch_specific_label(self, i):
        '''
        Set the formatter units if the deconvolution is channel-specific.
        '''
        if self.deconv and (self.deconv in ['CHAN']):
            ch = self.stream[i].stats.channel
            if ('HZ' in ch) or ('HN' in ch) or ('HE' in ch):
                unit = rs.UNITS['VEL'][1]
            elif ('EN' in ch):
                unit = rs.UNITS['ACC'][1]
            else:
                unit = rs.UNITS['CHAN'][1]
            self.ax[i * self.mult].yaxis.set_major_formatter(EngFormatter(unit='%s' % unit.lower()))

    def _draw_lines(self, i, start, end, mean):
        '''
        Updates the line data in the plot.

        :param int i: the trace number
        :param numpy.datetime64 start: start time of the trace
        :param numpy.datetime64 end: end time of the trace
        :param float mean: the mean of data in the trace
        '''
        comp = 1 / self.per_lap  # spectrogram offset compensation factor
        r = np.arange(start, end, np.timedelta64(int(1000 / self.sps), 'ms'))[-len(
            self.stream[i].data[int(-self.sps * (self.seconds - (comp / 2))):-int(self.sps * (comp / 2))]):]
        self.lines[i].set_ydata(
            self.stream[i].data[int(-self.sps * (self.seconds - (comp / 2))):-int(self.sps * (comp / 2))] - mean)
        self.lines[i].set_xdata(r)  # (1/self.per_lap)/2
        self.ax[i * self.mult].set_xlim(left=start.astype(datetime) + timedelta(seconds=comp * 1.5),
                                        right=end.astype(datetime))
        self.ax[i * self.mult].set_ylim(bottom=np.min(self.stream[i].data - mean)
                                               - np.ptp(self.stream[i].data - mean) * 0.1,
                                        top=np.max(self.stream[i].data - mean)
                                            + np.ptp(self.stream[i].data - mean) * 0.1)

    def _update_specgram(self, i: int, mean: float):
        '''
        Updates the spectrogram and its labels.

        :param int i: the trace number
        :param float mean: the mean of data in the trace
        '''
        self.nfft1 = self.nearest_pow_2(self.sps)  # FFTs run much faster if the number of transforms is a power of 2
        self.nlap1 = self.nfft1 * self.per_lap
        # When the number of data points is low, we just need to kind of fake it for a few fractions of a second
        # Replaced Stream with Stream_uf
        if len(self.stream_uf[i].data) < self.nfft1:
            self.nfft1 = 8
            self.nlap1 = 6
        sg = self.ax[i * self.mult + 1].specgram(self.stream_uf[i].data - mean,  # Replaced Stream with Stream_uf
                                                 NFFT=int(self.nfft1), pad_to=int(self.nfft1 * 4),
                                                 # previously self.sps*4),
                                                 Fs=self.sps, noverlap=int(self.nlap1))[0]  # meat & potatoes
        # incredibly important, otherwise continues to draw over old images (gets exponentially slower)
        self.ax[i * self.mult + 1].clear()
        # imshow to update the spectrogram
        self.ax[i * self.mult + 1].imshow(np.flipud(sg ** (1 / float(10))), cmap='inferno',
                                          extent=(self.seconds - (1 / (self.sps / float(len(self.stream_uf[i].data)))),
                                                  self.seconds, 0, self.sps / 2),
                                          aspect='auto')  # Replaced Stream with Stream_uf
        # some things that unfortunately can't be in the setup function:
        self.ax[i * self.mult + 1].tick_params(axis='x', which='both',
                                               bottom=False, top=False, labelbottom=False)
        self.ax[i * self.mult + 1].set_ylabel('Frequency (Hz)', color=self.fgcolor)
        self.ax[i * self.mult + 1].set_xlabel('Time (UTC)', color=self.fgcolor)
        # logarithmic y axis
        if self.logarithmic_y_axis:
            custom_ticks = [0.5, 1, 2, 3, 5, 10, 20, 30, 50]
            custom_labels = ['0.5', '1', '2', '3', '5', '10', '20', '30', '50']
            self.ax[i * self.mult + 1].set_xlim(0.25, self.seconds - 0.25)
            self.ax[i * self.mult + 1].set_yscale('log')
            self.ax[i * self.mult + 1].set_ylim(10 ** (-0.25), (self.sps / 2))
            self.ax[i * self.mult + 1].set_yticks(custom_ticks)
            self.ax[i * self.mult + 1].set_yticklabels(custom_labels)
            self.ax[i * self.mult + 1].tick_params(which='minor', color=self.bgcolor)
        # cloogy way to shift the spectrogram to line up with the seismogram
        self.ax[i * self.mult + 1].set_xlim(0.25, self.seconds - 0.25)
        if self.spectrogram_freq_range:
            try:
                # validate upper_limit
                if self.upper_limit > 50:
                    raise ValueError("Upper limit cannot be greater than 50.")
                if self.upper_limit < self.lower_limit:
                    raise ValueError("Upper limit cannot be less than the lower limit.")

                # validate lower_limit
                if self.lower_limit == 0:
                    y_min = 0
                else:
                    # validate lower_limit for negative values
                    if self.lower_limit < 0:
                        raise ValueError("Lower limit cannot be negative.")
                    y_min = self.sps / (100 / self.lower_limit)
                y_max = self.sps / (100 / self.upper_limit)

            except ValueError as e:
                print(f"Warning: {e} Reverting to fallback values.")
                y_max = int(self.sps / 2)
                y_min = 0
        else:
            y_max = int(self.sps / 2)
            y_min = 0
        self.ax[i * self.mult + 1].set_ylim(y_min, y_max)

        # display filter info text when spectrogram filtering/range is/are enabled
        text_content = ''
        if self.filter_spectrogram and self.spectrogram_freq_range:
            text_content = (
                    'Bandpass (' + str(self.filter_highpass) + ' - ' + str(self.filter_lowpass) + ' Hz) | '
                                                                                                  'Range (' + str(
                int(self.lower_limit)) + ' - ' + str(int(self.upper_limit)) + ' Hz)'
            )
        elif self.filter_spectrogram:
            text_content = 'Bandpass (' + str(self.filter_highpass) + ' - ' + str(self.filter_lowpass) + ' Hz)'
        elif self.spectrogram_freq_range:
            text_content = 'Range (' + str(int(self.lower_limit)) + ' - ' + str(int(self.upper_limit)) + ' Hz)'

        # only add text if there's content
        if text_content:
            self.ax[i * self.mult + 1].text(
                0.005, -0.06, text_content,
                fontsize=8, color=self.fgcolor, horizontalalignment='left', verticalalignment='center',
                transform=self.ax[i * self.mult + 1].transAxes)

    def update_plot(self):
        '''
        Redraw the plot with new data.
        Called on every nth loop after the plot is set up, where n is
        the number of channels times the data packet arrival rate in Hz.
        This has the effect of making the plot update once per second.
        '''
        obstart = self.stream[0].stats.endtime - timedelta(seconds=self.seconds)  # obspy time
        start = np.datetime64(self.stream[0].stats.endtime) - np.timedelta64(self.seconds, 's')  # numpy time
        end = np.datetime64(self.stream[0].stats.endtime)  # numpy time
        self.raw = self.raw.slice(starttime=obstart)  # slice the stream to the specified length (seconds variable)
        self.stream = self.stream.slice(starttime=obstart)  # slice the stream to the specified length (seconds variable)
        for i in range(self.num_chans):  # for each channel, update the plots
            mean = int(round(np.mean(self.stream[i].data)))
            self._draw_lines(i, start, end, mean)
            self._set_ch_specific_label(i)
            if self.spectrogram:
                self._update_specgram(i, mean)
            else:
                # also can't be in the setup function
                self.ax[i * self.mult].set_xlabel('Time (UTC)', color=self.fgcolor)

    def getq(self, d):
        '''
        Get data from the queue and test for whether it has certain strings.
        ALARM and TERM both trigger specific behavior.
        ALARM messages cause the event counter to increment, and if
        :py:data:`screencap==True` then aplot image will be saved when the
        event is :py:data:`self.save_pct` of the way across the plot.
        '''
        if 'TERM' in str(d):
            plt.close()
            if 'SELF' in str(d):
                printM('Plot has been closed, plot thread will exit.', self.sender)
            self.alive = False
            self.controller.alive = False
            rs.producer = False

        elif 'ALARM' in str(d):
            self.events += 1  # add event to count
            self.save_timer -= 1  # don't push the save time forward if there are a large number of alarm events
            event = [self.save_timer + int(self.save_pct * self.pkts_in_period),
                     helpers.fsec(helpers.get_msg_time(d))]  # event = [save after count, datetime]
            self.last_event_str = '%s UTC' % (event[1].strftime('%Y-%m-%d %H:%M:%S.%f')[:22])
            printM('Event time: %s' % (self.last_event_str), sender=self.sender)  # show event time in the logs
            if self.screencap:
                printM('Saving png in about %i seconds' % (self.save_pct * (self.seconds)), self.sender)
                self.save.append(event)  # append
            self.fig.suptitle('Raspberry Shake %s Live Data - Detected Events: %s'  # title
                              % (self.stn, self.events),
                              fontsize=14, color=self.fgcolor, x=0.52)
            self.fig.canvas.manager.set_window_title('(%s) %s - Raspberry Shake Monitor' % (self.events, self.stn))

        if rs.getCHN(d) in self.chans:
            self.raw = rs.update_stream(
                stream=self.raw, d=d, fill_value='latest')
            return True
        else:
            return False

    def setup(self, controller, *args, **kwargs):
        """
        Sets up the plot. Quite a lot of stuff happens in this function.
        Matplotlib backends are not threadsafe, so things are a little weird.
        See code comments for details.
        """
        self.controller = controller
        for i in range((self.totchns) * 2):  # fill up a stream object
            self.controller.get_queue()
        self.set_sps()
        self.deconvolve()
        # instantiate a figure and set basic params
        self._init_plot()

        for i in range(self.num_chans):
            self._init_axes(i)

        for axis in self.ax:
            # set the rest of plot colors
            plt.setp(axis.spines.values(), color=self.fgcolor)
            plt.setp([axis.get_xticklines(), axis.get_yticklines()], color=self.fgcolor)

        # rs logos
        self._set_icon()
        # draw axes
        self._format_axes()
        self.handle_resize()
        # setup figure manager
        self.setup_fig_manager()
        # draw plot, loop, and resize the plot
        plt.draw()  # draw the canvas
        self.fig.canvas.start_event_loop(0.005)  # wait for canvas to update
        self.handle_resize()
        return

    def main(self, i, u, *args, **kwargs):
        '''
        The main loop in the :py:func:`rsudp.c_plot_controller.PlotsController.run`.

        :param int i: number of plot events without clearing the linecache
        :param int u: queue blocking counter
        :return: number of plot events without clearing the linecache and queue blocking counter
        :rtype: int, int
        '''
        if i > 10:
            linecache.clearcache()
            i = 0
        else:
            i += 1

        self.raw = rs.copy(self.raw)  # and could eventually crash the machine
        self.stream = rs.copy(self.stream)  # essential, otherwise the stream has a memory leak
        self.stream_uf = rs.copy(self.stream_uf)  # Applied the same fix/patch as above to prevent memory leak
        self.deconvolve()
        self.stream.detrend(type='demean')  # Detrend the stream to support filtering for a non-deconvolved stream
        self.stream_uf = self.stream.copy()  # Make an copy of the unfiltered Stream to be used with the Spectrogram
        if self.filter_waveform:  # filter stream if waveform filtering is enabled.
            self.stream.filter('bandpass', freqmin=self.filter_highpass, freqmax=self.filter_lowpass,
                               corners=self.filter_corners)  # Filter for the waveform.
        if self.filter_spectrogram:  # filter stream if spectrogram filtering is enabled.
            self.stream_uf.filter('bandpass', freqmin=self.filter_highpass, freqmax=self.filter_lowpass,
                                  corners=self.filter_corners)
        self.update_plot()
        if u >= 0:  # avoiding a matplotlib broadcast error
            self.figloop()

        if self.save:
            # save the plot
            if (self.save_timer > self.save[0][0]):
                self._eventsave()
        u = 0
        time.sleep(0.005)  # wait a ms to see if another packet will arrive
        return i, u


class PlotAlert(Plot):
    def __init__(self,
                 cha='all',
                 seconds=30,
                 filter_waveform=False,
                 filter_spectrogram=False,
                 filter_highpass=0,
                 filter_lowpass=45,
                 filter_corners=4,
                 logarithmic_y_axis=False,
                 spectrogram=True,
                 kiosk=False,
                 fullscreen=False,
                 spectrogram_freq_range=False,
                 upper_limit=50.0,
                 lower_limit=0.0,
                 alert=False,
                 screencap=False,
                 deconv=None,
                 testing=False,
                 s_line_color="b",
                 e_line_color="r"):
        """
        A separate Plot for displaying trigger alert intervals.
        """
        super().__init__(cha=cha,
                         seconds=seconds,
                         spectrogram=spectrogram,
                         kiosk=kiosk,
                         fullscreen=fullscreen,
                         filter_waveform=filter_waveform,
                         filter_spectrogram=filter_spectrogram,
                         filter_highpass=filter_highpass,
                         filter_lowpass=filter_lowpass,
                         filter_corners=filter_corners,
                         logarithmic_y_axis=logarithmic_y_axis,
                         spectrogram_freq_range=spectrogram_freq_range,
                         upper_limit=upper_limit,
                         lower_limit=lower_limit,
                         alert=alert,
                         screencap=screencap,
                         deconv=deconv,
                         testing=testing)

        self.sender = "PlotAlert"
        self.s_line_color = s_line_color
        self.e_line_color = e_line_color
        self.s_lines = []
        self.e_lines = []

        printM('Starting.', self.sender)

    def _draw_lines(self, i, start, end, mean):
        super()._draw_lines(i, start, end, mean)
        for line in self.s_lines:
            self.ax[i * self.mult].axvline(line, color=self.s_line_color, linewidth=2)
        for line in self.e_lines:
            self.ax[i * self.mult].axvline(line, color=self.e_line_color, linewidth=2)

    def getq(self, d):
        '''
        Get data from the queue and test for whether it has certain strings.
        '''
        if 'ALARM' in str(d):
            self.s_lines.append(np.datetime64(helpers.fsec(helpers.get_msg_time(d))))
        elif 'RESET' in str(d):
            self.e_lines.append(np.datetime64(helpers.fsec(helpers.get_msg_time(d))))
        return super().getq(d)

    def setup(self, controller, *args, **kwargs):
        """
        Sets up the plot. Quite a lot of stuff happens in this function.
        Matplotlib backends are not threadsafe, so things are a little weird.
        See code comments for details.
        """
        return super().setup(controller, *args, **kwargs)

    def main(self, i, u, *args, **kwargs):
        '''
        The main loop in the :py:func:`rsudp.c_plot_controller.PlotsController.run`.

        :param int i: number of plot events without clearing the linecache
        :param int u: queue blocking counter
        :return: number of plot events without clearing the linecache and queue blocking counter
        :rtype: int, int
        '''
        return super().main(i, u, *args, **kwargs)
