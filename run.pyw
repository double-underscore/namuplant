import os
import sys
from PySide2.QtWidgets import QApplication
from namuplant import main, storage

if __name__ == '__main__':
    print()
    os.chdir(os.path.join(os.getcwd(), 'namuplant'))
    storage.new_setting()
    app = QApplication(sys.argv)
    # app.setStyle('fusion')
    win = main.MainWindow()
    win.show()
    sys.exit(app.exec_())