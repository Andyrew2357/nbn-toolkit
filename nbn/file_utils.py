from . import *

def beautify_fft(D):
    """The format of the dataframe is initially messed up, because some of
    the columns are partially full. This fixes it by shifting some columns"""

    dt = D["#Timestamp"][0]
    D.iloc[[0]] = D.iloc[[0]].shift(-1, axis=1)
    h = D.columns[1:]
    D = D.iloc[:,:-1]
    D.columns = h
    D.insert(0, "#Timestamp", dt)

    return D

def extract_header(path, skiprows=None, compression='infer'):
    df = pd.read_csv(path, delimiter=r"\s*\t\s*", engine="python", 
                    skiprows=skiprows, compression=compression)
    print(df.columns)