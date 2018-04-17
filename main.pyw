import os
import threading
import tkinter as tk
from ctypes import windll
import configparser
from shutil import copyfile
import win32con
import win32api
try:
    import winxpgui as win32gui
except ImportError:
    import win32gui


import discord

import SysTrayIcon
from Dialog import LoginDialog

WIDTH = 30
HEIGHT = 15
REFRESH_RATE = 250

client = discord.Client()
config = configparser.ConfigParser()
if not os.path.isfile("config.ini"):
    copyfile("default.ini", "config.ini")
config.read("config.ini")
username = config['LoginInfo']['Username']
password = config['LoginInfo']['Password']
root = None
Canvas = None
connected_ind = None
muted_ind = None
threads = {}


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
                Canvas.itemconfig(connected_ind, fill='green')
                if vs.mute or vs.self_mute:
                    Canvas.itemconfig(muted_ind, fill='red')
                else:
                    Canvas.itemconfig(muted_ind, fill='green')
                break
            else:
                Canvas.itemconfig(connected_ind, fill='red')
                Canvas.itemconfig(muted_ind, fill='red')
    Canvas.update_idletasks()
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
    username, password = ld.result
    if username is None or password is None:
        return
    if ld.rememberMe.get():
        config["LoginInfo"]['Username'] = username
        config["LoginInfo"]['Password'] = password
        with open('config.ini', 'w') as cfg:
            config.write(cfg)
            print("Login info saved successfully!")
    attempt_login(username, password)


def main():
    global root, Canvas, connected_ind, muted_ind
    root = tk.Tk()
    root.wm_title("AppWindow Test")
    root.overrideredirect(True)
    root.attributes('-topmost', 'true')
    root.resizable(width=False, height=False)
    root.geometry('{}x{}'.format(WIDTH, HEIGHT))

    # Attempt to make the window click-through
    hwnd = root.winfo_id()
    lExStyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    lExStyle |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, lExStyle)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(1, 1, 1), 60, win32con.LWA_ALPHA)

    # init canvas
    Canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0)
    Canvas.pack()
    connected_ind = Canvas.create_rectangle(0, HEIGHT, HEIGHT, 0, fill='grey', width=1)
    muted_ind = Canvas.create_rectangle(HEIGHT, WIDTH, WIDTH, 0, fill='grey', width=1)

    if username != "None" and password != "None":
        attempt_login(username, password)

    root.after(REFRESH_RATE, lambda: update_status(root))

    menu_options = (('Log in', None, log_in_dialog),)

    def run_tray_icon(): SysTrayIcon.SysTrayIcon('eye.ico', "Minimal Discord Overlay", menu_options, on_quit=on_exit)

    t_tray = threading.Thread(target=run_tray_icon)
    t_tray.start()
    threads['t_tray'] = t_tray

    root.mainloop()


if __name__ == '__main__':
    main()
