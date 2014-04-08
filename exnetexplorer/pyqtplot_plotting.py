
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

from linghelper.phonetics.similarity.envelope import envelope_similarity,calc_envelope,correlate_envelopes

import matplotlib.mlab as mlab

from scipy.signal import resample
from scipy.io import wavfile

class Heatmap(pg.ImageItem):
    def __init__(self, image=None):

        if image is not None:
            self.image = image
        else:
            self.image = np.zeros((500, 500))
        pg.ImageItem.__init__(self, self.image)
        
    def updateImage(self, image):
        self.image = image
        self.render()
        self.update()


class SpecgramWidget(pg.PlotWidget):
    def __init__(self,parent=None):
        pg.PlotWidget.__init__(self,parent=parent,name = 'Spectrogram')
        self.heatmap = Heatmap()
        self.addItem(self.heatmap)
        self.setLabel('left', 'Frequency', units='Hz')
        self.setLabel('bottom', 'Time', units='s')
        
        
    def plot_specgram(self,token_path):
        newSr = 16000
        sr, sig = wavfile.read(token_path)
        t = len(sig)/sr
        numsamp = t * newSr
        proc = resample(sig,numsamp)
        
        #self.setXRange(0, len(proc)/newSr)
        #self.setYRange(0, newSr/2)
        Pxx, freq, t = mlab.specgram(proc,Fs = newSr)
        Z = 10. * np.log10(Pxx)
        #self.setLimits(xMin = 0, xMax = len(t),yMin=0,yMax=len(freq))
        self.getAxis('left').setScale((newSr/2)/len(freq))
        self.heatmap.updateImage(Z.T)
        self.show()
        self.update()
        

class EnvelopeWidget(pg.PlotWidget):
    def __init__(self,parent=None):
        pg.PlotWidget.__init__(self,parent=parent,name = 'Envelopes')
        self.setLabel('left', 'Amplitude')
        self.setLabel('bottom', 'Time', units='s')

    def plot_envelopes(self,envs):
        self.clear()
        print(len(envs))
        for e in envs:
            self.plot(e)
        self.getAxis('bottom').setScale(1/120)
        self.show()
        self.update()
    
class SimilarityWidget(pg.PlotWidget):
    pass
    