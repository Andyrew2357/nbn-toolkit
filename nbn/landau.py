from . import *

from .util_params import *
from .utils import dbscan, dog, VbVt_to_nD, nD_to_VbVt, transform_pnts

from scipy.signal import find_peaks
from scipy import odr

class landau_params:
    def __init__(self, w1, w2, w, eps, min_samples, trans, ind):
        self.w1 = w1
        self.w2 = w2
        self.w = w
        self.eps = eps
        self.min_samples = min_samples
        self.trans = trans
        self.ind = ind

def guess_good_args(X, Y, ind, guess_Cb, guess_Ct, num_levels):
    C = VbVt_to_nD(guess_Cb, guess_Ct)
    tpnts = transform_pnts(C, np.concatenate([X.reshape(1, -1), 
                                    Y.reshape(1, -1)], axis=0).T)
    xextent = tpnts[:,0].max() - tpnts[:,0].min()
    yextent = tpnts[:,1].max() - tpnts[:,1].min()
    B = np.array([[5/xextent, 0],[0, 1/yextent]])

    A = np.dot(B, C)

    stride = np.count_nonzero(ind == 0)

    w1 = 0.1*stride/num_levels
    w2 = 5*w1
    w = w1
    
    eps = EPS
    min_samples = MIN_SAMP

    return landau_params(w1, w2, w, eps, min_samples, A, ind)

def sweep_ridges(sweep, params):
    w1, w2 = params.w1, params.w2
    ridges, _ = find_peaks(dog(sweep, w1, w2))
    return ridges    

def all_sweep_ridges(X, Y, Z, params):
    ind = params.ind
    N = ind.size
    s = np.count_nonzero(ind == 0)
    M = N//s
    r = N%s

    pnts = []
    sweeps = Z[:M*s].reshape(M, s)
    for p, sweep in enumerate(sweeps):
        ridges = sweep_ridges(sweep, params)
        for r in ridges: pnts.append([X[p*s + r], Y[p*s + r]])

    return np.array(pnts)

def sweep_peaks(sweep, pnts, params):
    w = params.w
    N = pnts.size
    peaks = np.zeros(N)
    M = sweep.size

    for i,r in enumerate(pnts):
        l, h = int(max(0, r - w//2)), int(min(M - 1, r + w//2))
        peaks[i]+=l + np.argmax(sweep[l:h])
    
    return peaks.astype(int)

def all_sweep_peaks(X, Y, Z, params):
    ind = params.ind

    N = ind.size
    s = np.count_nonzero(ind == 0)
    M = N//s
    r = N%s

    pnts = []
    sweeps = Z[:M*s].reshape(M, s)

    for p, sweep in enumerate(sweeps):
        peaks = sweep_peaks(sweep, sweep_ridges(sweep, params), params)
        for r in peaks: pnts.append([X[p*s + r], Y[p*s + r]])

    return np.array(pnts)

def find_clusters(pnts, params):
    eps, min_samples, A = params.eps, params.min_samples, params.trans
    X = dbscan(transform_pnts(A, pnts), eps, min_samples)
    n, m = X.min()+1, X.max()+1 # we can ignore the isolated points
    return np.array([pnts[X==i,:] for i in range(n, m)], dtype=object)

def select_from_clusters(clusters, rules_):
    pass

def fit_clusters(clusters, beta0=(4, -1)):
    odr_model = odr.Model(lambda p, x: p[0]*x + p[1])
    results = []
    for cluster in clusters:
        data = odr.Data(x=cluster[:,0], y=cluster[:,1])
        ord_dist_reg = odr.ODR(data, odr_model, beta0=beta0)
        results.append(ord_dist_reg.run())

    return results

def extract_capacitance():
    pass