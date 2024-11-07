from . import *
from ..DBX import DBX

import webbrowser
from ast import literal_eval

JOPR, JOPC = 2, 0
class jobMenu(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent, width=JOB_MENU_WIDTH)
        self.grid_propagate(0)

        self.parent=parent
        
        self.dbx_connection_panel = ttk.Frame(self)
        change_dbx_button = ButtonWithTip(self.dbx_connection_panel, ttip="Manage Dropbox Connection",
                                          command=self.dropbox_connect, 
                                          image=os.path.join(ASSETS_FOLDER, 'dropbox_icon.png'),
                                          size=(15,15))
        
        dbx_text_label = ttk.Label(self.dbx_connection_panel, text="Dropbox API Helper", font=NORM_FONT)
        
        dbx_text_label.grid(row=0, column=0, sticky='w', padx=5)
        change_dbx_button.grid(row=0, column=1, sticky='e', padx=5)

        jobs = {
            'Load New Transport Data': new_dSet_Transport,
            'Load Saved Transport Data': saved_dSet_Transport,
            'Load New FFT Data': new_dSet_FFT,
            'Load Saved FFT Data': saved_dSet_FFT,
            'Load New FFTb Data': new_dSet_FFTb,
            'Load Saved FFTb Data': saved_dSet_FFTb
        }

        self.jobFrames = {}
        for j in jobs: self.jobFrames[j] = jobs[j](self)

        jbs = [(j, lambda j=j: self.jobStart(j)) for j in jobs]

        self.jobOptions = SearchableButtons(self, jbs, "Create a New Job", 
                                canvas_width=int((0.9)*JOB_MENU_WIDTH),
                                canvas_height=JOB_OPT_HEIGHT)

        self.dbx_connection_panel.grid(row=0, column=0, sticky='we', pady=5)
        sep1 = ttk.Separator(self, orient='horizontal')
        sep1.grid(row=1, column=0, sticky='we', pady=5, padx=5)
        self.jobOptions.grid(row=JOPR, column=JOPC, columnspan=1)
        sep2 = ttk.Separator(self, orient='horizontal')
        sep2.grid(row=3, column=0, sticky='we', pady=5, padx=5)

    def jobStart(self, jobType):
        self.jobOptions.grid_forget()
        self.jobFrames[jobType].grid(row=JOPR, column=JOPC)

    def dropbox_connect(self):
        dbx_startPage = tk.Toplevel(self.parent)
        dbx_startPage.wm_title("Enter App Credentials")

        ks_set = False
        dbx = None

        key_secret_page = ttk.Frame(dbx_startPage)
        L1 = ttk.Label(key_secret_page, text="Verify App Key and Secret")

        app_key = tk.StringVar()
        config_key = CONFIG['dropbox_settings']['app_key']
        app_key.set("Enter App Key" if config_key == '' else config_key)
        key_box = ttk.Entry(key_secret_page, textvariable=app_key, font=NORM_FONT)

        app_secret = tk.StringVar()
        config_secret = CONFIG['dropbox_settings']['app_secret']
        app_secret.set("Enter App Secret" if config_secret == '' else config_secret)
        secret_box = ttk.Entry(key_secret_page, textvariable=app_secret, font=NORM_FONT)

        L1.grid(row=0, column=0, columnspan=2)
        key_box.grid(row=1, column=0, padx=5)
        secret_box.grid(row=1, column=1, padx=5)

        key_secret_page.grid(row=0, column=0)

        auth_code_page = ttk.Frame(dbx_startPage)
        L2 = ttk.Label(auth_code_page, 
                       text="Click here to get the auth token.\nYou may have to log in.")

        auth_code = tk.StringVar()
        auth_code.set("")
        auth_box = ttk.Entry(auth_code_page, textvariable=auth_code, font=NORM_FONT,
                             width=50, show= '*')

        L2.grid(row=0, column=0, columnspan=2)
        auth_box.grid(row=1, column=0, columnspan=2)

        errors = ttk.Frame(dbx_startPage)
        Lerror = ttk.Label(errors)
        Lerror.pack()

        def dbxkill(): dbx_startPage.destroy()    
        
        def dbxenter():
            nonlocal ks_set, dbx

            Lerror.config(text="")
            if not ks_set:
                try:
                    dbx = DBX(app_key=app_key.get(), app_secret=app_secret.get())

                    dbx.start_oauth()
                    def link(*args): webbrowser.open_new(dbx.get_auth_url())
                    L2.bind('<Button-1>', link)

                    ks_set = True
                    key_secret_page.grid_forget()
                    auth_code_page.grid(row=0, column=0)
                except:
                    Lerror.config(text="An Error Occured.")
            else:
                try:
                    dbx.finish_oauth(auth_code.get())
                    
                    CONFIG['dropbox_settings']['app_key'] = app_key.get()
                    CONFIG['dropbox_settings']['app_secret'] = app_secret.get()

                    self.winfo_toplevel().dbx = dbx
                    dbxkill()
                except:
                    Lerror.config(text="An Error Occured.")

        buttons = ttk.Frame(dbx_startPage)
        cancel = ttk.Button(buttons, text="Cancel", command=dbxkill)
        enter = ttk.Button(buttons, text="Enter", command=dbxenter)

        cancel.grid(row=0, column=0)
        enter.grid(row=0, column=1)
        buttons.grid(row=1, column=0)

        errors.grid(row=2, column=0)

        dbx_startPage.mainloop()

