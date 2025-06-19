import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QProgressBar, QPushButton, 
                           QVBoxLayout, QMessageBox, QLineEdit, QComboBox, QLabel, 
                           QStyledItemDelegate, QGridLayout, QFileDialog, QInputDialog, QDialog,
                           QStackedWidget, QHBoxLayout)
from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtSignal, Qt, QThread, QPropertyAnimation, QPoint, QEasingCurve, QRect, QParallelAnimationGroup, QTimer
from PyQt6.QtGui import QValidator, QStandardItem, QTransform, QPixmap, QPainter, QPen, QColor
import os
import random
from decimal import Decimal, getcontext
import ast
from pathlib import Path
import getpass
import pyperclip
import pyzipper
import shutil

def get_application_path():
    return Path(os.environ.get("RUN_CADC_PATH", ""))

directory_path = get_application_path()
folder_path = directory_path / "list_CADC"

def check_folder_file():

    if not folder_path.is_dir():
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            pass
    return folder_path

class BaseEncodingClass:
    def generate_encoding_map(self):
        return {
            "00": "A", "01": "B", "02": "C", "03": "D", "04": "E",
            "05": "F", "06": "G", "07": "H", "08": "I", "09": "J",
            "10": "K", "11": "L", "12": "M", "13": "N", "14": "O",
            "15": "P", "16": "Q", "17": "R", "18": "S", "19": "T",
            "20": "U", "21": "V", "22": "W", "23": "X", "24": "Y",
            "25": "Z", "26": "AA", "27": "BB", "28": "CC", "29": "DD",
            "30": "EE", "31": "FF", "32": "GG", "33": "HH", "34": "II",
            "35": "JJ", "36": "KK", "37": "LL", "38": "MM", "39": "NN",
            "40": "OO", "41": "PP", "42": "QQ", "43": "RR", "44": "SS",
            "45": "TT", "46": "UU", "47": "VV", "48": "WW", "49": "XX",
            "50": "YY", "51": "ZZ", "52": "ab", "53": "bc", "54": "cd",
            "55": "de", "56": "ef", "57": "fg", "58": "gh", "59": "hi",
            "60": "ij", "61": "jk", "62": "kl", "63": "lm", "64": "mn",
            "65": "no", "66": "op", "67": "pq", "68": "qr", "69": "rs",
            "70": "st", "71": "tu", "72": "uv", "73": "vw", "74": "wx",
            "75": "xy", "76": "yz", "77": "12", "78": "23", "79": "34",
            "80": "45", "81": "56", "82": "67", "83": "78", "84": "89",
            "85": "90", "86": "@#", "87": "#$", "88": "$%", "89": "%^",
            "90": "^^", "91": "**", "92": "((", "93": "))", "94": "++",
            "95": "==", "96": "~~", "97": "!!", "98": "@@", "99": "##",
            ".": "{", ",": "}"
        }

    def encode_numbers(self, number_string):
        if len(number_string) % 2 != 0:
            number_string = '0' + number_string
            
        # Разбиваем на пары цифр
        pairs = [number_string[i:i+2] for i in range(0, len(number_string), 2)]
        
        # Кодируем каждую пару
        result = []
        for pair in pairs:
            if pair in self.encoding_map:
                result.append(self.encoding_map[pair])
            else:
                result.append('??')
        
        return ''.join(result)

    def decode_numbers(self, encoded_string):
        # Создаем обратную карту для двухсимвольных значений
        reverse_map = {v: k for k, v in self.encoding_map.items()}
        
        result = []
        i = 0
        while i < len(encoded_string):
            # Пробуем найти двухсимвольное значение
            if i + 2 <= len(encoded_string):
                chunk = encoded_string[i:i+2]
                if chunk in reverse_map:
                    result.append(reverse_map[chunk])
                    i += 2
                    continue
            
            # Пробуем найти односимвольное значение
            chunk = encoded_string[i]
            if chunk in reverse_map:
                result.append(reverse_map[chunk])
            i += 1
        
        # Объединяем результат
        decoded = ''.join(result)
        
        # Убираем ведущий ноль, если он был добавлен
        if decoded.startswith('0') and len(decoded) > 1:
            decoded = decoded[1:]
            
        return decoded

class CodingThread(QThread, BaseEncodingClass):
    status_button = pyqtSignal(str)
    status_signal_ok = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    public_key_signal = pyqtSignal(str)
    encoded_key_signal = pyqtSignal(str)

    def __init__(self, parent=None, directory_path=None, combo=None, label_ok=None, encode_numbers=None):
        QThread.__init__(self, parent)
        self.directory_path = directory_path
        self.combo = combo
        self.label_ok = label_ok
        self.encode_numbers = encode_numbers
        self.encoding_map = self.generate_encoding_map()

    def run(self):
        try:
            self.status_signal.emit("⌛ Идет генерация ключа, подождите.")
            file_path = folder_path
            file_name = self.combo.currentText()
            
            with open(file_path / file_name, 'r') as file:
                line = file.read()
            line = line.replace("'", '"')
            data_dict = ast.literal_eval(line)
            
            PK = str(data_dict.get('PK'))
            PK2 = str(data_dict.get('PK2'))
            prec = int(data_dict.get('prec'))
            getcontext().prec = prec
            key_len = int(data_dict.get('key_len'))
            
            OK = self.label_ok.text() or str(round(random.uniform(15.01, 999.99999), 5))
            self.status_signal_ok.emit(str(OK))
            
            str_key = str(pow(Decimal(PK), Decimal(float(OK) + float(PK2))))
            integer_part, fractional_part = str_key.split(".")
            key = integer_part + fractional_part
            self.public_key = key[prec - key_len: prec]

            self.public_key_signal.emit(self.public_key)
            self.encoded_key_signal.emit(self.encode_numbers(self.public_key))
            self.status_signal.emit("✅ Ключ успешно сгенерирован!")
            self.status_button.emit("cls")

        except FileNotFoundError:
            self.status_signal.emit("🤬 Ошибка! Файл не найден!")
        except Exception as e:
            self.status_signal.emit(f"🤬 Ошибка! {str(e)}!")

