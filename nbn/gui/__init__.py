import warnings
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from idlelib.tooltip import Hovertip
from PIL import Image, ImageTk
import json
import os

GUI_FOLDER = os.path.dirname(os.path.abspath(__file__))

SETTINGS_JSON = os.path.join(GUI_FOLDER, 'settings.json')
with open(SETTINGS_JSON, 'r') as ff:
        CONFIG = json.load(ff)

ASSETS_FOLDER = os.path.join(GUI_FOLDER, 'assets')

LARGE_FONT = ('Verdana', 12)
NORM_FONT = ('Verdana', 10)
SMALL_FONT = ('Verdana', 8)

GUI_RCPARAMS={
    'font.size':5,
    'legend.fontsize':5,
    'axes.titlesize':5,
    'axes.labelsize':5,
    'xtick.labelsize':5,
    'ytick.labelsize':5
}

JOB_MENU_WIDTH = 300
JOB_OPT_HEIGHT = 600

ICON_GRID_COLS = 4
ICON_GRID_ROWS = 5
JOB_ICON_WIDTH = 200
JOB_ICON_HEIGHT = 100

DATA_REFRESH_TIME_SECONDS = 10

def popupmsg(msg, title="!", bmsg="OK."):
    popup = tk.Toplevel()
    def leavemini(): popup.destroy()

    popup.wm_title(title)
    label = ttk.label(popup, text=msg, font=NORM_FONT)
    B1 = ttk.Button(popup, text=bmsg, command=leavemini)
    B1.pack()

    popup.mainloop()

def retag(tag, *args):
    for widget in args:
        widget.bindtags((tag,) + widget.bindtags())

class ButtonWithTip(ttk.Frame):
    def __init__(self, parent, text="", ttip="", command=lambda: None, image=None, size=None):
        ttk.Frame.__init__(self, parent)

        if image is not None: 
            image = Image.open(image)
            if size is not None: image = image.resize(size, Image.LANCZOS)
            image = ImageTk.PhotoImage(image)
        self.image = image

        btn = ttk.Button(self, text=text, command=command, image=image)
        btn.pack()
        tip = Hovertip(btn, ttip)

# I borrow the code for a scrollable frame from a blog written by Jose Salvatierra
# https://blog.teclado.com/tkinter-scrollable-frames/

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, canvas_width=100, canvas_height=None, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self, width=canvas_width, height=canvas_height)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, *args, **kwargs)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        # self.scrollable_frame.pack(fill="both", expand=True)

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class SearchableButtons(ttk.Frame):
    def __init__(self, parent, buttons, text="", canvas_width=100, canvas_height=100, **kwargs):
        ttk.Frame.__init__(self, parent)

        label = ttk.Label(self, text=text, font=NORM_FONT)

        query = tk.StringVar()
        search = ttk.Entry(self, textvariable=query, font=NORM_FONT)

        reduced_canvas_height = canvas_height - 50
        Bframe = ScrollableFrame(self, canvas_width=canvas_width, 
                                 canvas_height=reduced_canvas_height, **kwargs)
        Bframe.grid_propagate(0)

        maxLen = 1000
        B = {name:ttk.Button(Bframe.scrollable_frame, text=name.ljust(maxLen), 
                command=command) for name, command in buttons}

        def grid_Bframe(*args):
            for btn in B: B[btn].grid_forget()

            r=0
            key = query.get().lower().strip()
            for btn in B:
                if key in btn.lower(): 
                    B[btn].grid(row=r, column=0, padx=5, sticky='ew')
                    r+=1
        
        grid_Bframe()
        Bframe.scrollable_frame.columnconfigure(0, weight=1)

        label.pack(expand=True, fill='x', padx=5)
        search.pack(expand=True, fill='x', padx=5)
        Bframe.pack(pady=5)

        query.trace_add('write', grid_Bframe)

class DirEntry(ttk.Frame):
    def __init__(self, parent, pathvar, width=20):
        ttk.Frame.__init__(self, parent, width=width)

        def browse():
            filename = filedialog.askdirectory()
            pathvar.set(filename)

        self.text_box = ttk.Entry(self, textvariable=pathvar, font=NORM_FONT, width=width)
        self.browse_button = ButtonWithTip(self, ttip='Browse Files', command=browse, 
                    image=os.path.join(ASSETS_FOLDER, 'filesystem.png'), size=(8,8))

        self.text_box.grid(row=0, column=0)
        self.browse_button.grid(row=0, column=1)