# Loading Saved Data
#################################################################################################

class saved_dSet(ttk.Frame):
    def __init__(self, parent, title="Load Saved Data"):
        ttk.Frame.__init__(self, parent, 
            width=JOB_MENU_WIDTH, height=JOB_OPT_HEIGHT)
        self.grid_propagate(0)

        self.parent = parent

        self.label = ttk.Label(self, text=title, font=NORM_FONT)

        self.params_form = ttk.Frame(self)
        
        self.save_dir = tk.StringVar()
        self.save_box = DirEntry(self.params_form, self.save_dir, file_query=True)
        
        self.updating = tk.IntVar()
        self.upd_box = ttk.Checkbutton(self.params_form, text="Updating", variable=self.updating)
        self.upd_box.config(state=tk.DISABLED)
        
        self.save_box.grid(row=0, column=0, padx=5)
        self.upd_box.grid(row=0, column=1)

        self.buttons = ttk.Frame(self)
        self.cancel = ttk.Button(self.buttons, text="Cancel", command=self.close)
        self.start = ttk.Button(self.buttons, text="Start Job")
        
        self.cancel.grid(row=0, column=0, sticky='w')
        self.start.grid(row=0, column=1, sticky='e')

        self.label.grid(row=0, column=0, sticky='we', padx=5, pady=5)
        self.params_form.grid(row=1, column=0, sticky='we', padx=5, pady=5)
        self.buttons.grid(row=2, column=0, sticky='we', padx=5, pady=5)

    def close(self):
        self.grid_forget()
        self.parent.jobOptions.grid(row=JOPR, column=JOPC)

class saved_dSet_Transport(saved_dSet):
    def __init__(self, parent):
        saved_dSet.__init__(self, parent, title="Load Saved Transport Data")
        self.start.bind('<Button-1>', self.append_to_workspace)

    def append_to_workspace(self, *args):
        kwargs = {'path':self.save_dir.get()}
        self.winfo_toplevel().workspace.append_job('transport', params=kwargs, status='old')
        self.close()

class saved_dSet_FFT(saved_dSet):
    def __init__(self, parent):
        saved_dSet.__init__(self, parent, title="Load Saved FFTmap Data")
        self.start.bind('<Button-1>', self.append_to_workspace)

    def append_to_workspace(self, *args):
        kwargs = {'path':self.save_dir.get()}
        self.winfo_toplevel().workspace.append_job('FFTmap', params=kwargs, status='old')
        self.close()

class saved_dSet_FFTb(saved_dSet):
    def __init__(self, parent):
        saved_dSet.__init__(self, parent, title="Load Saved FFTmapb Data")
        self.start.bind('<Button-1>', self.append_to_workspace)

    def append_to_workspace(self, *args):
        kwargs = {'path':self.save_dir.get()}
        self.winfo_toplevel().workspace.append_job('FFTmapb', params=kwargs, status='old')
        self.close()

