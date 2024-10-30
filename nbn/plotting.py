import matplotlib.pyplot as plt

from . import *
from .disp_params import *
from .utils import sample_line_realspace, proj_on_line

plt.rcParams.update(RC_PARAMS)

# Tools for determining the color map
#################################################################################################

# This is a code block related to contrast normalization is borrowed from the CryoSparc user forums 
# https://discuss.cryosparc.com/t/differences-between-2d-ctf-when-viewed-in-cryosparc-vs-exported-ctf-diag-image-path/10511/6
def contrast_normalization(arr_bin, tile_size = 128):
    '''
    Computes the minimum and maximum contrast values to use
    by calculating the median of the 2nd/98th percentiles
    of the mic split up into tile_size * tile_size patches.
    :param arr_bin: the micrograph represented as a numpy array
    :type arr_bin: list
    :param tile_size: the size of the patch to split the mic by 
        (larger is faster)
    :type tile_size: int
    '''
    ny,nx = arr_bin.shape
    # set up start and end indexes to make looping code readable
    tile_start_x = np.arange(0, nx, tile_size)
    tile_end_x = tile_start_x + tile_size
    tile_start_y = np.arange(0, ny, tile_size)
    tile_end_y = tile_start_y + tile_size
    num_tile_x = len(tile_start_x)
    num_tile_y = len(tile_start_y)
    
    # initialize array that will hold percentiles of all patches
    tile_all_data = np.empty((num_tile_y*num_tile_x, 2), dtype=np.float32)

    index = 0
    for y in range(num_tile_y):
        for x in range(num_tile_x):
            # cut out a patch of the mic
            arr_tile = arr_bin[tile_start_y[y]:tile_end_y[y], tile_start_x[x]:tile_end_x[x]]
            # store 2nd and 98th percentile values
            tile_all_data[index:,0] = np.percentile(arr_tile, 98)
            tile_all_data[index:,1] = np.percentile(arr_tile, 2)
            index += 1

    # calc median of non-NaN percentile values
    all_tiles_98_median = np.nanmedian(tile_all_data[:,0])
    all_tiles_2_median = np.nanmedian(tile_all_data[:,1])
    vmid = 0.5*(all_tiles_2_median+all_tiles_98_median)
    vrange = abs(all_tiles_2_median-all_tiles_98_median)
    extend = 1.5
    # extend vmin and vmax enough to not include outliers
    vmin = vmid - extend*0.5*vrange
    vmax = vmid + extend*0.5*vrange

    return vmin, vmax

def validate_cscale(mode='auto', q1=None, q2=None):
    match mode:
        case 'auto':
            if q1 is not None or q2 is not None: 
                warnings.warn("""q1 and q2 should not be passed when cscale is 'auto'.
                              These will be overridden.""")
        case 'quant':
            if q1 is None or q2 is None:
                raise ValueError("q1 and q2 are required when cscale is quant")
            elif not 0 <= q1 < q2 <= 1:
                raise Exception("q1 and q2 should be between 0 and 1, with q1 < q2")
        case 'vrange':
            if not q1 < q2:
                raise Exception("q1 should be less than q2.")
        case _:
            raise Exception(f"{mode} is not a valid cscale. Try 'auto', 'quant', or 'vrange'")

def get_cscale(im, mode='auto', q1=None, q2=None):
    match mode:
            case 'auto':
                return contrast_normalization(im)
            case 'quant':
                return np.quantile(im,[q1, q2])
            case 'vrange':
                return q1, q2
        
# General plotting tools
#################################################################################################

