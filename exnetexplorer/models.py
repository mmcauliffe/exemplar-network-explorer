
import os
from functools import partial

from numpy import inf

from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime,QSettings,QSize,QPoint,QAbstractTableModel, QThread, Signal)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem,QDialog)

from acousticsim.main import analyze_directory
from acousticsim.clustering import ClusterNetwork


class LoadWorker(QThread):
    updateProgress = Signal(str)

    dataReady = Signal(object)

    def __init__(self):
        QThread.__init__(self)

    def set_params(self, settings):
        self.settings = settings

    def run(self):
        token_path = self.settings['path']
        if not os.path.exists(token_path):
            token_path = ''
        if not token_path:
            return
        self.updateProgress.emit("Processing acoustic tokens, please be patient...")
        kwarg_dict = self.settings.acousticsim_kwarg()

        scores,self.reps = analyze_directory(token_path, call_back = self.updateProgress.emit,**kwarg_dict)

        self.updateProgress.emit("Finished acoustic processing! Clustering tokens now...")
        cn = ClusterNetwork(self.reps)


        cluster_method = self.settings['cluster_alg']
        one_cluster = self.settings['one_cluster']

        cn.cluster(scores,cluster_method,one_cluster)
        self.updateProgress.emit("Ready")
        self.dataReady.emit(cn)

class ReclusterWorker(QThread):
    updateProgress = Signal(str)

    dataReady = Signal(object)

    def __init__(self):
        QThread.__init__(self)

    def set_params(self, settings, cn, redo_scores = False):
        self.settings = settings
        self.redo_scores = redo_scores
        self.cn = cn

    def run(self):
        token_path = self.settings['path']

        cluster_method = self.settings['cluster_alg']
        one_cluster = self.settings['one_cluster']
        if self.redo_scores:
            self.updateProgress.emit("Recalculating distances...")
            kwarg_dict = self.settings.acousticsim_kwarg()
            kwarg_dict['cache'] = self.cn.reps
            kwarg_dict['return_rep'] = False
            scores = analyze_directory(token_path,**kwarg_dict)
        else:
            scores = None
        self.updateProgress.emit("Clustering tokens...")
        self.cn.cluster(scores,cluster_method,one_cluster)

        self.updateProgress.emit("Ready")
        self.dataReady.emit(self.cn)

class ReductionWorker(QThread):
    updateProgress = Signal(str)

    dataReady = Signal(object)

    def __init__(self):
        QThread.__init__(self)

    def set_params(self, cn):
        self.cn = cn

    def run(self):
        self.updateProgress.emit("Calculating reduction...")
        self.cn.calc_reduction()

        self.updateProgress.emit("Ready")
        self.dataReady.emit(self.cn)


class GraphModel(QAbstractTableModel):
    plotUpdate = Signal()
    def __init__(self, data, parent=None):
        super(GraphModel, self).__init__(parent = parent)
        self.cluster_network = data
        self.columns = self.cluster_network.attributes
        self.display = {'brush': None,
                        'symbol': None,
                        'size': None}

        self.ranges = {}
        for n in self.cluster_network:
            for c in self.columns:
                if isinstance(n['rep'][c],str):
                    if c not in self.ranges:
                        self.ranges[c] = set([])
                    self.ranges[c].update([n['rep'][c]])
                elif isinstance(n['rep'][c], float):
                    if c not in self.ranges:
                        self.ranges[c] = (inf,-inf)
                    if n['rep'][c] < self.ranges[c][0]:
                        self.ranges[c] = (n['rep'][c],self.ranges[c][1])
                    if n['rep'][c] > self.ranges[c][1]:
                        self.ranges[c] = (self.ranges[c][0],n['rep'][c])

        for k,v in self.ranges.items():
            if isinstance(v,set):
                self.ranges[k] = sorted(list(v))


    def to_plot(self):
        adj = self.cluster_network.get_edges()
        out = []
        for n in self.cluster_network:
            outdict = {'pos': n['pos']}
            for k,colname in self.display.items():
                if colname is None:
                   outdict[k] = None
                else:
                    r = self.ranges[colname]
                    numeric = isinstance(r,tuple)
                    if numeric:
                        outdict[k] = ('numeric',(n['rep'][colname] - r[0]) / (r[1] - r[0]))
                    else:
                        for i,v in enumerate(r):
                            if v == n['rep'][colname]:
                                val = i
                                break
                        else:
                            val = 0
                        outdict[k] = ('factor',val, len(r))

            out.append(outdict)
        return out, adj

    def changeFactorDisplay(self,column,display):
        if self.display[display] == column:
            self.display[display] = None
        else:
            self.display[display] = column
        self.plotUpdate.emit()

    def rowCount(self,parent=None):
        if self.cluster_network is None:
            return 0
        return len(self.cluster_network)

    def columnCount(self,parent=None):
        return len(self.columns)

    def data(self, index, role=None):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        row = index.row()
        col = index.column()
        node = self.cluster_network[row]
        data = node['rep'][self.columns[col]]

        if isinstance(data,float):
            data = str(round(data,3))
        return data

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[col]
        return None

    def flags(self, index):
        if not index.isValid():
            return
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsUserCheckable

    def setData(self, index, value, role):
        if not index.isValid() or role!=Qt.CheckStateRole:
            return False
        self._checked[index.row()][index.column()]=value
        self.dataChanged.emit(index, index)
        return True


