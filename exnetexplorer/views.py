import math


import os
import networkx as nx
import numpy
import csv
from collections import Counter

from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime,QSettings,QSize,QPoint)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem,QDialog,
        QTableView,QAbstractItemView, QMenu)

from exnetexplorer.models import Graph

class TableWidget(QTableView):
    def __init__(self,parent=None):
        super(TableWidget, self).__init__(parent=parent)
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
        colourAction.setText('Colour')
        colourAction.triggered.connect(lambda: self.changeColumnDisplay(self.indexAt(pos),'colour'))
        # show menu about the column
        menu = QMenu(self)
        displayMenu = menu.addMenu('Change graph display')
        displayMenu.addAction(symbolAction)
        displayMenu.addAction(colourAction)
        menu.addAction(filterAction)

        menu.popup(header.mapToGlobal(pos))

    def filterColumn(self,index):
        print(index)
        column = self.columns[index.column()]

    def changeColumnDisplay(self, index, display):
        print(index)
        column = self.columns[index.column()]
        c = Counter()
        if display == 'symbol':
            default = 'o'
        elif display == 'colour':
            default = 'blue'


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
        print(index)
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
            writer.writerow(['Time','Band','Amplitude'])
            for i in range(num_frames):
                for j in range(num_bands):
                    writer.writerow([(i+1)*time_step,j+1,rep[i,j]])
        #if dialog.exec_():
        #    fileNames = dialog.selectedFiles()

class NetworkGraphicsScene(QGraphicsScene):
    def __init__(self,parent=None):
        super(NetworkGraphicsScene, self).__init__(parent=parent)

class NetworkGraphicsView(QAbstractItemView):
    def __init__(self,parent=None):
        super(NetworkGraphicsView, self).__init__(parent=parent)

        scene = NetworkGraphicsScene(self)
        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        scene.setSceneRect(-200, -200, 400, 400)
        self.setScene(scene)

    def setModel(self,model):
        super(NetworkGraphicsView, self).setModel(model)
        scene = self.scene()
        scene.clear()
        nodes = model.g.nodes(data=True)
        for n in nodes:
            node = Node(self,n[0],n[1]['label'])
            scene.addItem(node)
        nodeItems = [item for item in self.scene().items() if isinstance(item, Node)]
        edges = model.g.edges(data=True)
        for e in edges:
            scene.addItem(Edge(nodeItems[e[0]],nodeItems[e[1]],e[2]['weight']))
        pos = nx.spring_layout(model.g)
        r = 800
        m = -400
        for i,n in enumerate(nodeItems):
            x,y = pos[nodes[i][0]]
            x = r*x + m
            y = r*y + m
            n.setPos(x,y)

    def setScene(self,scene):
        self.graphicsScene = scene

    def scene(self):
        return self.graphicsScene

