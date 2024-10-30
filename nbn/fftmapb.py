from . import *
from .file_utils import beautify_fft

REQUIRED_META_FIELDS = ('freq', 'Vbias')

class FFTmapb:
    def __init__(self, spectra=None, background=None, meta=None):
        #DO PROPER INPUT VALIDATION RIGHT NOW THIS IS SILLY
        if (spectra is not None or background is not None) and not spectra.shape == background.shape:
            raise Exception("spectra and background must be ndarrays with the same shape.")

        self.spectra = spectra
        self.background = background
        self.meta = meta

    def __repr__(self):
        return '<nbn-toolkit FFTmapb object>'
    
    def __str__(self):
        return 'FFTmapb()'

    def console_log(self, msg, verbose):
        if verbose: print(msg)    

    #################################################################################################
    
    def get_req_meta_fields(self):
        return REQUIRED_META_FIELDS

    def get_data(self):
        return self.spectra, self.background, self.meta

    def set_data(self, spectra, background, meta=None):
        if not spectra.shape == background.shape:
            raise Exception("spectra and background must be ndarrays with the same shape.")
        
        N, M = spectra.shape
        self.spectra = spectra
        self.background = background

        if meta is None:
            self.meta = {'freq':np.arange(N), 'Vbias':np.arange(M)}
        
        self.meta = meta

        if not all(n in meta['colnames'] for n in REQUIRED_META_FIELDS):
            warnings.warn("""Not all required fields are represented in colnames.
                          Some functions may not work without these fields. To see
                          a list of required fields, call get_req_meta_fields()""")

    def get_data_shape(self):
        return self.spectra.shape

    def init_data_from_sweeps(self, folder, run_name, null_run_name, colnames, null_colnames=None, 
            source='local', skiprows=None, compression='zip', dBmode='power', dbx=None, verbose=False):
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

        if null_colnames == None:
            null_colnames = colnames
        elif not set(colnames) == set(null_colnames):
            raise Exception("colnames and null_colnames must have the same keys.")

        spectra, meta_spectra = self.init_partial_from_sweeps(folder, run_name, colnames, 
            source=source, dbx=dbx, skiprows=skiprows, compression=compression)
        background, meta_background = self.init_partial_from_sweeps(folder, null_run_name, 
            null_colnames, source=source, dbx=dbx, skiprows=skiprows, compression=compression)
    
        meta = {}
        for k in meta_spectra:
            meta[k] = meta_spectra[k]
            meta[f'{k}_background'] = meta_background[k]
                
        meta['dBmode'] = dBmode
        meta['run_name'] = run_name
        meta['null_run_name'] = null_run_name
        meta['null_colnames'] = null_colnames
        meta['colnames'] = colnames
        meta['null_colnames'] = null_colnames

        self.spectra = spectra
        self.background = background
        self.meta = meta

    def init_partial_from_sweeps(self, folder, run_name, colnames, source='local', 
                                 dbx=None, skiprows=None, compression='zip'):
        meta = {k:[] for k in colnames if k not in ('spec', 'freq')}
        nameswap = {colnames[k]:k for k in colnames}

        match source:
            case 'local':
                if not os.path.isdir(folder): raise FileNotFoundError(f"{folder} does not exist.")
                sweep_paths = [os.path.join(folder, fname) for fname in os.listdir(folder)
                               if run_name in fname]
                
                N=len(sweep_paths)
                for p, path in enumerate(sweep_paths):
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
                for p, path in enumerate(sweep_paths):
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
            
        return FFT_map, meta

    def init_data(self, path):
        with open(path, 'r') as f:
            self.meta = json.load(f)
            self.spectra = np.genfromtxt(self.meta['spec_path'], delimiter=',')
            self.background = np.genfromtxt(self.meta['back_path'], delimiter=',')

    def save_data_csv(self, save_folder, tag=None, override_path=None):
        if self.spectra is None or self.background is None or self.meta is None:
            raise AttributeError("spectra, background, and meta have not been properly initialized.")
        
        if tag is None: tag = self.meta['run_name']
        if override_path is None:
            spec_path = os.path.join(save_folder, f'{tag}_FFTb_spectra.csv')
        else:
            spec_path = override_path + '_FFTb_spectra.csv'

        np.savetxt(spec_path, self.spectra, delimiter=",")
        self.meta['spec_path'] = spec_path

        if override_path is None:
            back_path = os.path.join(save_folder, f'{tag}_FFTb_background.csv')
        else:
            back_path = override_path + '_FFTb_background.csv'

        np.savetxt(back_path, self.background, delimiter=",")
        self.meta['back_path'] = back_path

        self.save_meta_json(save_folder, tag, override_path)

    def save_meta_json(self, save_folder, tag=None, override_path=None):
        if self.spectra is None or self.background is None or self.meta is None:
            raise AttributeError("spectra, background, and meta have not been properly initialized.")
        
        if tag is None: tag = self.meta['run_name']
        if override_path is None:
            json_path = os.path.join(save_folder, f'{tag}.json')
        else:
            json_path = override_path + '.json'

        with open(json_path, 'w') as f:
            json.dump(self.meta, f, ensure_ascii=True, indent=4)