# Loading New Data
#################################################################################################

class new_dSet(ScrollableFrame):
    def __init__(self, parent, title="Load New Data"):
        ScrollableFrame.__init__(self, parent,
            canvas_width=int((0.9)*JOB_MENU_WIDTH),
            canvas_height=JOB_OPT_HEIGHT)
        self.parent=parent
        
        self.label = ttk.Label(self.scrollable_frame, text=title, font=NORM_FONT)

        self.params_form = ttk.Frame(self.scrollable_frame)

        self.source = tk.StringVar()
        sources = ['local', 'dropbox']

        self.source_upd_block = ttk.Frame(self.params_form)

        self.source_box = ttk.OptionMenu(self.source_upd_block, self.source, 
                                         'local', *sources)
        self.Lsour = ttk.Label(self.source_upd_block, text="Source: ", font=NORM_FONT)

        self.updating = tk.IntVar()
        self.upd_box = ttk.Checkbutton(self.source_upd_block, text="Updating", variable=self.updating)

        self.Lsour.grid(row=0, column=0)
        self.source_box.grid(row=0, column=1)
        self.upd_box.grid(row=0, column=2)
        self.source_upd_block.grid(row=0, column=0)

        self.buttons = ttk.Frame(self.scrollable_frame)
        self.cancel = ttk.Button(self.buttons, text="Cancel", command=self.close)
        self.start = ttk.Button(self.buttons, text="Start Job")
        
        self.cancel.grid(row=0, column=0, sticky='w')
        self.start.grid(row=0, column=1, sticky='e')

        self.label.pack(expand=True, fill='x', pady=5)
        self.params_form.pack(expand=True, fill='x', pady=5)
        self.buttons.pack(expand=True, fill='x', pady=5)

    def close(self):
        self.grid_forget()
        self.parent.jobOptions.grid(row=JOPR, column=JOPC)