class NoInputValidator(QValidator):
    def validate(self, input_text, pos):
        return QValidator.State.Invalid, input_text, pos

class CenteredItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        opt = option
        opt.displayAlignment = Qt.AlignmentFlag.AlignCenter
        super().paint(painter, opt, index)

class ArchiveEncryptionThread(QThread):
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(tuple)

    def __init__(self, file_params, encode_numbers):
        super().__init__()
        self.file_params = file_params
        self.encode_numbers = encode_numbers
        
    def run(self):
        try:
            self.status_signal.emit("⌛ Генерация ключа для архива...")
            
            with open(self.file_params, 'r') as file:
                line = file.read()
            line = line.replace("'", '"')
            data_dict = ast.literal_eval(line)
            
            PK = float(data_dict['PK'])
            PK2 = float(data_dict['PK2'])
            prec = int(data_dict['prec'])
            key_len = int(data_dict['key_len'])
            
            getcontext().prec = prec
            
            OK = str(round(random.uniform(1, 999.99999), 5))
            
            str_key = str(pow(Decimal(str(PK)), Decimal(str(float(OK) + PK2))))
            integer_part, fractional_part = str_key.split(".")
            key = integer_part + fractional_part
            self.public_key = key[prec - key_len: prec]
            
            encoded_key = self.encode_numbers(self.public_key)
            
            archive_password = self.public_key
            
            self.status_signal.emit("✅ Ключ успешно сгенерирован!")
            self.finished_signal.emit((encoded_key, archive_password, OK))
            
        except Exception as e:
            self.status_signal.emit(f"🤬 Ошибка при генерации ключа: {str(e)}")

