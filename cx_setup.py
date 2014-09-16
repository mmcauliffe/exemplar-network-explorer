

import sys
import os
from site import getsitepackages
from cx_Freeze import setup, Executable

def readme():
    with open('README.md') as f:
        return f.read()

group_name = 'ENE'

exe_name = 'Exemplar Network Explorer'

shortcut_table = [
    ("StartMenuShortcut",        # Shortcut
     "ProgramMenuFolder",          # Directory_
     "%s" % (exe_name,),           # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]pct.exe",# Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,   # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     )
    ]

build_exe_options = {"excludes": ['tkinter','tk', '_tkagg', '_gtkagg', '_gtk', 'tcl','matplotlib'],
                    "include_files": [(os.path.join(getsitepackages()[1],'scipy/sparse/sparsetools/_csr.pyd'),'_csr.pyd'),
                                        (os.path.join(getsitepackages()[1],'scipy/sparse/sparsetools/_csc.pyd'),'_csc.pyd'),
                                        (os.path.join(getsitepackages()[1],'scipy/sparse/sparsetools/_coo.pyd'),'_coo.pyd'),
                                        (os.path.join(getsitepackages()[1],'scipy/sparse/sparsetools/_dia.pyd'),'_dia.pyd'),
                                        (os.path.join(getsitepackages()[1],'scipy/sparse/sparsetools/_bsr.pyd'),'_bsr.pyd'),
                                        (os.path.join(getsitepackages()[1],'scipy/sparse/sparsetools/_csgraph.pyd'),'_csgraph.pyd'),
                                        (os.path.join(getsitepackages()[1],'numpy/core/libifcoremd.dll'),'libifcoremd.dll'),
                                        (os.path.join(getsitepackages()[1],'numpy/core/libifportmd.dll'),'libifportmd.dll'),
                                        (os.path.join(getsitepackages()[1],'numpy/core/libiompstubs5md.dll'),'libiompstubs5md.dll'),
                                        (os.path.join(getsitepackages()[1],'numpy/core/libmmd.dll'),'libmmd.dll'),
                                        (os.path.join(getsitepackages()[1],'numpy/core/svml_dispmd.dll'),'svml_dispmd.dll'),
                                        (os.path.join(getsitepackages()[1],'numpy/core/tbb.dll'),'tbb.dll')],
                    "includes": [
                                  "numpy.lib.format",
                                  "numpy.linalg",
                                  "numpy.linalg._umath_linalg",
                                  "numpy.linalg.lapack_lite",
                                  "scipy.io.matlab.streams",
                                  "scipy.integrate",
                                  "scipy.integrate.vode",
                                  "scipy.sparse.linalg.dsolve.umfpack",
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
                                  "acousticsim"]}

msi_data = {"Shortcut": shortcut_table}

bdist_msi_options = {
        'upgrade_code':'{9f3fd2c0-db11-4d9b-8124-2e91e6cfd19d}',
        'add_to_path': False,
        'initial_target_dir': r'[ProgramFiles64Folder]\%s\%s' % (group_name, exe_name),
        'data':msi_data}

base = None
#if sys.platform == "win32":
#    base = "Win32GUI"

setup(name='Exemplar Network Explorer',
      version='0.15',
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
          'build_exe': build_exe_options}
      )
