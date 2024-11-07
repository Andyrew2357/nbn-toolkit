from . import *
from .file_utils import beautify_fft
import logging

REQUIRED_META_FIELDS = ('freq', 'Vbias')

class FFTmap:
    def __init__(self, Data=None, meta=None):
        #DO PROPER INPUT VALIDATION RIGHT NOW THIS IS SILLY
        self.Data = Data
        self.meta = meta

    def __repr__(self):
        return '<nbn-toolkit FFTmap object>'
    
    def __str__(self):
        return 'FFTmap()'

    def console_log(self, msg, verbose):
        if verbose is None: return
        logging.info(f"{verbose}: {msg}")

    #################################################################################################
    
    def get_req_meta_fields(self):
        return REQUIRED_META_FIELDS

    def get_data(self):
        return self.Data, self.meta

    def set_data(self, Data, meta=None):
        N, M = Data.shape
        self.Data = Data
        if meta is None:
            self.meta = {'freq':np.arange(N), 'Vbias':np.arange(M)}
        
        self.meta = meta

        if not all(n in meta['colnames'] for n in REQUIRED_META_FIELDS):
            warnings.warn("""Not all required fields are represented in colnames.
                          Some functions may not work without these fields. To see
                          a list of required fields, call get_req_meta_fields()""")

    def get_data_shape(self):
        return self.Data.shape

    def init_data_from_sweeps(self, folder, run_name, colnames, source='local', skiprows=None, 
                              compression='zip', dBmode='power', dbx=None, verbose=False):
        if not all(n in colnames for n in REQUIRED_META_FIELDS):
            warnings.warn("""Not all required fields are represented in colnames.
                          Some functions may not work without these fields. To see
                          a list of required fields, call get_req_meta_fields()""")
        
        if not 'spec' in colnames:
            raise KeyError("colnames must have a 'spec' field.")
        if not 'freq' in colnames:
            raise KeyError("colnames must have a 'freq' field.")
        
        self.dBmode = dBmode
        match dBmode:
            case 'power':
                dBfactor = 20
            case 'voltage':
                dBfactor = 10
            case 'ignore':
                pass
            case _:
                try:
                    dBfactor = float(dBmode)
                except ValueError:
                    raise Exception(f"""{dBmode} is not a valid dBmode. 
                                    Try 'power', 'voltage', 'ignore', or a number.""")
                
        meta = {k:[] for k in colnames if k not in ('spec', 'freq')}
        nameswap = {colnames[k]:k for k in colnames}

        self.console_log(f"STARTING. source: {source}, folder: {folder}", verbose)
        match source:
            case 'local':
                if not os.path.isdir(folder): raise FileNotFoundError(f"{folder} does not exist.")
                sweep_paths = [os.path.join(folder, fname) for fname in os.listdir(folder)
                               if run_name in fname]
                N=len(sweep_paths)
                self.console_log(f"Initializing Data from {N} in Local Folder: {folder}", verbose)

                for p, path in enumerate(sweep_paths):
                    self.console_log(f"Reading Data from {path} ... ({p+1}/{N})", verbose)
                    df = pd.read_csv(path, delimiter=r"\s*\t\s*", engine="python", 
                                skiprows=skiprows, compression=compression)
                    df = beautify_fft(df).rename(nameswap, axis='columns')

                    for k in meta: 
                        if k == 'freq': continue
                        meta[k].append(df[colnames[k]][0])

                    try:
                        FFT_map[:, p]+=pd.to_numeric(df['spec'].to_numpy())
                    except:
                        FFT_map = np.zeros((len(df['spec']), N))
                        FFT_map[:, 0]+=pd.to_numeric(df['spec'].to_numpy())
                        meta['freq'] = df['freq'].to_list()

            case 'dropbox':
                if dbx is None: raise Exception("dbx is required if source is 'dropbox'.")
                sweep_paths = [f'{folder}/{fname}' for fname in dbx.listdir(folder) 
                               if run_name in fname]
                N=len(sweep_paths)
                self.console_log(f"Initializing Data from {N} in Local Folder: {folder}", verbose)

                for p, path in enumerate(sweep_paths):
                    self.console_log(f"Reading Data from {path} ... ({p+1}/{N})", verbose)
                    df = dbx.open_fft(path, skiprows=skiprows, 
                            compression=compression).rename(nameswap, axis='columns')
                    
                    for k in meta: 
                        if k == 'freq': continue
                        meta[k].append(df[k][0])

                    try:
                        FFT_map[:, p]+=pd.to_numeric(df['spec'].to_numpy())
                    except:
                        FFT_map = np.zeros((len(df['spec']), N))
                        FFT_map[:, 0]+=pd.to_numeric(df['spec'].to_numpy())
                        meta['freq'] = df['freq'].to_list()

            case _:
                raise Exception(f"{source} is not a recognized source. Use 'local' or 'dropbox'.")
        
        meta['dBmode'] = dBmode
        meta['run_name'] = run_name
        meta['colnames'] = colnames

        self.Data = FFT_map
        self.meta = meta

    def init_data(self, path):
        with open(path, 'r') as f:
            self.meta = json.load(f)
            self.Data = np.genfromtxt(self.meta['spec_path'], delimiter=',')

    def save_data_csv(self, save_folder, tag=None, override_path=None):
        if self.Data is None or self.meta is None:
            raise AttributeError("Data and meta have not been properly initialized.")
        
        if tag is None: tag = self.meta['run_name']
        if override_path is None:
            spec_path = os.path.join(save_folder, f'{tag}_FFT_map.csv')
        else:
            spec_path = override_path + '_FFT_map.csv'

        np.savetxt(spec_path, self.Data, delimiter=",")

        self.meta['spec_path'] = spec_path
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