class ArchiveManager(QWidget, BaseEncodingClass):
    def __init__(self, parent=None):
        QWidget.__init__(self)
        self.parent = parent
        self.selected_path = None
        self.archive_password = None
        self.encoding_map = self.generate_encoding_map() 
        self.setup_ui()
        
    def create_down_arrow(self):
        arrow = QPixmap(12, 12)
        arrow.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(arrow)
        pen = QPen(QColor('lightgrey'))
        pen.setWidth(2)
        painter.setPen(pen)
        
        painter.drawLine(2, 4, 6, 8)
        painter.drawLine(6, 8, 10, 4)
        painter.end()
        
        arrow.save('down_arrow.png')

    def setup_ui(self):
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заменяем обычный QLabel на ScrollingLabel
        self.path_label = ScrollingLabel("Выбрано: list")
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.path_label.setFixedSize(378, 25)
        self.path_label.setStyleSheet("color: gray;")

        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.line_edit = self.combo.lineEdit()
        self.combo.setItemDelegate(CenteredItemDelegate())
        self.combo.setValidator(NoInputValidator())
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.combo.setFixedSize(378, 25)
        self.update_file_list()
        
        self.select_folder_button = QPushButton("Выбор папки для архивации")
        self.select_archive_button = QPushButton("Выбор архива для расшифровки")
        self.action_button = QPushButton("Заархивировать")
        
        for button in [self.select_folder_button, self.select_archive_button, self.action_button]:
            button.setFixedSize(378, 25)
        
        self.all_widgets = [
            self.path_label,
            self.combo,
            self.select_folder_button,
            self.select_archive_button,
            self.action_button
        ]
        
        layout.addWidget(self.path_label)
        layout.addWidget(self.combo)
        layout.addWidget(self.select_folder_button)
        layout.addWidget(self.select_archive_button)
        layout.addWidget(self.action_button)
        
        layout.addStretch()
        
        self.select_folder_button.clicked.connect(self.select_folder)
        self.select_archive_button.clicked.connect(self.select_archive)
        self.action_button.clicked.connect(self.process_archive)
        
        self.action_button.hide()
        
        self.setLayout(layout)
        self.updateWindowSize()

        self.setStyleSheet("""
            QWidget {
                background-color: black;
            }
            QLabel, QPushButton, QComboBox {
                border: 1px solid lightgrey;
                color: lightgrey;
                background-color: black;
            }
            QPushButton:pressed {
                border: 1px solid black;
                background-color: white;
                color: black;           
            }
            QComboBox QAbstractItemView {
                border: 1px solid lightgrey;
                color: lightgrey;
                background-color: black;
                selection-background-color: #404040;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
        """)

    def showEvent(self, event):
        super().showEvent(event)
        self.updateWindowSize()

    def updateWindowSize(self):
        visible_widgets = sum(widget.isVisible() for widget in self.all_widgets)
        height = (20 + 
                 (visible_widgets * 25) + 
                 ((visible_widgets - 1) * 10) + 
                 20)
        self.setFixedSize(400, height)

    def update_file_list(self):
        self.combo.clear()
        try:
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    if filename.endswith('.txt'):
                        self.combo.addItem(filename)
        except Exception as e:
            pass
            
    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для архивации")
        if path:
            self.selected_path = path
            self.path_label.setText(f"Выбрано: {os.path.basename(path)}")
            self.action_button.setText("Заархивировать")
            self.action_button.show()
            self.updateWindowSize()

    def select_archive(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите архив для расшифровки",
            "",
            "Зашифрованные архивы (*.cp)"
        )
        if path:
            self.selected_path = path
            self.path_label.setText(f"Выбрано: {os.path.basename(path)}")
            self.action_button.setText("Разархивировать")
            self.action_button.show()
            self.updateWindowSize()

    def process_archive(self):
        if not self.selected_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку или архив!")
            return
            
        if not self.combo.currentText():
            QMessageBox.warning(self, "Ошибка", "Выберите файл параметров!")
            return

        try:
            params_file = os.path.join(folder_path, self.combo.currentText())
            mode = 'decrypt' if self.selected_path.endswith('.cp') else 'encrypt'
            
            self.action_button.setEnabled(False)
            self.select_folder_button.setEnabled(False)
            self.select_archive_button.setEnabled(False)
            
            self.archive_thread = ArchiveThread(
                parent=self,
                mode=mode,
                selected_path=self.selected_path,
                params_file=params_file,
                encoding_map=self.encoding_map
            )
            
            self.archive_thread.status_signal.connect(self.update_status)
            self.archive_thread.finished_signal.connect(self.handle_archive_result)
            self.archive_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при подготовке к {mode}: {str(e)}")
            self.action_button.setEnabled(True)
            self.select_folder_button.setEnabled(True)
            self.select_archive_button.setEnabled(True)

    def handle_archive_result(self, success, message):
        try:
            self.action_button.setEnabled(True)
            self.select_folder_button.setEnabled(True)
            self.select_archive_button.setEnabled(True)
            
            if success:
                QMessageBox.information(self, "Успех", message)
            else:
                QMessageBox.critical(self, "Ошибка", message)
        except Exception as e:
            pass

    def update_status(self, message):
        try:
            if isinstance(self, FileViewer):
                self.label_status.setText(message)
            else:
                self.path_label.setText(message)
        except Exception as e:
            pass

    def show_archive_manager(self):
        self.archive_manager = ArchiveManager(self)
        self.archive_manager.show()
        self.hide()

    @staticmethod
    def get_stylesheet():
        return """
            QLabel, QPushButton, QWidget {
                border: 1px solid lightgrey;
                color: lightgrey;
                background-color: black;
            }         
            QPushButton:pressed {
                border: 1px solid black;
                background-color: white;
                color: black;           
            }
        """

    def setup_connections(self):
        try:
            self.all_clear_button.clicked.connect(self.clear_all)
            self.generator_button.clicked.connect(self.generate)
            self.label_ok.textChanged.connect(lambda: self.change_button("gnt"))
            
            # Правильно привязываем функции копирования к соответствующим полям
            self.copy_buttons[0].clicked.connect(lambda: self.copy_text(self.label_ok, "Публичный ключ"))
            self.copy_buttons[1].clicked.connect(lambda: self.copy_text(self.label_okey, "Закрытый ключ"))
            self.copy_buttons[2].clicked.connect(lambda: self.copy_text(self.label_skey, "Закрытый ключ"))
        except Exception as e:
            pass

    def generate(self):
        try:
            self.thread = CodingThread(
                parent=self,
                directory_path=str(self.folder_path if hasattr(self, 'folder_path') else folder_path),
                combo=self.combo,
                label_ok=self.label_ok,
                encode_numbers=self.encode_numbers
            )
            self.thread.status_button.connect(self.change_button)
            self.thread.status_signal_ok.connect(self.update_status_ok)
            self.thread.status_signal.connect(self.update_status)
            self.thread.public_key_signal.connect(self.update_public_key)
            self.thread.encoded_key_signal.connect(self.update_encoded_key)
            self.thread.start()
        except Exception as e:
            self.update_status(f"🤬 Ошибка при генерации: {str(e)}")

    def change_button(self, button):
        try:
            self.generator_button.setVisible(button != "cls")
            self.all_clear_button.setVisible(button == "cls")
        except Exception as e:
            pass

    def update_status_ok(self, message):
        try:
            self.label_ok.setText(message)
        except Exception as e:
            pass

    def update_status(self, message):
        try:
            if isinstance(self, FileViewer):
                self.label_status.setText(message)
            else:
                self.path_label.setText(message)
        except Exception as e:
            pass

    def update_public_key(self, public_key):
        try:
            self.label_okey.setText(public_key)
            self.label_okey.setStyleSheet("color: lightgray;")
        except Exception as e:
            pass

    def update_encoded_key(self, encoded_key):
        try:
            self.label_skey.setText(encoded_key)
            self.label_skey.setStyleSheet("color: lightgray;")
        except Exception as e:
            pass

    def copy_text(self, label, placeholder_text):
        try:
            if isinstance(label, QLineEdit):
                text = label.text()
            else:
                text = label.text()
                
            if text == placeholder_text or not text or text in ["Закрытый ключ", "Публичный ключ"]:
                self.path_label.setText("🤬 Ошибка! Текстовое поле пустое!")
                return
                
            pyperclip.copy(text)
            self.path_label.setText(f"✅ Скопировано: {text[:10]}...")
        except Exception as e:
            self.path_label.setText("🤬 Ошибка при копировании!")

    def clear_all(self):
        try:
            self.label_ok.clear()
            for label in [self.label_okey, self.label_skey]:
                label.setText("Закрытый ключ")
                label.setStyleSheet("color: gray;")
            self.change_button("gnt")
        except Exception as e:
            pass

    def create_file(self):
        if self.parent:
            self.parent.handle_left_button()
            
    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для архивации")
        if path:
            self.selected_path = path
            self.path_label.setText(f"Выбрано: {os.path.basename(path)}")
            self.action_button.setText("Заархивировать")
            self.action_button.show()
            self.updateWindowSize()

    def generate_encoding_map(self):
        return {
            "00": "A", "01": "B", "02": "C", "03": "D", "04": "E",
            "05": "F", "06": "G", "07": "H", "08": "I", "09": "J",
            "10": "K", "11": "L", "12": "M", "13": "N", "14": "O",
            "15": "P", "16": "Q", "17": "R", "18": "S", "19": "T",
            "20": "U", "21": "V", "22": "W", "23": "X", "24": "Y",
            "25": "Z", "26": "AA", "27": "BB", "28": "CC", "29": "DD",
            "30": "EE", "31": "FF", "32": "GG", "33": "HH", "34": "II",
            "35": "JJ", "36": "KK", "37": "LL", "38": "MM", "39": "NN",
            "40": "OO", "41": "PP", "42": "QQ", "43": "RR", "44": "SS",
            "45": "TT", "46": "UU", "47": "VV", "48": "WW", "49": "XX",
            "50": "YY", "51": "ZZ", "52": "ab", "53": "bc", "54": "cd",
            "55": "de", "56": "ef", "57": "fg", "58": "gh", "59": "hi",
            "60": "ij", "61": "jk", "62": "kl", "63": "lm", "64": "mn",
            "65": "no", "66": "op", "67": "pq", "68": "qr", "69": "rs",
            "70": "st", "71": "tu", "72": "uv", "73": "vw", "74": "wx",
            "75": "xy", "76": "yz", "77": "12", "78": "23", "79": "34",
            "80": "45", "81": "56", "82": "67", "83": "78", "84": "89",
            "85": "90", "86": "@#", "87": "#$", "88": "$%", "89": "%^",
            "90": "^^", "91": "**", "92": "((", "93": "))", "94": "++",
            "95": "==", "96": "~~", "97": "!!", "98": "@@", "99": "##",
            ".": "{", ",": "}"
        }

    def show_success_dialog(self, public_key, OK):
        dialog = QDialog(self)
        dialog.setWindowTitle("Успех")
        dialog.setFixedSize(400, 100)
        
        layout = QVBoxLayout()
        
        message = QLabel(f"OK={OK}")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        dialog.setLayout(layout)
        dialog.setStyleSheet("""
            QDialog, QLabel {
                background-color: black;
                color: lightgrey;
                border: 1px solid lightgrey;
            }
        """)
        
        dialog.exec()
            
