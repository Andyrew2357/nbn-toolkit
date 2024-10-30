from . import *

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

matplotlib.use('TkAgg')
plt.rcParams.update(GUI_RCPARAMS)

class graphFrame(ttk.Frame):
    def __init__(self, parent, figure, tbar=True):
        tk.Frame.__init__(self, parent)

        graph = FigureCanvasTkAgg(figure, self)
        graph.draw()

        if tbar:
            toolbar = NavigationToolbar2Tk(graph, self)
            toolbar.update()
        graph._tkcanvas.pack(fill=tk.BOTH, expand=True)
        graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)