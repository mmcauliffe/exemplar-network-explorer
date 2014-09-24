
from PySide.QtCore import (qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand,
        Qt, QTime,QSettings,QSize,QPoint)
from PySide.QtGui import (QBrush, QKeySequence, QColor, QLinearGradient, QPainter,
        QPainterPath, QPen, QPolygonF, QRadialGradient, QApplication, QGraphicsItem, QGraphicsScene,
        QGraphicsView, QStyle,QMainWindow, QAction, QDialog, QDockWidget, QHBoxLayout, QWidget,
        QFileDialog, QListWidget, QMessageBox,QTableWidget,QTableWidgetItem,QDialog,QItemSelectionModel,
        QPushButton,QLabel,QTabWidget,QGroupBox, QRadioButton,QVBoxLayout,QLineEdit,QFormLayout,
        QCheckBox,QFont,QSound, QComboBox)

class BasePane(QWidget):
    """Abstract, don't use"""

    prev_state = {}

    def get_current_state(self):
        return None

    def is_changed(self):
        return self.get_current_state() != self.prev_state


class NetworkPane(BasePane):
    def __init__(self, setting_dict):
        BasePane.__init__( self )

        networkLayout = QFormLayout()

        matchAlgorithmBox = QGroupBox()
        self.ccRadio = QRadioButton('Cross-correlation')
        self.dtwRadio = QRadioButton('DTW')
        self.dctRadio = QRadioButton('DCT')

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

        hbox = QHBoxLayout()
        hbox.addWidget(self.completeRadio)
        hbox.addWidget(self.thresholdRadio)
        hbox.addWidget(self.apRadio)
        hbox.addWidget(self.scRadio)
        clusterBox.setLayout(hbox)

        networkLayout.addRow(QLabel('Cluster algorithm:'),clusterBox)

        self.oneClusterCheck = QCheckBox()
        networkLayout.addRow(QLabel('Enforce single cluster:'),self.oneClusterCheck)

        self.thresholdEdit = QLineEdit()
        networkLayout.addRow(QLabel('Similarity threshold:'),self.thresholdEdit)

        self.setLayout(networkLayout)

        #set up defaults

        matchAlgorithm = setting_dict['dist_func']
        clustAlgorithm = setting_dict['cluster_alg']
        oneCluster = setting_dict['one_cluster']

        if matchAlgorithm == 'xcorr':
            self.ccRadio.setChecked(True)
        elif matchAlgorithm == 'dct':
            self.dctRadio.setChecked(True)
        else:
            self.dtwRadio.setChecked(True)

        if clustAlgorithm == 'complete':
            self.completeRadio.setChecked(True)
        elif clustAlgorithm == 'threshold':
            self.thresholdRadio.setChecked(True)
        elif clustAlgorithm == 'affinity':
            self.apRadio.setChecked(True)
        elif clustAlgorithm == 'spectral':
            self.scRadio.setChecked(True)

        if oneCluster:
            self.oneClusterCheck.setChecked(True)
        self.thresholdEdit.setText(str(setting_dict['threshold']))

        self.prev_state = setting_dict

    def get_current_state(self):
        setting_dict = {}

        if self.ccRadio.isChecked():
            setting_dict['dist_func'] = 'xcorr'
        elif self.dctRadio.isChecked():
            setting_dict['dist_func'] = 'dct'
        elif self.dtwRadio.isChecked():
            setting_dict['dist_func'] = 'dtw'

        if self.completeRadio.isChecked():
            setting_dict['cluster_alg'] = 'complete'
        elif self.thresholdRadio.isChecked():
            setting_dict['cluster_alg'] = 'threshold'
        elif self.apRadio.isChecked():
            setting_dict['cluster_alg'] = 'affinity'
        elif self.scRadio.isChecked():
            setting_dict['cluster_alg'] = 'spectral'

        setting_dict['one_cluster'] = int(self.oneClusterCheck.isChecked())
        setting_dict['threshold'] = float(self.thresholdEdit.text())

        return setting_dict

    def is_changed(self):
        cur_state = self.get_current_state()
        if self.prev_state['dist_func'] != cur_state['dist_func']:
            return True
        return False
        for k in ['dist_func','cluster_alg']:
            if self.prev_state[k] != cur_state[k]:
                return True
        if cur_state['cluster_alg'] == 'threshold':
            if self.prev_state['threshold'] != cur_state['threshold']:
                return True
        elif cur_state['cluster_alg'] in {'affinity','spectral'}:
            if self.prev_state['one_cluster'] != cur_state['one_cluster']:
                return True
        return False