class FileCreator(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        # Создаем основной контейнер с фиксированным размером
        self.setFixedSize(400, 200)
        
        # Создаем layout с отступами
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Создание полей ввода
        parameters = ["Название файла", "ключ 1", "ключ 2", "сложность генерации", "длина ключа"]
        self.line_edits = []
        for param in parameters:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(param)
            line_edit.setFixedSize(378, 25)
            self.line_edits.append(line_edit)
            layout.addWidget(line_edit)
        
        # Создание кнопок
        self.create_button = QPushButton("Создать ключ")
        self.gen_random_param_button = QPushButton("Рандомная генерация ключа")
        
        for button in [self.create_button, self.gen_random_param_button]:
            button.setFixedSize(378, 25)
            layout.addWidget(button)
        
        self.create_button.clicked.connect(self.create_file)
        self.gen_random_param_button.clicked.connect(self.gen_random_param)

        layout.addStretch()
        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: black;
            }
            QLineEdit, QPushButton {
                border: 1px solid lightgrey;
                color: lightgrey;
                background-color: black;
            }
            QPushButton:pressed {
                border: 1px solid black;
                background-color: white;
                color: black;           
            }
        """)

    def gen_random_param(self):
        self.line_edits[1].setText(str(round(random.uniform(999, 99999.99999), 5)))
        self.line_edits[2].setText(str(round(random.uniform(999, 99999.99999), 5)))
        self.line_edits[3].setText(str(random.randint(4000, 5000)))
        self.line_edits[4].setText(str(random.randint(30, 40)))
    
    @staticmethod
    def validate_input(value):
        return bool(value and value.replace(".", "").isdigit())
    
    def create_file(self):
        file_name = self.line_edits[0].text()
        if not file_name:
            QMessageBox.warning(self, "🤬 Ошибка", "Введите название файла.")
            return

        try:
            key_len = int(self.line_edits[4].text())
            prec = int(self.line_edits[3].text())
            if key_len >= 100 or key_len >= prec:
                QMessageBox.warning(self, "🤬 Ошибка", "Большая длина ключа (:99 & !> Сложности генерации)")
                return
        except ValueError:
            QMessageBox.warning(self, "🤬 Ошибка", "Сложность генерации и Длина ключа должны быть целыми числами!")
            return

        params = {}
        for i, param in enumerate(["PK", "PK2", "prec", "key_len"]):
            value = self.line_edits[i+1].text()
            if not self.validate_input(value):
                QMessageBox.warning(self, "🤬 Ошибка", 
                                  f"Параметр '{param}' должен быть целым или десятичным числом.")
                return
            params[param] = value

        try:
            with open(folder_path / f"{file_name}.txt", "w") as file:
                file.write(str(params))
            QMessageBox.information(self, "👌 Успех", "Файл успешно создан!")
            for line_edit in self.line_edits:
                line_edit.clear()
            
            # Обновляем список файлов во всех окнах
            if isinstance(self.parent, MainWindow):
                self.parent.file_viewer.update_file_list()
                self.parent.archive_manager.update_file_list()
            elif isinstance(self.parent, FileViewer):
                self.parent.update_file_list()
                if hasattr(self.parent.parent, 'archive_manager'):
                    self.parent.parent.archive_manager.update_file_list()
            elif isinstance(self.parent, ArchiveManager):
                self.parent.update_file_list()
                if hasattr(self.parent.parent, 'file_viewer'):
                    self.parent.parent.file_viewer.update_file_list()
            
            # Возвращаемся на главную страницу
            if hasattr(self.parent, 'handle_left_button'):
                self.parent.handle_left_button()
            elif hasattr(self.parent, 'parent') and hasattr(self.parent.parent, 'handle_left_button'):
                self.parent.parent.handle_left_button()
                
        except Exception as e:
            QMessageBox.critical(self, "🤬 Ошибка", f"Не удалось создать файл: {e}")

class MainWindow(QWidget, BaseEncodingClass):
    def __init__(self):
        QWidget.__init__(self)
        self.setup_ui()
        self.animation_in_progress = False
        self.encoding_map = self.generate_encoding_map()
        
    def setup_ui(self):
        self.setWindowTitle("CADC")
        self.setFixedSize(450, 200)
        
        # Создаем главный горизонтальный layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Создаем левую кнопку
        self.left_button = QPushButton("С\nо\nз\nд\nа\nт\nь\n\nк\nл\nю\nч")
        self.left_button.setFixedSize(25, 200)
        self.left_button.clicked.connect(self.handle_left_button)
        
        # Создаем правую кнопку
        self.right_button = QPushButton("Д\nе\nй\nс\nт\nв\nи\nя")
        self.right_button.setFixedSize(25, 200)
        self.right_button.clicked.connect(self.handle_right_button)
        
        # Создаем центральный контейнер
        self.central_widget = QWidget()
        self.central_widget.setFixedSize(400, 200)
        central_layout = QVBoxLayout(self.central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        
        # Создаем QStackedWidget для страниц
        self.stack = QStackedWidget()
        self.stack.setFixedSize(400, 200)
        central_layout.addWidget(self.stack)
        
        # Создаем страницы
        self.file_viewer = FileViewer(folder_path)
        self.archive_manager = ArchiveManager(self)
        self.file_creator = FileCreator(self)
        
        # Устанавливаем фиксированные размеры для всех страниц
        for widget in [self.file_viewer, self.archive_manager, self.file_creator]:
            widget.setFixedSize(400, 200)
        
        # Добавляем страницы в стек
        self.stack.addWidget(self.file_viewer)  # индекс 0
        self.stack.addWidget(self.archive_manager)  # индекс 1
        self.stack.addWidget(self.file_creator)  # индекс 2
        
        # Добавляем все в главный layout
        main_layout.addWidget(self.left_button)
        main_layout.addWidget(self.central_widget)
        main_layout.addWidget(self.right_button)
        
        self.setLayout(main_layout)
        
        # Устанавливаем стили
        self.setStyleSheet("""
            QWidget {
                background-color: black;
            }
            QPushButton {
                color: lightgrey;
                border: 1px solid lightgrey;
                font-size: 10px;
            }
            QPushButton:pressed {
                background-color: white;
                color: black;
            }
            QStackedWidget {
                background-color: black;
            }
        """)
    
    def slide_to_page(self, index, direction):
        if self.animation_in_progress:
            return
            
        if self.stack.currentIndex() == index:
            return
            
        self.animation_in_progress = True
        
        # Текущий и следующий виджеты
        current = self.stack.currentWidget()
        next_widget = self.stack.widget(index)
        
        # Подготавливаем следующий виджет
        # direction: -1 для движения влево, 1 для движения вправо
        next_widget.setGeometry(direction * 400, 0, 400, 200)
        next_widget.show()
        next_widget.raise_()
        
        # Создаем анимации
        current_anim = QPropertyAnimation(current, b"geometry")
        current_anim.setDuration(300)
        current_anim.setStartValue(current.geometry())
        current_anim.setEndValue(QRect(-direction * 400, 0, 400, 200))
        current_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        next_anim = QPropertyAnimation(next_widget, b"geometry")
        next_anim.setDuration(300)
        next_anim.setStartValue(next_widget.geometry())
        next_anim.setEndValue(QRect(0, 0, 400, 200))
        next_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Группируем анимации
        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(current_anim)
        self.anim_group.addAnimation(next_anim)
        self.anim_group.finished.connect(lambda: self.animation_finished(index))
        
        # Запускаем анимацию
        self.anim_group.start()
    
    def animation_finished(self, index):
        # Устанавливаем текущий индекс после завершения анимации
        self.stack.setCurrentIndex(index)
        # Сбрасываем геометрию всех виджетов
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            widget.setGeometry(0, 0, 400, 200)
        self.animation_in_progress = False
        
        # Обновляем состояние кнопок
        self.update_button_states()
    
    def sequential_animation(self, target_index, direction):
        if self.animation_in_progress:
            return
            
        current_index = self.stack.currentIndex()
        if current_index == target_index:
            return
            
        # Запускаем первую анимацию к промежуточной странице
        intermediate_index = 0  # Главная страница как промежуточная
        
        # Если мы уже на главной, идем сразу к цели
        if current_index == 0:
            self.slide_to_page(target_index, direction)
        else:
            # Сначала к главной странице
            self.slide_to_page(intermediate_index, direction)
            
            # После завершения первой анимации, запускаем следующую
            def start_second_animation():
                # Отключаем старый обработчик
                try:
                    self.anim_group.finished.disconnect()
                except:
                    pass
                # Запускаем вторую анимацию в том же направлении
                self.slide_to_page(target_index, direction)
            
            self.anim_group.finished.connect(start_second_animation)
    
    def update_button_states(self):
        current_index = self.stack.currentIndex()
        
        # Обновляем текст и доступность кнопок
        if current_index == 0:  # Главная страница
            self.left_button.setText("С\nо\nз\nд\nа\nт\nь\n\nк\nл\nю\nч")
            self.right_button.setText("Д\nе\nй\nс\nт\nв\nи\nя")
            self.left_button.setEnabled(True)
            self.right_button.setEnabled(True)
        elif current_index == 1:  # Страница действий
            self.right_button.setText("Н\nа\nз\nа\nд")
            self.left_button.setText("С\nо\nз\nд\nа\nт\nь\n\nк\nл\nю\nч")
            self.left_button.setEnabled(True)
        elif current_index == 2:  # Страница создания ключа
            self.left_button.setText("Н\nа\nз\nа\nд")
            self.right_button.setText("Д\nе\nй\nс\nт\nв\nи\nя")
            self.right_button.setEnabled(True)
    
    def handle_left_button(self):
        current_index = self.stack.currentIndex()
        if current_index == 0:  # Если на главной странице
            self.slide_to_page(2, -1)  # Влево к созданию ключа
        elif current_index == 1:  # Если на странице действий
            self.sequential_animation(2, -1)  # Влево через главную к созданию ключа
        else:  # Если на странице создания ключа
            self.slide_to_page(0, 1)  # Вправо к главной
    
    def handle_right_button(self):
        current_index = self.stack.currentIndex()
        if current_index == 0:  # Если на главной странице
            self.slide_to_page(1, 1)  # Вправо к действиям
        elif current_index == 2:  # Если на странице создания ключа
            self.sequential_animation(1, 1)  # Вправо через главную к действиям
        else:  # Если на странице действий
            self.slide_to_page(0, -1)  # Влево к главной

    def generate_encoding_map(self):
        return {
            "00": "A", "01": "B", "02": "C", "03": "D", "04": "E",
            "05": "F", "06": "G", "07": "H", "08": "I", "09": "J",
            "10": "K", "11": "L", "12": "M", "13": "N", "14": "O",
            "15": "P", "16": "Q", "17": "R", "18": "S", "19": "T",
            "20": "U", "21": "V", "22": "W", "23": "X", "24": "Y",
            "25": "Z", "26": "AA", "27": "BB", "28": "CC", "29": "DD",
            "30": "EE", "31": "FF", "32": "GG", "33": "HH", "34": "II",
            "35": "JJ", "36": "KK", "37": "LL", "38": "MM", "39": "NN",
            "40": "OO", "41": "PP", "42": "QQ", "43": "RR", "44": "SS",
            "45": "TT", "46": "UU", "47": "VV", "48": "WW", "49": "XX",
            "50": "YY", "51": "ZZ", "52": "ab", "53": "bc", "54": "cd",
            "55": "de", "56": "ef", "57": "fg", "58": "gh", "59": "hi",
            "60": "ij", "61": "jk", "62": "kl", "63": "lm", "64": "mn",
            "65": "no", "66": "op", "67": "pq", "68": "qr", "69": "rs",
            "70": "st", "71": "tu", "72": "uv", "73": "vw", "74": "wx",
            "75": "xy", "76": "yz", "77": "12", "78": "23", "79": "34",
            "80": "45", "81": "56", "82": "67", "83": "78", "84": "89",
            "85": "90", "86": "@#", "87": "#$", "88": "$%", "89": "%^",
            "90": "^^", "91": "**", "92": "((", "93": "))", "94": "++",
            "95": "==", "96": "~~", "97": "!!", "98": "@@", "99": "##",
            ".": "{", ",": "}"
        }
        
    def encode_numbers(self, number_string):
        pairs = [number_string[i:i+2] for i in range(0, len(number_string), 2)]
        return ''.join(self.encoding_map.get(pair, '?') for pair in pairs)

class ScrollingLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_text)
        self.text_position = 0
        self.full_text = ""
        self.scroll_speed = 1
        self.space_padding = "          "  # Пробелы между повторами текста
        
    def setText(self, text):
        # Если текст не изменился, не перезапускаем анимацию
        if text == self.full_text:
            return
            
        self.full_text = text
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        
        # Если текст короче метки, просто показываем его
        if text_width <= self.width():
            super().setText(text)
            self.timer.stop()
            return
            
        # Подготавливаем текст для прокрутки
        self.scroll_text = text + self.space_padding
        
        # Запускаем или перезапускаем таймер
        if not self.timer.isActive():
            self.text_position = 0
            self.timer.start(50)  # Обновление каждые 50 мс
            
        self.update_text()
        
    def update_text(self):
        if not self.full_text:
            return
            
        # Вычисляем позицию для отображения
        text_length = len(self.scroll_text)
        start_pos = self.text_position % text_length
        
        # Формируем отображаемый текст
        display_text = self.scroll_text[start_pos:] + self.scroll_text[:start_pos]
        display_text = display_text * 3  # Утраиваем текст для заполнения всей ширины
        
        super().setText(display_text)
        self.text_position = (self.text_position + self.scroll_speed) % text_length

class FileViewer(QWidget, BaseEncodingClass):
    def __init__(self, folder_path):
        QWidget.__init__(self)
        self.folder_path = folder_path
        self.encoding_map = self.generate_encoding_map()
        self.setup_ui()
        self.update_file_list()
        
    def setup_ui(self):
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.progressBar = QProgressBar()
        
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.line_edit = self.combo.lineEdit()
        self.combo.setItemDelegate(CenteredItemDelegate())
        self.combo.setValidator(NoInputValidator())
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.combo.setFixedSize(378, 25)
        
        input_layout = QHBoxLayout()
        self.label_ok = QLineEdit()
        self.label_ok.setPlaceholderText("Публичный ключ")
        self.label_ok.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_ok.setFixedSize(262, 25)
        
        self.generator_button = QPushButton("Сгенерировать")
        self.all_clear_button = QPushButton("Очистить все")
        self.generator_button.setFixedSize(109, 25)
        self.all_clear_button.setFixedSize(109, 25)
        
        input_layout.addWidget(self.label_ok)
        input_layout.addWidget(self.generator_button)
        input_layout.addWidget(self.all_clear_button)
        self.all_clear_button.hide()
        
        # Заменяем обычный QLabel на ScrollingLabel
        self.label_status = ScrollingLabel("⏳ Ожидание!")
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status.setFixedSize(378, 25)
        
        self.label_okey = QLabel("Закрытый ключ")
        self.label_okey.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_okey.setStyleSheet("color: gray;")
        self.label_okey.setFixedSize(378, 25)
        
        self.label_skey = QLabel("Закрытый ключ")
        self.label_skey.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_skey.setStyleSheet("color: gray;")
        self.label_skey.setFixedSize(378, 25)
        
        self.copy_buttons = [QPushButton("📑") for _ in range(3)]
        for btn in self.copy_buttons:
            btn.setFixedSize(25, 25)
        
        layout.addWidget(self.label_status)
        layout.addWidget(self.combo)
        layout.addLayout(input_layout)
        
        for label, copy_btn in zip([self.label_okey, self.label_skey], self.copy_buttons[1:]):
            label_layout = QHBoxLayout()
            label_layout.addWidget(label)
            label_layout.addWidget(copy_btn)
            layout.addLayout(label_layout)
        
        self.setup_connections()
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: black;
            }
            QLabel, QPushButton, QComboBox, QLineEdit {
                border: 1px solid lightgrey;
                color: lightgrey;
                background-color: black;
            }
            QPushButton:pressed {
                border: 1px solid black;
                background-color: white;
                color: black;
            }
            QComboBox QAbstractItemView {
                border: 1px solid lightgrey;
                color: lightgrey;
                background-color: black;
                selection-background-color: #404040;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
        """)
        
    def setup_connections(self):
        try:
            self.all_clear_button.clicked.connect(self.clear_all)
            self.generator_button.clicked.connect(self.generate)
            self.label_ok.textChanged.connect(lambda: self.change_button("gnt"))
            
            # Правильно привязываем функции копирования к соответствующим полям
            self.copy_buttons[0].clicked.connect(lambda: self.copy_text(self.label_ok, "Публичный ключ"))
            self.copy_buttons[1].clicked.connect(lambda: self.copy_text(self.label_okey, "Закрытый ключ"))
            self.copy_buttons[2].clicked.connect(lambda: self.copy_text(self.label_skey, "Закрытый ключ"))
        except Exception as e:
            pass

    def get_stylesheet(self):
        return """
            QWidget {
                background-color: black;
            }
            QLabel, QPushButton, QComboBox, QLineEdit {
                border: 1px solid lightgrey;
                color: lightgrey;
                background-color: black;
            }
            QPushButton:pressed {
                border: 1px solid black;
                background-color: white;
                color: black;
            }
            QComboBox QAbstractItemView {
                border: 1px solid lightgrey;
                color: lightgrey;
                background-color: black;
                selection-background-color: #404040;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
        """

    def update_file_list(self):
        try:
            self.combo.clear()
            if os.path.exists(self.folder_path):
                for filename in os.listdir(self.folder_path):
                    if filename.endswith('.txt'):
                        self.combo.addItem(filename)
        except Exception as e:
            pass

    def create_file(self):
        self.window2 = FileCreator(self)
        self.window2.show()

    def clear_all(self):
        try:
            self.label_ok.clear()
            for label in [self.label_okey, self.label_skey]:
                label.setText("Закрытый ключ")
                label.setStyleSheet("color: gray;")
            self.change_button("gnt")
        except Exception as e:
            pass

    def change_button(self, button):
        try:
            self.generator_button.setVisible(button != "cls")
            self.all_clear_button.setVisible(button == "cls")
        except Exception as e:
            pass

    def copy_text(self, label, placeholder_text):
        try:
            if isinstance(label, QLineEdit):
                text = label.text()
            else:
                text = label.text()
                
            if text == placeholder_text or not text or text in ["Закрытый ключ", "Публичный ключ"]:
                self.label_status.setText("🤬 Ошибка! Текстовое поле пустое!")
                return
                
            pyperclip.copy(text)
            self.label_status.setText("✔️ Текстовое поле скопировано!")
        except Exception as e:
            self.label_status.setText("🤬 Ошибка при копировании!")

    def generate(self):
        try:
            self.thread = CodingThread(
                parent=self,
                directory_path=str(self.folder_path if hasattr(self, 'folder_path') else folder_path),
                combo=self.combo,
                label_ok=self.label_ok,
                encode_numbers=self.encode_numbers
            )
            self.thread.status_button.connect(self.change_button)
            self.thread.status_signal_ok.connect(self.update_status_ok)
            self.thread.status_signal.connect(self.update_status)
            self.thread.public_key_signal.connect(self.update_public_key)  
            self.thread.encoded_key_signal.connect(self.update_encoded_key)
            self.thread.start()
        except Exception as e:
            self.update_status(f"🤬 Ошибка при генерации: {str(e)}")

    def update_status_ok(self, message):
        try:
            self.label_ok.setText(message)
        except Exception as e:
            pass

    def update_status(self, message):
        try:
            if isinstance(self, FileViewer):
                self.label_status.setText(message)
            else:
                self.path_label.setText(message)
        except Exception as e:
            pass

    def update_public_key(self, public_key):
        try:
            self.label_okey.setText(public_key)
            self.label_okey.setStyleSheet("color: lightgray;")
        except Exception as e:
            pass

    def update_encoded_key(self, encoded_key):
        try:
            self.label_skey.setText(encoded_key)
            self.label_skey.setStyleSheet("color: lightgray;")
        except Exception as e:
            pass

