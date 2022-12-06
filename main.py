import logging
import sys
from collections import deque
from datetime import timedelta as td

import matplotlib as mpl
import matplotlib.animation as animation
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.widgets import Button

from configuration import dialog_window, get_file_name

LIM = 500
CHN = ["JJI", "NPM", "NWC", "JJY", "NTS"]
COLOR = ["green", "blue", "red", "white", "yellow"]
FONT = {"weight": "bold", "size": 12}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

mpl.rc("xtick", labelsize=12)
mpl.rc("ytick", labelsize=12)
mpl.rcParams["toolbar"] = "None"
plt.style.use("dark_background")
fig, ax = plt.subplots()
fig.subplots_adjust(left=0.06, right=0.95, bottom=0.05, top=0.95)
plt.xlabel("Время, часы", fontdict=FONT)
plt.ylabel("Амплитуда, дБ", fontdict=FONT)
dir = dialog_window()


class Reader:
    def __init__(self, dir, short_name):
        self.data_dir = dir
        self.short_name = short_name
        self.file_name = get_file_name(short_name, self.data_dir)
        self.cached_time = None
        self.stop = False
        self.stop_read = False
        self.retries_read = 0
        self.retries = 0
        self.pointer = 0

    def read(self):
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
            if self.stop_read:
                self.stop_read = False
                self.retries_read = 0
                logger.info("Новые данные получены")
            self.cached_time = new_time[-1]
            for time in new_time:
                n_xdata.append(float(time))
                n_ydata.append(float(data[time]))
        elif not self.stop_read and self.cached_time:
            if self.retries_read < 3:
                self.retries_read += 1

            if self.retries_read == 3:
                logger.error(
                    f"В файле {self.file_name} нет новых данных, последние данные: {td(seconds=float(self.cached_time))}"
                )
                self.stop_read = True

        if self.cached_time == "86380.000":
            if self.retries > 10:
                logger.error(
                    f"Новый файл датчика {self.short_name} не найден, последний файл от: {self.file_name[9:11]}.{self.file_name[7:9]}.{self.file_name[3:7]}"
                )
                self.stop = True
                self.retries = 0
            old_file_name = self.file_name
            self.file_name = get_file_name(self.short_name, self.data_dir)

            if old_file_name != self.file_name:
                ax.set_title(
                    f"{self.file_name[9:11]}.{self.file_name[7:9]}.{self.file_name[3:7]}"
                )
                self.cached_time = None
                self.pointer = 0
                self.stop = False
            elif not self.stop:
                self.retries += 1

        return n_xdata, n_ydata


class Container:
    def __init__(self, reader_class, color=None):
        self.reader_class = reader_class
        self.xs = deque([None], maxlen=LIM)
        self.ys = deque([None], maxlen=LIM)
        self.lines = ax.plot([], [], label=reader_class.short_name, color=color)

    def clear(self):
        self.xs.clear()
        self.ys.clear()


class Loop:
    def __init__(self, container_list):
        self.container_list = container_list

    def loop(self, i):
        for container in self.container_list:
            x, y = container.reader_class.read()
            container.xs.extend(x)
            container.ys.extend(y)
            for line in container.lines:
                line.set_data(container.xs, container.ys)
            if 86380.0 in x:
                container.clear()
        ax.relim()
        ax.autoscale_view(True, True, True)


def time_format_func(x, pos=None):
    x = str(td(seconds=x))
    return x[:-3]


def full_screen_button(event):
    mng = plt.get_current_fig_manager()
    mng.full_screen_toggle()


container_list = [Container(Reader(dir, chn), clr) for chn, clr in zip(CHN, COLOR)]
loopclass = Loop(container_list)

file_name = container_list[0].reader_class.file_name
ax.set_title(f"{file_name[9:11]}.{file_name[7:9]}.{file_name[3:7]}")

locator = mdates.AutoDateLocator(minticks=4, maxticks=32)
ax.xaxis.set_major_locator(locator)
ax.yaxis.set_major_locator(ticker.LinearLocator(13))
ax.xaxis.set_major_formatter(time_format_func)

ax_button = plt.axes([0.96, 0.94, 0.04, 0.06])
next_button = Button(ax_button, label="←↕→", color="black", hovercolor="grey")
next_button.on_clicked(full_screen_button)

ax.legend(ncol=2, title="UltraMSK", fontsize=17, title_fontsize="17")
ax.grid(which="major", ls="-", lw=0.5, color="#373737")

anim = animation.FuncAnimation(fig, loopclass.loop, interval=1000)

plt.show()
