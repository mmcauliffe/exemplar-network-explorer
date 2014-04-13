import math
import sys
from linghelper.phonetics.similarity.envelope import envelope_similarity,calc_envelope,correlate_envelopes
from linghelper.distance.dtw import generate_distance_matrix, regularDTW

import os
import networkx as nx
import numpy
import scipy.signal

import PySide

from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime,QSettings,QSize,QPoint)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget, QHBoxLayout, QWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem,QDialog,QItemSelectionModel,
        QPushButton,QLabel,QTabWidget,QGroupBox, QRadioButton,QVBoxLayout,QLineEdit,QFormLayout,
        QCheckBox)

from pyqtplot_plotting import SpecgramWidget,EnvelopeWidget,DistanceWidget
from matplotlib_plotting import SimilarityWidget

from views import GraphWidget, TableWidget, NetworkGraphicsView
from models import Graph

class PreferencesDialog(QDialog):
    def __init__(self, parent, settings):
        QDialog.__init__( self, parent )

        self.settings = settings

        tabWidget = QTabWidget()
        
        specLayout = QFormLayout()
        self.winLenEdit = QLineEdit()
        self.winLenEdit.setText(str(settings.value('spectrogram/WinLen',0.025)))
        specLayout.addRow(QLabel('Window length (s):'),self.winLenEdit)
        self.timeStepEdit = QLineEdit()
        self.timeStepEdit.setText(str(settings.value('spectrogram/TimeStep',0.01)))
        specLayout.addRow(QLabel('Time step (s):'),self.timeStepEdit)
        
        
        specWidget = QWidget()
        specWidget.setLayout(specLayout)
        
        tabWidget.addTab(specWidget,'Spectrogram')
        
        #Network Tab
        networkLayout = QFormLayout()
        clusterBox = QGroupBox()
        self.completeRadio = QRadioButton('Complete')
        self.thresholdRadio = QRadioButton('Threshold')
        self.incrementalRadio = QRadioButton('Incremental')
        
        clustAlgorithm = settings.value('network/clusterAlgorithm','complete')
        
        if clustAlgorithm == 'complete':
            self.completeRadio.setChecked(True)
        elif clustAlgorithm == 'threshold':
            self.thresholdRadio.setChecked(True)
        else:
            self.incrementalRadio.setChecked(True)
            
        hbox = QHBoxLayout()
        hbox.addWidget(self.completeRadio)
        hbox.addWidget(self.thresholdRadio)
        hbox.addWidget(self.incrementalRadio)
        clusterBox.setLayout(hbox)
        
        networkLayout.addRow(QLabel('Cluster algorithm:'),clusterBox)
        
        self.thresholdEdit = QLineEdit()
        self.thresholdEdit.setText(str(settings.value('network/Threshold',0.9)))
        networkLayout.addRow(QLabel('Similarity threshold:'),self.thresholdEdit)
        
        
        networkWidget = QWidget()
        networkWidget.setLayout(networkLayout)
        
        
        tabWidget.addTab(networkWidget, 'Network')
        
        
        #Similarity
        simLayout = QVBoxLayout()
        
        envLayout = QFormLayout()
        self.bandEdit = QLineEdit()
        self.bandEdit.setText(str(settings.value('envelopes/NumBands',4)))
        envLayout.addRow(QLabel('Number of bands:'),self.bandEdit)
        self.minFreqEdit = QLineEdit()
        self.minFreqEdit.setText(str(settings.value('envelopes/MinFreq',80)))
        envLayout.addRow(QLabel('Minimum frequency (Hz):'),self.minFreqEdit)
        self.maxFreqEdit = QLineEdit()
        self.maxFreqEdit.setText(str(settings.value('envelopes/MaxFreq',7800)))
        envLayout.addRow(QLabel('Maximum frequency (Hz):'),self.maxFreqEdit)
        self.erbCheck = QCheckBox()
        if self.settings.value('envelopes/ERB',False):
            self.erbCheck.setChecked(True)
        envLayout.addRow(QLabel('ERB:'),self.erbCheck)
        
        
        matchAlgorithmBox = QGroupBox()
        self.ccRadio = QRadioButton('Cross-correlation')
        self.dtwRadio = QRadioButton('DTW')
        
        matchAlgorithm = settings.value('envelopes/MatchAlgorithm','xcorr')
        
        if matchAlgorithm == 'xcorr':
            self.ccRadio.setChecked(True)
        else:
            self.dtwRadio.setChecked(True)
            
        hbox = QHBoxLayout()
        hbox.addWidget(self.ccRadio)
        hbox.addWidget(self.dtwRadio)
        matchAlgorithmBox.setLayout(hbox)
        
        envLayout.addRow(QLabel('Envelope matching algorithm:'),matchAlgorithmBox)
        
        envWidget = QGroupBox('Amplitude envelopes')
        envWidget.setLayout(envLayout)
        
        simLayout.addWidget(envWidget)
        
        mfccLayout = QFormLayout()
        self.numCCEdit = QLineEdit()
        self.numCCEdit.setText(str(settings.value('mfcc/NumCC',12)))
        mfccLayout.addRow(QLabel('Number of coefficents:'),self.numCCEdit)
        self.maxMFCCFreqEdit = QLineEdit()
        self.maxMFCCFreqEdit.setText(str(settings.value('mfcc/MaxFreq',7800)))
        mfccLayout.addRow(QLabel('Maximum frequency (Hz):'),self.maxMFCCFreqEdit)
        self.ampNormCheck = QCheckBox()
        if settings.value('mfcc/NormAmp',True):
            self.ampNormCheck.setChecked(True)
        mfccLayout.addRow(QLabel('Amplitude normalization:'),self.ampNormCheck)
        
        mfccWidget = QGroupBox('MFCC DTW')
        mfccWidget.setLayout(mfccLayout)
        
        simLayout.addWidget(mfccWidget)
        
        simWidget = QWidget()
        simWidget.setLayout(simLayout)
        
        tabWidget.addTab(simWidget,'Similarity')
        

        layout = QVBoxLayout()
        layout.addWidget(tabWidget)
        
        #Accept cancel
        self.acceptButton = QPushButton('Ok')
        self.cancelButton = QPushButton('Cancel')
        
        self.acceptButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.acceptButton)
        hbox.addWidget(self.cancelButton)
        ac = QWidget()
        ac.setLayout(hbox)
        layout.addWidget(ac)
        
        self.setLayout( layout )
        
    def accept(self):
        
        self.settings.setValue('spectrogram/WinLen',float(self.winLenEdit.text()))
        self.settings.setValue('spectrogram/TimeStep',float(self.timeStepEdit.text()))
        
        if self.completeRadio.isChecked():
            clust = 'complete'
        elif self.thresholdRadio.isChecked():
            clust = 'threshold'
        else:
            clust = 'incremental'
        self.settings.setValue('network/ClusterAlgorithm',clust)
        self.settings.setValue('network/Threshold',float(self.thresholdEdit.text()))
        
        
        self.settings.setValue('envelopes/NumBands',int(self.bandEdit.text()))
        self.settings.setValue('envelopes/MinFreq',int(self.minFreqEdit.text()))
        self.settings.setValue('envelopes/MaxFreq',int(self.maxFreqEdit.text()))
        
        if self.ccRadio.isChecked():
            match = 'xcorr'
        else:
            match = 'dtw'
        self.settings.setValue('envelopes/MatchAlgorithm',match)
        
        self.settings.setValue('mfcc/NumCC',int(self.numCCEdit.text()))
        self.settings.setValue('mfcc/MaxFreq',int(self.maxMFCCFreqEdit.text()))
        self.settings.setValue('mfcc/NormAmp',self.ampNormCheck.isChecked())
        
        QDialog.accept(self)

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
        if not os.path.exists(token_path):
            token_path = ''
            self.settings.setValue('path','')
        if not token_path:
            return
        num_bands = int(self.settings.value('envelopes/NumBands',4))
        erb = self.settings.value('envelopes/ERB',False)
        freq_lims = (int(self.settings.value('envelopes/MinFreq',80)),int(self.settings.value('envelopes/MaxFreq',7800)))
        files = os.listdir(token_path)
        nodes = []
        ind = 0
        for f in files:
            if not (f.endswith('.wav') or f.endswith('.WAV')):
                continue
            env = calc_envelope(os.path.join(token_path,f),num_bands,freq_lims,erb)

            nodes.append((ind,{'label':f,'acoustics':{'envelopes':env}}))
            ind += 1
        g.add_nodes_from(nodes)
        clusterAlgorithm = self.settings.value('network/ClusterAlgorithm','complete')
        matchAlgorithm = self.settings.value('envelopes/MatchAlgorithm','xcorr')
        edges = []
        if clusterAlgorithm == 'incremental':
            pass
        else:
            threshold = float(self.settings.value('network/Threshold'))
            for i in range(len(nodes)-1):
                envsOne = nodes[i][1]['acoustics']['envelopes']
                for j in range(i+1,len(nodes)):
                    envsTwo = nodes[j][1]['acoustics']['envelopes']
                    
                    sim = correlate_envelopes(envsOne,envsTwo)
                    if clusterAlgorithm == 'threshold' and sim < threshold:
                        continue
                    edges.append((nodes[i][0],nodes[j][0],sim))

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
        dialog = PreferencesDialog(self,self.settings)
        result = dialog.exec_()
        if result:
            self.settings = dialog.settings
            self.loadWordTokens()

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
        self.distanceWindow.plot_dist_mat(envsOne,envsTwo)

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


        dock = QDockWidget("Distance", self)
        self.distanceWindow = DistanceWidget(parent=dock)
        dock.setWidget(self.distanceWindow)
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
