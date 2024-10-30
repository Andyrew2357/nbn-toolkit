import dropbox
import io

from . import *
from .file_utils import beautify_fft

class DBX:
    def __init__(self, app_key=None, app_secret=None):
        self.app_key = app_key
        self.app_secret = app_secret

    def __repr__(self):
        return '<nbn-toolkit DBX object>'
    
    def __str__(self):
        return f'app_key = {self.app_key}, app_secret = {self.app_secret}'
    
    def console_log(self, msg, verbose):
        if verbose: print(msg)
    
    #################################################################################################    

    def set_app_key(self, app_key):
        self.app_key = app_key

    def set_app_secret(self, app_secret):
        self.app_secret = app_secret

    def start_oauth(self):
        if self.app_key is None: raise AttributeError("Please provide an app_key.")
        if self.app_secret is None: raise AttributeError("Please provide an app_secret.")

        self.auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(self.app_key, self.app_secret)
        self.auth_url = self.auth_flow.start()
    
    def finish_oauth(self, auth_code):
        self.oauth_result = self.auth_flow.finish(auth_code)
        self.dbx = dropbox.Dropbox(oauth2_access_token=self.oauth_result.access_token,
                                   oauth2_access_token_expiration=self.oauth_result.expires_at,
                                   oauth2_refresh_token=self.oauth_result.refresh_token,
                                   app_key=self.app_key,
                                   app_secret=self.app_secret)

    def get_auth_url(self):
        try:
            return self.auth_url
        except:
            raise AttributeError("auth_url does not exist. Try calling start_oauth first.")

    def oauth_from_console(self):
        self.start_oauth()

        print("1. Go to: " + self.auth_url)
        print("2. Click \"Allow\" (you might have to log in first).")
        print("3. Copy the authorization code.")
        auth_code = input("Enter the authorization code here: ").strip()

        self.finish_oauth(auth_code)

    #################################################################################################

    def listdir(self, folder):
        """returns a list of files from a dropbox. """

        # make an initial API call. This should cover the first 500
        # files in the folder
        listed = self.dbx.files_list_folder(folder)
        files = [e.name for e in listed.entries]
        
        # keep making API calls until all files have been listed
        while listed.has_more:
            listed = self.dbx.files_list_folder_continue(listed.cursor)
            files = [*files, *[e.name for e in listed.entries]]

        return files
    
    def open_trace(self, path, skiprows=None, compression='infer'):
        """reads regular files such as those produced during parameter sweeps."""

        # make an API call to request the file data from dropbox
        metadata, f = self.dbx.files_download(path)
        # convert the data from bytes into a file-like object
        filelike = io.BytesIO(f.content)
        # read the file-like object into a dataframe
        D = pd.read_csv(filelike, delimiter=r"\s*\t\s*", engine="python", 
                        skiprows=skiprows, compression=compression)

        return D
    
    def open_fft(self, path, skiprows=None, compression='zip'):
        """reads an FFT file from dropbox into a pandas Dataframe."""
        
        return beautify_fft(self.open_trace(path, skiprows=skiprows, 
                                            compression=compression))
    
    def extract_header(self, path, skiprows=None, compression='infer'):
        df = self.open_trace(path, skiprows=skiprows, compression=compression)
        print(df.columns)