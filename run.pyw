import os
import sys
from PySide2.QtWidgets import QApplication
# from PySide2.QtCore import Qt
from namuplant import main, storage

if __name__ == '__main__':
    os.chdir(os.path.join(os.getcwd(), 'namuplant'))
    storage.new_setting()
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    # app.setStyle('fusion')
    win = main.MainWindow()
    win.show()
    sys.exit(app.exec_())