class new_dSet_Transport(new_dSet):
    def __init__(self, parent):
        PX, PY = 13, 5
        new_dSet.__init__(self, parent, title="Load New Transport Data")
        self.start.bind('<Button-1>', self.append_to_workspace)

        # def save_data_csv(self, save_folder, tag=None, override_path=None, compression='zip')

        self.specific_params = ttk.Frame(self.params_form)

        self.Lfolder = ttk.Label(self.specific_params, text="Path to Data Folder: ", 
                                 font=NORM_FONT, anchor='e')
        self.folder = tk.StringVar()
        self.folder_browser = DirEntry(self.specific_params, self.folder, width=20)
        self.Lfolder.grid(row=0, column=0, padx=PX, pady=PY, sticky='w')
        self.folder_browser.grid(row=1, column=0, padx=PX, pady=PY, sticky='we')

        self.lbl_entry = ttk.Frame(self.specific_params)

        self.Lstride = ttk.Label(self.lbl_entry, text="Points/Sweep:", 
                                 font=NORM_FONT, anchor='e')
        self.stride = tk.IntVar()
        self.stride_box = ttk.Entry(self.lbl_entry, textvariable=self.stride)
        self.Lstride.grid(row=0, column=0, padx=PX, pady=PY)
        self.stride_box.grid(row=0, column=1, padx=PX, pady=PY)

        self.Lrun_name = ttk.Label(self.lbl_entry, text="Run Name:", 
                                   font=NORM_FONT, anchor='e')
        self.run_name = tk.StringVar()
        self.run_name_box = ttk.Entry(self.lbl_entry, textvariable=self.run_name)
        self.Lrun_name.grid(row=1, column=0, padx=PX, pady=PY)
        self.run_name_box.grid(row=1, column=1, padx=PX, pady=PY)

        self.Lskiprows = ttk.Label(self.lbl_entry, text="Skip Rows:", 
                                   font=NORM_FONT, anchor='e')
        self.skiprows = tk.IntVar()
        self.skiprows_box = ttk.Entry(self.lbl_entry, textvariable=self.skiprows)
        self.Lskiprows.grid(row=2, column=0, padx=PX, pady=PY)
        self.skiprows_box.grid(row=2, column=1, padx=PX, pady=PY)

        self.Lcompression = ttk.Label(self.lbl_entry, text="Compression: ", 
                                      font=NORM_FONT, anchor='e')
        self.compression = tk.StringVar()
        compression_schemes = ['infer', 'zip']
        self.compression_box = ttk.OptionMenu(self.lbl_entry, self.compression, 
                                              'infer', *compression_schemes)
        self.Lcompression.grid(row=3, column=0, padx=PX, pady=PY)
        self.compression_box.grid(row=3, column=1, padx=PX, pady=PY)

        self.colnames_form = ttk.Frame(self.specific_params)
        self.Lcolnames = ttk.Label(self.colnames_form, text="Column Names: ", 
                                   font=NORM_FONT, anchor='e')
        self.colnames_box = tk.Text(self.colnames_form, width=30, height=15, wrap=tk.WORD)
        self.Lcolnames.pack(side='top', padx=PX, pady=PY)
        self.colnames_box.pack(side='bottom', padx=PX, pady=PY, expand=True, fill='both')

        def toggle_source(*args):
            state = self.source.get()
            if state == 'local':
                self.folder_browser.browse_button.grid(row=0, column=1)
            elif state == 'dropbox':
                self.folder_browser.browse_button.grid_forget()

        def toggle_upd(*args):
            if self.updating.get():
                self.stride_box.config(state='!readonly')
            else:
                self.stride_box.config(state='readonly')
                self.stride.set("")

        self.source.trace_add('write', toggle_source)
        self.updating.trace_add('write', toggle_upd)

        self.lbl_entry.grid(row=2, column=0, columnspan=3, sticky='w')
        self.colnames_form.grid(row=3, column=0, columnspan=3, sticky='w')
        self.specific_params.grid(row=1, column=0, columnspan=3)

        self.source.set(CONFIG['new_dSet_transport_settings']['source'])
        self.updating.set(CONFIG['new_dSet_transport_settings']['updating'])
        self.folder.set(CONFIG['new_dSet_transport_settings']['folder'])
        self.stride.set(CONFIG['new_dSet_transport_settings']['stride'])
        self.run_name.set(CONFIG['new_dSet_transport_settings']['run_name'])
        self.skiprows.set(CONFIG['new_dSet_transport_settings']['skiprows'])
        self.compression.set(CONFIG['new_dSet_transport_settings']['compression'])
        self.colnames_box.insert('1.0',
            str(CONFIG['new_dSet_transport_settings']['colnames'])[1:-1].replace(', ',',\n'))

    def append_to_workspace(self, *args):
        kwargs = {
            'source'     : self.source.get(),
            'updating'   : self.updating.get(),
            'folder'     : self.folder.get(),
            'stride'     : None if self.stride.get() == 0 else self.stride.get(),
            'run_name'   : self.run_name.get(),
            'skiprows'   : None if self.skiprows.get() == 0 else self.skiprows.get(),
            'compression': self.compression.get(),
            'colnames'   : 
            literal_eval('{'+ self.colnames_box.get('1.0', tk.END).strip().replace('\n','')+'}')
        }
        self.winfo_toplevel().workspace.append_job('transport', params=kwargs, status='new')
        self.close()

