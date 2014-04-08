
from PySide.QtGui import QSizePolicy
from PySide.QtCore import QSize

import numpy as np

from linghelper.phonetics.similarity.envelope import envelope_similarity,calc_envelope,correlate_envelopes


from scipy.signal import resample
from scipy.io import wavfile
import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'

import matplotlib.pyplot as plt

import matplotlib.mlab as mlab

from matplotlib.ticker import MultipleLocator

matplotlib.rcParams['xtick.direction'] = 'out'
matplotlib.rcParams['ytick.direction'] = 'out'


from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure


class MatplotlibWidget(Canvas):
    """
    MatplotlibWidget inherits PyQt4.QtGui.QWidget
    and matplotlib.backend_bases.FigureCanvasBase

    Options: option_name (default_value)
    -------
    parent (None): parent widget
    title (''): figure title
    xlabel (''): X-axis label
    ylabel (''): Y-axis label
    xlim (None): X-axis limits ([min, max])
    ylim (None): Y-axis limits ([min, max])
    xscale ('linear'): X-axis scale
    yscale ('linear'): Y-axis scale
    width (4): width in inches
    height (3): height in inches
    dpi (100): resolution in dpi
    hold (False): if False, figure will be cleared each time plot is called

    Widget attributes:
    -----------------
    figure: instance of matplotlib.figure.Figure
    axes: figure axes

    Example:
    -------
    self.widget = MatplotlibWidget(self, yscale='log', hold=True)
    from numpy import linspace
    x = linspace(-10, 10)
    self.widget.axes.plot(x, x**2)
    self.wdiget.axes.plot(x, x**3)
    """
    def __init__(self, parent=None, title='', xlabel='', ylabel='',
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=4, height=3, dpi=100, hold=False):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.figure.set_facecolor('white')
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        if xscale is not None:
            self.axes.set_xscale(xscale)
        if yscale is not None:
            self.axes.set_yscale(yscale)
            print(yscale)
        if xlim is not None:
            self.axes.set_xlim(*xlim)
        if ylim is not None:
            self.axes.set_ylim(*ylim)
        self.axes.hold(hold)

        Canvas.__init__(self, self.figure)
        self.setParent(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

    def rstyle(self):
        """Styles an axes to appear like ggplot2
        Must be called after all plot and axis manipulation operations have been carried out (needs to know final tick spacing)
        """
        #set the style of the major and minor grid lines, filled blocks
        self.axes.grid(True, 'major', color='w', linestyle='-', linewidth=1.4)
        self.axes.grid(True, 'minor', color='0.92', linestyle='-', linewidth=0.7)
        self.axes.patch.set_facecolor('0.85')
        self.axes.set_axisbelow(True)

        #set minor tick spacing to 1/2 of the major ticks
        #self.axes.xaxis.set_minor_locator(MultipleLocator( (plt.xticks()[0][1]-plt.xticks()[0][0]) / 2.0 ))
        #self.axes.yaxis.set_minor_locator(MultipleLocator( (plt.yticks()[0][1]-plt.yticks()[0][0]) / 2.0 ))

        #remove axis border
        for child in self.axes.get_children():
            if isinstance(child, matplotlib.spines.Spine):
                child.set_alpha(0)

        #restyle the tick lines
        for line in self.axes.get_xticklines() + self.axes.get_yticklines():
            line.set_markersize(5)
            line.set_color("gray")
            line.set_markeredgewidth(1.4)

        #remove the minor tick lines
        for line in self.axes.xaxis.get_ticklines(minor=True) + self.axes.yaxis.get_ticklines(minor=True):
            line.set_markersize(0)

        #only show bottom left ticks, pointing out of axis
        self.axes.xaxis.set_ticks_position('bottom')
        self.axes.yaxis.set_ticks_position('left')


        if self.axes.legend_ != None:
            lg = self.axes.legend_
            lg.get_frame().set_linewidth(0)
            lg.get_frame().set_alpha(0.5)

    def sizeHint(self):
        w, h = self.get_width_height()
        return QSize(w, h)

    def minimumSizeHint(self):
        return QSize(10, 10)


class SpecgramWidget(MatplotlibWidget):
    def __init__(self,parent=None):
        MatplotlibWidget.__init__(self,parent=parent,xlabel='Time',ylabel='Frequency',yscale='log')

    def plot(self,token_path):
        newSr = 16000
        sr, sig = wavfile.read(token_path)
        t = len(sig)/sr
        numsamp = t * newSr
        proc = resample(sig,numsamp)

        self.axes.cla()
        self.axes.set_xlim([0,len(proc)/newSr])
        self.axes.set_ylim([0,newSr/2])
        Pxx, freq, t = mlab.specgram(proc,Fs =newSr)

        Z = 10. * np.log10(Pxx)
        #Z = np.flipud(Z)

        xextent = 0, np.amax(t)
        xmin, xmax = xextent
        extent = xmin, xmax, freq[0], freq[-1]

        #im = self.axes.imshow(Z, plt.cm.gist_heat)
        self.axes.pcolormesh(t,freq, Z,cmap=plt.cm.gist_heat)
        #self.axes.set_yscale('log')
        #self.rstyle()
        self.updateGeometry()
        #plt.plot(Pxx)
        #plt.show()

class EnvelopeWidget(MatplotlibWidget):
    def __init__(self,parent=None):
        MatplotlibWidget.__init__(self,parent=parent,xlabel='Time',ylabel='Amplitude')

    def plot(self,envs):
        self.axes.cla()
        maxAmp = 0
        to_plot = []
        maxX = len(envs[0])
        x = np.array(range(maxX)) / 120
        for i,e in enumerate(envs):
            if i == 0:
                cl = 'r-'
            elif i == 1:
                cl = 'y-'
            elif i == 2:
                cl = 'g-'
            else:
                cl = 'b-'
            to_plot.extend([x,e,cl])
            maxAmp = max(e+[maxAmp])
        self.axes.plot(*to_plot)
        self.axes.set_ylim([0,maxAmp])
        self.axes.set_xlim([0,max(x)])
        self.rstyle()
        self.updateGeometry()
        #plt.plot(Pxx)
        #plt.show()


class SimilarityWidget(MatplotlibWidget):
    def __init__(self,parent=None):
        MatplotlibWidget.__init__(self,parent=parent,xlabel='Envelope one band',ylabel='Envelope two band')
        self.colorbar = None

    def plot(self,envsOne,envsTwo,xlab=None,ylab=None):
        self.axes.cla()

        sims = np.zeros((len(envsOne),len(envsTwo)))

        for i in range(len(envsOne)):
            for j in range(len(envsTwo)):
                sims[i,j] = correlate_envelopes([envsOne[i]],[envsTwo[j]])

        mesh = self.axes.pcolormesh(sims,cmap=plt.cm.gist_heat)
        if self.colorbar is None:
            self.colorbar = self.figure.colorbar(mesh,ax=self.axes)
        else:
            self.colorbar.update_bruteforce(mesh)
        #self.axes.set_yscale('log')
        #self.rstyle()
        self.rstyle()
        self.updateGeometry()
