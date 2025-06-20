from PyQt6.QtWidgets import QFileDialog, QMessageBox, QMainWindow, QApplication
from PyQt6.QtCore import pyqtSlot, QStringListModel, Qt
from sys import argv
from PyQt6.QtGui import QPixmap, QImage
import os
import pymupdf
import shutil

from MainWindow import Ui_MainWindow

def convert_pixmap_to_qpixmap(pix):
    """Converts a PyMuPDF Pixmap to a PyQt QPixmap."""
    if pix.alpha:
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGBA8888)
    else:
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(image)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.list_model = QStringListModel()
        self.LoadedPDFs.setModel(self.list_model)

        self.LoadPDFs.clicked.connect(self.open_dialog)
        self.ClearPDFs.clicked.connect(self.clear_loaded_files)
        self.ConvertPDFs.clicked.connect(self.convert_to_jpg)
        self.Next.clicked.connect(lambda: self.update_image(1))
        self.Previous.clicked.connect(lambda: self.update_image(-1))
        self.ImageTitle.textEdited.connect(lambda: self.update_title(False))
        self.ImageTitle.returnPressed.connect(lambda: self.update_image(1))
        self.Save.clicked.connect(self.save)

        self.ImageIndex.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        #structure is {name: {'Location':'','JPG':[],'Titles':[]}
        # 
        #}
        self.loaded_files = {}
        self.Open_dir = "${HOME}"

    def update_loaded_files(self,name,location,size,JPG=[],Titles=[]):
        #Skip loading files that already exist
        if name in self.loaded_files:
            pass
        else:
            self.loaded_files.update({name:{'Location':location,'Size':size,'JPG':JPG.copy(),'Titles':Titles.copy()}})
        
    @pyqtSlot()
    def open_dialog(self):
        fname = QFileDialog.getOpenFileNames(
            self,
            "Open File",
            self.Open_dir,
            "PDF Files (*.pdf)",
        )
        self.loaded_files = {}
        self.clear_loaded_files()
        for loc in fname[0]:
            name = loc.split(os.sep)[-1]
            if '(' not in loc and ')' not in loc:
                self.DisplayError('PDF load error',f'Error: {loc} missing (size) in title')
                return
            size = name.split('(')[1].split(')')[0].replace(' ','')
            #Remove 'in'
            size = size.replace('i','').replace('n','')
            if '16x20' in size:
                size = '16x20_8x10_4x5'
            self.update_loaded_files(name,loc,size)

            #Update Open_dir
            self.Open_dir = loc[:len(loc)-len(fname[0])]

        self.update_loaded_files_view()



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
        for name in self.loaded_files:
            if len(self.loaded_files[name]['JPG']) == 0:
                loc = self.loaded_files[name]['Location']
                for page in pymupdf.open(loc):
                    self.loaded_files[name]['JPG'].append(page.get_pixmap(dpi=300))
                pages = len(self.loaded_files[name]['JPG'])
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
            self.Image.setPixmap(QPixmap())
            self.ImageIndex.setText(f'0/0')
            self.update_title(img_changed=True)
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
            new_indx = new_indx % num_images

        tmp = self.loaded_files[first_key]['JPG'][new_indx]
        self.loaded_files['cur_img'] = new_indx

        #imagetmp = ImageQt.ImageQt(tmp)
        #pixmap = QPixmap.fromImage(tmp)
        pixmap = convert_pixmap_to_qpixmap(tmp)
        self.Image.setPixmap(pixmap.scaled(self.Image.width(),self.Image.height(),Qt.AspectRatioMode.KeepAspectRatio))
        self.Image.setMask(pixmap.mask());
        self.Image.show();

        self.ImageIndex.setText(f'{new_indx+1}/{num_images}')
        self.update_title(img_changed=True)

    def update_title(self,img_changed=False):
        #check that loaded_files is not empty
        if len(self.loaded_files.keys()) == 0:          
            self.ImageTitle.setText('')
            return
        first_key = list(self.loaded_files.keys())[0]
        if len(self.loaded_files[first_key]['JPG']) == 0:
            self.DisplayError('Title Error','Error: No files converted')
            return
        cur_img = self.loaded_files['cur_img']

        if img_changed:
            self.ImageTitle.setText(self.loaded_files[first_key]['Titles'][cur_img])
        else:
            self.loaded_files[first_key]['Titles'][cur_img] = self.ImageTitle.text()
        title = self.ImageTitle.text()

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
        save_path = QFileDialog.getExistingDirectory(
                parent=self,
                caption='Select directory',
                directory='${HOME}'
                )

        for indx, dir_title in enumerate(Titles):
            save_loc = save_path + os.sep + dir_title
            os.makedirs(save_loc, exist_ok=True)
            os.makedirs(save_loc+ os.sep + 'Listing Photos', exist_ok=True)
            for name in self.loaded_files:
                if 'cur_img' not in name:
                    file_title = self.loaded_files[name]['Titles'][indx]
                    self.loaded_files[name]['JPG'][indx].save(f'{save_loc}{os.sep}{file_title}.jpg','JPEG')

        #If jpgs saved lets move the PDFs as well
        for name in self.loaded_files:
            if 'cur_img' not in name:
                src = self.loaded_files[name]['Location']
                shutil.move(src,save_path+'/'+name)
        self.clear_loaded_files()
        self.update_image()

    def DisplayError(self,title,message):
        dlg = QMessageBox(self)
        dlg.setWindowTitle(title)
        dlg.setText(message)
        button = dlg.exec()

app = QApplication(argv)

window = MainWindow()
window.show()
app.exec()
