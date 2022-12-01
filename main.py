import sys
import logging
from collections import deque
from datetime import timedelta as td


import matplotlib as mpl
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from configuration import dialog_window, get_file_name

LIM = 500
CHN = ["JJI", "NPM", "NWC", "JJY"]
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

dir = dialog_window()
plt.style.use('dark_background')

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
            if self.stop_read == True:
                self.stop_read = False
                self.retries_read = 0
                logger.info("Новые данные получены")
            self.cached_time = new_time[-1]
            for time in new_time:
                n_xdata.append(float(time))
                n_ydata.append(float(data[time]))
        elif self.stop_read == False and self.cached_time:
            if self.retries_read < 3:
                self.retries_read += 1
            if self.retries_read == 3:
                logger.error(
                    f"{self.file_name}: нет новых данных, последние данные: {td(seconds=float(self.cached_time))}"
                )
                self.stop_read = True
        if self.cached_time == "86380.000":
            if self.retries > 10:
                logger.error(
                    f"Новый файл не найден, последний файл: {self.short_name} {self.file_name[9:11]}.{self.file_name[7:9]}.{self.file_name[3:7]}"
                )
                self.stop = True
                self.retries = 0
            old_dir, old_file_name, old_short_name = (
                self.data_dir,
                self.file_name,
                self.short_name,
            )
            self.file_name = get_file_name(old_short_name, old_dir)
            self.shot_name = self.file_name[:3]
            if old_file_name != self.file_name:
                self.cached_time = None
                self.pointer = 0
                self.stop = False
            elif self.stop == False:
                self.retries += 1
        return n_xdata, n_ydata


class Loop:
    def __init__(self, r0, r1, r2, r3):
        self.r0 = r0
        self.r1 = r1
        self.r2 = r2
        self.r3 = r3

    def loop(self, i):
        if self.r0.cached_time == "86380.000" or self.r1.cached_time == "86380.000" or self.r2.cached_time == "86380.000" or self.r3.cached_time == "86380.000":
            ax.set_title(f'{self.r0.file_name[9:11]}.{self.r0.file_name[7:9]}.{self.r0.file_name[3:7]}')
            xs0.clear()
            ys0.clear()
            xs1.clear()
            ys1.clear()
            xs2.clear()
            ys2.clear()
            xs3.clear()
            ys3.clear()
        x0, y0 = self.r0.read()
        x1, y1 = self.r1.read()
        x2, y2 = self.r2.read()
        x3, y3 = self.r3.read()
        xs0.extend(x0)
        ys0.extend(y0)
        xs1.extend(x1)
        ys1.extend(y1)
        xs2.extend(x2)
        ys2.extend(y2)
        xs3.extend(x3)
        ys3.extend(y3)
        l1.set_data(xs0, ys0)
        l2.set_data(xs1, ys1)
        l3.set_data(xs2, ys2)
        l4.set_data(xs3, ys3)
        ax.relim()
        ax.autoscale_view(True, True, True)


mpl.rcParams["toolbar"] = "None"

fig, ax = plt.subplots()
fig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95)
(xs0, ys0, xs1, ys1, xs2, ys2, xs3, ys3) = (
    deque([None], maxlen=LIM),
    deque([None], maxlen=LIM),
    deque([None], maxlen=LIM),
    deque([None], maxlen=LIM),
    deque([None], maxlen=LIM),
    deque([None], maxlen=LIM),
    deque([None], maxlen=LIM),
    deque([None], maxlen=LIM),
)

(l1,) = ax.plot([], [], label='JJI', color='green')
(l2,) = ax.plot([], [], label='NPM')
(l3,) = ax.plot([], [], label='NWC', color='red')
(l4,) = ax.plot([], [], label='JJY')

reader0 = Reader(dir, 'JJI')
reader1 = Reader(dir, 'NPM')
reader2 = Reader(dir, 'NWC')
reader3 = Reader(dir, 'JJY')
loopclass = Loop(reader0, reader1, reader2, reader3)


def time_format_func(x, pos=None):
    x = str(td(seconds=x))
    return x[:-3]


def full_screen_button(event):
    mng = plt.get_current_fig_manager()
    mng.full_screen_toggle()


plt.xlabel("Время")
plt.ylabel("Амплитуда")
ax.set_title(f'{reader0.file_name[9:11]}.{reader0.file_name[7:9]}.{reader0.file_name[3:7]}')
ax.xaxis.set_major_formatter(time_format_func)
ax_button = plt.axes([0.96, 0.94, 0.04, 0.06])
next_button = Button(ax_button, label="←↕→", color="black", hovercolor="grey")
next_button.on_clicked(full_screen_button)
ax.legend(ncol=2, title='UltraMSK', fontsize = 15, title_fontsize = '15')
ax.grid(which="major", ls="-", lw=0.5, color="#373737")

anim = animation.FuncAnimation(fig, loopclass.loop, interval=20000)

plt.show()
