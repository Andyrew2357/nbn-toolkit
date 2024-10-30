CURR_UNIT = 'A'
VOLT_UNIT = 'V'
FREQ_UNIT = 'Hz'
DENS_UNIT = r'$cm^{{-3}}$'
DISP_UNIT = r'$V-nm^{{-1}}$'
BFLD_UNIT = 'T'
RSST_UNIT = 'Ohm'
COND_UNIT = 'S'
CAPT_UNIT = r'F-cm^{{-2}}'

PRESET_LABELS = {
    'V':    r'[{}]'.format(VOLT_UNIT),
    'Vb':   r'$V_{{bg}}$ [{}]'.format(VOLT_UNIT),
    'Vt':   r'$V_{{tg}}$ [{}]'.format(VOLT_UNIT),
    'n':    r'n [{}]'.format(DENS_UNIT),
    'D':    r'$D/\epsilon_{{\circ}}$ [{}]'.format(DISP_UNIT),
    'B':    r'B [{}]'.format(BFLD_UNIT),
    'I':    r'[{}]'.format(CURR_UNIT),
    'Ix':   r'$I_{{x}}$ [{}]'.format(CURR_UNIT),
    'Iy':   r'$I_{{y}}$ [{}]'.format(CURR_UNIT),
    'R':    r'R [{}]'.format(RSST_UNIT),
    'dR':   r'$(dI/dV)^{{-1}}$ [{}]'.format(RSST_UNIT),
    'G':    r'G [{}]'.format(COND_UNIT),
    'dG':   r'dI/dV [{}]'.format(COND_UNIT),
    'C':    r'$C/\Delta A$ [{}]'.format(CAPT_UNIT),
}

CMAP = 'afmhot'
CLUSTER_CMAP = 'jet'
CLUSTER_MARKERS = markers = ["o","v","^","<",">","s","p","H","d"]
FIG_SIZE = (6, 4)
FFT_FIG_SIZE = (6, 10)
LIN_FIG_SIZE = (4, 3)
RC_PARAMS = {
    "text.usetex": True,
    "font.family": "Helvetica"
}