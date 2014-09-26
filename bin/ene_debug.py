import os
import sys
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base)
from exnetexplorer.main import QApplication, MainWindow

if __name__ == '__main__':




    app = QApplication(sys.argv)

    main = MainWindow()
    main.show()

    #app.aboutToQuit.connect(main.cleanUp)

    sys.exit(app.exec_())

