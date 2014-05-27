
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import networkx as nx


from linghelper.distance.dtw import generate_distance_matrix

import matplotlib.mlab as mlab

from scipy.signal import resample
from scipy.io import wavfile

class Heatmap(pg.ImageItem):
    def __init__(self, image=None):

        if image is not None:
            self.image = image
        else:
            self.image = np.zeros((10, 10))
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
        
        Pxx, freq, t = mlab.specgram(proc,Fs = newSr)
        Z = 10. * np.log10(Pxx)
        #self.setLimits(xMin = 0, xMax = len(t),yMin=0,yMax=len(freq))
        self.setXRange(0, len(t))
        self.setYRange(0, len(freq))
        self.getAxis('left').setScale((newSr/2)/len(freq))
        self.heatmap.setImage(Z.T,opacity=0.7)
        self.show()
        self.update()

class NetworkGraph(pg.GraphItem):
    def __init__(self):
        pg.GraphItem.__init__(self)
        self.scatter.sigClicked.connect(self.clicked)
    
    def mouseClickEvent(self,event):
        print(event)
        pos = event.pos()
        print(pos)
        pts = self.scatter.pointsAt(pos)
        if len(pts) == 0:
            event.ignore()
            return
        print(pts)
        
    
    def clicked(self,pts):
        print(pts.data)

class NetworkWidget(pg.GraphicsWindow):
    def __init__(self,parent=None):
        pg.GraphicsWindow.__init__(self,parent=parent)
        self.graphModel = None
        self.selectionGraphModel = None
        self.v = self.addViewBox()
        self.g = NetworkGraph()
        self.v.addItem(self.g)
        self.pos = None
        self.adj = None
        self.symbols = None
        
    def setModel(self,model):
        self.graphModel = model
        spring = nx.spring_layout(self.graphModel.g)
        self.pos = np.array([spring[k] for k in sorted(spring.keys())])
        self.adj = np.array(self.graphModel.g.edges(data=False))
        self.symbols = np.array(['o']*len(self.graphModel.g))
        self.update()
        
    def setSelectionModel(self,selectionModel):
        self.selectionGraphModel = selectionModel
        selected = self.selectionModel().selectedRows()
        if not selected:
            return
        selectedInd = selected[0].row()
        self.symbols = np.array(['o']*len(self.graphModel.g))
        self.symbols[selectedInd] = '+'
        self.update()
        
    def model(self):
        return self.graphModel
        
    def selectionModel(self):
        return self.selectionGraphModel
    
    
    def update(self):
        self.g.setData(pos=self.pos,adj=self.adj,symbol = self.symbols)
        #r = 800
        #m = -400
        #for i,n in enumerate(nodeItems):
        #    x,y = pos[nodes[i][0]]
        #    x = r*x + m
        #    y = r*y + m
        #    n.setPos(x,y)

class EnvelopeWidget(pg.PlotWidget):
    def __init__(self,parent=None):
        pg.PlotWidget.__init__(self,parent=parent,name = 'Envelopes')
        self.setLabel('left', 'Amplitude')
        self.setLabel('bottom', 'Time', units='s')

    def plot_envelopes(self,envs):
        self.clear()
        num_bands = envs.shape[1]
        for i in range(num_bands):
            self.plot(envs[:,i])
        self.getAxis('bottom').setScale(1/120)
        self.show()
        self.update()
    
class DistanceWidget(pg.PlotWidget):
    def __init__(self,parent=None):
        pg.PlotWidget.__init__(self,parent=parent,name = 'Distance')
        self.heatmap = Heatmap()
        self.addItem(self.heatmap)
        #self.setLabel('left', 'Frequency', units='Hz')
        #self.setLabel('bottom', 'Time', units='s')
        
        
    def plot_dist_mat(self,source,target):
        
        distMat = generate_distance_matrix(source,target)
        self.setXRange(0, source.shape[0])
        self.setYRange(0, target.shape[0])
        self.heatmap.setImage(distMat,autoLevels=[0,1],opacity=0.7)
        self.show()
        self.update()
    
