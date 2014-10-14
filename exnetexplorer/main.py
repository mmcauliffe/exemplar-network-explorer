
import os
from collections import OrderedDict

import numpy
import csv

import PySide

from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime,QSettings,QSize,QPoint)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget, QHBoxLayout, QWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem,QDialog,QItemSelectionModel,
        QPushButton,QLabel,QTabWidget,QGroupBox, QRadioButton,QVBoxLayout,QLineEdit,QFormLayout,
        QCheckBox,QFont,QSound)

from exnetexplorer.config import Settings,PreferencesDialog
from exnetexplorer.models import GraphModel, LoadWorker, ReclusterWorker, ReductionWorker
from exnetexplorer.views import TableWidget, NetworkWidget, SpecgramWidget,RepresentationWidget,DistanceWidget

class ClusterAnalysisWindow(QDialog):

    def __init__(self, parent,silhouette,completeness,homogeneity,v_score,AMI,ARS):
        QDialog.__init__( self, parent )
        layout = QVBoxLayout()

        viewLayout = QFormLayout()
        viewLayout.addRow(QLabel('Silhouette score: '),QLabel(silhouette))
        viewLayout.addRow(QLabel('Completeness: '),QLabel(completeness))
        viewLayout.addRow(QLabel('Homogeneity: '),QLabel(homogeneity))
        viewLayout.addRow(QLabel('V score: '),QLabel(v_score))
        viewLayout.addRow(QLabel('Adjusted mutual information: '),QLabel(AMI))
        viewLayout.addRow(QLabel('Adjusted Rand score: '),QLabel(ARS))

        viewWidget = QGroupBox()
        viewWidget.setLayout(viewLayout)

        layout.addWidget(viewWidget)

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
        self.setLayout(layout)



