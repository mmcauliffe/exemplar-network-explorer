import math
import sys

import os
import numpy

import PySide

from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime,QSettings,QSize,QPoint)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget, QHBoxLayout, QWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem,QDialog,QItemSelectionModel,
        QPushButton,QLabel,QTabWidget,QGroupBox, QRadioButton,QVBoxLayout,QLineEdit,QFormLayout,
        QCheckBox,QFont)

from exnetexplorer.pyqtplot_plotting import SpecgramWidget,EnvelopeWidget,DistanceWidget,NetworkWidget

from exnetexplorer.views import GraphWidget, TableWidget, NetworkGraphicsView
from exnetexplorer.models import Graph



class PreferencesDialog(QDialog):
    def __init__(self, parent, settings):
        QDialog.__init__( self, parent )

        self.settings = settings

        tabWidget = QTabWidget()

        specLayout = QFormLayout()
        self.winLenEdit = QLineEdit()
        self.winLenEdit.setText(str(settings.value('general/WinLen',0.025)))
        specLayout.addRow(QLabel('Window length (s):'),self.winLenEdit)
        self.timeStepEdit = QLineEdit()
        self.timeStepEdit.setText(str(settings.value('general/TimeStep',0.01)))
        specLayout.addRow(QLabel('Time step (s):'),self.timeStepEdit)
        self.minFreqEdit = QLineEdit()
        self.minFreqEdit.setText(str(settings.value('general/MinFreq',80)))
        specLayout.addRow(QLabel('Minimum frequency (Hz):'),self.minFreqEdit)
        self.maxFreqEdit = QLineEdit()
        self.maxFreqEdit.setText(str(settings.value('general/MaxFreq',7800)))
        specLayout.addRow(QLabel('Maximum frequency (Hz):'),self.maxFreqEdit)


        specWidget = QWidget()
        specWidget.setLayout(specLayout)

        tabWidget.addTab(specWidget,'General')

        #Network Tab
        networkLayout = QFormLayout()

        rep = settings.value('network/Representation','mfcc')

        repBox = QGroupBox()
        self.envelopeRadio = QRadioButton('Amplitude envelopes')
        self.mfccRadio = QRadioButton('MFCCs')
        self.mhecRadio = QRadioButton('MHECs')
        self.prosodyRadio = QRadioButton('Prosody')
        self.formantRadio = QRadioButton('Formants')

        if rep == 'mfcc':
            self.mfccRadio.setChecked(True)
        elif rep == 'mhec':
            self.mhecRadio.setChecked(True)
        elif rep == 'prosody':
            self.prosodyRadio.setChecked(True)
        elif rep == 'formant':
            self.formantRadio.setChecked(True)
        elif rep == 'envelopes':
            self.envelopeRadio.setChecked(True)
        hbox = QHBoxLayout()
        hbox.addWidget(self.envelopeRadio)
        hbox.addWidget(self.mfccRadio)
        hbox.addWidget(self.mhecRadio)
        hbox.addWidget(self.prosodyRadio)
        hbox.addWidget(self.formantRadio)
        repBox.setLayout(hbox)

        networkLayout.addRow(QLabel('Token representation:'),repBox)

        matchAlgorithmBox = QGroupBox()
        self.ccRadio = QRadioButton('Cross-correlation')
        self.dtwRadio = QRadioButton('DTW')
        self.dctRadio = QRadioButton('DCT')

        matchAlgorithm = settings.value('network/MatchAlgorithm','xcorr')

        if matchAlgorithm == 'xcorr':
            self.ccRadio.setChecked(True)
        elif matchAlgorithm == 'dct':
            self.dctRadio.setChecked(True)
        else:
            self.dtwRadio.setChecked(True)

        hbox = QHBoxLayout()
        hbox.addWidget(self.ccRadio)
        hbox.addWidget(self.dtwRadio)
        hbox.addWidget(self.dctRadio)
        matchAlgorithmBox.setLayout(hbox)

        networkLayout.addRow(QLabel('Similarity algorithm:'),matchAlgorithmBox)

        clusterBox = QGroupBox()
        self.completeRadio = QRadioButton('Complete')
        self.thresholdRadio = QRadioButton('Threshold')
        self.apRadio = QRadioButton('Affinity propagation')
        self.scRadio = QRadioButton('Spectral clustering')

        clustAlgorithm = settings.value('network/clusterAlgorithm','complete')

        if clustAlgorithm == 'complete':
            self.completeRadio.setChecked(True)
        elif clustAlgorithm == 'threshold':
            self.thresholdRadio.setChecked(True)
        elif clustAlgorithm == 'affinity':
            self.apRadio.setChecked(True)
        elif clustAlgorithm == 'spectral':
            self.scRadio.setChecked(True)

        hbox = QHBoxLayout()
        hbox.addWidget(self.completeRadio)
        hbox.addWidget(self.thresholdRadio)
        hbox.addWidget(self.apRadio)
        hbox.addWidget(self.scRadio)
        clusterBox.setLayout(hbox)

        networkLayout.addRow(QLabel('Cluster algorithm:'),clusterBox)


        self.oneClusterCheck = QCheckBox()
        if self.settings.value('network/OneCluster',True):
            self.oneClusterCheck.setChecked(True)
        networkLayout.addRow(QLabel('Enforce single cluster:'),self.oneClusterCheck)

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
        self.gammatoneCheck = QCheckBox()
        if self.settings.value('envelopes/Gammatone',False):
            self.gammatoneCheck.setChecked(True)
        envLayout.addRow(QLabel('Gammatone:'),self.gammatoneCheck)
        self.windowCheck = QCheckBox()
        if self.settings.value('envelopes/Windowed',False):
            self.windowCheck.setChecked(True)
        envLayout.addRow(QLabel('Windowed:'),self.windowCheck)


        envWidget = QGroupBox('Amplitude envelopes')
        envWidget.setLayout(envLayout)

        simLayout.addWidget(envWidget)

        mfccLayout = QFormLayout()
        self.numCCEdit = QLineEdit()
        self.numCCEdit.setText(str(settings.value('mfcc/NumCC',20)))
        mfccLayout.addRow(QLabel('Number of coefficents:'),self.numCCEdit)

        mfccWidget = QGroupBox('MFCC')
        mfccWidget.setLayout(mfccLayout)

        simLayout.addWidget(mfccWidget)

        simWidget = QWidget()
        simWidget.setLayout(simLayout)

        tabWidget.addTab(simWidget,'Representations')


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

        self.settings.setValue('general/WinLen',float(self.winLenEdit.text()))
        self.settings.setValue('general/TimeStep',float(self.timeStepEdit.text()))
        self.settings.setValue('general/MinFreq',int(self.minFreqEdit.text()))
        self.settings.setValue('general/MaxFreq',int(self.maxFreqEdit.text()))

        if self.mfccRadio.isChecked():
            rep = 'mfcc'
        elif self.mhecRadio.isChecked():
            rep = 'mhec'
        elif self.prosodyRadio.isChecked():
            rep = 'prosody'
        elif self.formantRadio.isChecked():
            rep = 'formant'
        else:
            rep = 'envelopes'

        self.settings.setValue('network/Representation',rep)

        if self.ccRadio.isChecked():
            match = 'xcorr'
        elif self.dctRadio.isChecked():
            match = 'dct'
        else:
            match = 'dtw'
        self.settings.setValue('network/MatchAlgorithm',match)

        if self.completeRadio.isChecked():
            clust = 'complete'
        elif self.thresholdRadio.isChecked():
            clust = 'threshold'
        elif self.apRadio.isChecked():
            clust = 'affinity'
        elif self.scRadio.isChecked():
            clust = 'spectral'
        self.settings.setValue('network/ClusterAlgorithm',clust)

        self.settings.setValue('network/OneCluster',int(self.oneClusterCheck.isChecked()))
        self.settings.setValue('network/Threshold',float(self.thresholdEdit.text()))


        self.settings.setValue('envelopes/NumBands',int(self.bandEdit.text()))
        self.settings.setValue('envelopes/Gammatone',int(self.gammatoneCheck.isChecked()))
        self.settings.setValue('envelopes/Windowed',int(self.windowCheck.isChecked()))

        self.settings.setValue('mfcc/NumCC',int(self.numCCEdit.text()))

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
        font = QFont("Courier New", 14)
        self.tokenTable.setFont(font)
        self.graphWidget = NetworkWidget(parent=self)
        self.wrapper = QWidget()
        layout = QHBoxLayout(self.wrapper)
        layout.addWidget(self.tokenTable)
        layout.addWidget(self.graphWidget)
        self.wrapper.setLayout(layout)
        self.setCentralWidget(self.wrapper)


        self.setWindowTitle("Exemplar Network Explorer")
        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        self.createDockWindows()

        self.loadWordTokens()

    def createActions(self):

        self.createNetworkWavAct = QAction( "&Create network from folder",
                self, shortcut=QKeySequence.Open,
                statusTip="Create network from folder", triggered=self.createNetworkWav)

        self.createNetworkPickleAct = QAction( "Create network from pickled objects",
                self,
                statusTip="Create network from folder", triggered=self.createNetworkPickle)

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

    def loadWordTokens(self,full_reset=False,wav=True):
        self.graph = Graph()
        if wav:
            self.graph.loadDataFromWav(self.settings,)
        else:
            self.graph.loadDataFromPickles(self.settings)
        graphSelectionModel = QItemSelectionModel(self.graph)
        self.tokenTable.setModel(self.graph)
        self.tokenTable.setSelectionModel(graphSelectionModel)
        self.tokenTable.selectionModel().selectionChanged.connect(self.selectTableToken)
        self.tokenTable.resizeColumnsToContents()
        self.graphWidget.setModel(self.tokenTable.model())
        self.graphWidget.setSelectionModel(graphSelectionModel)
        self.graphWidget.selectionModel().selectionChanged.connect(self.selectGraphToken)

    def createNetworkWav(self):
        token_path = QFileDialog.getExistingDirectory(self,
                "Choose a directory")
        if not token_path:
            return
        self.settings.setValue('path',token_path)
        self.loadWordTokens(wav=True)

    def createNetworkPickle(self):
        token_path = QFileDialog.getExistingDirectory(self,
                "Choose a directory")
        if not token_path:
            return
        self.settings.setValue('path',token_path)
        self.loadWordTokens(wav=False)

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
        self.fileMenu.addAction(self.createNetworkWavAct)
        #self.fileMenu.addAction(self.createNetworkPickleAct)
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
        node = self.graph[selectedInd]
        self.specgramWindow.plot_specgram(node['sound'].fileName())



    def details(self):
        return

    def envelope(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        if not selected:
            return
        if len(selected) > 1:
            return

        selectedInd = selected[0].row()
        node = self.graph[selectedInd]
        self.envelopeWindow.plot_envelopes(node['representation'])

    def similarity(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        if len(selected) != 2:
            return

        selectedIndOne = selected[0].row()
        selectedIndTwo = selected[1].row()

        repOne = self.graph[selectedIndOne]['representation']
        repTwo = self.graph[selectedIndTwo]['representation']
        self.distanceWindow.plot_dist_mat(repOne,repTwo)

    def playfile(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        ind = selected[0].row()
        self.graph[ind]['sound'].play()


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
        self.tokenTable.viewport().update()

    def selectTableToken(self):
        self.graphWidget.setSelectionModel(self.tokenTable.selectionModel())
        self.selectToken()

    def selectGraphToken(self):
        self.tokenTable.setSelectionModel(self.graphWidget.selectionModel())
        self.selectToken()


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

def dependencies_for_myprogram():
    from scipy.sparse.csgraph import _validation
    from scipy.special import _ufuncs_cxx
    from matplotlib.backends import backend_tkagg