class ArchiveThread(QThread, BaseEncodingClass):
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, parent=None, mode='encrypt', selected_path=None, params_file=None, encoding_map=None):
        QThread.__init__(self, parent)
        self.mode = mode
        self.selected_path = selected_path
        self.params_file = params_file
        self.parent = parent
        self.encoding_map = parent.encoding_map if parent else self.generate_encoding_map()
        self.public_key = None
        self.OK = None
        
    def run(self):
        try:
            if self.mode == 'encrypt':
                self.encrypt_archive()
            else:
                self.decrypt_archive()
        except Exception as e:
            self.finished_signal.emit(False, str(e))
            
    def encrypt_archive(self): 
        archive_path = None
        try:
            if not self.selected_path or not os.path.exists(self.selected_path):
                raise Exception("Выбранный путь не существует")

            self.status_signal.emit("⌛ Генерация ключа...")
            
            with open(self.params_file, 'r') as file:
                line = file.read()
                
            line = line.replace("'", '"')
            data_dict = ast.literal_eval(line)
            
            self.PK = str(data_dict.get('PK'))
            self.PK2 = str(data_dict.get('PK2'))
            self.prec = int(data_dict.get('prec'))
            getcontext().prec = self.prec
            self.key_len = int(data_dict.get('key_len'))
            
            # Генерация OK
            self.OK = round(random.uniform(15.01, 999.99999), 5)
            ok_str = f"{self.OK:.5f}"  # Фиксируем формат сразу при создании
            self.status_signal.emit(f"Сгенерированный OK: {ok_str}")
            
            # Генерация ключа
            ok_decimal = Decimal(ok_str)
            pk2_decimal = Decimal(str(float(self.PK2)))
            str_key = str(pow(Decimal(self.PK), ok_decimal + pk2_decimal))
            integer_part, fractional_part = str_key.split(".")
            key = integer_part + fractional_part
            self.public_key = key[self.prec - self.key_len : self.prec]

            self.status_signal.emit("⌛ Подготовка архива...")
            
            # Форматируем и шифруем OK для названия архива
            ok_str_for_encoding = ok_str.replace(".", "")
            encoded_ok = self.encode_numbers(ok_str_for_encoding)
            
            # Используем ту же директорию, что и исходный файл/папка
            source_dir = Path(self.selected_path)
            if source_dir.is_file():
                target_dir = source_dir.parent
            else:
                target_dir = source_dir.parent
                
            archive_path = target_dir / f"{encoded_ok}.cp"
            
            if os.path.exists(archive_path):
                os.remove(archive_path)
                
            self.status_signal.emit("⌛ Создание архива...")
            
            # Создаем защищенный архив
            with pyzipper.AESZipFile(archive_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zipf:
                zipf.setpassword(str(self.public_key).encode())
                zipf.setencryption(pyzipper.WZ_AES, nbits=256)
                
                if os.path.isfile(self.selected_path):
                    self.status_signal.emit(f"⌛ Добавление файла {os.path.basename(self.selected_path)}...")
                    arcname = os.path.basename(self.selected_path)
                    zipf.write(self.selected_path, arcname)
                else:
                    # Подсчитываем общее количество файлов
                    total_files = sum([len(files) for _, _, files in os.walk(source_dir)])
                    processed_files = 0
                    
                    # Получаем имя главной папки
                    base_folder_name = source_dir.name
                    
                    for root, dirs, files in os.walk(source_dir):
                        # Создаем относительный путь, сохраняя структуру папок
                        rel_path = os.path.relpath(root, source_dir.parent)
                        
                        # Добавляем пустые директории
                        if not files and not dirs:
                            empty_dir_path = os.path.join(rel_path, "")
                            zipf.writestr(empty_dir_path, "")
                        
                        for file in files:
                            processed_files += 1
                            self.status_signal.emit(f"⌛ Архивация: {processed_files}/{total_files} файлов...")
                            
                            file_path = Path(root) / file
                            try:
                                arcname = os.path.join(rel_path, file)
                                zipf.write(file_path, arcname)
                            except Exception as e:
                                self.status_signal.emit(f"⚠️ Пропуск файла {file}: {str(e)}")
                                continue
            
            self.status_signal.emit(f"✅ Архив успешно создан: {encoded_ok}.cp")
            self.finished_signal.emit(True, f"✅ Архив создан: {encoded_ok}.cp")
            
        except Exception as e:
            if archive_path and os.path.exists(archive_path):
                try:
                    os.remove(archive_path)
                except:
                    pass
            self.finished_signal.emit(False, str(e))
            
    def decrypt_archive(self):
        try:
            if not self.selected_path or not os.path.exists(self.selected_path):
                raise Exception("Выбранный архив не существует")
                
            if not self.selected_path.endswith('.cp'):
                raise Exception("Неверный формат архива")
                
            # Получаем зашифрованный OK из имени файла
            encoded_ok = os.path.basename(self.selected_path).replace('.cp', '')
            
            self.status_signal.emit("⌛ Расшифровка архива...")
            
            # Расшифровываем OK
            decoded_numbers = self.decode_numbers(encoded_ok)
            if not decoded_numbers:
                raise Exception("Не удалось расшифровать OK из имени файла")
            
            # Преобразуем расшифрованное число обратно в float с фиксированной точностью
            try:
                decoded_str = str(decoded_numbers)
                if len(decoded_str) < 6:
                    raise ValueError("Некорректная длина расшифрованного значения")
                    
                # Восстанавливаем OK с точным форматированием
                ok_str = f"{decoded_str[:-5]}.{decoded_str[-5:]}"
                self.OK = float(ok_str)
            except ValueError as e:
                raise Exception(f"Некорректный формат зашифрованного OK: {str(e)}")
                
            # Читаем параметры и генерируем ключ
            with open(self.params_file, 'r') as file:
                line = file.read()
            line = line.replace("'", '"')
            data_dict = ast.literal_eval(line)
            
            self.PK = str(data_dict.get('PK'))
            self.PK2 = str(data_dict.get('PK2'))
            self.prec = int(data_dict.get('prec'))
            getcontext().prec = self.prec
            self.key_len = int(data_dict.get('key_len'))
            
            # Используем тот же подход с Decimal как при шифровании
            ok_decimal = Decimal(ok_str)
            pk2_decimal = Decimal(str(float(self.PK2)))
            str_key = str(pow(Decimal(self.PK), ok_decimal + pk2_decimal))
            integer_part, fractional_part = str_key.split(".")
            key = integer_part + fractional_part
            self.public_key = key[self.prec - self.key_len : self.prec]
            
            # Используем директорию архива для распаковки
            archive_dir = Path(self.selected_path).parent
            
            try:
                with pyzipper.AESZipFile(self.selected_path, 'r') as zipf:
                    try:
                        zipf.setpassword(str(self.public_key).encode())
                        
                        # Проверяем возможность чтения файлов и считаем их количество
                        file_list = zipf.namelist()
                        if not file_list:
                            raise Exception("Архив пуст")
                            
                        # Проверяем содержимое архива
                        for item in file_list:
                            try:
                                zipf.read(item)
                            except:
                                raise Exception("Неверный ключ")
                        
                        self.status_signal.emit("⌛ Распаковка архива...")                    
                        # Определяем путь для распаковки
                        if len(file_list) > 1:
                            # Создаем папку с именем архива (без .cp)
                            archive_name = os.path.splitext(os.path.basename(self.selected_path))[0]
                            extract_path = archive_dir / f"CADC_{archive_name}"
                            
                            # Если папка существует, добавляем номер
                            counter = 1
                            original_path = extract_path
                            while os.path.exists(extract_path):
                                extract_path = f"{original_path}_{counter}"
                                counter += 1
                            
                            os.makedirs(extract_path)
                            self.status_signal.emit(f"⌛ Создана папка для распаковки: {os.path.basename(extract_path)}")
                        else:
                            extract_path = archive_dir
                        
                        # Распаковываем файлы
                        total_files = len(file_list)
                        for index, item in enumerate(file_list, 1):
                            self.status_signal.emit(f"⌛ Распаковка файлов: {index}/{total_files}")
                            zipf.extract(item, extract_path)
                                
                    except (pyzipper.BadZipFile, KeyError):
                        raise Exception("Неверный ключ или поврежденный архив")
                        
                success_message = "Архив успешно расшифрован и распакован"
                if len(file_list) > 1:
                    success_message += f" в папку {os.path.basename(extract_path)}"
                else:
                    success_message += f" в {os.path.basename(archive_dir)}"
                    
                self.finished_signal.emit(True, success_message)
                
            except Exception as e:
                raise Exception(f"Ошибка при распаковке: {str(e)}")
                
        except Exception as e:
            self.finished_signal.emit(False, str(e))

    def encode_numbers(self, number_string):
        return self.parent.encode_numbers(number_string) if self.parent else super().encode_numbers(number_string)

    def decode_numbers(self, encoded_string):
        return self.parent.decode_numbers(encoded_string) if self.parent else super().decode_numbers(encoded_string)

def main():
    check_folder_file()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