class RepresentationPane(BasePane):
    def __init__(self, setting_dict):
        BasePane.__init__( self )

        repLayout = QVBoxLayout()

        genLayout = QFormLayout()
        self.winLenEdit = QLineEdit()
        genLayout.addRow(QLabel('Window length (s):'),self.winLenEdit)
        self.timeStepEdit = QLineEdit()
        genLayout.addRow(QLabel('Time step (s):'),self.timeStepEdit)
        self.minFreqEdit = QLineEdit()
        genLayout.addRow(QLabel('Minimum frequency (Hz):'),self.minFreqEdit)
        self.maxFreqEdit = QLineEdit()
        genLayout.addRow(QLabel('Maximum frequency (Hz):'),self.maxFreqEdit)
        self.numCoresEdit = QLineEdit()
        genLayout.addRow(QLabel('Number of cores (multiprocessing):'),self.numCoresEdit)

        repBox = QGroupBox()
        self.envelopeRadio = QRadioButton('Amplitude envelopes')
        self.mfccRadio = QRadioButton('MFCCs')
        self.mhecRadio = QRadioButton('MHECs')
        self.prosodyRadio = QRadioButton('Prosody')
        self.formantRadio = QRadioButton('Formants')
        hbox = QHBoxLayout()
        hbox.addWidget(self.envelopeRadio)
        hbox.addWidget(self.mfccRadio)
        #hbox.addWidget(self.mhecRadio)
        #hbox.addWidget(self.prosodyRadio)
        #hbox.addWidget(self.formantRadio)
        repBox.setLayout(hbox)

        genLayout.addRow(QLabel('Token representation:'),repBox)

        genWidget = QGroupBox('General')
        genWidget.setLayout(genLayout)
        repLayout.addWidget(genWidget)

        envLayout = QFormLayout()
        self.bandEdit = QLineEdit()
        envLayout.addRow(QLabel('Number of bands:'),self.bandEdit)
        self.gammatoneCheck = QCheckBox()
        envLayout.addRow(QLabel('Gammatone:'),self.gammatoneCheck)
        self.windowCheck = QCheckBox()
        envLayout.addRow(QLabel('Windowed:'),self.windowCheck)


        envWidget = QGroupBox('Amplitude envelopes')
        envWidget.setLayout(envLayout)
        repLayout.addWidget(envWidget)

        mfccLayout = QFormLayout()
        self.numCCEdit = QLineEdit()
        mfccLayout.addRow(QLabel('Number of coefficents:'),self.numCCEdit)
        self.numFiltersEdit = QLineEdit()
        mfccLayout.addRow(QLabel('Number of filters:'),self.numFiltersEdit)
        self.powerCheck = QCheckBox()
        mfccLayout.addRow(QLabel('Use power (first coefficient):'),self.powerCheck)

        mfccWidget = QGroupBox('MFCC')
        mfccWidget.setLayout(mfccLayout)

        repLayout.addWidget(mfccWidget)

        self.setLayout(repLayout)

        self.winLenEdit.setText(str(setting_dict['win_len']))
        self.timeStepEdit.setText(str(setting_dict['time_step']))
        freq_lims = setting_dict['freq_lims']
        self.minFreqEdit.setText(str(freq_lims[0]))
        self.maxFreqEdit.setText(str(freq_lims[1]))
        self.numCoresEdit.setText(str(setting_dict['num_cores']))

        rep = setting_dict['rep']
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

        self.bandEdit.setText(str(setting_dict['envelope_bands']))

        if setting_dict['use_gammatone']:
            self.gammatoneCheck.setChecked(True)
        if setting_dict['use_window']:
            self.windowCheck.setChecked(True)

        self.numFiltersEdit.setText(str(setting_dict['mfcc_filters']))
        self.numCCEdit.setText(str(setting_dict['num_coeffs']))
        if setting_dict['use_power']:
            self.powerCheck.setChecked(True)

        self.prev_state = setting_dict

    def get_current_state(self):
        setting_dict = {}

        if self.mfccRadio.isChecked():
            setting_dict['rep'] = 'mfcc'
        elif self.mhecRadio.isChecked():
            setting_dict['rep'] = 'mhec'
        elif self.prosodyRadio.isChecked():
            setting_dict['rep'] = 'prosody'
        elif self.formantRadio.isChecked():
            setting_dict['rep'] = 'formant'
        elif self.envelopeRadio.isChecked():
            setting_dict['rep'] = 'envelopes'

        setting_dict['win_len'] = float(self.winLenEdit.text())
        setting_dict['time_step'] = float(self.timeStepEdit.text())
        setting_dict['freq_lims'] = (int(self.minFreqEdit.text()),
                                    int(self.maxFreqEdit.text()))
        setting_dict['num_cores'] = int(self.numCoresEdit.text())

        setting_dict['envelope_bands'] = int(self.bandEdit.text())
        setting_dict['use_gammatone'] = int(self.gammatoneCheck.isChecked())
        setting_dict['use_window'] = int(self.windowCheck.isChecked())

        setting_dict['num_coeffs'] = int(self.numCCEdit.text())
        setting_dict['mfcc_filters'] = int(self.numFiltersEdit.text())
        setting_dict['use_power'] = int(self.powerCheck.isChecked())

        return setting_dict

    def is_changed(self):
        cur_state = self.get_current_state()
        if self.prev_state['rep'] != cur_state['rep']:
            return True
        if cur_state['rep'] == 'mfcc':
            for k in ['win_len','time_step','freq_lims',
                    'num_coeffs','mfcc_filters','use_power']:
                if cur_state[k] != self.prev_state[k]:
                    return True
        elif cur_state['rep'] == 'envelopes':
            for k in ['freq_lims','envelope_bands',
                        'use_gammatone', 'use_window']:
                if cur_state[k] != self.prev_state[k]:
                    return True
            if cur_state['use_window']:
                for k in ['win_len','time_step']:
                    if cur_state[k] != self.prev_state[k]:
                        return True
        return False

