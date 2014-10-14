

import os
import csv
from collections import Counter

from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime,QSettings,QSize,QPoint, Signal)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem,QDialog,
        QTableView,QAbstractItemView, QMenu, QItemSelectionModel, QItemSelection)

from numpy import zeros,array

import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

from acousticsim.distance.dtw import generate_distance_matrix
from acousticsim.representations import to_specgram

class TableWidget(QTableView):
    def __init__(self,parent=None):
        super(TableWidget, self).__init__(parent=parent)

        self.verticalHeader().hide()

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popup)
        header = self.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect( self.showHeaderMenu )

    def showHeaderMenu( self, pos ):
        header = self.horizontalHeader()
        column = header.logicalIndexAt(pos.x())

        filterAction = QAction(self)
        filterAction.setText('Filter column')
        filterAction.triggered.connect(lambda: self.filterColumn(self.indexAt(pos)))
        symbolAction = QAction(self)
        symbolAction.setText('Symbol')
        symbolAction.triggered.connect(lambda: self.changeColumnDisplay(self.indexAt(pos),'symbol'))
        colourAction = QAction(self)
        colourAction.setText('Color')
        colourAction.triggered.connect(lambda: self.changeColumnDisplay(self.indexAt(pos),'brush'))
        sizeAction = QAction(self)
        sizeAction.setText('Size')
        sizeAction.triggered.connect(lambda: self.changeColumnDisplay(self.indexAt(pos),'size'))
        # show menu about the column
        menu = QMenu(self)
        displayMenu = menu.addMenu('Change graph display')
        displayMenu.addAction(symbolAction)
        displayMenu.addAction(colourAction)
        displayMenu.addAction(sizeAction)
        menu.addAction(filterAction)

        menu.popup(header.mapToGlobal(pos))

    def filterColumn(self,index):
        column = self.columns[index.column()]

    def changeColumnDisplay(self, index, display):
        column = self.model().columns[index.column()]
        self.model().changeFactorDisplay(column,display)


    def popup(self,pos):
        menu = QMenu()

        saveRepAction = QAction(self)
        saveRepAction.setText('Save representation...')
        saveRepAction.triggered.connect(lambda: self.saveRep(self.indexAt(pos)))
        menu.addAction(saveRepAction)
        action = menu.exec_(self.mapToGlobal(pos))

    def saveRep(self,index):
        #dialog = QFileDialog(self)
        #dialog.setFileMode(QFileDialog.AnyFile)
        #dialog.setNameFilter("Text files (*.txt)")
        #dialog.setViewMode(QFileDialog.Detail)
        #dialog.setDirectory(os.getcwd())
        #dialog.selectFile(
        gInd = index.row()
        name = self.model().data(index)
        filename,filt = QFileDialog.getSaveFileName(self,"Save representation",os.path.join(os.getcwd(),name.replace('.wav','.txt')),"Text files (*.txt)")

        rep = self.model().rep
        for n in self.model().g.nodes_iter(data=True):
            if n[0] == gInd:
                rep = n[1]['acoustics'][rep]
                break

        time_step = self.model().time_step
        num_frames,num_bands = rep.shape
        with open(filename,'w') as f:
            writer = csv.writer(f,delimiter='\t')
            writer.writerow(['Time','Band','Value'])
            for i in range(num_frames):
                for j in range(num_bands):
                    writer.writerow([(i+1)*time_step,j+1,rep[i,j]])
        #if dialog.exec_():
        #    fileNames = dialog.selectedFiles()

class Heatmap(pg.ImageItem):
    def __init__(self, image=None):

        if image is not None:
            self.image = image
        else:
            self.image = zeros((10, 10))
        pg.ImageItem.__init__(self, self.image)

    def updateImage(self, image):
        self.image = image
        self.render()
        self.update()


class SpecgramWidget(pg.PlotWidget):
    def __init__(self,parent=None):
        v = pg.ViewBox(enableMouse=False)
        pg.PlotWidget.__init__(self,parent=parent,name = 'Spectrogram',viewBox=v,enableMenu=False)
        self.heatmap = Heatmap()
        self.addItem(self.heatmap)
        self.setLabel('left', 'Frequency', units='Hz')
        self.setLabel('bottom', 'Time', units='s')

    def reset(self):
        self.heatmap.setImage(zeros((10, 10)),opacity=0)
        self.show()
        self.update()


    def plot_specgram(self,token_path, win_len= 0.005, time_step = 0.01):
        win_len= 0.005
        spec,freqs,times = to_specgram(token_path,win_len)
        dynamic_range = 70
        spec[spec < spec.max()-dynamic_range] = spec.max()-dynamic_range
        self.heatmap.setImage(spec,opacity=0.7,levels=[spec.max(),spec.min()])

        self.show()
        self.update()


class RepresentationWidget(pg.PlotWidget):
    def __init__(self,parent=None):
        v = pg.ViewBox(enableMouse=False)
        pg.PlotWidget.__init__(self,parent=parent,name = 'Auditory representation',viewBox=v,enableMenu=False)
        self.heatmap = Heatmap()
        self.addItem(self.heatmap)
        self.setLabel('bottom', 'Time', units='s')

        def changed(obj, range):
            print(range)
        #self.sigRangeChanged.connect(changed)

    def reset(self):
        self.heatmap.setImage(zeros((10, 10)),opacity=0)
        self.show()
        self.update()

    def plot_representation(self,rep):
        self.setXRange(0, rep.shape[0])
        self.setYRange(0, rep.shape[1])
        self.heatmap.setImage(rep,levels=[rep.max(),rep.min()],opacity=0.7)
        self.show()
        self.update()

