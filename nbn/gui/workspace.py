from . import *

from ..transport import Transport
from ..fftmap import FFTmap
from ..fftmapb import FFTmapb

import threading, logging, time
from tkinter import scrolledtext

PX, PY = 20, 20
class workSpace(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.ncols = ICON_GRID_COLS

        root = self.winfo_toplevel()
        W, H = root.winfo_screenwidth() - JOB_MENU_WIDTH, root.winfo_screenheight()

        self.bkgd_im = ImageTk.PhotoImage(Image.open(os.path.join(ASSETS_FOLDER, 
            'workspace_background.png')).resize((W, H), Image.LANCZOS))
        self.background = ttk.Label(self, image=self.bkgd_im)
        self.background.place(relx=0.5, rely=0.5, anchor='center')

        self.supported_jobs = {
            'transport': dSet_transport
        }

        self.jobs = []
        self.jobind = 1

        self.icon_grid = tk.Frame(self, background='')
        for r in range(ICON_GRID_ROWS): self.icon_grid.rowconfigure(r, weight=1)
        for c in range(ICON_GRID_COLS): self.icon_grid.columnconfigure(c, weight=1)

        self.icon_grid.pack_forget()
        self.raise_icon_grid()

        # Logging configuration
        logging.basicConfig(level=logging.INFO)        

    def regrid_icons(self):
        for J in self.jobs: J.icon.grid_forget()

        for i, J in enumerate(self.jobs): J.icon.grid(row=i//self.ncols, column=i%self.ncols,
                                                        padx=10, pady=10)
            
    def raise_fullscreen(self, J):
        self.icon_grid.pack_forget()
        J.fullscreen.pack(expand=True, fill='both',
                          padx=PX, pady=PY)

    def raise_icon_grid(self):
        for J in self.jobs: J.fullscreen.pack_forget()
        self.icon_grid.pack(expand=True, fill='both',
                            padx=PX, pady=PY)
        self.regrid_icons()
        
    def append_job(self, jobType, params):
        tag = f'J{self.jobind}'
        self.jobind+=1
        J = self.supported_jobs[jobType](self, tag, params)
        self.jobs.append(J)
        self.regrid_icons()

# Handler for logging asynchronously to text widgets
# I take from this forum post https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget
# which is itself adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
#################################################################################################
class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

# Skeleton for a generic job
#################################################################################################

class job_icon(tk.Canvas):
    def __init__(self, parent, tag):
        tk.Canvas.__init__(self, parent, width=JOB_ICON_WIDTH, height=JOB_ICON_HEIGHT)
        self.tag = tag

        self.L = tk.Label(self, font=NORM_FONT)
        self.buttonframe = tk.Frame(self, background='')
        self.fancyframe = tk.Frame(self, background='')


        self.L.place(x=0, y=0, width=JOB_ICON_WIDTH, height=JOB_ICON_HEIGHT//5)
        self.buttonframe.place(x=0, y=4*JOB_ICON_HEIGHT//5, 
                               width=JOB_ICON_WIDTH, height=JOB_ICON_HEIGHT//5)
        self.fancyframe.place(x=0, y=JOB_ICON_HEIGHT//5, 
                               width=JOB_ICON_WIDTH, height=3*JOB_ICON_HEIGHT//5)

        retag(self.tag, self, self.L, self.buttonframe, self.fancyframe)

class job_fullscreen(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, background='')
        self.parent=parent
        self.menubar = ttk.Frame(self)
        self.menubar.place(x=0, y=0, relwidth=1)

        exit_button = ttk.Button(self.menubar, text='Exit', command=self.parent.raise_icon_grid)
        exit_button.pack()

class job():
    def __init__(self, parent, tag):
        self.parent = parent
        self.tag = tag
        self.icon = job_icon(parent.icon_grid, tag)
        self.fullscreen = job_fullscreen(parent)
        self.icon.bind_class(tag, '<Button-1>', self.raise_fullscreen)

    def raise_fullscreen(self, *args):
        self.parent.raise_fullscreen(self)

# Dataset managers
#################################################################################################

class dSet_transport(job):
    def __init__(self, parent, tag, params, status):
        super().__init__(parent, tag)
        self.transport_data = Transport()
        self.params = params
        
        self.icon.L.config(text=f"{tag} - Transport Dataset")
        save_button = ButtonWithTip(self.icon.buttonframe, ttip="Save Dataset", 
                command=self.save, image=os.path.join(ASSETS_FOLDER, 'save_icon.png'), size=(10, 10))
        save_button.pack()

        self.broadcast_log = scrolledtext.ScrolledText(self.fullscreen, state=tk.DISABLED)
        self.broadcast_log.pack(expand=True, fill='both')

        if status == 'old':
            self.init_from_local()
        else:
            self.broadcastHandler = TextHandler(self.broadcast_log)
            self.logger = logging.getLogger()
            self.logger.addHandler(self.broadcastHandler)
            if params['updating']:
                self.update()
            else:
                self.init_from_sweeps()

    def save(self):
        print(self.icon.winfo_toplevel())
        savePage = tk.Toplevel(self.icon.winfo_toplevel())
        savePage.wm_title(f"Save Data from {self.tag}")

        container = ttk.Frame(savePage)
        container.pack(expand=True, fill='both')

        Lsave_folder = ttk.Label(container, text="Save Folder:", font=NORM_FONT)
        save_folder = tk.StringVar()
        save_folder_box = DirEntry(container, save_folder)
        save_folder.set(CONFIG['default_save_folder'])

        Lttag = ttk.Label(container, text="Tag:", font=NORM_FONT)
        ttag = tk.StringVar()
        ttag_box = ttk.Entry(container, textvariable=ttag)

        def kill(): savePage.destroy()

        def submit(): 
            self.transport_data.save_data_csv(save_folder.get(), 
                                              None if ttag.get() == '' else ttag.get())
            kill()

        cancel_button = ttk.Button(container, text="Cancel", command=kill)
        submit_button = ttk.Button(container, text="Submit", command=submit)

        Lsave_folder.grid(row=1, column=0, padx=5, pady=5)
        save_folder_box.grid(row=1, column=1, padx=5, pady=5)
        Lttag.grid(row=2, column=0, padx=5, pady=5)
        ttag_box.grid(row=2, column=1, padx=5, pady=5)
        cancel_button.grid(row=3, column=0, sticky='w', padx=5, pady=10)
        submit_button.grid(row=3, column=1, sticky='e', padx=5, pady=10)

    def init_from_local(self):
        kwargs = {k:v for k, v in self.params.items() if k not in ('updating', 'stride')} 
        kwargs['verbose'] = self.broadcast_log
        self.transport_data.init_data_from_sweeps(**kwargs)

    def init_from_sweeps(self):
        kwargs = {'path':self.params['path']}
        self.transport_data.init_data

    def update(self):
        kwargs = {k:v for k, v in self.params.items() if k not in ('updating',)}
        kwargs['verbose'] = self.broadcast_log
        self.transport_data.update_data_from_sweeps