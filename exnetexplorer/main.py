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
        QCheckBox)

from pyqtplot_plotting import SpecgramWidget,EnvelopeWidget,DistanceWidget

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
        
        rep = settings.value('network/Representation','envelope')
        
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
        else:
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
        if matchAlgorithm == 'dct':
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
        
        
        envWidget = QGroupBox('Amplitude envelopes')
        envWidget.setLayout(envLayout)
        
        simLayout.addWidget(envWidget)
        
        mfccLayout = QFormLayout()
        self.numCCEdit = QLineEdit()
        self.numCCEdit.setText(str(settings.value('mfcc/NumCC',20)))
        mfccLayout.addRow(QLabel('Number of coefficents:'),self.numCCEdit)
        self.mfccWinLenEdit = QLineEdit()
        self.mfccWinLenEdit.setText(str(settings.value('mfcc/WindowLength',0.015)))
        mfccLayout.addRow(QLabel('Window length (s):'),self.mfccWinLenEdit)
        self.mfccTimeStepEdit = QLineEdit()
        self.mfccTimeStepEdit.setText(str(settings.value('mfcc/TimeStep',0.005)))
        mfccLayout.addRow(QLabel('Maximum frequency (Hz):'),self.mfccTimeStepEdit)
        self.maxMFCCFreqEdit = QLineEdit()
        self.maxMFCCFreqEdit.setText(str(settings.value('mfcc/MaxFreq',7800)))
        mfccLayout.addRow(QLabel('Maximum frequency (Hz):'),self.maxMFCCFreqEdit)
        
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
        
        if self.mfccRadio.isChecked():
            rep = 'mfcc'
        elif self.mhecRadio.isChecked():
            rep = 'mhec'
        elif self.mfccRadio.isChecked():
            rep = 'prosody'
        elif self.mfccRadio.isChecked():
            rep = 'formant'
        else:
            rep = 'envelope'
            
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
        else:
            clust = 'incremental'
        self.settings.setValue('network/ClusterAlgorithm',clust)
        self.settings.setValue('network/Threshold',float(self.thresholdEdit.text()))
        
        
        self.settings.setValue('envelopes/NumBands',int(self.bandEdit.text()))
        self.settings.setValue('envelopes/MinFreq',int(self.minFreqEdit.text()))
        self.settings.setValue('envelopes/MaxFreq',int(self.maxFreqEdit.text()))
        
        self.settings.setValue('mfcc/NumCC',int(self.numCCEdit.text()))
        self.settings.setValue('mfcc/WindowLength',float(self.mfccWinLenEdit.text()))
        self.settings.setValue('mfcc/TimeStep',float(self.mfccTimeStepEdit.text()))
        self.settings.setValue('mfcc/MaxFreq',int(self.maxMFCCFreqEdit.text()))
        
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


        self.setWindowTitle("Exemplar Network Explorer")
        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        self.createDockWindows()
        
        self.graph = Graph()
        self.graph.loadData(self.settings)
        self.tokenTable.setModel(self.graph)
        self.tokenTable.setSelectionModel(QItemSelectionModel(self.graph))
        self.tokenTable.selectionModel().selectionChanged.connect(self.selectToken)
        self.graphWidget.setModel(self.tokenTable.model())

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

    def loadWordTokens(self,full_reset=False):
        self.graph.loadData(self.settings)

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

        rep = self.settings.value('network/Representation','envelope')
        selectedInd = selected[0].row()
        for n in self.graph.g.nodes_iter(data=True):
            if n[0] == selectedInd:
                self.envelopeWindow.plot_envelopes(n[1]['acoustics'][rep])
                break

    def similarity(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        if len(selected) != 2:
            return

        selectedIndOne = selected[0].row()
        selectedIndTwo = selected[1].row()
        envsOne = []
        envsTwo = []
        rep = self.settings.value('network/Representation','envelope')
        for n in self.graph.g.nodes_iter(data=True):
            if n[0] == selectedIndOne:
                envsOne = n[1]['acoustics'][rep]
            elif n[0] == selectedIndTwo:
                envsTwo = n[1]['acoustics'][rep]
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
