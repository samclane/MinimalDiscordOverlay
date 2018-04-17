from tkinter import *

# boilerplate code from http://effbot.org/tkinterbook/tkinter-dialog-windows.htm
class Dialog(Toplevel):

    def __init__(self, parent, title=None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                  parent.winfo_rooty() + 50))

        self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set()  # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

        return 0

    #
    # command hooks

    def validate(self):

        return 1  # override

    def apply(self):
        pass  # override

class LoginDialog(Dialog):
    result = (None, None)

    def body(self, master):
        Label(master, text="Username:").grid(row=0)
        Label(master, text="Password:").grid(row=1)
        self.rememberMe = BooleanVar()

        self.usr = Entry(master)
        self.pwd = Entry(master, show="*")
        self.rememberChk = Checkbutton(master, text="Remember info?", variable=self.rememberMe)

        self.usr.grid(row=0, column=1)
        self.pwd.grid(row=1, column=1)
        self.rememberChk.grid(row=2, column=1)

    def validate(self):
        usr = str(self.usr.get())
        pwd = str(self.pwd.get())

        self.result = (usr, pwd)

        return 1