class GraphWidget(QGraphicsView):
    def __init__(self,main):
        super(GraphWidget, self).__init__()

        self.main = main
        self.timerId = 0

        scene = QGraphicsScene(self)
        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        scene.setSceneRect(-200, -200, 400, 400)
        self.setScene(scene)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)



        self.scale(1.0, 1.0)
        self.setMinimumSize(400, 400)

    def setModel(self,model):
        scene = self.scene()
        scene.clear()
        self.graphModel = model
        nodes = model.g.nodes(data=True)
        for n in nodes:
            node = Node(self,n[0],n[1]['label'])
            scene.addItem(node)
        nodeItems = [item for item in self.scene().items() if isinstance(item, Node)]
        edges = model.g.edges(data=True)
        for e in edges:
            scene.addItem(Edge(nodeItems[e[0]],nodeItems[e[1]],e[2]['weight']))

        seed = numpy.random.RandomState(seed=3)
        mds = manifold.MDS(n_components=2, eps=1e-9, random_state=seed,
                   dissimilarity="precomputed", n_jobs=4)
        pos = mds.fit(-1 * model.simMat).embedding_
        clf = PCA(n_components=2)
        pos = clf.fit_transform(pos)
        for i,n in enumerate(nodeItems):
            x,y = pos[nodes[i][0],0],pos[nodes[i][0],1]
            n.setPos(x,y)

    def model(self):
        return self.graphModel


   # def itemMoved(self):
   #     if not self.timerId:
   #         self.timerId = self.startTimer(1000 / 25)

    def keyPressEvent(self, event):
        key = event.key()

        #if key == Qt.Key_Up:
        #    self.centerNode.moveBy(0, -20)
        #elif key == Qt.Key_Down:
        #    self.centerNode.moveBy(0, 20)
        #elif key == Qt.Key_Left:
        #    self.centerNode.moveBy(-20, 0)
        #elif key == Qt.Key_Right:
        #    self.centerNode.moveBy(20, 0)
        if key == Qt.Key_Plus:
            self.scaleView(1.2)
        elif key == Qt.Key_Minus:
            self.scaleView(1 / 1.2)
        #elif key == Qt.Key_Space or key == Qt.Key_Enter:
        #    for item in self.scene().items():
        #        if isinstance(item, Node):
        #            item.setPos(-150 + qrand() % 300, -150 + qrand() % 300)
        else:
            super(GraphWidget, self).keyPressEvent(event)

    #def timerEvent(self, event):
        #nodes = [item for item in self.scene().items() if isinstance(item, Node)]

        ##for node in nodes:
        ##    node.calculateForces()

        #itemsMoved = False
        #for node in nodes:
            #if node.advance():
                #itemsMoved = True

        #if not itemsMoved:
            #self.killTimer(self.timerId)
            #self.timerId = 0

    def wheelEvent(self, event):
        self.scaleView(math.pow(2.0, event.delta() / 240.0))

    #def drawBackground(self, painter, rect):
        ## Shadow.
        #sceneRect = self.sceneRect()
        #rightShadow = QRectF(sceneRect.right(), sceneRect.top() + 5, 5,
                #sceneRect.height())
        #bottomShadow = QRectF(sceneRect.left() + 5, sceneRect.bottom(),
                #sceneRect.width(), 5)
        #if rightShadow.intersects(rect) or rightShadow.contains(rect):
            #painter.fillRect(rightShadow, Qt.darkGray)
        #if bottomShadow.intersects(rect) or bottomShadow.contains(rect):
            #painter.fillRect(bottomShadow, Qt.darkGray)

        ## Fill.
        #gradient = QLinearGradient(sceneRect.topLeft(), sceneRect.bottomRight())
        #gradient.setColorAt(0, Qt.white)
        #gradient.setColorAt(1, Qt.lightGray)
        #painter.fillRect(rect.intersected(sceneRect), QBrush(gradient))
        #painter.setBrush(Qt.NoBrush)
        #painter.drawRect(sceneRect)

        ## Text.
        #textRect = QRectF(sceneRect.left() + 4, sceneRect.top() + 4,
                #sceneRect.width() - 4, sceneRect.height() - 4)
        #message = "Click and drag the nodes around, and zoom with the " \
                #"mouse wheel or the '+' and '-' keys"

        #font = painter.font()
        #font.setBold(True)
        #font.setPointSize(14)
        #painter.setFont(font)
        #painter.setPen(Qt.lightGray)
        #painter.drawText(textRect.translated(2, 2), message)
        #painter.setPen(Qt.black)
        #painter.drawText(textRect, message)

    def scaleView(self, scaleFactor):
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()

        if factor < 0.07 or factor > 100:
            return

        self.scale(scaleFactor, scaleFactor)



class Edge(QGraphicsItem):
    Pi = math.pi
    TwoPi = 2.0 * Pi

    Type = QGraphicsItem.UserType + 2

    def __init__(self, sourceNode, destNode, similarity):
        super(Edge, self).__init__()

        self.similarity = similarity

        self.arrowSize = 10.0
        self.sourcePoint = QPointF()
        self.destPoint = QPointF()

        #self.setAcceptedMouseButtons(Qt.NoButton)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.source = sourceNode
        self.dest = destNode
        self.source.addEdge(self)
        self.dest.addEdge(self)
        self.adjust()

    def type(self):
        return Edge.Type

    def sourceNode(self):
        return self.source

    def setSourceNode(self, node):
        self.source = node
        self.adjust()

    def destNode(self):
        return self.dest

    def setDestNode(self, node):
        self.dest = node
        self.adjust()

    def adjust(self):
        if not self.source or not self.dest:
            return

        line = QLineF(self.mapFromItem(self.source, 0, 0),
                self.mapFromItem(self.dest, 0, 0))
        length = line.length()

        self.prepareGeometryChange()

        if length > 20.0:
            edgeOffset = QPointF((line.dx() * 10) / length,
                    (line.dy() * 10) / length)

            self.sourcePoint = line.p1() + edgeOffset
            self.destPoint = line.p2() - edgeOffset
        else:
            self.sourcePoint = line.p1()
            self.destPoint = line.p1()

    def boundingRect(self):
        if not self.source or not self.dest:
            return QRectF()

        penWidth = 1.0
        extra = (penWidth + self.arrowSize) / 2.0

        return QRectF(self.sourcePoint,
                QSizeF(self.destPoint.x() - self.sourcePoint.x(),
                        self.destPoint.y() - self.sourcePoint.y())).normalized().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget):
        if not self.source or not self.dest:
            return

        # Draw the line itself.
        line = QLineF(self.sourcePoint, self.destPoint)

        if line.length() == 0.0:
            return

        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine, Qt.RoundCap,
                Qt.RoundJoin))
        painter.drawLine(line)

        # Draw the arrows if there's enough room.
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = Edge.TwoPi - angle

        #sourceArrowP1 = self.sourcePoint + QPointF(math.sin(angle + Edge.Pi / 3) * self.arrowSize,
                                                          #math.cos(angle + Edge.Pi / 3) * self.arrowSize)
        #sourceArrowP2 = self.sourcePoint + QPointF(math.sin(angle + Edge.Pi - Edge.Pi / 3) * self.arrowSize,
                                                          #math.cos(angle + Edge.Pi - Edge.Pi / 3) * self.arrowSize);
        #destArrowP1 = self.destPoint + QPointF(math.sin(angle - Edge.Pi / 3) * self.arrowSize,
                                                      #math.cos(angle - Edge.Pi / 3) * self.arrowSize)
        #destArrowP2 = self.destPoint + QPointF(math.sin(angle - Edge.Pi + Edge.Pi / 3) * self.arrowSize,
                                                      #math.cos(angle - Edge.Pi + Edge.Pi / 3) * self.arrowSize)

        #painter.setBrush(Qt.black)
        #painter.drawPolygon(QPolygonF([line.p1(), sourceArrowP1, sourceArrowP2]))
        #painter.drawPolygon(QPolygonF([line.p2(), destArrowP1, destArrowP2]))


    def mouseDoubleClickEvent(self, event):
        print(self.similarity)
        super(Edge, self).mouseDoubleClickEvent(event)

