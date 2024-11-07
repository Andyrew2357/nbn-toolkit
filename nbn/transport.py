from . import *
import logging

REQUIRED_COLUMNS = ()

class Transport:
    def __init__(self, Data=None, meta=None):
        if Data is not None and not isinstance(Data, pd.DataFrame):
            raise TypeError("Data should be type pd.DataFrame")
        
        if not all(n in Data.columns for n in REQUIRED_COLUMNS):
            warnings.warn("""Not all required columns are represented in Data. Some 
                          functions may not work without these columns. To see a 
                          list of required columns, call get_req_cols()""")

        self.Data = Data
        self.meta = meta
        self.completed_files = set()

    def __repr__(self):
        return '<nbn-toolkit Transport object>'
    
    def __str__(self):
        return 'Transport()'
    
    def console_log(self, msg, verbose):
        if verbose is None: return
        logging.info(f"{verbose}: {msg}")        

    #################################################################################################

    def get_req_cols(self):
        return REQUIRED_COLUMNS

    def get_data(self):
        return self.Data, self.meta
    
    def set_data(self, Data, meta=None):
        if not isinstance(Data, pd.DataFrame):
            raise TypeError("Data should be type pd.DataFrame")
        
        if not all(n in Data.columns for n in REQUIRED_COLUMNS):
            warnings.warn("""Not all required columns are represented in Data. Some 
                          functions may not work without these columns. To see a 
                          list of required columns, call get_req_cols()""")
        
        self.Data = Data
        self.meta = meta

    def init_data_from_sweeps(self, folder, run_name, colnames, source='local', skiprows=None, 
                            compression='infer', dbx=None, verbose=False):
        
        if not all(n in colnames for n in REQUIRED_COLUMNS):
            warnings.warn("""Not all required columns are represented in colnames.
                          Some functions may not work without these columns. To see
                          a list of required columns, call get_req_cols()""")
        
        if 'ind' in colnames: 
            raise Exception("Column name 'ind' in colnames is protected. Please use a different name.")
        nameswap = {colnames[k]:k for k in colnames}

        self.console_log(f"STARTING. source: {source}, folder: {folder}", verbose)
        match source:
            case 'local':
                if not os.path.isdir(folder): raise FileNotFoundError(f"{folder} does not exist.")
                sweep_paths = [os.path.join(folder, fname) for fname in os.listdir(folder)
                               if run_name in fname]
                num_files = len(sweep_paths)
                self.console_log(f"Initializing Data from {num_files} in Local Folder: {folder}", verbose)
                
                for p, path in enumerate(sweep_paths):
                    self.console_log(f"Reading Data from {path} ... ({p+1}/{num_files})", verbose)
                    df = pd.read_csv(path, delimiter=r"\s*\t\s*", engine="python", skiprows=skiprows, 
                                     compression=compression).rename(nameswap, axis='columns')
                    df['ind'] = p
                    try:
                        Data = pd.concat([Data, df])
                    except:
                        Data = df.copy()

            case 'dropbox':
                if dbx is None: raise Exception("dbx is required if source is 'dropbox'.")
                sweep_paths = [f'{folder}/{fname}' for fname in dbx.listdir(folder)
                               if run_name in fname]
                num_files = len(sweep_paths)
                self.console_log(f"Initializing Data from {num_files} in Local Folder: {folder}", verbose)
                
                for p, path in enumerate(sweep_paths):
                    self.console_log(f"Reading Data from {path} ... ({p+1}/{num_files})", verbose)
                    df = dbx.open_trace(path, skiprows=skiprows, 
                                    compression=compression).rename(nameswap, axis='columns')
                    df['ind'] = p
                    try:
                        Data = pd.concat([Data, df])
                    except:
                        Data = df.copy()

            case _:
                raise Exception(f"{source} is not a recognized source. Use 'local' or 'dropbox'.")

        self.Data = Data
        self.meta = {}
        self.meta['colnames'] = colnames
        self.meta['run_name'] = run_name

    def init_data(self, path):
        with open(path, 'r') as f:
            self.meta = json.load(f)
            self.Data = pd.read_csv(self.meta['transport_path'], sep=',', 
                                    compression=self.meta['compression'])

    def save_data_csv(self, save_folder, tag=None, override_path=None, compression='zip'):
        if self.Data is None or self.meta is None: 
            raise AttributeError("Data and meta have not been properly initialized.")
        
        if tag is None: tag = self.meta['run_name']
        if override_path is None:
            transport_path = os.path.join(save_folder, f'{tag}_Transport.csv')
        else:
            transport_path = override_path + '_Transport.csv'

        self.meta['compression'] = compression
        self.meta['transport_path'] = transport_path
        self.Data.to_csv(transport_path, sep=',', compression=compression)
        self.save_meta_json(save_folder, tag, override_path)

    def save_meta_json(self, save_folder, tag=None, override_path=None):
        if self.Data is None or self.meta is None: 
            raise AttributeError("Data and meta have not been properly initialized.")

        if tag is None: tag = self.meta['run_name']
        if override_path is None:
            json_path = os.path.join(save_folder, f'{tag}.json')
        else:
            json_path = override_path + '.json'

        with open(json_path, 'w') as f:
            json.dump(self.meta, f, ensure_ascii=True, indent=4)

    # updating data (useful if the data is being appended to live)
    #################################################################################################

    def update_data_from_sweeps(self, folder, run_name, stride, colnames, source='local', 
                                skiprows=None, compression='infer', dbx=None, verbose=False):
        
        if not all(n in colnames for n in REQUIRED_COLUMNS):
            warnings.warn("""Not all required columns are represented in colnames.
                          Some functions may not work without these columns. To see
                          a list of required columns, call get_req_cols()""")
        
        if 'ind' in colnames: 
            raise Exception("Column name 'ind' in colnames is protected. Please use a different name.")
        nameswap = {colnames[k]:k for k in colnames}

        match source:
            case 'local':
                if not os.path.isdir(folder): raise FileNotFoundError(f"{folder} does not exist.")
                sweep_paths = [os.path.join(folder, fname) for fname in os.listdir(folder)
                               if run_name in fname]
                
                for p, path in enumerate(sweep_paths):
                    if path in self.completed_files: continue

                    df = pd.read_csv(path, delimiter=r"\s*\t\s*", engine="python", skiprows=skiprows, 
                                     compression=compression).rename(nameswap, axis='columns')
                    df['ind'] = p
                    if len(df) >= stride: self.completed_files.add(path)

                    try:
                        Data = Data.merge(df, how='outer')
                    except:
                        Data = df.copy()

            case 'dropbox':
                if dbx is None: raise Exception("dbx is required if source is 'dropbox'.")
                sweep_paths = [f'{folder}/{fname}' for fname in dbx.listdir(folder)
                               if run_name in fname]
                
                for p, path in enumerate(sweep_paths):
                    if path in self.completed_files: continue

                    df = dbx.open_trace(path, skiprows=skiprows, 
                                    compression=compression).rename(nameswap, axis='columns')
                    df['ind'] = p
                    if len(df) >= stride: self.completed_files.add(path)

                    try:
                        Data = Data.merge(df, how='outer')
                    except:
                        Data = df.copy()

            case _:
                raise Exception(f"{source} is not a recognized source. Use 'local' or 'dropbox'.")

        if self.Data is None:
            self.Data = Data
        else:
            self.Data = self.Data.merge(Data, how='outer')
        
        self.meta = {}
        self.meta['colnames'] = colnames
        self.meta['run_name'] = run_name

    def clear_history(self):
        self.completed_files.clear()
        self.Data = None