def plot2D(imarr, bin=None, bin_x=None, bin_y=None, cmap=CMAP, figsize = FIG_SIZE, cscale='auto', 
           q1=None, q2=None, xlabel="", ylabel="", title="", colorbar=True, extent=None, 
           xlim=[None, None], ylim=[None, None]):

        if bin is not None:
            if bin_x is not None or bin_y is not None: 
                warnings.warn("""bin_x and bin_y should not be passed when passing
                              bin. These will be overidden.""")
            bin_x, bin_y = 1
        else:
            if bin_x is None: bin_x = 1
            if bin_y is None: bin_y = 1

        validate_cscale(cscale,q1,q2)

        N, M = imarr.shape
        im = np.mean(imarr[:bin_y*(N//bin_y), :bin_x*(M//bin_x)].reshape(
            (N//bin_y, bin_y, M//bin_x, bin_x)), axis=(1, 3))

        vmin, vmax = get_cscale(im, cscale, q1, q2)

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)

        img = ax.imshow(im, cmap=cmap, vmin=vmin, vmax=vmax, extent=extent, 
                        interpolation='none', aspect='auto')

        if colorbar: plt.colorbar(img, ax=ax)

        # ax.set_xlim(xlim)
        # ax.set_ylim(ylim)

        return fig

def implicit_mesh(X, Y, Z, ind):
    N = ind.size
    s = np.count_nonzero(ind == 0)
    M = N//s
    r = N%s

    a1x = X[1] - X[0]
    a1y = Y[1] - Y[0]
    a2x = X[s] - X[0]
    a2y = Y[s] - Y[0]

    if r == 0:
        X_ = np.pad(X.reshape(M, s), ((0,1),(0,1)), mode='constant')
        X_[:,-1]+=(X_[:,-2] + a1x)
        X_[-1,:]+=(X_[-2,:] + a2x)

        Y_ = np.pad(Y.reshape(M, s), ((0,1),(0,1)), mode='constant')
        Y_[:,-1]+=(Y_[:,-2] + a1y)
        Y_[-1,:]+=(Y_[-2,:] + a2y)

        Z_ = Z.reshape(M, s)

    else:
        X_ = np.pad(X[:M*s].reshape(M, s), ((0,2),(0,1)), mode='constant')
        X_[:,-1]+=(X_[:,-2] + a1x)
        X_[-2,:]+=(X_[-3,:] + a2x)
        X_[-1,:]+=(X_[-2,:] + a2x)

        Y_ = np.pad(Y[:M*s].reshape(M, s), ((0,2),(0,1)), mode='constant')
        Y_[:,-1]+=(Y_[:,-2] + a1y)
        Y_[-2,:]+=(Y_[-3,:] + a2y)
        Y_[-1,:]+=(Y_[-2,:] + a2y)

        Z_ = np.pad(Z[:M*s].reshape(M, s), ((0,1),(0,0)), mode='constant',
                    constant_values=np.nan)
        Z_[-1,:r] = Z[N*s:]

    if not np.all(np.diff(X_, axis=0) > 0):
        X_ = np.flip(X_, axis=0)
        Y_ = np.flip(Y_, axis=0)
        Z_ = np.flip(Z_, axis=0)
    if not np.all(np.diff(Y_, axis=1) > 0):
        X_ = np.flip(X_, axis=1)
        Y_ = np.flip(Y_, axis=1)
        Z_ = np.flip(Z_, axis=1)

    return X_, Y_, Z_

def plotMesh(X, Y, Z, cmap=CMAP, figsize=FIG_SIZE, cscale='auto', q1=None, q2=None,
             xlabel="", ylabel="", zlabel="", title="", colorbar=True, extent=None, 
             xlim=[None, None], ylim=[None, None]):
    
    validate_cscale(cscale, q1, q2)
    vmin, vmax = get_cscale(Z, cscale, q1, q2)

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)
    im = ax.pcolormesh(X, Y, Z, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    if colorbar: 
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(zlabel)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    return fig

def plotLine(X, Y, Z, ind, X1, Y1, X2, Y2, color='r', figsize=LIN_FIG_SIZE, llabel="", 
            zlabel="", title=""):
    
    X_, Y_, Z_ = sample_line_realspace(X, Y, Z, ind, X1, Y1, X2, Y2)

    L = proj_on_line(np.concatenate([X_.reshape(1, -1), Y_.reshape(1, -1)], axis=0), 
                     np.array([[X1], [Y1]]), np.array([[X2], [Y2]]))
    
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)
    ax.scatter(L,Z_, color=color, alpha=0.5, s=2)

    ax.set_xlabel(llabel)
    ax.set_ylabel(zlabel)
    ax.set_title(title)

    return fig

# Tools for managing axis labels
#################################################################################################

def preset_label(preset, label=""):
    if preset == '_': return label
    if not preset in PRESET_LABELS:
        raise Exception(f"""{preset} is not a valid preset. Consult 
                documentation for a complete list of preset options.""")

    return PRESET_LABELS[preset]
    
def preset_nd_label(preset, *axlabels):
    if preset is None: return axlabels
    axsets = preset.strip().split(',')
    if not len(axsets) == len(axlabels):
        raise Exception("Presets and labels should be one to one.")

    return [preset_label(axset, label) for axset, label in zip(axsets, axlabels)]

# Tools for plotting particular object types
#################################################################################################

def plot_FFTmap(Data, meta, bin=None, bin_x=None, bin_y=None, x_unit=VOLT_UNIT, y_unit=FREQ_UNIT, cmap=CMAP, 
                figsize=FFT_FIG_SIZE, cscale='auto', q1=None, q2=None, xlabel=None, ylabel=None, title=None, 
                colorbar=True, xlim=[None, None], ylim=[None,None]):

    if not 'freq' in meta: 
        raise KeyError("'freq' is required in self.meta for plot2D")
    if not 'Vbias' in meta:
        raise KeyError("'Vbias' is required in self.meta for plot2D")
    
    Vbias, freq = np.array(meta['Vbias']), np.array(meta['freq'])
    x0, x1 = Vbias.min(), Vbias.max()
    y0, y1 = freq.min(), freq.max() 
    # frequency array return appears to be slightly broken for MATLAB script

    if xlabel is None: xlabel = r'$V_{{bias}}$ [{}]'.format(x_unit)
    if ylabel is None: ylabel = r'$\nu$ [{}]'.format(y_unit)
    if title is None: title = meta['run_name']

    fig = plot2D(Data, bin=bin, bin_x=bin_x, bin_y=bin_y, cmap=cmap, figsize=figsize, cscale=cscale, 
                q1=q1, q2=q2, xlabel=xlabel, ylabel=ylabel, title=title, colorbar=colorbar, 
                extent=[x0, x1, y1, y0], xlim=xlim, ylim=ylim)

    return fig

def plot_Transport(Data, X, Y, Z, cmap=CMAP, figsize=FIG_SIZE, cscale='auto', q1=None, q2=None,
                xlabel="", ylabel="", zlabel="", title="", colorbar=True, extent=None, preset=None, 
                xlim=[None, None], ylim=[None, None]):

    if not all(n in Data.columns for n in (X, Y, Z)):
        raise SyntaxError("X, Y, and Z should be data column names.")
    
    xlabel, ylabel, zlabel = preset_nd_label(preset, xlabel, ylabel, zlabel)
    
    X_, Y_, Z_ = implicit_mesh(Data[X].to_numpy(), Data[Y].to_numpy(), 
                        Data[Z].to_numpy(), Data['ind'].to_numpy())
    
    fig = plotMesh(X_, Y_, Z_, cmap=cmap, figsize=figsize, cscale=cscale, q1=q1, q2=q2, xlabel=xlabel, 
        ylabel=ylabel, zlabel=zlabel, title=title, colorbar=colorbar, extent=extent, xlim=xlim, ylim=ylim)
    
    return fig

def plotLine_Transport(Data, X, Y, Z, X1, Y1, X2, Y2, color='r', figsize=LIN_FIG_SIZE, 
                       llabel="", zlabel="", title="", preset=None):
    
    if not all(n in Data.columns for n in (X, Y, Z)):
        raise SyntaxError("X, Y, and Z should be data column names.")
    
    llabel, zlabel = preset_nd_label(preset, llabel, zlabel)

    X_, Y_, Z_ = Data[X].to_numpy(), Data[Y].to_numpy(), Data[Z].to_numpy()

    fig = plotLine(X_, Y_, Z_, Data['ind'].to_numpy(), X1, Y1, X2, Y2, color=color, 
                   figsize=figsize, llabel=llabel, zlabel=zlabel, title=title)

    return fig

# Tools for plotting results of landau
#################################################################################################

def plot_ridges(ridges, fig=None, figsize=FIG_SIZE, color='r', alpha=0.5, extent=None):
    if fig is None:
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
    else:
        ax = fig.axes[0]

    ax.scatter(ridges[:,0], ridges[:,1], color=color, alpha=alpha, s=2)

    return fig

def plot_clusters(clusters, fig=None, figsize=FIG_SIZE, cmap=CLUSTER_CMAP, alpha=0.5, extent=None):
    if fig is None:
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
    else:
        ax = fig.axes[0]

    N = clusters.size
    M = len(CLUSTER_MARKERS)
    clrs = plt.get_cmap(cmap)
    colors = clrs(np.linspace(0, 1, N))
    for i, ridges in enumerate(clusters):
        ax.scatter(ridges[:,0], ridges[:,1], color=colors[i], 
                   marker=CLUSTER_MARKERS[i%M], alpha=alpha, s=2)

    return fig

def plot_cluster_fits(clusters, fits, fig=None, figsize=FIG_SIZE, color='r',
                    xlim=[None, None], ylim=[None, None]):
    if fig is None:
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
    else:
        ax = fig.axes[0]
    
    for c, f in zip(clusters, fits):
        x = np.array([c[:,0].min(), c[:,0].max()])
        a, b = f.beta
        ax.plot(x, a*x+b, color=color)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    
    return fig

# Tools for plotting cross correlations from sliders.py
#################################################################################################

def plot_cross_corr(CC, Vbticks, fticks, figsize=FFT_FIG_SIZE, cmap=CMAP, cscale='auto', q1=None, q2=None):
    validate_cscale(cscale,q1,q2)

    N, M = CC.shape
    vmin, vmax = get_cscale(CC, cscale, q1, q2)

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)

    extent = [Vbticks.min(), Vbticks.max(), fticks.max(), fticks.min()]
    ax.imshow(CC, cmap=cmap, vmin=vmin, vmax=vmax, extent=extent, interpolation='none', aspect='auto')

    return fig