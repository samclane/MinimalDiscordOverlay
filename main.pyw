import os
import threading
import tkinter as tk
from ctypes import windll

import discord

import SysTrayIcon
from Dialog import LoginDialog


GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080
WIDTH = 30
HEIGHT = 15

cp = '$'
client = discord.Client()
username = None
password = None
root = None
Canvas = None
connected_ind = None
muted_ind = None


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


def set_appwindow(root):
    '''Keeps the overlay on top'''
    hwnd = windll.user32.GetParent(root.winfo_id())
    style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
    style = style & ~WS_EX_TOOLWINDOW
    style = style | WS_EX_APPWINDOW
    res = windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
    # re-assert the new window style
    root.wm_withdraw()
    root.after(10, lambda: root.wm_deiconify())


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
    root.after(1000, lambda: update_status(root))


def on_exit(_):
    os._exit(1)


def log_in_dialog(_):
    ld = LoginDialog(root)
    username, password = ld.result
    t_client = threading.Thread(target=client.run, args=(username, password))
    t_client.start()


def main():
    global root, Canvas, connected_ind, muted_ind
    root = tk.Tk()
    root.wm_title("AppWindow Test")
    root.overrideredirect(True)
    root.after(10, lambda: set_appwindow(root))
    root.attributes('-topmost', 'true')
    root.resizable(width=False, height=False)
    root.geometry('{}x{}'.format(WIDTH, HEIGHT))
    Canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0)
    Canvas.pack()
    connected_ind = Canvas.create_rectangle(0, HEIGHT, HEIGHT, 0, fill='grey', width=1)
    muted_ind = Canvas.create_rectangle(HEIGHT, WIDTH, WIDTH, 0, fill='grey', width=1)

    root.after(1000, lambda: update_status(root))

    menu_options = (('Log in', None, log_in_dialog),)

    def run_tray_icon(): SysTrayIcon.SysTrayIcon('eye.ico', "Minimal Discord Overlay", menu_options, on_quit=on_exit)

    t_tray = threading.Thread(target=run_tray_icon)
    t_tray.start()

    root.mainloop()


if __name__ == '__main__':
    main()