class new_dSet_FFT(new_dSet):
    def __init__(self, parent):
        PX, PY = 13, 5
        new_dSet.__init__(self, parent, title="Load New FFT Data")
        self.start.bind('<Button-1>', self.append_to_workspace)

        self.specific_params = ttk.Frame(self.params_form)

        self.Lfolder = ttk.Label(self.specific_params, text="Path to Data Folder: ", 
                                 font=NORM_FONT, anchor='e')
        self.folder = tk.StringVar()
        self.folder_browser = DirEntry(self.specific_params, self.folder, width=20)
        self.Lfolder.grid(row=0, column=0, padx=PX, pady=PY, sticky='w')
        self.folder_browser.grid(row=1, column=0, padx=PX, pady=PY, sticky='we')

        self.lbl_entry = ttk.Frame(self.specific_params)

        self.Lrun_name = ttk.Label(self.lbl_entry, text="Run Name:", 
                                   font=NORM_FONT, anchor='e')
        self.run_name = tk.StringVar()
        self.run_name_box = ttk.Entry(self.lbl_entry, textvariable=self.run_name)
        self.Lrun_name.grid(row=1, column=0, padx=PX, pady=PY)
        self.run_name_box.grid(row=1, column=1, padx=PX, pady=PY)

        self.Lskiprows = ttk.Label(self.lbl_entry, text="Skip Rows:", 
                                   font=NORM_FONT, anchor='e')
        self.skiprows = tk.IntVar()
        self.skiprows_box = ttk.Entry(self.lbl_entry, textvariable=self.skiprows)
        self.Lskiprows.grid(row=2, column=0, padx=PX, pady=PY)
        self.skiprows_box.grid(row=2, column=1, padx=PX, pady=PY)

        self.Lcompression = ttk.Label(self.lbl_entry, text="Compression: ", 
                                      font=NORM_FONT, anchor='e')
        self.compression = tk.StringVar()
        compression_schemes = ['infer', 'zip']
        self.compression_box = ttk.OptionMenu(self.lbl_entry, self.compression, 
                                              'zip', *compression_schemes)
        self.Lcompression.grid(row=3, column=0, padx=PX, pady=PY)
        self.compression_box.grid(row=3, column=1, padx=PX, pady=PY)

        self.LdBmode = ttk.Label(self.lbl_entry, text="dBmode: ", 
                                      font=NORM_FONT, anchor='e')
        self.dBmode = tk.StringVar()
        dBmodes = ['power', 'voltage', 'ignore']
        self.dBmode_box = ttk.OptionMenu(self.lbl_entry, self.dBmode, 
                                              'power', *dBmodes)
        self.LdBmode.grid(row=4, column=0, padx=PX, pady=PY)
        self.dBmode_box.grid(row=4, column=1, padx=PX, pady=PY)

        self.colnames_form = ttk.Frame(self.specific_params)
        self.Lcolnames = ttk.Label(self.colnames_form, text="Column Names: ", 
                                   font=NORM_FONT, anchor='e')
        self.colnames_box = tk.Text(self.colnames_form, width=30, height=15, wrap=tk.WORD)
        self.Lcolnames.pack(side='top', padx=PX, pady=PY)
        self.colnames_box.pack(side='bottom', padx=PX, pady=PY, expand=True, fill='both')

        def toggle_source(*args):
            state = self.source.get()
            if state == 'local':
                self.folder_browser.browse_button.grid(row=0, column=1)
            elif state == 'dropbox':
                self.folder_browser.browse_button.grid_forget()

        # def toggle_upd(*args):
        #     if self.updating.get():
        #         self.stride_box.config(state='!readonly')
        #     else:
        #         self.stride_box.config(state='readonly')
        #         self.stride.set("")

        self.source.trace_add('write', toggle_source)
        # self.updating.trace_add('write', toggle_upd)

        self.lbl_entry.grid(row=2, column=0, columnspan=3, sticky='w')
        self.colnames_form.grid(row=3, column=0, columnspan=3, sticky='w')
        self.specific_params.grid(row=1, column=0, columnspan=3)

        self.source.set(CONFIG['new_dSet_FFT_settings']['source'])
        self.updating.set(0)
        self.upd_box.config(state=tk.DISABLED)
        self.folder.set(CONFIG['new_dSet_FFT_settings']['folder'])
        # self.stride.set(CONFIG['new_dSet_FFT_settings']['stride'])
        self.run_name.set(CONFIG['new_dSet_FFT_settings']['run_name'])
        self.skiprows.set(CONFIG['new_dSet_FFT_settings']['skiprows'])
        self.compression.set(CONFIG['new_dSet_FFT_settings']['compression'])
        self.dBmode.set(CONFIG['new_dSet_FFT_settings']['dBmode'])
        self.colnames_box.insert('1.0',
            str(CONFIG['new_dSet_FFT_settings']['colnames'])[1:-1].replace(', ',',\n'))

    def append_to_workspace(self, *args):
        kwargs = {
            'source'     : self.source.get(),
            # 'updating'   : self.updating.get(),
            'folder'     : self.folder.get(),
            'run_name'   : self.run_name.get(),
            'skiprows'   : None if self.skiprows.get() == 0 else self.skiprows.get(),
            'compression': self.compression.get(),
            'dBmode': self.dBmode.get(),
            'colnames'   : 
            literal_eval('{'+ self.colnames_box.get('1.0', tk.END).strip().replace('\n','')+'}')
        }
        self.winfo_toplevel().workspace.append_job('FFTmap', params=kwargs, status='new')
        self.close()
        
