# DESIGNED TO WORK WITH FFTmapb
from . import *

def cross_correlate(spectra, background, meta, N, fl, fh):
    freq = np.array(meta['freq'])
    Vbias = np.array(meta['Vbias'])
    fl, fh
    r0 = np.abs(freq - fl).argmin()
    r1 = np.abs(freq - fh).argmin()
    Nfbin = (r1-r0)//N

    Vbunique = np.unique(Vbias)
    Ncols = Vbunique.size
    CC = np.zeros((N, Ncols))

    # this is a cumbersome way of doing this, but I want to avoid weird edge cases
    # that can arise if the data is taken slightly differently than I assumed.
    for i, V in enumerate(Vbunique):
        back_subtracted = spectra[r0:r1, Vbias == V] - background[r0:r1, Vbias == V]
        C = (back_subtracted[:,0]*back_subtracted[:,1]).flatten()
        CC[:, i]+= C[:N*Nfbin].reshape(N, Nfbin).sum(1)

    return CC, Vbunique, np.linspace(fl, fh, N)