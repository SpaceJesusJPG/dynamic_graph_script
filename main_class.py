import time
from collections import deque
from datetime import timedelta as td

import matplotlib as mpl
import matplotlib.animation as animation
import matplotlib.pyplot as plt

from configuration import configuration

LIM = 100


class DynamicGraph:

    mpl.rcParams["toolbar"] = "None"

    def __init__(self):
        self.data_dir, self.file_name, self.short_name = configuration()
        self.cached_time = None
        self.fig, self.ax = plt.subplots()
        self.xs, self.ys = deque([None], maxlen=LIM), deque([None], maxlen=LIM)
        (self.ln,) = self.ax.plot([1,2,3], [1,2,10])
        self.pointer = 216

    def reader(self):
        n_xdata, n_ydata = [], []
        data = {}
        new_time = None
        with open(f"{self.data_dir}/{self.file_name}", "r") as f:
            f.seek(self.pointer)
            for line in f:
                rows = line.strip("\n").split()
                if rows:
                    data[rows[0]] = rows[1]
            self.pointer = f.tell()
        if self.cached_time and data.keys():
            if self.cached_time < list(data.keys())[-1]:
                new_time = list(
                    filter(lambda x: x > self.cached_time, list(data.keys()))
                )
        elif self.cached_time is None and data.keys():
            new_time = list(data.keys())
            self.cached_time = list(data.keys())[-1]
        if new_time:
            self.cached_time = new_time[-1]
            for time in new_time:
                n_xdata.append(float(time))
                n_ydata.append(float(data[time]))
        return n_xdata, n_ydata

    def animate(self, *args):
        new_data = self.reader()
        self.xs.extend(new_data[0])
        self.ys.extend(new_data[1])
        self.ln.set_data(self.xs, self.ys)
        self.ax.relim()
        self.ax.autoscale_view(True, True, True)
        if self.cached_time == "86380.000":
            old_dir, old_name, old_file_name = (
                self.data_dir,
                self.short_name,
                self.file_name,
            )
            self.data_dir, self.file_name, self.short_name = configuration(
                old_dir, old_name
            )
            if old_file_name != self.file_name:
                self.cached_time = None
                self.pointer = 0
                self.xs.clear()
                self.ys.clear()
                plt.title(self.file_name.strip(".txt"))
        return self.ln, self.ax

    def time_format_func(self, x, pos=None):
        x = str(td(seconds=x))
        return x[:-3]

    def show(self):
        self.ax.xaxis.set_major_formatter(self.time_format_func)
        plt.xlabel("Время")
        plt.ylabel("Амплитуда")
        plt.title(self.file_name.strip(".txt"))
        self.anim = animation.FuncAnimation(self.fig, self.animate, interval=2000)
        self.fig.autofmt_xdate()
        plt.show()
