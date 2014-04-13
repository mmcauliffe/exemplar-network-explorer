import math
from linghelper.phonetics.similarity.envelope import envelope_similarity,calc_envelope,correlate_envelopes


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
    def __init__(self,g,parent=None):
        super(Graph, self).__init__(parent=parent)
        self.g = g
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