class SpecgramPane(BasePane):
    def __init__(self, setting_dict):
        BasePane.__init__( self )
        specLayout = QFormLayout()

        analysisLayout = QFormLayout()

        self.winLenEdit = QLineEdit()
        analysisLayout.addRow(QLabel('Window length:'),self.winLenEdit)

        self.methodCombo = QComboBox()
        self.methodCombo.addItem("Fourier")
        analysisLayout.addRow(QLabel('Method:'),self.methodCombo)

        self.winTypeCombo = QComboBox()
        self.winTypeCombo.addItem("Square (rectangular)")
        self.winTypeCombo.addItem("Hamming (raised sine-squared)")
        self.winTypeCombo.addItem("Bartlett (triangular)")
        self.winTypeCombo.addItem("Welch (parabolic)")
        self.winTypeCombo.addItem("Hanning (sine-squared)")
        self.winTypeCombo.addItem("Gaussian")
        analysisLayout.addRow(QLabel('Window type:'),self.winTypeCombo)

        analysisWidget = QGroupBox('Analysis')
        analysisWidget.setLayout(analysisLayout)
        specLayout.addWidget(analysisWidget)


        resLayout = QFormLayout()
        self.freqStepsEdit = QLineEdit()
        resLayout.addRow(QLabel('Number of frequency steps:'),self.freqStepsEdit)

        self.timeStepsEdit = QLineEdit()
        resLayout.addRow(QLabel('Number of time steps:'),self.timeStepsEdit)


        resWidget = QGroupBox('Frequency and time resolution')
        resWidget.setLayout(resLayout)
        specLayout.addWidget(resWidget)


        viewLayout = QFormLayout()
        self.autoScaleCheck = QCheckBox()
        viewLayout.addRow(QLabel('Autoscale:'),self.autoScaleCheck)

        self.dynamicRangeEdit = QLineEdit()
        viewLayout.addRow(QLabel('Dynamic range (dB):'),self.dynamicRangeEdit)

        self.maxEdit = QLineEdit()
        viewLayout.addRow(QLabel('Maximum (dB/Hz):'),self.maxEdit)

        self.preEmphAlphaEdit = QLineEdit()
        viewLayout.addRow(QLabel('Pre-emphasis alpha:'),self.preEmphAlphaEdit)


        viewWidget = QGroupBox('View settings')
        viewWidget.setLayout(viewLayout)
        specLayout.addWidget(viewWidget)



        self.prev_state = setting_dict

    def get_current_state(self):
        setting_dict = {}
        return setting_dict


