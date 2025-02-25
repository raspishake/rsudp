import sys, time
import rsudp.raspberryshake as rs
from rsudp import printM


class PlotsController():
    def __init__(self, q, plots, seconds=30, refresh_interval=0):
        '''
        A controller that manages and coordinates multiple plots.
        Manages and extracts data from queue and distributes it to plots.
        It is also responsible for managing main cycle that updates and draw changes across all plots.
        To ensure compatibility, any plot implemented by the class must be a subclass of AbcPlot, which is defined in the c_plots.py file.
        This inheritance guarantees that the necessary methods and functionalities required for plotting are properly implemented.

        :param int seconds: number of seconds to plot. Defaults to 30.
        :param int refresh_interval: number of seconds for run main loop. If set, then time will be counted. Otherwise,
        iterations without delay will be counted. Defaults to 0.
        :param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`
        '''
        self._plots = plots

        self.queue = q
        self.seconds = seconds
        self.master_queue = None # careful with this, this goes directly to the master consumer. gets set by main thread.

        self.sender = 'PlotsController'
        self.alive = True
        self.save_timer = 0
        self.refresh_interval = refresh_interval
        self.delay = rs.tr if (self._plots[0].spectrogram) else 1
        self.delay = 0.5 if (self._plots[0].chans == ['SHZ']) else self.delay

        printM('Starting.', self.sender)

    def qu(self, u):
        '''
        Get a queue object and increment the queue counter.
        This is a way to figure out how many channels have arrived in the queue.

        :param int u: queue blocking counter
        :return: queue blocking counter
        :rtype: int
        '''
        u += 1 if self.get_queue() else 0
        return u

    def get_queue(self):
        '''
        Get data from the queue and send it to all plots.
        '''
        d = self.queue.get()
        self.queue.task_done()
        results = []
        for plot in self._plots:
            results.append(plot.getq(d))
        return results[0]

    def run(self):
        self.get_queue()
        for plot in self._plots:
            plot.setup(self)

        n = 0  # number of iterations without plotting
        i = 0  # number of plot events without clearing the linecache
        u = -1  # number of blocked queue calls (must be -1 at startup)
        while True:  # main loop
            refresh_start = time.time()
            while True:  # sub loop
                if self.alive == False:  # break if the user has closed the plot
                    break
                n += 1
                self.save_timer += 1
                if self.queue.qsize() > 0:
                    self.get_queue()
                    time.sleep(0.009)  # wait a ms to see if another packet will arrive
                else:
                    u = self.qu(u)
                    refresh_current = time.time()
                    if not self.refresh_interval and n > (self.delay * rs.numchns):
                        n = 0
                        break
                    elif self.refresh_interval and refresh_current - refresh_start > self.refresh_interval:
                        n = 0
                        break
            if self.alive == False:  # break if the user has closed the plot
                printM('Exiting.', self.sender)
                break
            results = []
            for plot in self._plots:
                results.append(plot.main(i, u))
            sys.stdout.flush()
            i, u = results[0]
        return