class new_dSet_FFTb(new_dSet):
    def __init__(self, parent):
        PX, PY = 13, 5
        new_dSet.__init__(self, parent, title="Load New FFTmapb Data")
        self.start.bind('<Button-1>', self.append_to_workspace)

        self.specific_params = ttk.Frame(self.params_form)

        self.Lfolder = ttk.Label(self.specific_params, text="Path to Data Folder: ", 
                                 font=NORM_FONT, anchor='e')
        self.folder = tk.StringVar()
        self.folder_browser = DirEntry(self.specific_params, self.folder, width=20)
        self.Lfolder.grid(row=0, column=0, padx=PX, pady=PY, sticky='w')
        self.folder_browser.grid(row=1, column=0, padx=PX, pady=PY, sticky='we')

        self.lbl_entry = ttk.Frame(self.specific_params)

        self.Lrun_name = ttk.Label(self.lbl_entry, text="Run Name:", 
                                   font=NORM_FONT, anchor='e')
        self.run_name = tk.StringVar()
        self.run_name_box = ttk.Entry(self.lbl_entry, textvariable=self.run_name)
        self.Lrun_name.grid(row=1, column=0, padx=PX, pady=PY)
        self.run_name_box.grid(row=1, column=1, padx=PX, pady=PY)

        self.Lnull_run_name = ttk.Label(self.lbl_entry, text="Null Run Name:", 
                                   font=NORM_FONT, anchor='e')
        self.Lnull_run_name2 = ttk.Label(self.lbl_entry, text="(leave blank if same)", 
                                   font=NORM_FONT, anchor='e')
        self.null_run_name = tk.StringVar()
        self.null_run_name_box = ttk.Entry(self.lbl_entry, textvariable=self.null_run_name)
        self.Lnull_run_name.grid(row=2, column=0, padx=PX, pady=PY)
        self.null_run_name_box.grid(row=2, column=1, padx=PX, pady=PY)
        self.Lnull_run_name2.grid(row=3, column=0, padx=PX, pady=0, columnspan=2)

        self.Lskiprows = ttk.Label(self.lbl_entry, text="Skip Rows:", 
                                   font=NORM_FONT, anchor='e')
        self.skiprows = tk.IntVar()
        self.skiprows_box = ttk.Entry(self.lbl_entry, textvariable=self.skiprows)
        self.Lskiprows.grid(row=4, column=0, padx=PX, pady=PY)
        self.skiprows_box.grid(row=4, column=1, padx=PX, pady=PY)

        self.Lcompression = ttk.Label(self.lbl_entry, text="Compression: ", 
                                      font=NORM_FONT, anchor='e')
        self.compression = tk.StringVar()
        compression_schemes = ['infer', 'zip']
        self.compression_box = ttk.OptionMenu(self.lbl_entry, self.compression, 
                                              'zip', *compression_schemes)
        self.Lcompression.grid(row=5, column=0, padx=PX, pady=PY)
        self.compression_box.grid(row=5, column=1, padx=PX, pady=PY)

        self.LdBmode = ttk.Label(self.lbl_entry, text="dBmode: ", 
                                      font=NORM_FONT, anchor='e')
        self.dBmode = tk.StringVar()
        dBmodes = ['power', 'voltage', 'ignore']
        self.dBmode_box = ttk.OptionMenu(self.lbl_entry, self.dBmode, 
                                              'power', *dBmodes)
        self.LdBmode.grid(row=6, column=0, padx=PX, pady=PY)
        self.dBmode_box.grid(row=6, column=1, padx=PX, pady=PY)

        self.colnames_form = ttk.Frame(self.specific_params)
        self.Lcolnames = ttk.Label(self.colnames_form, text="Column Names: ", 
                                   font=NORM_FONT, anchor='e')
        self.colnames_box = tk.Text(self.colnames_form, width=30, height=15, wrap=tk.WORD)
        self.Lcolnames.pack(side='top', padx=PX, pady=PY)
        self.colnames_box.pack( padx=PX, pady=PY, expand=True, fill='both')

        self.null_colnames_form = ttk.Frame(self.specific_params)
        self.Lnull_colnames = ttk.Label(self.colnames_form, text="Null Column Names: \n(leave blank if same)", 
                                   font=NORM_FONT, anchor='e')
        self.null_colnames_box = tk.Text(self.colnames_form, width=30, height=15, wrap=tk.WORD)
        self.Lnull_colnames.pack(padx=PX, pady=PY)
        self.null_colnames_box.pack(side='bottom', padx=PX, pady=PY, expand=True, fill='both')

        def toggle_source(*args):
            state = self.source.get()
            if state == 'local':
                self.folder_browser.browse_button.grid(row=0, column=1)
            elif state == 'dropbox':
                self.folder_browser.browse_button.grid_forget()

        # def toggle_upd(*args):
        #     if self.updating.get():
        #         self.stride_box.config(state='!readonly')
        #     else:
        #         self.stride_box.config(state='readonly')
        #         self.stride.set("")

        self.source.trace_add('write', toggle_source)
        # self.updating.trace_add('write', toggle_upd)

        self.lbl_entry.grid(row=2, column=0, columnspan=3, sticky='w')
        self.colnames_form.grid(row=3, column=0, columnspan=3, sticky='w')
        self.specific_params.grid(row=1, column=0, columnspan=3)

        self.source.set(CONFIG['new_dSet_FFTb_settings']['source'])
        self.updating.set(0)
        self.upd_box.config(state=tk.DISABLED)
        self.folder.set(CONFIG['new_dSet_FFTb_settings']['folder'])
        # self.stride.set(CONFIG['new_dSet_FFT_settings']['stride'])
        self.run_name.set(CONFIG['new_dSet_FFTb_settings']['run_name'])
        self.null_run_name.set(CONFIG['new_dSet_FFTb_settings']['null_run_name'])
        self.skiprows.set(CONFIG['new_dSet_FFTb_settings']['skiprows'])
        self.compression.set(CONFIG['new_dSet_FFTb_settings']['compression'])
        self.dBmode.set(CONFIG['new_dSet_FFTb_settings']['dBmode'])
        self.colnames_box.insert('1.0',
            str(CONFIG['new_dSet_FFTb_settings']['colnames'])[1:-1].replace(', ',',\n'))
        self.null_colnames_box.insert('1.0',
            str(CONFIG['new_dSet_FFTb_settings']['null_colnames'])[1:-1].replace(', ',',\n'))

    def append_to_workspace(self, *args):
        kwargs = {
            'source'     : self.source.get(),
            # 'updating'   : self.updating.get(),
            'folder'     : self.folder.get(),
            'run_name'   : self.run_name.get(),
            'skiprows'   : None if self.skiprows.get() == 0 else self.skiprows.get(),
            'compression': self.compression.get(),
            'dBmode': self.dBmode.get(),
            'colnames'   : 
            literal_eval('{'+ self.colnames_box.get('1.0', tk.END).strip().replace('\n','')+'}')
        }

        if self.null_run_name.get() == '':
            kwargs['null_run_name'] = kwargs['run_name'] 
        else: 
            kwargs['null_run_name'] = self.null_run_name.get()

        if self.colnames_box.get('1.0', tk.END).strip() == '':
            kwargs['null_colnames'] = kwargs['colnames'] 
        else: 
            kwargs['null_colnames'] = literal_eval('{'+ 
                self.null_colnames_box.get('1.0', tk.END).strip().replace('\n','')+'}')
            
        self.winfo_toplevel().workspace.append_job('FFTmapb', params=kwargs, status='new')
        self.close()
        
#################################################################################################