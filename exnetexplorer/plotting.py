
from PySide.QtGui import QSizePolicy
from PySide.QtCore import QSize

from scipy.signal import resample
from scipy.io import wavfile
import numpy
import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'

import matplotlib.pyplot as plt



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
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        if xscale is not None:
            self.axes.set_xscale(xscale)
        if yscale is not None:
            self.axes.set_yscale(yscale)
        if xlim is not None:
            self.axes.set_xlim(*xlim)
        if ylim is not None:
            self.axes.set_ylim(*ylim)
        self.axes.hold(hold)

        Canvas.__init__(self, self.figure)
        self.setParent(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

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
        print(token_path)
        print(len(sig))
        t = len(sig)/sr
        numsamp = t * newSr
        proc = resample(sig,numsamp)

        self.axes.cla()
        self.axes.set_xlim([0,len(proc)/newSr])
        self.axes.set_ylim([0,newSr/2])
        self.axes.specgram(proc,Fs =newSr,cmap=plt.cm.gist_heat)
        self.updateGeometry()
        #plt.plot(Pxx)
        #plt.show()

class EnvelopeWidget(MatplotlibWidget):
    def __init__(self,parent=None):
        MatplotlibWidget.__init__(self,parent=parent,xlabel='Time',ylabel='Amplitude')

    def plot(self,envs):
        self.axes.cla()
        print(len(envs))
        maxAmp = 0
        to_plot = []
        maxX = len(envs[0])
        x = numpy.array(range(maxX)) / 120
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
        self.updateGeometry()
        #plt.plot(Pxx)
        #plt.show()