class Settings(object):

    key_to_ini = {'path': ('general/path',''),
                    'size':('size', QSize(270, 225)),
                    'pos': ('pos', QPoint(50, 50)),
                    'rep': ('general/Representation','mfcc'),
                    'freq_lims': [('general/MinFreq',80),('general/MaxFreq',7800)],
                    'win_len': ('general/WindowLength',0.025),
                    'time_step': ('general/TimeStep',0.01),
                    'num_cores': ('general/NumCores',1),
                    'num_coeffs': ('mfcc/NumCC',20),
                    'mfcc_filters': ('mfcc/NumFilters',26),
                    'use_power': ('mfcc/UsePower',False),
                    'envelope_bands': ('envelopes/NumBands',4),
                    'use_gammatone': ('envelopes/UseGammatone',False),
                    'use_window': ('envelopes/UseWindow',False),
                    'dist_func': ('network/DistanceFunction','dtw'),
                    'cluster_alg': ('network/ClusterAlgorithm','complete'),
                    'one_cluster': ('network/OneCluster',False),
                    'threshold': ('network/Threshold',0),
                    'spec_win_len':('spectrogram/WindowLength',0.005),
                    'spec_win_type':('spectrogram/WindowType','gaussian'),
                    'spec_freq_steps':('spectrogram/FreqSteps',250),
                    'spec_time_steps':('spectrogram/TimeSteps',1000),
                    'spec_autoscale':('spectrogram/Autoscale',True),
                    'spec_dynamic_range':('spectrogram/DynamicRange',70),
                    'spec_max':('spectrogram/Maximum',100),
                    'spec_alpha':('spectrogram/PreEmphAlpha',0.97)}

    rep_setting_keys = ['rep','freq_lims','win_len','time_step','num_coeffs',
                'mfcc_filters','envelope_bands','use_power','num_cores',
                'use_gammatone', 'use_window']

    asim_kwarg_keys = ['rep','freq_lims','win_len','time_step','num_coeffs',
                'num_filters','use_power','num_cores','dist_func']

    network_setting_keys = ['dist_func', 'cluster_alg', 'one_cluster', 'threshold']

    specgram_setting_keys = ['spec_win_len','spec_win_type','spec_freq_steps',
                            'spec_time_steps','spec_autoscale', 'spec_dynamic_range',
                            'spec_max','spec_alpha']

    def __init__(self):
        self.qs = QSettings('settings.ini',QSettings.IniFormat)
        self.qs.setFallbacksEnabled(False)

    def __getitem__(self, key):
        if key == 'num_filters':
            if self['rep'] == 'mfcc':
                return self['mfcc_filters']
            elif self['rep'] == 'envelopes':
                return self['envelope_bands']

        mapped_key = self.key_to_ini[key]
        if isinstance(mapped_key, list):
            return tuple(type(d)(self.qs.value(k,d)) for k, d in mapped_key)
        else:
            inikey, default = mapped_key
            return type(default)(self.qs.value(inikey,default))

    def __setitem__(self, key, value):
        mapped_key = self.key_to_ini[key]
        if isinstance(mapped_key, list):
            if not isinstance(value,list) and not isinstance(value,tuple):
                raise(KeyError)
            if len(mapped_key) != len(value):
                raise(KeyError)
            for i,(k, d) in enumerate(mapped_key):
                self.qs.setValue(k,value[i])
        else:
            inikey, default = mapped_key
            self.qs.setValue(inikey,value)


    def update(self,setting_dict):
        for k,v in setting_dict.items():
            self[k] = v

    def acousticsim_kwarg(self):
        out = {x: self[x] for x in self.asim_kwarg_keys}
        out['return_rep'] = True
        return out

    def get_rep_settings(self):
        out = {x: self[x] for x in self.rep_setting_keys}
        return out

    def get_network_settings(self):
        out = {x: self[x] for x in self.network_setting_keys}
        return out

    def get_specgram_settings(self):
        out = {x: self[x] for x in self.specgram_setting_keys}
        return out

class PreferencesDialog(QDialog):

    def __init__(self, parent, settings):
        QDialog.__init__( self, parent )

        self.settings = settings

        tabWidget = QTabWidget()

        #Representations
        self.repWidget = RepresentationPane(self.settings.get_rep_settings())

        tabWidget.addTab(self.repWidget,'Representations')


        #Network Tab

        self.networkWidget = NetworkPane(self.settings.get_network_settings())
        tabWidget.addTab(self.networkWidget, 'Network')


        self.specWidget = SpecgramPane(self.settings.get_specgram_settings())
        tabWidget.addTab(self.specWidget,'Spectrogram')


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

        self.setLayout(layout)

        self.network_changed = False
        self.rep_changed = False
        self.specgram_changed = False


    def accept(self):
        self.network_changed = self.networkWidget.is_changed()
        self.rep_changed = self.repWidget.is_changed()
        self.specgram_changed = self.specWidget.is_changed()

        self.settings.update(self.networkWidget.get_current_state())
        self.settings.update(self.repWidget.get_current_state())
        self.settings.update(self.specWidget.get_current_state())

        QDialog.accept(self)
