from . import *
from .utils import gaussian_filter, background_subtracted

class slider_params:
    def __init__(self, wmin, wmax):
        self.wmin = wmin
        self.wmax = wmax

def slider_filter(Data, meta, params):
    wmax = params.wmax

    im = np.pad(background_subtracted(im), wmax)

    