class DistanceWidget(pg.PlotWidget):
    def __init__(self,parent=None):
        v = pg.ViewBox(enableMouse=False)
        pg.PlotWidget.__init__(self,parent=parent,name = 'Distance matrix',viewBox=v,enableMenu=False)
        self.heatmap = Heatmap()
        self.addItem(self.heatmap)

    def reset(self):
        self.heatmap.setImage(zeros((10, 10)),opacity=0)
        self.show()
        self.update()


    def plot_dist_mat(self,source,target,distance):

        distMat = generate_distance_matrix(source,target)
        self.setXRange(0, source.shape[0])
        self.setYRange(0, target.shape[0])
        self.heatmap.setImage(distMat,levels=[distMat.max(),distMat.min()],opacity=0.7)
        self.getPlotItem().setTitle('Overall distance: %.2f'%distance)
        self.show()
        self.update()

class NetworkScatter(pg.ScatterPlotItem):
    sigClicked = Signal(object, object) ## points, mode
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

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            pts = self.pointsAt(ev.pos())
            if len(pts) > 0:
                self.ptsClicked = pts
                if ev.modifiers() in [Qt.ControlModifier,Qt.ShiftModifier]:

                    self.sigClicked.emit(self.ptsClicked,True)
                else:
                    self.sigClicked.emit(self.ptsClicked,False)
                ev.accept()
            else:
                #print "no spots"
                ev.ignore()
        else:
            ev.ignore()


class NetworkGraph(pg.GraphItem):
    def __init__(self, **kwds):
        pg.GraphicsObject.__init__(self)
        self.scatter = NetworkScatter()
        self.scatter.setParentItem(self)
        self.adjacency = None
        self.pos = None
        self.picture = None
        self.pen = 'default'
        self.setData(**kwds)


s_r = (7,50)
h_r = (0,255 * 3)
c_r = (0,255)
symbols = ['o','s','t','d','+']

class NetworkWidget(pg.GraphicsLayoutWidget):
    def __init__(self,parent=None):
        pg.GraphicsWindow.__init__(self,parent=parent)
        self.graphModel = None
        self.selectionGraphModel = None
        self.v = self.addViewBox(enableMenu=False)
        self.g = NetworkGraph()
        self.v.addItem(self.g)
        self.v.setMouseEnabled(x=True,y=True)
        self.v.enableAutoRange('xy')
        self.adj = None
        self.symbolPen = pg.mkPen(color=pg.mkColor('k'))
        self.g.scatter.sigClicked.connect(self.clicked)
        self.spots = None

    def clicked(self,pts,mode):

        if mode:
            selectMode = QItemSelectionModel.Toggle
        else:
            selectMode = QItemSelectionModel.ClearAndSelect
        for p in pts:
            ind = self.graphModel.createIndex(p[0],0)
            ind1 = self.graphModel.createIndex(p[0],self.model().columnCount())
            selection = QItemSelection(ind,ind1)
            self.selectionModel().select(selection,selectMode)
        self.to_update()

    def get_defaults(self,*args):

        if self.graphModel.cluster_network is None:
            return
        self.to_update()
        #self.update_data()

    def setModel(self,model):
        self.graphModel = model
        self.graphModel.plotUpdate.connect(self.to_update)


    def setSelectionModel(self,selectionModel):
        self.selectionGraphModel = selectionModel
        self.to_update()

    def model(self):
        return self.graphModel

    def selectionModel(self):
        return self.selectionGraphModel

    def to_update(self,obj=None):
        self.spots,self.adj = self.graphModel.to_plot()
        self.pos = []
        try:
            selected = self.selectionModel().selectedRows()
            selected = [x.row() for x in selected]
        except AttributeError:
            selected = []
        for i,s in enumerate(self.spots):
            if i in selected:
                s['pen'] = pg.mkPen('r')
            else:
                s['pen'] = pg.mkPen('k')
            for k,v in s.items():
                if k == 'pos':
                    self.pos.append(v)
                elif k == 'symbol':
                    if v is None:
                        val = symbols[0]
                    elif v[0] == 'factor':
                        if v[1] > len(symbols) - 1:
                            val = symbols[-1]
                        else:
                            val = symbols[v[1]]
                    else:
                        val = symbols[0]
                    s[k] = val
                elif k == 'size':
                    if v is None:
                        val = s_r[0]
                    elif v[0] == 'factor':
                        val = ((s_r[1] - s_r[0]) * (v[1]/v[2])) + s_r[0]
                    else:
                        val = ((s_r[1] - s_r[0]) * v[1]) + s_r[0]
                    s[k] = val
                elif k == 'brush':
                    if v is None:
                        val = pg.mkBrush('c')
                    elif v[0] == 'factor':
                        s[k] = pg.mkBrush(pg.intColor(v[1], hues = v[2]))
                    else:
                        s[k] = pg.mkBrush(0,0,((c_r[1] - c_r[0]) * v[1]) + c_r[0])
            self.spots[i] = s
        self.update_data()

    def update_data(self):
        if self.spots is not None and len(self.spots) > 0:
            self.g.setData(pos = array(self.pos), spots=self.spots,adj=self.adj,
                symbolPen= self.symbolPen)
            #self.g._update()

