from . import *

# DESIGNED TO WORK WITH FFTmapb
def cross_correlate(spectra, background, freq, Vbias, N, fl, fh):
    r0 = np.abs(freq - fl).argmin()
    r1 = np.abs(freq - fh).argmin()
    r0, r1 = (r0, r1) if r0<r1 else (r1, r0)
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

def integrated_power(spectra, freq, fl, fh, background=None):
    r0 = np.abs(freq - fl).argmin()
    r1 = np.abs(freq - fh).argmin()
    r0, r1 = (r0, r1) if r0<r1 else (r1, r0)

    if background is None:
        V2 = 10**(spectra[r0:r1,:]/10)
    else:
        M = min(spectra.shape[1], background.shape[1])
        V2 = (10**(spectra[r0:r1,:M]/20) - 10**(background[r0:r1,:M]/20))**2

    return V2.mean(0)/(freq[r1] - freq[r0])