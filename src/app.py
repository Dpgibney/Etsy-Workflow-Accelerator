from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog, QLineEdit, QMessageBox
from PyQt6.QtCore import pyqtSlot, QStringListModel, Qt
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

        self.ImageIndex.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.Next.clicked.connect(lambda: self.update_image(1))
        self.Previous.clicked.connect(lambda: self.update_image(-1))

        self.ImageTitle.textEdited.connect(lambda: self.update_title(False))

        #structure is {name: {'Location':'','JPG':[],'Titles':[]}
        # 
        #}
        self.loaded_files = {}

    def update_loaded_files(self,name,location,size,JPG=[],Titles=[]):
        if name in self.loaded_files:
            pass
        else:
            self.loaded_files.update({name:{'Location':location,'Size':size,'JPG':JPG,'Titles':Titles}})

        
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
            if '(' not in loc and ')' not in loc:
                dlg = QMessageBox(self)
                dlg.setWindowTitle('PDF load error')
                dlg.setText(f"Error: {loc} missing (size) in title")
                button = dlg.exec()
                return
            size = loc.split('(')[1].split(')')[0]
            self.update_loaded_files(name,loc,size)
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
        self.update_image()

    def update_image(self,move=0):
        #check that loaded_files is not empty
        if len(self.loaded_files.keys()) == 0:          
            return

        #Move = 0 denotes set to the first image (only use the first size for previewing images)
        first_key = list(self.loaded_files.keys())[0]
        num_images = len(self.loaded_files[first_key]['JPG'])

        #Ensure that the current image is in the dict
        if 'cur_img' in self.loaded_files:
            pass
        else:
            self.loaded_files.update({'cur_img':0})
        cur_img = self.loaded_files['cur_img']

        if move == 0:
            tmp = self.loaded_files[first_key]['JPG'][0]
            self.loaded_files['cur_img'] = move
            new_indx = 0
        else:
            new_indx = cur_img+move
            #Make sure its in bounds
            if new_indx < 0:
                new_indx = num_images - 1
            print("new_indx",new_indx)
            new_indx = new_indx % num_images
            print("new_indx % num_images",new_indx)

        tmp = self.loaded_files[first_key]['JPG'][new_indx]
        self.loaded_files['cur_img'] = new_indx

        imagetmp = ImageQt.ImageQt(tmp)
        pixmap = QPixmap.fromImage(imagetmp)
        self.Image.setPixmap(pixmap.scaled(self.Image.width(),self.Image.height()))
        self.Image.setMask(pixmap.mask());
        self.Image.show();

        self.ImageIndex.setText(f'{new_indx+1}/{num_images}')
        self.update_title(img_changed=True)

    def update_title(self,img_changed=False):
        #check that loaded_files is not empty
        if len(self.loaded_files.keys()) == 0:          
            return
        first_key = list(self.loaded_files.keys())[0]
        cur_img = self.loaded_files['cur_img']
        print(img_changed)

        if img_changed:
            self.ImageTitle.setText(self.loaded_files[first_key]['Titles'][cur_img])
        else:
            self.loaded_files[first_key]['Titles'][cur_img] = self.ImageTitle.text()
        title = self.ImageTitle.text()
        print(title)

        

        


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()
app.exec()
