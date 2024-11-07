from . import *

from ..transport import Transport
from ..fftmap import FFTmap
from ..fftmapb import FFTmapb

import threading, logging, time
from tkinter import scrolledtext

class workSpace(tk.Canvas):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.ncols = ICON_GRID_COLS
        self.nrows = ICON_GRID_ROWS

        root = self.winfo_toplevel()
        W, H = root.winfo_screenwidth() - JOB_MENU_WIDTH, root.winfo_screenheight()
        self.bkgd_im = ImageTk.PhotoImage(Image.open(os.path.join(ASSETS_FOLDER, 
            'workspace_background.png')).resize((W, H), Image.LANCZOS))
        self.background = ttk.Label(self, image=self.bkgd_im)
        self.background.place(relx=0.5, rely=0.5, anchor='center')

        self.jobs = []
        self.jobind = 1

        # Logging configuration
        logging.basicConfig(level=logging.INFO) 
        self.logger = logging.getLogger()  

        self.supported_jobs = {
            'transport': dSet_transport,
            'FFTmap': dSet_FFTmap,
            'FFTmapb': dSet_FFTmapb,
            'generic': job
        }

    def regrid_icons(self):
        for J in self.jobs: J.icon.place_forget()
        PX, PY = 0.02, 0.02
        for i, J in enumerate(self.jobs): J.icon.place(relx=PX+(i%self.ncols)/self.ncols, 
                                                       rely=PY+(i//self.ncols)/self.nrows, 
                                                       relwidth=1/self.ncols - 2*PX, 
                                                       relheight=1/self.nrows - 2*PY)
            
    def raise_fullscreen(self, J):
        for j in self.jobs: j.icon.place_forget()
        PX, PY = 0.02, 0.02
        J.fullscreen.place(relx=PX, rely=PY, relwidth=1-2*PX, relheight=1-2*PY)

    def raise_icon_grid(self):
        for J in self.jobs: J.fullscreen.place_forget()
        self.regrid_icons()
        
    def append_job(self, jobType, **kwargs):
        tag = f'J{self.jobind}'
        self.jobind+=1
        J = self.supported_jobs[jobType](self, tag, **kwargs)
        self.jobs.append(J)
        self.raise_icon_grid()

# Handler for logging asynchronously to text widgets
# I take from this forum post https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget
# which is itself adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
# I modified this to accound for different jobs
#################################################################################################
class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    def __init__(self, text, tag):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text
        self.tag = tag

    def emit(self, record):
        msg = self.format(record)
        if not msg.startswith(self.tag): return
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

class job_icon(ttk.Frame):
    def __init__(self, parent, tag):
        ttk.Frame.__init__(self, parent)
        self.tag = tag

        self.L = ttk.Label(self, font=NORM_FONT)
        self.buttonframe = ttk.Frame(self)
        self.fancyframe = ttk.Frame(self)

        self.L.place(relx=0, rely=0, relwidth=1, relheight=0.2)
        self.fancyframe.place(relx=0, rely=0.2, relwidth=1, relheight=0.6)
        self.buttonframe.place(relx=0, rely=0.8, relwidth=1, relheight=0.2)

        retag(self.tag, self, self.L, self.buttonframe, self.fancyframe)

class job_fullscreen(ttk.Frame):
    def __init__(self, parent, tag):
        ttk.Frame.__init__(self, parent)
        self.tag = tag
        self.parent = parent
        self.menubar = ttk.Frame(self)
        self.menubar.place(relx=0, rely=0, relwidth=1, relheight=0.05)
        self.palette = ttk.Frame(self)
        self.palette.place(relx=0, rely=0.05, relwidth=1, relheight=0.95)

        exit_button = ButtonWithTip(self.menubar, ttip="Exit", 
                        command=self.parent.raise_icon_grid,
                        image=os.path.join(ASSETS_FOLDER, 'exit_button.png'),
                        size=(20, 20))
        exit_button.pack(anchor='e', side='right', expand=True, fill='y')


class job():
    def __init__(self, parent, tag):
        self.parent = parent
        self.tag = tag
        self.icon = job_icon(parent, tag)
        self.fullscreen = job_fullscreen(parent, tag)
        self.icon.bind_class(tag, '<Button-1>', self.raise_fullscreen)

    def raise_fullscreen(self, *args):
        self.parent.raise_fullscreen(self)


# Dataset managers
#################################################################################################

# Transport
class dSet_transport(job):
    def __init__(self, parent, tag, params, status):
        job.__init__(self, parent, tag)
        self.transport_data = Transport()
        self.params = params
        
        self.icon.L.config(text=f"{tag} - Transport Dataset")
        save_button = ButtonWithTip(self.icon.buttonframe, ttip="Save Dataset", 
                command=self.save, image=os.path.join(ASSETS_FOLDER, 'save_icon.png'), size=(10, 10))
        save_button.pack(anchor='e', side='left')

        self.broadcast_log = scrolledtext.ScrolledText(self.fullscreen.palette, state=tk.DISABLED)
        self.broadcast_log.pack(expand=True, fill='both', padx=10, pady=10)
        self.broadcast_log.configure(state='normal')
        self.broadcast_log.insert(tk.END, f"Starting New Transport Dataset Job {self.tag}...\n")
        self.broadcast_log.configure(state='disabled')
        self.broadcast_log.yview(tk.END)

        if params is None: return

        self.stable = True
        if status == 'old':
            self.init_from_local()
        else:
            self.broadcastHandler = TextHandler(self.broadcast_log, self.tag)
            self.parent.logger.addHandler(self.broadcastHandler)
            if params['updating']:
                thread = threading.Thread(target=self.update, args=[])
                thread.start()
            else:
                thread = threading.Thread(target=self.init_from_sweeps, args=[])
                thread.start()

    def save(self):
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
            chosen_dir = save_folder.get()
            chosen_fname = os.path.join(chosen_dir, self.transport_data.meta['run_name'] + '.json')
            if os.path.isdir(chosen_fname):
                popup = tk.Toplevel(self.icon.winfo_toplevel())
                Lwarning = ttk.Label(popup, text=f"WARNING: {chosen_fname} already exists. Do you want to overwrite this file?")

                def approve():
                    self.transport_data.save_data_csv(chosen_dir, None if ttag.get() == '' else ttag.get())
                    popup.destroy()
                    kill()

                reject_button = ttk.Button(popup, text="Cancel", command=popup.destroy)
                approve_button = ttk.Button(popup, text="Approve", command=approve)

            else:
                self.transport_data.save_data_csv(chosen_dir, None if ttag.get() == '' else ttag.get())
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
        kwargs = {'path':self.params['path']}
        self.transport_data.init_data(**kwargs)
        self.broadcast_log.pack(expand=True, fill='both', padx=10, pady=10)
        self.broadcast_log.configure(state='normal')
        self.broadcast_log.insert(tk.END, 
                f"{self.tag}: Loaded Data from {self.params['path']}\n")
        self.broadcast_log.configure(state='disabled')
        self.broadcast_log.yview(tk.END)

    def init_from_sweeps(self):
        kwargs = {k:v for k, v in self.params.items() if k not in ('updating', 'stride')} 
        kwargs['verbose'] = self.tag
        kwargs['dbx'] = self.icon.winfo_toplevel().dbx
        self.stable = False
        self.transport_data.init_data_from_sweeps(**kwargs)
        self.stable = True

    def update(self):
        kwargs = {k:v for k, v in self.params.items() if k not in ('updating',)}
        kwargs['verbose'] = self.tag
        kwargs['dbx'] = self.icon.winfo_toplevel().dbx
        while self.params['updating']:
            self.stable = False
            self.transport_data.update_data_from_sweeps(**kwargs)
            self.stable = True
            time.sleep(DATA_REFRESH_TIME_SECONDS)

# FFT
class dSet_FFTmap(job):
    def __init__(self, parent, tag, params, status):
        job.__init__(self, parent, tag)
        self.transport_data = FFTmap()
        self.params = params
        
        self.icon.L.config(text=f"{tag} - FFTmap Dataset")
        save_button = ButtonWithTip(self.icon.buttonframe, ttip="Save Dataset", 
                command=self.save, image=os.path.join(ASSETS_FOLDER, 'save_icon.png'), size=(10, 10))
        save_button.pack(anchor='e', side='left')

        self.broadcast_log = scrolledtext.ScrolledText(self.fullscreen.palette, state=tk.DISABLED)
        self.broadcast_log.pack(expand=True, fill='both', padx=10, pady=10)
        self.broadcast_log.configure(state='normal')
        self.broadcast_log.insert(tk.END, f"Starting New FFTmap Dataset Job {self.tag}...\n")
        self.broadcast_log.configure(state='disabled')
        self.broadcast_log.yview(tk.END)

        if params is None: return

        self.stable = True
        if status == 'old':
            self.init_from_local()
        else:
            self.broadcastHandler = TextHandler(self.broadcast_log, self.tag)
            self.parent.logger.addHandler(self.broadcastHandler)
            # if params['updating']:
            #     thread = threading.Thread(target=self.update, args=[])
            #     thread.start()
            # else:
            #     thread = threading.Thread(target=self.init_from_sweeps, args=[])
            #     thread.start()
            thread = threading.Thread(target=self.init_from_sweeps, args=[])
            thread.start()            

    def save(self):
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
            chosen_dir = save_folder.get()
            chosen_fname = os.path.join(chosen_dir, self.transport_data.meta['run_name'] + '.json')
            if os.path.isdir(chosen_fname):
                popup = tk.Toplevel(self.icon.winfo_toplevel())
                Lwarning = ttk.Label(popup, text=f"WARNING: {chosen_fname} already exists. Do you want to overwrite this file?")

                def approve():
                    self.transport_data.save_data_csv(chosen_dir, None if ttag.get() == '' else ttag.get())
                    popup.destroy()
                    kill()

                reject_button = ttk.Button(popup, text="Cancel", command=popup.destroy)
                approve_button = ttk.Button(popup, text="Approve", command=approve)
                
                Lwarning.grid(row=0, column=0, padx=10, pady=10, columnspan=2)
                reject_button.grid(row=1, column=0, padx=10, pady=10)
                approve_button.grid(row=1, column=1, padx=10, pady=10)

            else:
                self.transport_data.save_data_csv(chosen_dir, None if ttag.get() == '' else ttag.get())
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
        kwargs = {'path':self.params['path']}
        self.transport_data.init_data(**kwargs)
        self.broadcast_log.pack(expand=True, fill='both', padx=10, pady=10)
        self.broadcast_log.configure(state='normal')
        self.broadcast_log.insert(tk.END, 
                f"{self.tag}: Loaded Data from {self.params['path']}\n")
        self.broadcast_log.configure(state='disabled')
        self.broadcast_log.yview(tk.END)

    def init_from_sweeps(self):
        # kwargs = {k:v for k, v in self.params.items() if k not in ('updating', 'stride')}
        kwargs = {k:v for k, v in self.params.items()} 
        kwargs['verbose'] = self.tag
        kwargs['dbx'] = self.icon.winfo_toplevel().dbx
        self.stable = False
        self.transport_data.init_data_from_sweeps(**kwargs)
        self.stable = True

    # def update(self):
    #     kwargs = {k:v for k, v in self.params.items() if k not in ('updating',)}
    #     kwargs['verbose'] = self.tag
    #     kwargs['dbx'] = self.icon.winfo_toplevel().dbx
    #     while self.params['updating']:
    #         self.stable = False
    #         self.transport_data.update_data_from_sweeps(**kwargs)
    #         self.stable = True
    #         time.sleep(DATA_REFRESH_TIME_SECONDS)

# FFTb
class dSet_FFTmapb(job):
    def __init__(self, parent, tag, params, status):
        job.__init__(self, parent, tag)
        self.transport_data = FFTmapb()
        self.params = params
        
        self.icon.L.config(text=f"{tag} - FFTmap Dataset")
        save_button = ButtonWithTip(self.icon.buttonframe, ttip="Save Dataset", 
                command=self.save, image=os.path.join(ASSETS_FOLDER, 'save_icon.png'), size=(10, 10))
        save_button.pack(anchor='e', side='left')

        self.broadcast_log = scrolledtext.ScrolledText(self.fullscreen.palette, state=tk.DISABLED)
        self.broadcast_log.pack(expand=True, fill='both', padx=10, pady=10)
        self.broadcast_log.configure(state='normal')
        self.broadcast_log.insert(tk.END, f"Starting New FFTmap Dataset Job {self.tag}...\n")
        self.broadcast_log.configure(state='disabled')
        self.broadcast_log.yview(tk.END)

        if params is None: return

        self.stable = True
        if status == 'old':
            self.init_from_local()
        else:
            self.broadcastHandler = TextHandler(self.broadcast_log, self.tag)
            self.parent.logger.addHandler(self.broadcastHandler)
            # if params['updating']:
            #     thread = threading.Thread(target=self.update, args=[])
            #     thread.start()
            # else:
            #     thread = threading.Thread(target=self.init_from_sweeps, args=[])
            #     thread.start()
            thread = threading.Thread(target=self.init_from_sweeps, args=[])
            thread.start()            

    def save(self):
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
            chosen_dir = save_folder.get()
            chosen_fname = os.path.join(chosen_dir, self.transport_data.meta['run_name'] + '.json')
            if os.path.isdir(chosen_fname):
                popup = tk.Toplevel(self.icon.winfo_toplevel())
                Lwarning = ttk.Label(popup, text=f"WARNING: {chosen_fname} already exists. Do you want to overwrite this file?")

                def approve():
                    self.transport_data.save_data_csv(chosen_dir, None if ttag.get() == '' else ttag.get())
                    popup.destroy()
                    kill()

                reject_button = ttk.Button(popup, text="Cancel", command=popup.destroy)
                approve_button = ttk.Button(popup, text="Approve", command=approve)
                
                Lwarning.grid(row=0, column=0, padx=10, pady=10, columnspan=2)
                reject_button.grid(row=1, column=0, padx=10, pady=10)
                approve_button.grid(row=1, column=1, padx=10, pady=10)

            else:
                self.transport_data.save_data_csv(chosen_dir, None if ttag.get() == '' else ttag.get())
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
        kwargs = {'path':self.params['path']}
        self.transport_data.init_data(**kwargs)
        self.broadcast_log.pack(expand=True, fill='both', padx=10, pady=10)
        self.broadcast_log.configure(state='normal')
        self.broadcast_log.insert(tk.END, 
                f"{self.tag}: Loaded Data from {self.params['path']}\n")
        self.broadcast_log.configure(state='disabled')
        self.broadcast_log.yview(tk.END)

    def init_from_sweeps(self):
        # kwargs = {k:v for k, v in self.params.items() if k not in ('updating', 'stride')}
        kwargs = {k:v for k, v in self.params.items()} 
        kwargs['verbose'] = self.tag
        kwargs['dbx'] = self.icon.winfo_toplevel().dbx
        self.stable = False
        self.transport_data.init_data_from_sweeps(**kwargs)
        self.stable = True

    # def update(self):
    #     kwargs = {k:v for k, v in self.params.items() if k not in ('updating',)}
    #     kwargs['verbose'] = self.tag
    #     kwargs['dbx'] = self.icon.winfo_toplevel().dbx
    #     while self.params['updating']:
    #         self.stable = False
    #         self.transport_data.update_data_from_sweeps(**kwargs)
    #         self.stable = True
    #         time.sleep(DATA_REFRESH_TIME_SECONDS)

# Plotting Jobs
#################################################################################################