class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setMinimumSize(1000, 800)

        self.settings = Settings()

        self.loader = LoadWorker()
        self.loader.dataReady.connect(self.get_data, Qt.QueuedConnection)
        self.loader.updateProgress.connect(self.update_status, Qt.QueuedConnection)
        self.reclusterer = ReclusterWorker()
        self.reclusterer.dataReady.connect(self.get_data, Qt.QueuedConnection)
        self.reclusterer.updateProgress.connect(self.update_status, Qt.QueuedConnection)
        self.reductioner = ReductionWorker()
        self.reductioner.dataReady.connect(self.get_data, Qt.QueuedConnection)
        self.reductioner.updateProgress.connect(self.update_status, Qt.QueuedConnection)

        self.resize(self.settings['size'])
        self.move(self.settings['pos'])
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

        self.status = QLabel()
        self.status.setText("Ready")
        self.statusBar().addWidget(self.status)

        self.setWindowTitle("Exemplar Network Explorer")
        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createDockWindows()
        self.graphModel = None
        #self.load_data()


    def update_status(self,message):
        self.status.setText(message)

    def createActions(self):

        self.createNetworkWavAct = QAction( "&Create network from folder...",
                self, shortcut=QKeySequence.Open,
                statusTip="Create network from folder", triggered=self.createNetwork)

        self.exportTableAct = QAction( "Export table as text file...",
                self,
                statusTip="Export table as text file", triggered=self.exportTable)

        self.editPreferencesAct = QAction( "&Preferences...",
                self,
                statusTip="Edit preferences", triggered=self.editPreferences)

        self.networkStatisticsAct = QAction( "&Network statistics",
                self,
                statusTip="Network statistics", triggered=self.networkStatistics)

        self.clusterAnalysisAct = QAction( "&Analyze clustering performance...",
                self,
                statusTip="Analyze clustering performance", triggered=self.clusterAnalysis)

        self.exemplarReductionAct = QAction( "&Calculate exemplar reduction measure...",
                self,
                statusTip="Calculate exemplar reduction", triggered=self.exemplarReduction)

        self.specgramAct = QAction( "&View token spectrogram",
                self,
                statusTip="View token spectrogram", triggered=self.specgram)

        self.detailsAct = QAction( "&View token details",
                self,
                statusTip="View token details", triggered=self.details)

        self.representationAct = QAction( "&View token representation",
                self,
                statusTip="View token amplitude representation", triggered=self.representation)

        self.playfileAct = QAction( "&Play token",
                self,
                statusTip="Play token", triggered=self.playfile)

        self.quitAct = QAction("&Quit", self, shortcut="Ctrl+Q",
                statusTip="Quit the application", triggered=self.close)

        self.aboutAct = QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

    def batchExemplarReduction(self):
        token_dir = QFileDialog.getExistingDirectory(self,
                "Choose a directory")
        if not token_dir:
            return


    def clusterAnalysis(self):
        if self.graphModel is None:
            silhouette = "N/A"
            completeness = "N/A"
            homogeneity = "N/A"
            v_score = "N/A"
            AMI = "N/A"
            ARS = "N/A"
        else:
            silhouette = str(round(self.graphModel.cluster_network.silhouette_coefficient(),4))
            completeness = str(round(self.graphModel.cluster_network.completeness(),4))
            homogeneity = str(round(self.graphModel.cluster_network.homogeneity(),4))
            v_score = str(round(self.graphModel.cluster_network.v_score(),4))
            AMI = str(round(self.graphModel.cluster_network.adjusted_mutual_information(),4))
            ARS = str(round(self.graphModel.cluster_network.adjusted_rand_score(),4))

        dialog = ClusterAnalysisWindow(self,silhouette,
                                    completeness,homogeneity,v_score,AMI,ARS)

        result = dialog.exec_()


    def networkStatistics(self):
        pass

    def exemplarReduction(self):
        if self.graphModel is None:
            return
        self.reductioner.set_params(self.graphModel.cluster_network)
        self.reductioner.start()

    def load_data(self):
        self.loader.set_params(self.settings)
        self.loader.start()

    def get_data(self, data):
        self.graphModel = GraphModel(data)
        graphSelectionModel = QItemSelectionModel(self.graphModel)

        self.tokenTable.setModel(self.graphModel)
        self.graphWidget.setModel(self.tokenTable.model())

        self.tokenTable.setSelectionModel(graphSelectionModel)
        self.graphWidget.setSelectionModel(self.tokenTable.selectionModel())

        self.tokenTable.selectionModel().selectionChanged.connect(self.selectTableToken)
        self.graphWidget.selectionModel().selectionChanged.connect(self.selectGraphToken)

        self.tokenTable.resizeColumnsToContents()

    def createNetwork(self):
        token_path = QFileDialog.getExistingDirectory(self,
                "Choose a directory")
        if not token_path:
            return
        self.settings['path'] = token_path
        self.load_data()

    def exportTable(self):
        out_path = QFileDialog.getSaveFileName(self,
                "Specify a file path")
        if not out_path[0]:
            return
        with open(out_path[0],'w') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(self.graphModel.columns)
            for rowNumber in range(self.graphModel.rowCount()):
                fields = [
                    self.graphModel.data(
                        self.graphModel.index(rowNumber, columnNumber),
                        Qt.DisplayRole
                    )
                    for columnNumber in range(self.graphModel.columnCount())
                ]
                writer.writerow(fields)

    def about(self):
        QMessageBox.about(self, "About Exemplar Network Explorer",
                "Placeholder "
                "Go on... ")

    def recluster(self,redo_scores = False):
        self.reclusterer.set_params(self.settings, self.graphModel.cluster_network, redo_scores)
        self.reclusterer.start()

    def editPreferences(self):
        dialog = PreferencesDialog(self,self.settings)
        result = dialog.exec_()
        if result:
            self.settings = dialog.settings
            if dialog.rep_changed:
                self.load_data()
            elif dialog.network_changed:
                self.recluster(True)
                self.graphWidget.get_defaults()
            else:
                self.recluster(False)
                self.graphWidget.get_defaults()

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.createNetworkWavAct)
        self.fileMenu.addAction(self.exportTableAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAct)

        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.editPreferencesAct)

        self.analysisMenu = self.menuBar().addMenu("&Analysis")
        self.analysisMenu.addAction(self.networkStatisticsAct)
        self.analysisMenu.addAction(self.clusterAnalysisAct)
        self.analysisMenu.addAction(self.exemplarReductionAct)

        self.viewMenu = self.menuBar().addMenu("&Windows")

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def specgram(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        if not selected:
            self.specgramWindow.reset()
            return
        if len(selected) > 1:
            return

        selectedInd = selected[0].row()
        node = self.graphModel.cluster_network[selectedInd]
        win_len = 0.025
        time_step = 0.01

        token_path = self.settings['path']
        if not token_path:
            return
        self.specgramWindow.plot_specgram(
                    node['rep']._filepath,
                    win_len, time_step)



    def details(self):
        return

    def representation(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        if not selected:
            self.representationWindow.reset()
            return
        if len(selected) > 1:
            return

        selectedInd = selected[0].row()
        node = self.graphModel.cluster_network[selectedInd]
        self.representationWindow.plot_representation(node['rep']._rep)

    def similarity(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        if len(selected) != 2:
            self.distanceWindow.reset()
            return

        selectedIndOne = selected[0].row()
        selectedIndTwo = selected[1].row()

        repOne = self.graphModel.cluster_network[selectedIndOne]['rep']._rep
        repTwo = self.graphModel.cluster_network[selectedIndTwo]['rep']._rep
        distance = self.graphModel.cluster_network[selectedIndOne,selectedIndTwo]
        self.distanceWindow.plot_dist_mat(repOne,repTwo,distance)

    def playfile(self):
        selected = self.tokenTable.selectionModel().selectedRows()
        ind = selected[0].row()

        token_path = self.settings['path']
        if not token_path:
            return
        QSound(os.path.join(token_path,self.graphModel.cluster_network[ind]['rep']._filepath)).play()


    def createToolBars(self):
        self.fileToolBar = self.addToolBar("Details")
        self.fileToolBar.addAction(self.playfileAct)

    def selectToken(self):
        self.specgram()
        self.representation()
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

        dock = QDockWidget("Auditory Representation", self)
        self.representationWindow = RepresentationWidget(parent=dock)
        dock.setWidget(self.representationWindow)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())


        dock = QDockWidget("Distance", self)
        self.distanceWindow = DistanceWidget(parent=dock)
        dock.setWidget(self.distanceWindow)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())


    def closeEvent(self, e):
        self.settings['size'] = self.size()
        self.settings['pos'] = self.pos()
        e.accept()



def dependencies_for_cxfreeze():
    from scipy.sparse.csgraph import _validation
    from scipy.special import _ufuncs_cxx
