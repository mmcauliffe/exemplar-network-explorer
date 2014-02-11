import math
import sys
sys.path.append('/home/michael/dev/Linguistics/linguistic-helper-functions')
sys.path.append('/home/michael/dev/Linguistics/python-praat-scripts')
from linghelper.phonetics.similarity.envelope import envelope_similarity,calc_envelope,envelope_match


import os
import networkx as nx
import numpy
import scipy.signal

from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem)

from plotting import SpecgramWidget,EnvelopeWidget

token_path = os.path.normpath(r'/home/michael/dev/Data/Jam/102_words')

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

        self.setAcceptedMouseButtons(Qt.NoButton)
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
        #self.update()
        super(Node, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        #self.update()
        super(Node, self).mouseReleaseEvent(event)


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

    def setGraph(self,g,center_id):
        scene = self.scene()
        nodes = g.nodes(data=True)
        for n in nodes:
            node = Node(self,n[0],n[1]['label'])
            scene.addItem(node)
            if center_id == n[0]:
                node.setPos(0,0)
        nodeItems = [item for item in self.scene().items() if isinstance(item, Node)]
        edges = g.edges(data=True)
        for e in edges:
            scene.addItem(Edge(nodeItems[e[0]],nodeItems[e[1]],e[2]['weight']))
        pos = nx.spring_layout(g)
        r = 400
        m = -200
        for i,n in enumerate(nodeItems):
            x,y = pos[nodes[i][0]]
            x = r*x + m
            y = r*y + m
            n.setPos(x,y)
        #node1.setPos(-50, -50)
        #node2.setPos(0, -50)
        #node3.setPos(50, -50)
        #node4.setPos(-50, 0)
        #self.centerNode.setPos(0, 0)
        #node6.setPos(50, 0)
        #node7.setPos(-50, 50)
        #node8.setPos(0, 50)
        #node9.setPos(50, 50)

   # def itemMoved(self):
   #     if not self.timerId:
   #         self.timerId = self.startTimer(1000 / 25)

    #def keyPressEvent(self, event):
        #key = event.key()

        #if key == Qt.Key_Up:
            #self.centerNode.moveBy(0, -20)
        #elif key == Qt.Key_Down:
            #self.centerNode.moveBy(0, 20)
        #elif key == Qt.Key_Left:
            #self.centerNode.moveBy(-20, 0)
        #elif key == Qt.Key_Right:
            #self.centerNode.moveBy(20, 0)
        #elif key == Qt.Key_Plus:
            #self.scaleView(1.2)
        #elif key == Qt.Key_Minus:
            #self.scaleView(1 / 1.2)
        #elif key == Qt.Key_Space or key == Qt.Key_Enter:
            #for item in self.scene().items():
                #if isinstance(item, Node):
                    #item.setPos(-150 + qrand() % 300, -150 + qrand() % 300)
        #else:
            #super(GraphWidget, self).keyPressEvent(event)

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
        self.scaleView(math.pow(2.0, event.angleDelta().y() / 240.0))

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

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.graph = GraphWidget(self)
        self.setCentralWidget(self.graph)

        self.g = nx.Graph()

        files = os.listdir(token_path)
        nodes = []
        ind = 0
        for f in files:
            if not f.endswith('.wav'):
                continue
            env = calc_envelope(os.path.join(token_path,f))
            nodes.append((ind,{'label':f,'envelope':env}))
            ind += 1

        edges = []
        for i in range(len(nodes)-1):
            for j in range(i+1,len(nodes)):
                sim = envelope_match(nodes[i][1]['envelope'],nodes[j][1]['envelope'])
                if sim > 0.9:
                    edges.append((nodes[i][0],nodes[j][0],sim))

        #nodes = [
                    #(0,{'label':'hello'}),
                    #(1,{'label':'hi'}),
                    #(2,{'label':'how'}),
                    #(3,{'label':'are'}),
                    #(4,{'label':'you'}),
                    #(5,{'label':'howdy'}),
                    #(6,{'label':'hey'}),
                    #(7,{'label':'sup'}),
                    #(8,{'label':'buddy'}),
                    #]
        self.g.add_nodes_from(nodes)
        #edges = [
                    #(0,1,0.8),
                    #(1,2,0.3),
                    #(1,4,0.5),
                    #(2,5,0.6),
                    #(3,0,0.2),
                    #(3,4,0.5),
                    #(4,5,0.5),
                    #(4,7,0.5),
                    #(5,8,0.7),
                    #(6,3,0.3),
                    #(7,6,0.1),
                    #(8,7,0.6)
                    #]
        self.g.add_weighted_edges_from(edges)
        self.graph.setGraph(self.g,4)
        self.setWindowTitle("Exemplar Network Explorer")
        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        self.createDockWindows()
        self.setMinimumSize(1000, 800)

    def createActions(self):
        self.loadNetworkFileAct = QAction( "&Load pickled network",
                self, shortcut=QKeySequence.Open,
                statusTip="Load pickled network", triggered=self.loadNetworkFile)

        self.createNetworkAct = QAction( "&Create network from folder",
                self, shortcut=QKeySequence.Open,
                statusTip="Create network from folder", triggered=self.createNetwork)

        self.specgramAct = QAction( "&View token spectrogram",
                self,
                statusTip="View token spectrogram", triggered=self.specgram)

        self.detailsAct = QAction( "&View token details",
                self,
                statusTip="View token details", triggered=self.details)

        self.envelopeAct = QAction( "&View token envelopes",
                self,
                statusTip="View token amplitude envelopes", triggered=self.envelope)

        self.playfileAct = QAction( "&Play token",
                self,
                statusTip="Play token", triggered=self.playfile)

        self.quitAct = QAction("&Quit", self, shortcut="Ctrl+Q",
                statusTip="Quit the application", triggered=self.close)

        self.aboutAct = QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

    def createNetwork(self):
        return

    def loadNetworkFile(self):
        filename, _ = QFileDialog.getOpenFileName(self,
                "Choose a file name", '.', "TXT (*.txt)")
        if not filename:
            return

        file = QFile(filename)
        if not file.open(QFile.ReadOnly | QFile.Text):
            QMessageBox.warning(self, "Dock Widgets",
                    "Cannot write file %s:\n%s." % (filename, file.errorString()))
            return

        out = QTextStream(file)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        out << self.textEdit.toHtml()
        QApplication.restoreOverrideCursor()

        self.statusBar().showMessage("Saved '%s'" % filename, 2000)

    def about(self):
        QMessageBox.about(self, "About Exemplar Network Explorer",
                "Placeholder "
                "Go on... ")

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.loadNetworkFileAct)
        self.fileMenu.addAction(self.createNetworkAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAct)

        self.viewMenu = self.menuBar().addMenu("&View")

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def specgram(self):
        selected = self.tokenList.selectedItems()
        print(selected)
        if not selected:
            return
        if len(selected) > 1:
            return

        selectedInd = selected[0].row()
        print(selectedInd)
        wavfile = self.tokenList.item(selectedInd,1).text()
        print(wavfile)
        self.specgramWindow.plot(os.path.join(token_path,wavfile))
        self.specgramWindow.resize(4,3)



    def details(self):
        return

    def envelope(self):
        selected = self.tokenList.selectedItems()
        if not selected:
            return
        if len(selected) > 1:
            return

        selectedInd = selected[0].row()
        for n in self.g.nodes_iter(data=True):
            if n[0] == selectedInd:
                self.envelopeWindow.plot(n[1]['envelope'])
                break
        self.envelopeWindow.resize(4,3)

    def playfile(self):
        return

    def createToolBars(self):
        self.fileToolBar = self.addToolBar("Details")
        self.fileToolBar.addAction(self.specgramAct)
        self.fileToolBar.addAction(self.detailsAct)
        self.fileToolBar.addAction(self.envelopeAct)
        self.fileToolBar.addAction(self.playfileAct)

    def createStatusBar(self):
        self.statusBar().showMessage("Ready")

    def selectToken(self):
        selected = self.tokenList.selectedItems()
        rows = set([x.row() for x in selected])
        inds = [int(self.tokenList.item(x,0).text()) for x in rows]
        print(inds)
        self.specgram()
        self.envelope()
        return

    def createDockWindows(self):
        dock = QDockWidget("Tokens", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        nodes = self.g.nodes(data=True)
        self.tokenList = QTableWidget(len(nodes),2,dock)
        self.tokenList.setHorizontalHeaderLabels(['Id','Word'])
        for i,n in enumerate(nodes):
            self.tokenList.setItem(i,0,QTableWidgetItem(str(n[0])))
            self.tokenList.setItem(i,1,QTableWidgetItem(n[-1]['label']))
        dock.setWidget(self.tokenList)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

        dock = QDockWidget("Spectrogram", self)
        self.specgramWindow = SpecgramWidget(parent=dock)
        dock.setWidget(self.specgramWindow)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())
        self.specgramWindow.plot(os.path.join(token_path,n[-1]['label']))

        dock = QDockWidget("Envelopes", self)
        self.envelopeWindow = EnvelopeWidget(parent=dock)
        dock.setWidget(self.envelopeWindow)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

        self.tokenList.itemSelectionChanged.connect(self.selectToken)
        #self.paragraphsList.currentTextChanged.connect(self.addParagraph)



if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    qsrand(QTime(0,0,0).secsTo(QTime.currentTime()))

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())
