from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog, QLineEdit
from PyQt6.QtCore import pyqtSlot, QStringListModel
import sys
from pdf2image import convert_from_path
from PIL import ImageQt
from PyQt6.QtGui import QPixmap

from MainWindow import Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.LoadPDFs.clicked.connect(self.open_dialog)

        self.list_model = QStringListModel()
        self.LoadedPDFs.setModel(self.list_model)

        self.ClearPDFs.clicked.connect(self.clear_loaded_files)

        self.ConvertPDFs.clicked.connect(self.convert_to_jpg)

        #structure is {name: {'Location':'','JPG':[],'Titles':[]}
        # 
        #}
        self.loaded_files = {}

    def update_loaded_files(self,name,location,JPG=[],Titles=[]):
        if name in self.loaded_files:
            pass
        else:
            self.loaded_files.update({name:{'Location':location,'JPG':JPG,'Titles':Titles}})

        
    @pyqtSlot()
    def open_dialog(self):
        fname = QFileDialog.getOpenFileNames(
            self,
            "Open File",
            "${HOME}",
            "PDF Files (*.pdf)",
        )
        self.loaded_files = {}
        for loc in fname[0]:
            name = loc.split('/')[-1]
            self.update_loaded_files(name,loc)
        self.update_loaded_files_view()
        print(self.loaded_files)


    def update_loaded_files_view(self):
        for name in self.loaded_files:
            self.list_model.insertRows(self.list_model.rowCount(), 1)
            index = self.list_model.index(self.list_model.rowCount() - 1)
            self.list_model.setData(index, name)

    def clear_loaded_files(self):
        self.list_model.removeRows(0,self.list_model.rowCount())
        self.loaded_files = {}

    def convert_to_jpg(self):
        tmp = None
        for name in self.loaded_files:
            if len(self.loaded_files[name]['JPG']) == 0:
                loc = self.loaded_files[name]['Location']
                self.loaded_files[name]['JPG'] = convert_from_path(loc,dpi=300)
                tmp = convert_from_path(loc,dpi=300)[0]
                print(tmp)
                for _ in range(len(self.loaded_files[name]['JPG'])):
                    self.loaded_files[name]['Titles'].append('')
        print(tmp)
        imagetmp = ImageQt.ImageQt(tmp)
        pixmap = QPixmap.fromImage(imagetmp)
        self.Image.setPixmap(pixmap.scaled(self.Image.width(),self.Image.height()))
        self.Image.setMask(pixmap.mask());

        self.Image.show();
        

        


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()
app.exec()
