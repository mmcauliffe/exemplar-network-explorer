
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
    def mouseHoverEvent(self, ev):
        ev.acceptDrags(pg.Qt.QtCore.Qt.LeftButton)
    def updateImage(self, image):
        self.image = image
        self.render()
        self.update()
    def mouseDragEvent(self, ev):
        if ev.button() != pg.Qt.QtCore.Qt.LeftButton:
            ev.ignore()
            return
        else:
            ev.accept()
        heatmap = self.heatmap.copy()
        p1 = ev.buttonDownPos()
        p2 = ev.pos()
        x1, x2 = sorted([p1.x(), p2.x()])
        y1, y2 = sorted([p1.y(), p2.y()])
        heatmap[x1:x2, y1:y2] += 1
        self.setImage(heatmap, levels=[0,20])
        if ev.isFinish():
            self.heatmap = heatmap


class SpecgramWidget(pg.PlotWidget):
    def __init__(self,parent=None):
        pg.PlotWidget.__init__(self,parent=parent,name = 'Spectrogram')
        self.heatmap = Heatmap()
        self.addItem(self.heatmap)
        self.setLabel('left', 'Frequency', units='Hz')
        self.setLabel('bottom', 'Time', units='s')
        
        
    def plot(self,token_path):
        newSr = 16000
        sr, sig = wavfile.read(token_path)
        t = len(sig)/sr
        numsamp = t * newSr
        proc = resample(sig,numsamp)
        
        self.setXRange(0, len(proc)/newSr)
        self.setYRange(0, newSr/2)
        Pxx, freq, t = mlab.specgram(proc,Fs =newSr)
        Z = 10. * np.log10(Pxx)
        self.heatmap.updateImage(Z)
        

class EnvelopeWidget(pg.PlotWidget):
    pass
    
class SimilarityWidget(pg.PlotWidget):
    pass
    