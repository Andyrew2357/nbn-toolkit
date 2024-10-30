from scipy.spatial import KDTree
from scipy.ndimage import gaussian_filter

from . import *
from .util_params import *

def dbscan(X, eps=EPS, min_samples=MIN_SAMP):
    kd_tree = KDTree(X)
    clusters = np.zeros(len(X), dtype=int) - 1
    visited = set()
    cluster_id = 0
    
    def expand_cluster(point_id, neighbors):
        clusters[point_id] = cluster_id
        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                new_neighbors = kd_tree.query_ball_point(X[neighbor], eps)
                if len(new_neighbors) >= min_samples:
                    expand_cluster(neighbor, new_neighbors)
            if clusters[neighbor] == -1:
                clusters[neighbor] = cluster_id
    
    for i in range(len(X)):
        if i in visited:
            continue
        visited.add(i)
        neighbors = kd_tree.query_ball_point(X[i], eps)
        if len(neighbors) < min_samples:
            clusters[i] = -1  # Noise point
        else:
            expand_cluster(i, neighbors)
            cluster_id += 1
    
    return clusters

# I've taken this implementation of Bresenham's line drawing algorithm from
# a project on GitHub. The repository is here, https://github.com/asweigart/pybresenham
# and the copyright notice is below.
# small modifications have been made for my use case.
# Copyright (c) 2018, Al Sweigart
# All rights reserved.
def line(x1, y1, x2, y2, _skipFirst=False):

    x1, y1, x2, y2 = round(x1), round(y1), round(x2), round(y2)

    isSteep = abs(y2-y1) > abs(x2-x1)
    if isSteep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    isReversed = x1 > x2

    if isReversed:
        x1, x2 = x2, x1
        y1, y2 = y2, y1

        deltax = x2 - x1
        deltay = abs(y2-y1)
        error = int(deltax / 2)
        y = y2
        ystep = None
        if y1 < y2:
            ystep = 1
        else:
            ystep = -1
        for x in range(x2, x1 - 1, -1):
            if isSteep:
                if not (_skipFirst and (x, y) == (x2, y2)):
                    yield (y, x)
            else:
                if not (_skipFirst and (x, y) == (x2, y2)):
                    yield (x, y)
            error -= deltay
            if error <= 0:
                y -= ystep
                error += deltax
    else:
        deltax = x2 - x1
        deltay = abs(y2-y1)
        error = int(deltax / 2)
        y = y1
        ystep = None
        if y1 < y2:
            ystep = 1
        else:
            ystep = -1
        for x in range(x1, x2 + 1):
            if isSteep:
                if not (_skipFirst and (x, y) == (x1, y1)):
                    yield (y, x)
            else:
                if not (_skipFirst and (x, y) == (x1, y1)):
                    yield (x, y)
            error -= deltay
            if error < 0:
                y += ystep
                error += deltax

def sample_line(X, Y, Z, stride, x1, y1, x2, y2):
    X_, Y_, Z_ = [], [], []

    for swp, sw in line(x1, y1, x2, y2):
        X_.append(X[stride*sw + swp])
        Y_.append(Y[stride*sw + swp])
        Z_.append(Z[stride*sw + swp])

    return np.array(X_), np.array(Y_), np.array(Z_)

def sample_line_realspace(X, Y, Z, ind, X1, Y1, X2, Y2):
    N = ind.size
    s = np.count_nonzero(ind == 0)
    M = N//s
    r = N%s

    a1x = X[1] - X[0]
    a1y = Y[1] - Y[0]
    a2x = X[s] - X[0]
    a2y = Y[s] - Y[0]

    X1-=X[0]
    X2-=X[0]
    Y1-=Y[0]
    Y2-=Y[0]

    det = a1x*a2y - a1y*a2x
    x1, y1 = (a2y*X1 - a2x*Y1)/det, (a1x*Y1 - a1y*X1)/det
    x2, y2 = (a2y*X2 - a2x*Y2)/det, (a1x*Y2 - a1y*X2)/det

    return sample_line(X, Y, Z, s, x1, y1, x2, y2)

def proj_on_line(v, x1, x2):
    n = (x2-x1)/np.linalg.norm(x2-x1)
    return np.linalg.matmul(n.T,v-x1)[0]

def dog(im, w1, w2):
    return gaussian_filter(im, w1) - gaussian_filter(im, w2)

def background_subtracted(im):
    return im - im.mean(1)

def floor_filter(im, q=0.97):
    return np.clip(im, a_min=np.quantile(im, q), amax=None)

def VbVt_to_nD(Cb, Ct):
    return np.array([[Cb/ELECTRON_CHARGE_S, Ct/ELECTRON_CHARGE_S],
            [-Cb/(2*EPSILON_NAUGHT_S), Ct/(2*EPSILON_NAUGHT_S)]])

def nD_to_VbVt(Cb, Ct):
    return np.linalg.inv(VbVt_to_nD(Cb, Ct))

def transform_pnts(A, pnts):
    return np.dot(A, pnts.T).T

def transform_clusters(A, clusters):
    return np.array([transform_pnts(A, c) for c in clusters], dtype=object)

def add_transformed_cols(Data, A, inx, iny, outx, outy, override=False):
    if not all(n in Data.columns for n in (inx, iny)):
        raise Exception("inx and iny should be columns names in Data.")
    if any(n in Data.columns for n in (outx, outy)) and not override:
        warnings.warn("""setting outx or outy to an existing column name
                      will cause that column to be overwritten. If this
                      Is intended, call with override=True.""")
        return

    ins = np.concatenate([Data[inx].to_numpy().reshape(1, -1), 
                        Data[iny].to_numpy().reshape(1, -1)], axis=0).T
    outs = transform_pnts(A, ins)

    Data[outx] = outs[:,0]
    Data[outy] = outs[:,1]