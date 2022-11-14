import os
import re
import sys
from tkinter import *
from tkinter import filedialog, ttk


def get_file_name(short_name, data_dir):
    if short_name and data_dir:
        file_list = os.listdir(data_dir)
        pattern = short_name + r"\d{8}"
        try:
            match_list = filter(
                lambda x: x is not None, map(lambda x: re.search(pattern, x), file_list)
            )
            str_match_list = sorted(list(map(lambda x: x.string, match_list)))
            return data_dir, str_match_list[-1], short_name
        except AttributeError:
            raise FileNotFoundError("Файл не был найден")
    else:
        sys.exit()


def dialog_window():
    def save_and_exit():
        root.destroy()

    def get_directory():
        dir = filedialog.askdirectory()
        data_dir.set(dir)
        if dir:
            label["text"] = dir

    def on_closing():
        root.destroy()
        sys.exit()

    root = Tk()
    root.title("Конфигурация")
    root.geometry("450x143")
    btn_text = Label(text="Выберите название датчика")
    btn_text.pack(anchor=W, padx=6)
    name = StringVar()
    name.set("JJI")
    options = OptionMenu(root, name, "JJI", "JJY", "NPM", "NWC")
    options.pack(anchor=W, padx=6)
    data_dir = StringVar()
    dir_btn = ttk.Button(text="Выберите папку с файлами", command=get_directory)
    dir_btn.pack(anchor=W, padx=6)
    label = ttk.Label(text="Папка не выбрана")
    label.pack(anchor=W, padx=6)
    btn = ttk.Button(text="Запустить", command=save_and_exit)
    btn.pack(fill=X, padx=6, pady=6)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
    return name.get().upper(), data_dir.get()


def configuration(data_dir=None, short_name=None):
    if data_dir is None:
        short_name, data_dir = dialog_window()
        return get_file_name(short_name, data_dir)
    return get_file_name(short_name, data_dir)
