from . import *
from .jobmenu import jobMenu
from .workspace import workSpace

class nbn_gui(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "nbn-toolkit Interface")

        self.dbx = None

        self.jobMenuBar = jobMenu(self)
        self.jobMenuBar.pack(side='left', anchor='nw', expand=False, fill='y')

        self.workspace = workSpace(self)
        self.workspace.pack(expand=True, fill='both')

def launch():

    app = nbn_gui()
    app.geometry("1280x720")

    style = ttk.Style(app)
    style.theme_use('clam')

    # REFRESH_TIME = 1000
    # ani = animation.FuncAnimation(f, animate, interval=REFRESH_TIME, cache_frame_data=False)
    app.mainloop()