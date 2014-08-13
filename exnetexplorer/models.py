import math
from acousticsim.main import analyze_directory

import multiprocessing
from functools import partial

import os
import networkx as nx
import numpy
import scipy.signal
import pickle


from sklearn.cluster import AffinityPropagation
from sklearn import metrics
from sklearn import manifold
from sklearn.decomposition import PCA

from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime,QSettings,QSize,QPoint,QAbstractTableModel)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem,QDialog,
        QSound)



class Graph(QAbstractTableModel):
    def __init__(self,parent=None):
        super(Graph, self).__init__(parent=parent)
        self.g = nx.Graph()
        self.columns = []
        self.time_step = 0

    def loadDataFromWav(self,settings):
        self.g = nx.Graph()
        token_path = settings.value('path','')
        if not os.path.exists(token_path):
            token_path = ''
        if not token_path:
            return

        rep = settings.value('network/Representation','mfcc')
        if rep == 'envelopes':
            num_filters = int(settings.value('envelopes/NumBands',8))
        elif rep == 'mfcc':
            num_filters = int(settings.value('mfcc/NumFilters',26))

        kwarg_dict = {'rep': rep,
                    'freq_lims': (int(settings.value('general/MinFreq',80)),int(settings.value('general/MaxFreq',7800))),
                    'win_len': float(settings.value('general/WindowLength',0.025)),
                    'time_step': float(settings.value('general/TimeStep',0.01)),
                    'num_coeffs': int(settings.value('mfcc/NumCC',20)),
                    'num_filters': num_filters,
                    'use_power': bool(settings.value('general/UsePower',False)),
                    'num_cores': 4,
                    'return_rep': True}
        scores,reps = analyze_directory(token_path,**kwarg_dict)
        lookup = {}
        nodes = []
        for i,r in enumerate(sorted(reps.keys())):
            lookup[r] = i
            nodes.append((i,
                            {'label':r,
                            'representation':reps[r],
                            'sound':QSound(os.path.join(token_path,r))}))
        self.g.add_nodes_from(nodes)

        clusterAlgorithm = settings.value('network/clusterAlgorithm','complete')
        oneCluster = bool(settings.value('network/OneCluster',1))
        self.simMat = numpy.zeros((len(nodes),len(nodes)))
        for k,v in scores.items():
            indOne = lookup[k[0]]
            indTwo = lookup[k[1]]
            self.simMat[indOne,indTwo] = v
            self.simMat[indTwo,indOne] = v
        if clusterAlgorithm == 'incremental':
            pass
        elif clusterAlgorithm == 'affinity':
            edges = []
            if oneCluster:
                pref = numpy.min(self.simMat)
            else:
                pref = None
            af = AffinityPropagation(affinity = 'precomputed',preference=pref).fit(self.simMat)

            cluster_centers_indices = af.cluster_centers_indices_
            n_clusters_ = len(cluster_centers_indices)
            labels = af.labels_

            for k in range(n_clusters_):
                clust = cluster_centers_indices[k]
                class_members = labels == k

                for i, x in enumerate(class_members):
                    if not x:
                        continue
                    n = nodes[i]
                    edges.append((clust,n[0],self.simMat[n[0],clust]))
        else:
            edges = [(lookup[k[0]],lookup[k[1]],v) for k,v in scores.items()]
        self.g.add_weighted_edges_from(edges)
        node = next(self.g.nodes_iter(data=True))
        if node is not None:

            self.columns = [x for x in node[1].keys()
                        if x not in ('representation','sound')]
        else:
            self.columns = []

    def rowCount(self,parent=None):
        return self.g.number_of_nodes()

    def columnCount(self,parent=None):
        return len(self.columns)
        n = next(self.g.nodes_iter(data=True))
        return len(n[1].keys()) + 1

    def data(self, index, role=None):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        row = index.row()
        col = index.column()
        node = self.g.node[row]
        data = node[self.columns[col]]
        return data

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[col]
        return None

    def __getitem__(self,ind):
        if isinstance(ind,int):
            return self.g.node[ind]
        #elif isinstance(ind,str):

    #def setData(self):
    #    pass

    #def flags(self):
    #    pass

