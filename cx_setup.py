

import sys
import scipy.special
import os
from cx_Freeze import setup, Executable

def readme():
    with open('README.md') as f:
        return f.read()

ufuncs_path = scipy.special._ufuncs.__file__
incl_files = [(ufuncs_path,os.path.split(ufuncs_path)[1])]

group_name = 'ENE'

exe_name = 'Exemplar Network Explorer'

shortcut_table = [
    ("StartMenuShortcut",        # Shortcut
     "ProgramMenuFolder",          # Directory_
     "%s" % (exe_name,),           # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]ene.exe",# Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,   # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     )
    ]

build_exe_options = {"excludes": ['tkinter',
                                'tk', 
                                '_tkagg', 
                                '_gtkagg', 
                                '_gtk', 
                                'tcl',
                                'matplotlib'
                                ],
                    "include_files": incl_files,
                    "includes": [
                                  "PySide",
                                  "atexit",
                                  "numpy",
                                  "scipy",
                                  "numpy.core.multiarray",
                                  "numpy.lib.format",
                                  "numpy.linalg",
                                  "numpy.linalg._umath_linalg",
                                  "numpy.linalg.lapack_lite",
                                  "scipy.integrate",
                                  "scipy.integrate.vode",
                                  #"scipy.sparse.linalg.dsolve.umfpack",
                                  "scipy.integrate.lsoda",
                                  "scipy.special",
                                  "scipy.special._ufuncs_cxx",
                                  "scipy.sparse.csgraph._validation",
                                  'sklearn.utils.sparsetools._graph_validation',
                                  'sklearn.neighbors.typedefs',
                                  'sklearn.utils.lgamma',
                                  'sklearn.utils.weight_vector',
                                  'pyqtgraph.graphicsItems.GraphItem',
                                  "sys",
                                  "acousticsim",
                                  "networkx"]}

msi_data = {"Shortcut": shortcut_table}

bdist_msi_options = {
        'upgrade_code':'{e4bd823f-e5bd-444c-b094-e4e6c76f990d}',
        'add_to_path': False,
        'initial_target_dir': r'[ProgramFiles64Folder]\%s\%s' % (group_name, exe_name),
        'data':msi_data}

bdist_mac_options = {'bundle_name':exe_name,
                     'qt_menu_nib':'/usr/local/Cellar/qt5/5.3.2/plugins/platforms',}

bdist_dmg_options = {'applications_shortcut':True}

base = None
#if sys.platform == "win32":
#    base = "Win32GUI"

setup(name='Exemplar Network Explorer',
      version='0.1',
      description='',
      long_description='',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering',
        'Topic :: Text Processing :: Linguistic',
      ],
      keywords='phonetics acoustics clustering',
      url='https://github.com/mmcauliffe/exemplar-network-explorer',
      author='Michael McAuliffe',
      author_email='michael.e.mcauliffe@gmail.com',
      packages=['exnetexplorer'],
      executables = [Executable('bin/ene.py',
                            #targetName = 'PhonologicalCorpusTools',
                            base=base,
                            #shortcutDir=r'[StartMenuFolder]\%s' % group_name,
                            #shortcutName=exe_name,
                            #icon='docs/images/logo.ico'
                            )],
      options={
          'bdist_msi': bdist_msi_options,
          'build_exe': build_exe_options,
          'bdist_mac': bdist_mac_options,
          'bdist_dmg':bdist_dmg_options}
      )
