import configparser
import os
import threading
import tkinter as tk
import win32api
from shutil import copyfile
from tkinter import Label, BooleanVar, Entry, Checkbutton

import win32con

from Dialog import Dialog

try:
    import winxpgui as win32gui
except ImportError:
    import win32gui

import discord

import SysTrayIcon

REFRESH_RATE = 250

client = discord.Client()
config = configparser.ConfigParser()
if not os.path.isfile("config.ini"):
    copyfile("default.ini", "config.ini")
config.read("config.ini")
width = config['Display']['Width']
height = config['Display']['Height']
username = config['LoginInfo']['Username']
password = config['LoginInfo']['Password']
root = None
canv = None
connected_ind = None
muted_ind = None
threads = {}


class LoginDialog(Dialog):
    result = (None, None)

    def body(self, master):
        Label(master, text="Username:").grid(row=0)
        Label(master, text="Password:").grid(row=1)
        self.rememberMe = BooleanVar()

        self.usr = Entry(master)
        self.usr.insert(tk.END, username)
        self.pwd = Entry(master, show="*")
        self.pwd.insert(tk.END, password)
        self.rememberChk = Checkbutton(master, text="Remember info?", variable=self.rememberMe)

        self.usr.grid(row=0, column=1)
        self.pwd.grid(row=1, column=1)
        self.rememberChk.grid(row=2, column=1)

    def validate(self):
        usr = str(self.usr.get())
        pwd = str(self.pwd.get())

        self.result = (usr, pwd)

        return 1


class SettingsDialog(Dialog):

    def body(self, master):
        Label(master, text="Height").grid(row=0)
        Label(master, text="Width").grid(row=1)
        Label(master, text="OffsetX:").grid(row=2)
        Label(master, text="OffsetY").grid(row=3)

        self.height = Entry(master)
        self.height.insert(tk.END, config["Display"]["Height"])
        self.width = Entry(master)
        self.width.insert(tk.END, config["Display"]["Width"])
        self.offx = Entry(master)
        self.offx.insert(tk.END, config["Display"]["OffsetX"])
        self.offy = Entry(master)
        self.offy.insert(tk.END, config["Display"]["OffsetY"])

        self.height.grid(row=0, column=1)
        self.width.grid(row=1, column=1)
        self.offx.grid(row=2, column=1)
        self.offy.grid(row=3, column=1)

    def validate(self):
        h = str(self.height.get())
        w = str(self.width.get())
        offx = str(self.offx.get())
        offy = str(self.offy.get())

        config["Display"]["Height"] = h
        config["Display"]["Width"] = w
        config["Display"]["OffsetX"] = offx
        config["Display"]["OffsetY"] = offy

        with open('config.ini', 'w') as cfg:
            config.write(cfg)
            print("Settings info saved successfully!")

        refresh_settings()

        return 1


# a subclass of Canvas for dealing with resizing of windows
class ResizingCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width) / self.width
        hscale = float(event.height) / self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas
        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.scale("all", 0, 0, wscale, hscale)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


def update_status(root):
    '''Checks signed-in user's status'''
    if client.is_logged_in:
        for server in client.servers:
            mem = server.get_member(client.user.id)
            vs = mem.voice
            if vs.voice_channel is not None:
                canv.itemconfig(connected_ind, fill='green')
                if vs.mute or vs.self_mute:
                    canv.itemconfig(muted_ind, fill='red')
                else:
                    canv.itemconfig(muted_ind, fill='green')
                break
            else:
                canv.itemconfig(connected_ind, fill='red')
                canv.itemconfig(muted_ind, fill='red')
    canv.update_idletasks()
    root.after(REFRESH_RATE, lambda: update_status(root))


def attempt_login(username, password):
    print("Attempting to log in as {}...".format(username))
    if threads.get("t_client"):
        client.logout()
    t_client = threading.Thread(target=client.run, args=(username, password))
    t_client.start()
    threads['t_client'] = t_client


def on_exit(_):
    print("Closing...")
    os._exit(1)


def log_in_dialog(_):
    global username, password
    ld = LoginDialog(root, "Log in")
    if not ld.result:
        return
    username, password = ld.result
    if ld.rememberMe.get():
        config["LoginInfo"]['Username'] = username
        config["LoginInfo"]['Password'] = password
        with open('config.ini', 'w') as cfg:
            config.write(cfg)
            print("Login info saved successfully!")
    attempt_login(username, password)


def settings_dialog(_):
    sd = SettingsDialog(root, "Settings")


def refresh_settings():
    global width, height
    width = config['Display']['Width']
    height = config['Display']['Height']
    root.geometry('{}x{}'.format(width, height))
    root.geometry("+{}+{}".format(config["Display"]["OffsetX"], config["Display"]["OffsetY"]))
    root.update_idletasks()


def main():
    global root, canv, connected_ind, muted_ind, width, height
    root = tk.Tk()
    root.wm_title("AppWindow Test")
    root.overrideredirect(True)
    root.attributes('-topmost', 'true')
    root.resizable(0, 0)
    root.geometry('{}x{}'.format(width, height))
    root.geometry("+{}+{}".format(config["Display"]["OffsetX"], config["Display"]["OffsetY"]))

    # Attempt to make the window click-through
    hwnd = root.winfo_id()
    lExStyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    lExStyle |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, lExStyle)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(1, 1, 1), 60, win32con.LWA_ALPHA)

    canv = ResizingCanvas(root, width=width, height=height, highlightthickness=0)
    canv.pack(fill=tk.BOTH, expand=tk.YES)
    connected_ind = canv.create_rectangle(0, 0, int(width)/2, height, fill='grey', width=1)
    muted_ind = canv.create_rectangle(int(width)/2, 0, width, height, fill='grey', width=1)
    canv.addtag_all("all")

    if username != "None" and password != "None":
        attempt_login(username, password)

    root.after(REFRESH_RATE, lambda: update_status(root))

    menu_options = (('Log in', None, log_in_dialog),
                    ('Settings', None, settings_dialog))

    def run_tray_icon(): SysTrayIcon.SysTrayIcon('eye.ico', "Minimal Discord Overlay", menu_options, on_quit=on_exit)

    t_tray = threading.Thread(target=run_tray_icon)
    t_tray.start()
    threads['t_tray'] = t_tray

    root.mainloop()


if __name__ == '__main__':
    main()
