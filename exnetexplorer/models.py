import math
from linghelper.phonetics.representations.amplitude_envelopes import to_envelopes
from linghelper.phonetics.representations.prosody import to_pitch,to_intensity,to_prosody
from linghelper.phonetics.representations.mfcc import to_mfcc,freq_to_mel
from linghelper.phonetics.representations.mhec import to_mhec
from linghelper.distance.dtw import dtw_distance
from linghelper.distance.dct import dct_distance
from linghelper.distance.xcorr import xcorr_distance


import os
import networkx as nx
import numpy
import scipy.signal

from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime,QSettings,QSize,QPoint,QAbstractTableModel)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem,QDialog)

class Graph(QAbstractTableModel):
    def __init__(self,parent=None):
        super(Graph, self).__init__(parent=parent)
        self.g = nx.Graph()
        self.columns = []
        self.time_step = 0
        self.rep = ''

    def loadData(self,settings):
        self.g = nx.Graph()
        token_path = settings.value('path','')
        if not os.path.exists(token_path):
            token_path = ''
        if not token_path:
            return
        rep = settings.value('network/Representation','envelope')
        files = os.listdir(token_path)
        nodes = []
        ind = 0
        self.rep = rep
        if rep == 'envelope':
            self.time_step = 1/120
            num_bands = int(settings.value('envelopes/NumBands',4))
            erb = settings.value('envelopes/ERB',False)
            freq_lims = (int(settings.value('envelopes/MinFreq',80)),int(settings.value('envelopes/MaxFreq',7800)))
            for f in files:
                if not (f.endswith('.wav') or f.endswith('.WAV')):
                    continue
                env = to_envelopes(os.path.join(token_path,f),num_bands,freq_lims,erb)

                nodes.append((ind,{'label':f,'acoustics':{rep:env}}))
                ind += 1
        elif rep == 'mfcc':
            numCC = int(settings.value('mfcc/NumCC',20))
            winLen = float(settings.value('mfcc/WindowLength',0.015))
            timeStep = float(settings.value('mfcc/TimeStep',0.005))
            self.time_step = timeStep
            maxFreq = freq_to_mel(int(settings.value('mfcc/MaxFreq',7800)))
            for f in files:
                if not (f.endswith('.wav') or f.endswith('.WAV')):
                    continue
                mfcc = to_mfcc(os.path.join(token_path,f),numCC,winLen,timeStep,maxFreq)
                nodes.append((ind,{'label':f,'acoustics':{rep:mfcc}}))
                ind += 1
        elif rep == 'mhec':
            numCC = int(settings.value('mhec/NumCC',12))
            numBands = int(settings.value('mhec/NumBands',48))
            winLen = float(settings.value('mhec/WindowLength',0.025))
            timeStep = float(settings.value('mhec/TimeStep',0.01))
            self.time_step = timeStep
            freq_lims = (int(settings.value('mhec/MinFreq',80)),int(settings.value('mhec/MaxFreq',7800)))
            for f in files:
                if not (f.endswith('.wav') or f.endswith('.WAV')):
                    continue
                mhec = to_mhec(os.path.join(token_path,f),numCC,numBands,freq_lims,winLen,timeStep)
                nodes.append((ind,{'label':f,'acoustics':{rep:mhec}}))
                ind += 1
        elif rep == 'prosody':
            timeStep = float(settings.value('prosody/TimeStep',0.01))
            self.time_step = timeStep
            for f in files:
                if not (f.endswith('.wav') or f.endswith('.WAV')):
                    continue
                prosody = to_prosody(os.path.join(token_path,f),timeStep)
                nodes.append((ind,{'label':f,'acoustics':{rep:prosody}}))
                ind += 1
        else:
            return
        self.g.add_nodes_from(nodes)
        clusterAlgorithm = settings.value('network/ClusterAlgorithm','complete')
        matchAlgorithm = settings.value('envelopes/MatchAlgorithm','xcorr')
        if matchAlgorithm == 'xcorr':
            dist_func = xcorr_distance
        elif matchAlgorithm == 'dtw':
            dist_func = dtw_distance
        elif matchAlgorithm == 'dct':
            dist_func = dct_distance
        edges = []
        if clusterAlgorithm == 'incremental':
            pass
        else:
            threshold = float(settings.value('network/Threshold'))
            for i in range(len(nodes)-1):
                repOne = nodes[i][1]['acoustics'][rep]
                for j in range(i+1,len(nodes)):
                    repTwo = nodes[j][1]['acoustics'][rep]
                    
                    sim = 1/math.pow(math.e,dist_func(repOne,repTwo))
                    if clusterAlgorithm == 'threshold' and sim < threshold:
                        continue
                    edges.append((nodes[i][0],nodes[j][0],sim))

        self.g.add_weighted_edges_from(edges)
        node = next(self.g.nodes_iter(data=True))
        if node is not None:

            self.columns = [x for x in node[1].keys()
                        if not isinstance(node[1][x],dict)
                        and not isinstance(node[1][x],list)]
        else:
            self.columns = []

    def rowCount(self,parent=None):
        return self.g.number_of_nodes()

    def columnCount(self,parent=None):
        return len(self.columns)
        n = next(self.g.nodes_iter(data=True))
        return len(n[1].keys()) + 1

    def data(self, index, role=None):
        row = index.row()
        col = index.column()
        node = self.g.node[row]
        data = node[self.columns[col]]
        return data

    #def headerData(self):
    #   pass

    #def setData(self):
    #    pass

    #def flags(self):
    #    pass

