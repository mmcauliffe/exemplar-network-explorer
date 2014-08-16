
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
import networkx as nx


from acousticsim.representations.helper import preproc
from acousticsim.distance.dtw import generate_distance_matrix

import matplotlib.mlab as mlab

from sklearn import manifold
from sklearn.decomposition import PCA

class Heatmap(pg.ImageItem):
    def __init__(self, image=None):

        if image is not None:
            self.image = image
        else:
            self.image = np.zeros((10, 10))
        pg.ImageItem.__init__(self, self.image,levels=[1,0])

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


    def plot_specgram(self,token_path, win_len= 0.025, time_step = 0.01):
        sr, proc = preproc(token_path)
        nwin = int(sr * win_len)
        nstep = int(sr * time_step)
        Pxx, freq, t = mlab.specgram(proc, NFFT=nwin,Fs = sr,noverlap = nstep)
        Z = 10. * np.log10(Pxx)
        #self.setLimits(xMin = 0, xMax = len(t),yMin=0,yMax=len(freq))
        self.setXRange(0, len(t))
        self.setYRange(0, len(freq))
        self.getAxis('left').setScale((sr/2)/len(freq))
        self.heatmap.setImage(Z.T,levels=[np.max(Z.T),np.min(Z.T)],opacity=0.7)
        self.show()
        self.update()

class NetworkScatter(pg.ScatterPlotItem):
    def pointsAt(self, pos):
        x = pos.x()
        y = pos.y()
        pw = self.pixelWidth()
        ph = self.pixelHeight()
        pts = []
        for i,s in enumerate(self.points()):
            sp = s.pos()
            ss = s.size()
            sx = sp.x()
            sy = sp.y()
            s2x = s2y = ss * 0.5
            if self.opts['pxMode']:
                s2x *= pw
                s2y *= ph
            if x > sx-s2x and x < sx+s2x and y > sy-s2y and y < sy+s2y:
                pts.append((i,s))
        return pts[::-1]


class NetworkGraph(pg.GraphItem):
    def __init__(self, **kwds):
        pg.GraphItem.__init__(self, **kwds)
        self.scatter = NetworkScatter()
        self.scatter.setParentItem(self)
        self.adjacency = None
        self.pos = None
        self.picture = None
        self.pen = 'default'
        self.setData(**kwds)




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
        self.symbolPen = pg.mkPen(color=pg.mkColor('k'))
        self.g.scatter.sigClicked.connect(self.clicked)

    def clicked(self,scatter,pts):

        self.symbols = np.array(['o']*len(self.graphModel.g))
        for p in pts:
            ind = self.graphModel.createIndex(p[0],0)
            self.selectionModel().select(ind,QtGui.QItemSelectionModel.SelectCurrent)
            self.symbols[p[0]] = '+'

    def setModel(self,model):
        self.graphModel = model

        if len(model.g) == 0:
            return

        seed = np.random.RandomState(seed=3)
        mds = manifold.MDS(n_components=2, max_iter=3000, eps=1e-9, random_state=seed,
                   dissimilarity="precomputed", n_jobs=4)
        pos = mds.fit(-1 * model.simMat).embedding_
        clf = PCA(n_components=2)
        self.pos = clf.fit_transform(pos)

        #self.pos = np.array([spring[k] for k in sorted(spring.keys())])
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
        if len(self.pos) > 0:
            self.g.setData(pos=self.pos,adj=self.adj,symbol = self.symbols,symbolPen= self.symbolPen)
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
        self.heatmap = Heatmap()
        self.addItem(self.heatmap)
        self.setLabel('bottom', 'Time', units='s')

    def plot_envelopes(self,rep):
        self.setXRange(0, rep.shape[0])
        self.setYRange(0, rep.shape[1])
        self.heatmap.setImage(rep,levels=[np.max(rep),np.min(rep)],opacity=0.7)
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
        self.heatmap.setImage(distMat,levels=[np.max(distMat),np.min(distMat)],opacity=0.7)
        self.show()
        self.update()

