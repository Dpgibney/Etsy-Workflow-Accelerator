from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog, QLineEdit, QMessageBox
from PyQt6.QtCore import pyqtSlot, QStringListModel, Qt
import sys
from pdf2image import convert_from_path
from PIL import ImageQt
from PyQt6.QtGui import QPixmap
import os

from MainWindow import Ui_MainWindow

#So poppler is found on MacOS install
os.environ["PATH"]+=os.pathsep+os.path.join('_internal/poppler','bin')


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
        self.ImageTitle.returnPressed.connect(lambda: self.update_image(1))

        self.Save.clicked.connect(self.save)

        #structure is {name: {'Location':'','JPG':[],'Titles':[]}
        # 
        #}
        self.loaded_files = {}

    def update_loaded_files(self,name,location,size,JPG=[],Titles=[]):
        if name in self.loaded_files:
            pass
        else:
            self.loaded_files.update({name:{'Location':location,'Size':size,'JPG':JPG.copy(),'Titles':Titles.copy()}})

        
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
            name = loc.split(os.sep)[-1]
            if '(' not in loc and ')' not in loc:
                self.DisplayError('PDF load error',f'Error: {loc} missing (size) in title')
                return
            size = loc.split('(')[1].split(')')[0].replace(' ','')
            if '16x20' in size:
                size = '16x20_8x10_4x5'
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
        if len(self.loaded_files.keys()) == 0:
            self.DisplayError('Convert Error','No PDFs loaded')
            return
        pages = 0
        for name in self.loaded_files:
            if len(self.loaded_files[name]['JPG']) == 0:
                loc = self.loaded_files[name]['Location']
                self.loaded_files[name]['JPG'] = convert_from_path(loc,dpi=300,poppler_path=f'./_internal/poppler/bin')
                pages = len(self.loaded_files[name]['JPG'])
                print("Pages:",pages)
                for _ in range(pages):
                    self.loaded_files[name]['Titles'].append('')

        #Check that all PDFs had the same number of pages
        for name in self.loaded_files:
            if len(self.loaded_files[name]['JPG']) != pages:
                self.DisplayError('Convert Error','One of the PDFs loaded had a different number of pages. Try again')
                self.clear_loaded_files()
                self.loaded_files = {}
                return

        self.update_image()

    def update_image(self,move=0):
        #check that loaded_files is not empty
        if len(self.loaded_files.keys()) == 0:          
            return

        #Move = 0 denotes set to the first image (only use the first size for previewing images)
        first_key = list(self.loaded_files.keys())[0]
        num_images = len(self.loaded_files[first_key]['JPG'])

        if num_images == 0:
            return

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
        self.Image.setPixmap(pixmap.scaled(self.Image.width(),self.Image.height(),Qt.AspectRatioMode.KeepAspectRatio))
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

    def save(self):
        for name in self.loaded_files:
            print(self.loaded_files[name])
        #Check that the files all have titles
        if len(self.loaded_files.keys()) == 0:
            self.DisplayError('Save Error','Error: No files loaded')
            return

        first_key = list(self.loaded_files.keys())[0]
        if len(self.loaded_files[first_key]['JPG']) == 0:
            self.DisplayError('Save Error','Error: No files converted')
            return

        #Check that each JPG has a title
        for indx, title in enumerate(self.loaded_files[first_key]['Titles']):
            if title == '':
                self.DisplayError('Save Error',f'Error: Image {indx+1} is missing a title')
                return
        Titles = self.loaded_files[first_key]['Titles'].copy()
        for name in self.loaded_files:
            if 'cur_img' not in name:
                for indx in range(len(self.loaded_files[name]['Titles'])):
                    self.loaded_files[name]['Titles'][indx] = Titles[indx]+'_'+self.loaded_files[name]['Size']
                    print(self.loaded_files[name]['Titles'])

        save_path = QFileDialog.getExistingDirectory(
                parent=self,
                caption='Select directory',
                directory='${HOME}'
                )

        for indx, dir_title in enumerate(Titles):
            save_loc = save_path + os.sep + dir_title
            os.makedirs(save_loc, exist_ok=True)
            for name in self.loaded_files:
                if 'cur_img' not in name:
                    file_title = self.loaded_files[name]['Titles'][indx]
                    self.loaded_files[name]['JPG'][indx].save(f'{save_loc}{os.sep}{file_title}.jpg','JPEG')
                

    def DisplayError(self,title,message):
        dlg = QMessageBox(self)
        dlg.setWindowTitle(title)
        dlg.setText(message)
        button = dlg.exec()


        


app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()
app.exec()
