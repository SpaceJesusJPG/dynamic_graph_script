import sys
import time
import logging
from collections import deque
from datetime import timedelta as td
from itertools import cycle

import matplotlib as mpl
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from configuration import configuration

LIM = 100
LST = ["JJY", "NPM", "NWC", "JJI"]


class DynamicGraph:


    mpl.rcParams["toolbar"] = "None"

    def __init__(self):
        self.stop = False
        self.stop_read = False
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.handler = logging.StreamHandler(sys.stdout)
        self.formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        self.retries = 0
        self.retries_read = 0
        self.pointer = 0
        self.pool = cycle(LST)
        self.data_dir, self.file_name = configuration()
        self.short_name = self.file_name[:3]
        self.cached_time = None
        self.fig, self.ax = plt.subplots()
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95)
        self.ax.grid(
            which = 'major',
            ls = '-',
            lw = 0.5,
            color = '#3B3D3A'
        )
        self.xs, self.ys = deque([None], maxlen=LIM), deque([None], maxlen=LIM)
        (self.ln,) = self.ax.plot([], [], color='black')

    def reader(self):
        n_xdata, n_ydata = [], []
        data = {}
        new_time = None
        with open(f"{self.data_dir}/{self.file_name}", "r") as f:
            f.seek(self.pointer)
            for line in f:
                if line[0] == "%":
                    continue
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
            if self.stop_read == True:
                self.stop_read = False
                self.retries_read = 0
                self.logger.info('Новые данные получены')
            self.cached_time = new_time[-1]
            for time in new_time:
                n_xdata.append(float(time))
                n_ydata.append(float(data[time]))
        elif self.stop_read == False:
            if self.retries_read < 3:
                self.retries_read += 1
            if self.retries_read == 3:
                self.logger.error(f'Нет новых данных, последние данные: {td(seconds=float(self.cached_time))}, были получены 1 минуту назад')
                self.stop_read = True
        return n_xdata, n_ydata

    def animate(self, *args):
        if self.stop == False:
            new_data = self.reader()
            self.xs.extend(new_data[0])
            self.ys.extend(new_data[1])
            self.ln.set_data(self.xs, self.ys)
            self.ax.relim()
            self.ax.autoscale_view(True, True, True)
        if self.cached_time == "86380.000":
            if self.retries > 10:
                self.logger.error(f'Новый файл не найден, последний файл: {self.short_name} {self.file_name[9:11]}.{self.file_name[7:9]}.{self.file_name[3:7]}')
                self.stop = True
                self.retries = 0
            old_dir, old_file_name, old_short_name = (
                self.data_dir,
                self.file_name,
                self.short_name,
            )
            self.data_dir, self.file_name = configuration(old_dir, old_short_name)
            self.shot_name = self.file_name[:3]
            if old_file_name != self.file_name:
                self.cached_time = None
                self.pointer = 0
                self.xs.clear()
                self.ys.clear()
                plt.title(
                    f"{self.short_name} {self.file_name[9:11]}.{self.file_name[7:9]}.{self.file_name[3:7]}"
                )
                self.stop = False
            elif self.stop == False:
                self.retries += 1
        return self.ln, self.ax

    def go_to_next(self, event):
        old_dir = self.data_dir
        self.data_dir, self.file_name = configuration(old_dir, next(self.pool))
        self.short_name = self.file_name[:3]
        self.cached_time = None
        self.pointer = 0
        self.xs.clear()
        self.ys.clear()
        plt.title(
            f"{self.short_name} {self.file_name[9:11]}.{self.file_name[7:9]}.{self.file_name[3:7]}"
        )

    def time_format_func(self, x, pos=None):
        x = str(td(seconds=x))
        return x[:-3]

    def show(self):
        self.ax.xaxis.set_major_formatter(self.time_format_func)
        plt.xlabel("Время")
        plt.ylabel("Амплитуда")
        ax_button = plt.axes([0.5, 0.9, 0.05, 0.05])
        next_button = Button(ax_button, "->", color="white", hovercolor="grey")
        next_button.on_clicked(self.go_to_next)
        plt.title(
            f"{self.short_name} {self.file_name[9:11]}.{self.file_name[7:9]}.{self.file_name[3:7]}")
        self.anim = animation.FuncAnimation(self.fig, self.animate, interval=1000)
        self.fig.autofmt_xdate()
        plt.show()