class Node(QGraphicsItem):
    Type = QGraphicsItem.UserType + 1

    def __init__(self, graphWidget,id,label):
        super(Node, self).__init__()
        self.id = id
        self.label = label
        self.graph = graphWidget
        self.edgeList = []
        self.newPos = QPointF()

        #self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(1)

    def type(self):
        return Node.Type

    def addEdge(self, edge):
        self.edgeList.append(edge)
        edge.adjust()

    def edges(self):
        return self.edgeList

    #def calculateForces(self):
        #if not self.scene() or self.scene().mouseGrabberItem() is self:
            #self.newPos = self.pos()
            #return

        ## Sum up all forces pushing this item away.
        #xvel = 0.0
        #yvel = 0.0
        #for item in self.scene().items():
            #if not isinstance(item, Node):
                #continue

            #line = QLineF(self.mapFromItem(item, 0, 0), QPointF(0, 0))
            #dx = line.dx()
            #dy = line.dy()
            #l = 2.0 * (dx * dx + dy * dy)
            #if l > 0:
                #xvel += (dx * 150.0) / l
                #yvel += (dy * 150.0) / l

        ## Now subtract all forces pulling items together.
        #weight = (len(self.edgeList) + 1) * 10.0
        #for edge in self.edgeList:
            #if edge.sourceNode() is self:
                #pos = self.mapFromItem(edge.destNode(), 0, 0)
            #else:
                #pos = self.mapFromItem(edge.sourceNode(), 0, 0)
            #xvel += pos.x() / weight
            #yvel += pos.y() / weight

        #if qAbs(xvel) < 0.1 and qAbs(yvel) < 0.1:
            #xvel = yvel = 0.0

        #sceneRect = self.scene().sceneRect()
        #self.newPos = self.pos() + QPointF(xvel, yvel)
        #self.newPos.setX(min(max(self.newPos.x(), sceneRect.left() + 10), sceneRect.right() - 10))
        #self.newPos.setY(min(max(self.newPos.y(), sceneRect.top() + 10), sceneRect.bottom() - 10))

    def advance(self):
        if self.newPos == self.pos():
            return False

        self.setPos(self.newPos)
        return True

    def boundingRect(self):
        adjust = 2.0
        return QRectF(-10 - adjust, -10 - adjust, 23 + adjust, 23 + adjust)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(-10, -10, 20, 20)
        return path

    def paint(self, painter, option, widget):
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.darkGray)
        painter.drawEllipse(-7, -7, 20, 20)

        gradient = QRadialGradient(-3, -3, 10)
        if option.state & QStyle.State_Sunken:
            gradient.setCenter(3, 3)
            gradient.setFocalPoint(3, 3)
            gradient.setColorAt(1, QColor(Qt.yellow).lighter(120))
            gradient.setColorAt(0, QColor(Qt.darkYellow).lighter(120))
        else:
            gradient.setColorAt(0, Qt.yellow)
            gradient.setColorAt(1, Qt.darkYellow)

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(Qt.black, 0))
        painter.drawEllipse(-10, -10, 20, 20)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edgeList:
                edge.adjust()
            #self.graph.itemMoved()

        return super(Node, self).itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        print(self.id,self.label)
        super(Node, self).mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button == 1:
            self.setSelected(True)
        if event.modifiers() == Qt.ControlModifier:
            print(dir(event.modifiers()))
        #self.update()
        super(Node, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        #self.update()
        super(Node, self).mouseReleaseEvent(event)
