import sys
import os
 
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
 
try:
    import sysv_ipc
    SYSV_DISPONIBIL = True
except ImportError:
    SYSV_DISPONIBIL = False
 
# Constante pentru coada de mesaje
CHEIE_COADA = 0x48540001  
TIP_MESAJ   = 1

DIMENSIUNE_CHUNK = 1024
 

def converteste_in_html(continut: str) -> str:
    """
    Converteste continutul unui fisier text in HTML.
    Prima linie devine <h1>, liniile negoale urmatoare devin <p>.
    Liniile goale sunt ignorate.
    """
    linii = continut.splitlines()
    if not linii:
        return ""
 
    # Filtreaza liniile goale, pastrand ordinea
    linii_nevide = [l.strip() for l in linii if l.strip()]
    if not linii_nevide:
        return ""
 
    titlu = linii_nevide[0]
    paragrafe = linii_nevide[1:]
 
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"ro\">",
        "<head>",
        "    <meta charset=\"UTF-8\">",
        f"    <title>{titlu}</title>",
        "</head>",
        "<body>",
        f"    <h1>{titlu}</h1>",
    ]
    for paragraf in paragrafe:
        html_parts.append(f"    <p>{paragraf}</p>")
 
    html_parts += ["</body>", "</html>"]
    return "\n".join(html_parts)
 

class FereastaPrincipala(QWidget):

 
    def __init__(self) -> None:
        super().__init__()
        self.html_generat: str = ""
        self._construieste_interfata()
        self.setWindowTitle("Convertor Text -> HTML")
        self.resize(700, 520)
 

    def _construieste_interfata(self) -> None:
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(10)
        layout_principal.setContentsMargins(16, 16, 16, 16)
 

        layout_cale = QHBoxLayout()
 
        self.entry_cale = QLineEdit()
        self.entry_cale.setPlaceholderText("/path/to/a/text/file")
        self.entry_cale.setFont(QFont("Courier New", 10))
 
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.setFixedWidth(90)
        self.btn_browse.clicked.connect(self._la_browse)
 
        layout_cale.addWidget(self.entry_cale)
        layout_cale.addWidget(self.btn_browse)
 
       
        self.text_rezultat = QTextEdit()
        self.text_rezultat.setPlaceholderText("HTML result")
        self.text_rezultat.setFont(QFont("Courier New", 10))
        self.text_rezultat.setReadOnly(True)
#butoane
        layout_butoane = QVBoxLayout()
        layout_butoane.setSpacing(6)
 
        self.btn_convert = QPushButton("Convert to HTML")
        self.btn_convert.clicked.connect(self._la_convert)
 
        self.btn_send = QPushButton("Send to C program")
        self.btn_send.clicked.connect(self._la_send)
        self.btn_send.setEnabled(False)  
 
        layout_butoane.addStretch()
        layout_butoane.addWidget(self.btn_convert)
        layout_butoane.addWidget(self.btn_send)
 
     
        layout_centru = QHBoxLayout()
        layout_centru.addWidget(self.text_rezultat)
        layout_centru.addLayout(layout_butoane)
 
   
        layout_principal.addLayout(layout_cale)
        layout_principal.addLayout(layout_centru)
 
        self.setLayout(layout_principal)
 

 
    def _la_browse(self) -> None:
        cale, _ = QFileDialog.getOpenFileName(
            self,
            "Selecteaza un fisier text",
            os.path.expanduser("~"),
        )
        if cale:
            self.entry_cale.setText(cale)
 
    def _la_convert(self) -> None:
        cale = self.entry_cale.text().strip()
        if not cale:
            QMessageBox.warning(self, "Atentie", "Introduceticalea catre un fisier.")
            return
 
        if not os.path.isfile(cale):
            QMessageBox.critical(self, "Eroare", f"Fisierul nu exista:\n{cale}")
            return
 
        try:
            with open(cale, "r", encoding="utf-8") as f:
                continut = f.read()
        except OSError as ex:
            QMessageBox.critical(self, "Eroare la citire", str(ex))
            return
 
        self.html_generat = converteste_in_html(continut)
 
        if not self.html_generat:
            QMessageBox.warning(self, "Atentie", "Fisierul este gol")
            return
 
        self.text_rezultat.setPlainText(self.html_generat)
        self.btn_send.setEnabled(True)
 
    def _la_send(self) -> None:
        if not self.html_generat:
            QMessageBox.warning(self, "Atentie", "Nu exista HTML generat. Apasati 'Convert to HTML' mai intai.")
            return
 
        if not SYSV_DISPONIBIL:
            QMessageBox.critical(
                self,
                "Eroare",
                "Biblioteca sysv_ipc nu este disponibila.\n"
            )
            return
 
        try:
            coada = sysv_ipc.MessageQueue(CHEIE_COADA)
        except sysv_ipc.ExistentialError:
            QMessageBox.critical(
                self,
                "Eroare",
                "Coada de mesaje nu a fost gasita.\n"
            )
            return
 
        date = self.html_generat.encode("utf-8")
        try:
            for i in range(0, len(date), DIMENSIUNE_CHUNK):
                chunk = date[i:i + DIMENSIUNE_CHUNK]
                coada.send(chunk, type=TIP_MESAJ)
      
            coada.send(b"__END__", type=TIP_MESAJ)
        except Exception as ex:
            QMessageBox.critical(self, "Eroare la trimitere", str(ex))
            return
 
        QMessageBox.information(
            self,
            "Succes",

        )
 
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    fereastra = FereastaPrincipala()
    fereastra.show()
    sys.exit(app.exec_())