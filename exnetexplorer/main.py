import math
import sys
from linghelper.phonetics.similarity.envelope import envelope_similarity,calc_envelope,correlate_envelopes


import os
import networkx as nx
import numpy
import scipy.signal

from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime,QSettings,QSize,QPoint)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget, QHBoxLayout, QWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem,QDialog,QItemSelectionModel)

from pyqtplot_plotting import SpecgramWidget,EnvelopeWidget
from matplotlib_plotting import SimilarityWidget

from views import GraphWidget, TableWidget, NetworkGraphicsView
from models import Graph

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        from PySide import QtGui
        from PySide import QtCore
        QDialog.__init__( self, parent )

        firstButton = QtGui.QPushButton('a')
        secondButton = QtGui.QPushButton('b')
        thirdButton = QtGui.QPushButton('c')


        tabWidget = QTabWidget()
        tabWidget.addWidget( firstButton )
        tabWidget.addWidget( secondButton )
        tabWidget.addWidget( thirdButton )

        pageComboBox = QtGui.QComboBox()
        pageComboBox.setStyle
        pageComboBox.addItems( ['Page 1', 'Page 2', 'Page 3'] )
        QtCore.QObject.connect( pageComboBox, QtCore.SIGNAL( 'activated(int)'),
                                stackedWidget,
                                QtCore.SLOT('setCurrentIndex(int)') )

        layout = QtGui.QHBoxLayout()
        layout.addWidget( pageComboBox )
        layout.addWidget( stackedWidget )
        self.setLayout( layout )

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setMinimumSize(1000, 800)

        self.settings = QSettings('settings.ini',QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)

        self.resize(self.settings.value('size', QSize(270, 225)))
        self.move(self.settings.value('pos', QPoint(50, 50)))
        self.tokenTable = TableWidget(self)
        self.graphWidget = GraphWidget(self)
        self.wrapper = QWidget()
        layout = QHBoxLayout(self.wrapper)
        layout.addWidget(self.tokenTable)
        layout.addWidget(self.graphWidget)
        self.wrapper.setLayout(layout)
        self.setCentralWidget(self.wrapper)
        self.loadWordTokens()


        self.setWindowTitle("Exemplar Network Explorer")
        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        self.createDockWindows()

    def createActions(self):

        self.createNetworkAct = QAction( "&Create network from folder",
                self, shortcut=QKeySequence.Open,
                statusTip="Create network from folder", triggered=self.createNetwork)

        self.editPreferencesAct = QAction( "&Preferences...",
                self,
                statusTip="Edit preferences", triggered=self.editPreferences)

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

    def loadWordTokens(self):
        g = nx.Graph()
        token_path = self.settings.value('path','')
        if not token_path:
            return
        num_bands = self.settings.value('num_bands',8)
        erb = self.settings.value('erb',False)
        freq_lims = self.settings.value('freq_lims',(80,7800))
        if token_path != '':
            files = os.listdir(token_path)
            nodes = []
            ind = 0
            for f in files:
                if not (f.endswith('.wav') or f.endswith('.WAV')):
                    continue
                env = calc_envelope(os.path.join(token_path,f),num_bands,freq_lims,erb)

                nodes.append((ind,{'label':f,'acoustics':{'envelopes':env}}))
                ind += 1

            edges = []
            for i in range(len(nodes)-1):
                envsOne = nodes[i][1]['acoustics']['envelopes']
                for j in range(i+1,len(nodes)):
                    envsTwo = nodes[j][1]['acoustics']['envelopes']
                    sim = correlate_envelopes(envsOne,envsTwo)
                    if sim > 0.9:
                        edges.append((nodes[i][0],nodes[j][0],sim))

            g.add_nodes_from(nodes)
            g.add_weighted_edges_from(edges)
        self.graph = Graph(g)
        self.tokenTable.setModel(self.graph)
        self.tokenTable.setSelectionModel(QItemSelectionModel(self.graph))
        self.tokenTable.selectionModel().selectionChanged.connect(self.selectToken)
        self.graphWidget.setModel(self.tokenTable.model())

    def createNetwork(self):
        token_path = QFileDialog.getExistingDirectory(self,
                "Choose a directory")
        if not token_path:
            return
        self.settings.setValue('path',token_path)
        self.loadWordTokens()

    def about(self):
        QMessageBox.about(self, "About Exemplar Network Explorer",
                "Placeholder "
                "Go on... ")

    def editPreferences(self):
        dialog = PreferencesDialog(self)
        dialog.show()

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.createNetworkAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAct)

        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.editPreferencesAct)

        self.viewMenu = self.menuBar().addMenu("&View")

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def specgram(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        print(selected)
        if not selected:
            return
        if len(selected) > 1:
            return

        selectedInd = selected[0].row()
        wavfile = self.tokenTable.model().data(selected[0])
        token_path = self.settings.value('path','')
        self.specgramWindow.plot_specgram(os.path.join(token_path,wavfile))



    def details(self):
        return

    def envelope(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        if not selected:
            return
        if len(selected) > 1:
            return

        selectedInd = selected[0].row()
        for n in self.graph.g.nodes_iter(data=True):
            if n[0] == selectedInd:
                self.envelopeWindow.plot_envelopes(n[1]['acoustics']['envelopes'])
                break

    def similarity(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        if len(selected) != 2:
            return

        selectedIndOne = selected[0].row()
        selectedIndTwo = selected[1].row()
        envsOne = []
        envsTwo = []
        for n in self.graph.g.nodes_iter(data=True):
            if n[0] == selectedIndOne:
                envsOne = n[1]['acoustics']['envelopes']
            elif n[0] == selectedIndTwo:
                envsTwo = n[1]['acoustics']['envelopes']
        self.similarityWindow.plot(envsOne,envsTwo)
        self.similarityWindow.resize(4,3)

    def playfile(self):
        return

    def createToolBars(self):
        self.fileToolBar = self.addToolBar("Details")
        self.fileToolBar.addAction(self.playfileAct)

    def createStatusBar(self):
        self.statusBar().showMessage("Ready")

    def selectToken(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        if len(selected) == 1:
            self.specgram()
            self.envelope()
        elif len(selected) == 2:
            self.similarity()


    def createDockWindows(self):
        #dock = QDockWidget("Tokens", self)
        #dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        #dock.setWidget(self.tokenTable)
        #self.addDockWidget(Qt.RightDockWidgetArea, dock)
        #self.viewMenu.addAction(dock.toggleViewAction())

        dock = QDockWidget("Spectrogram", self)
        self.specgramWindow = SpecgramWidget(parent=dock)
        dock.setWidget(self.specgramWindow)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

        dock = QDockWidget("Envelopes", self)
        self.envelopeWindow = EnvelopeWidget(parent=dock)
        dock.setWidget(self.envelopeWindow)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())


        dock = QDockWidget("Similarity", self)
        self.similarityWindow = SimilarityWidget(parent=dock)
        dock.setWidget(self.similarityWindow)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

        #self.paragraphsList.currentTextChanged.connect(self.addParagraph)

    def closeEvent(self, e):
        self.settings.setValue('size', self.size())
        self.settings.setValue('pos', self.pos())
        e.accept()


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    qsrand(QTime(0,0,0).secsTo(QTime.currentTime()))

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())
