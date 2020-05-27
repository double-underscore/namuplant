from PySide2.QtWidgets import QDialog, QSizePolicy, QHBoxLayout, QVBoxLayout, QGridLayout, QShortcut
from PySide2.QtWidgets import QPushButton, QLabel, QLineEdit, QComboBox, QDoubleSpinBox
from PySide2.QtWidgets import QTableWidget, QTableWidgetItem, QTableWidgetSelectionRange, QAbstractItemView
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
import pyperclip
from . import storage


class DDOSDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.label = QLabel('reCAPTCHA를 해결하고 확인 버튼을 누르세요.\n'
                            '404 페이지가 로드되면 정상입니다. 완료 버튼을 눌러 종료하세요.')
        self.label.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        QWebEngineProfile.defaultProfile().setHttpAcceptLanguage('ko')
        self.browser = QWebEngineView()
        self.browser.setStyleSheet('border: 1px solid gray;')
        # self.browser.loadStarted.connect(self.test)
        # self.browser.loadFinished.connect(self.test2)
        self.btn_zoom_in = QPushButton('+')
        self.btn_zoom_in.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_zoom_in.setMaximumWidth(50)
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out = QPushButton('-')
        self.btn_zoom_out.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_zoom_out.setMaximumWidth(50)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        self.btn = QPushButton('완료')
        self.btn.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn.clicked.connect(self.accept)
        # self.btn.clicked.connect(self.test2)
        self.abc = False
        box_h = QHBoxLayout()
        box_h.addWidget(self.btn_zoom_in)
        box_h.addWidget(self.btn_zoom_out)
        box_h.addWidget(self.btn)
        box_h.setStretchFactor(self.btn_zoom_in, 1)
        box_h.setStretchFactor(self.btn_zoom_out, 1)
        box_h.setStretchFactor(self.btn, 18)
        box_v = QVBoxLayout()
        box_v.addWidget(self.label)
        box_v.addWidget(self.browser)
        box_v.addLayout(box_h)
        box_v.setContentsMargins(8, 10, 8, 8)
        self.setLayout(box_v)
        # self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('reCAPTCHA')
        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowMinimizeButtonHint)
        self.browser.setFocus()
        self.resize(480, 600)

    def zoom_in(self):
        self.zoom(True)

    def zoom_out(self):
        self.zoom(False)

    def zoom(self, b):
        if b:
            self.browser.setZoomFactor(self.browser.zoomFactor() + 0.25)
        else:
            self.browser.setZoomFactor(self.browser.zoomFactor() - 0.25)


class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.lbl_id = QLabel('계정명')
        self.lbl_id.setAlignment(Qt.AlignCenter)
        self.lbl_pw = QLabel('비밀번호')
        self.lbl_pw.setAlignment(Qt.AlignCenter)
        self.lbl_umi = QLabel('umi 쿠키')
        self.lbl_umi.setAlignment(Qt.AlignCenter)
        self.lbl_ua = QLabel('유저 에이전트')
        self.lbl_ua.setAlignment(Qt.AlignCenter)
        self.lbl_delay = QLabel('저속 간격')
        self.lbl_delay.setAlignment(Qt.AlignCenter)
        self.line_id = QLineEdit()
        self.line_pw = QLineEdit()
        self.line_pw.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.line_umi = QLineEdit()
        self.line_ua = QLineEdit()
        self.line_delay = QDoubleSpinBox()
        self.line_delay.setMinimum(3)
        self.line_delay.setDecimals(1)
        self.line_delay.setSuffix('초')
        self.line_delay.setSingleStep(0.1)
        self.btn_save = QPushButton('저장')
        self.btn_save.clicked.connect(self.save)
        self.btn_cancel = QPushButton('취소')
        self.btn_cancel.clicked.connect(self.reject)
        grid = QGridLayout()
        grid.addWidget(self.lbl_id, 0, 0, 1, 2)
        grid.addWidget(self.line_id, 0, 2, 1, 6)
        grid.addWidget(self.lbl_pw, 1, 0, 1, 2)
        grid.addWidget(self.line_pw, 1, 2, 1, 6)
        grid.addWidget(self.lbl_umi, 2, 0, 1, 2)
        grid.addWidget(self.line_umi, 2, 2, 1, 6)
        grid.addWidget(self.lbl_ua, 3, 0, 1, 2)
        grid.addWidget(self.line_ua, 3, 2, 1, 6)
        grid.addWidget(self.lbl_delay, 4, 0, 1, 2)
        grid.addWidget(self.line_delay, 4, 2, 1, 6)
        grid.addWidget(self.btn_save, 5, 4, 1, 2)
        grid.addWidget(self.btn_cancel, 5, 6, 1, 2)
        self.setLayout(grid)
        self.setWindowTitle('개인 정보')
        self.setWindowIcon(QIcon('icon.png'))
        self.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.resize(400, 160)
        self.c_login, self.c_work = {}, {}

    def show_config(self):
        self.line_id.setText(self.c_login['ID'])
        self.line_pw.setText(self.c_login['PW'])
        self.line_umi.setText(self.c_login['UMI'])
        self.line_ua.setText(self.c_login['UA'])
        self.line_ua.setCursorPosition(0)
        self.line_delay.setValue(float(self.c_work['DELAY']))

    def load(self, c_login, c_work):
        self.c_login = c_login
        self.c_work = c_work

    def save(self):
        self.c_login = {'ID': self.line_id.text().strip(), 'PW': self.line_pw.text().strip(),
                        'UMI': self.line_umi.text().strip(), 'UA': self.line_ua.text().strip()}
        self.c_work = {'DELAY': self.line_delay.value()}
        self.accept()


class NameEditDialog(QDialog):
    sig_name_edit = Signal(str, int)

    def __init__(self):
        super().__init__()
        self.cmb_option = QComboBox(self)
        self.cmb_option.addItems(['접두', '접미'])
        self.cmb_option.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_option.setMinimumWidth(70)
        self.cmb_option.setMaximumWidth(100)
        self.line_text = LineEnhanced()
        self.line_text.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_ok = QPushButton('실행')
        self.btn_ok.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_ok.setMinimumWidth(72)
        self.btn_ok.setMaximumWidth(100)
        self.btn_ok.clicked.connect(self.emit_sig_name_edit)

        box_h = QHBoxLayout()
        box_h.addWidget(self.line_text)
        box_h.addWidget(self.cmb_option)
        box_h.addWidget(self.btn_ok)
        box_h.setStretchFactor(self.cmb_option, 1)
        box_h.setStretchFactor(self.line_text, 4)
        box_h.setStretchFactor(self.btn_ok, 1)
        box_h.setContentsMargins(3, 3, 3, 3)
        self.setLayout(box_h)
        self.setWindowTitle('이미지 파일 표제어 일괄 변경')
        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        # self.resize(300, 40)

    def emit_sig_name_edit(self):
        self.sig_name_edit.emit(self.line_text.text(), self.cmb_option.currentIndex())


class LineEnhanced(QLineEdit):
    focused = Signal()

    def __init__(self):
        super().__init__()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self.focused.emit()

    def undo(self):
        super().undo()
        if self.text() == '':
            super().undo()

    def redo(self):
        super().redo()
        if self.text() == '':
            super().redo()

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_Up:
            self.undo()
        elif e.key() == Qt.Key_Down:
            self.redo()


class TableEnhanced(QTableWidget):
    sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setDefaultSectionSize(23)
        self.horizontalHeader().setMinimumSectionSize(30)
        self.verticalHeader().setSectionsClickable(False)
        self.shortcuts()

    def shortcuts(self):
        move_up = QShortcut(QKeySequence('Ctrl+Shift+Up'), self, context=Qt.WidgetShortcut)
        move_up.activated.connect(self.move_up)  # 한 칸 위로
        move_down = QShortcut(QKeySequence('Ctrl+Shift+Down'), self, context=Qt.WidgetShortcut)
        move_down.activated.connect(self.move_down)  # 한 칸 아래로
        move_up = QShortcut(QKeySequence('Ctrl+Shift+Left'), self, context=Qt.WidgetShortcut)
        move_up.activated.connect(self.move_top)  # 맨 위로
        move_up = QShortcut(QKeySequence('Ctrl+Shift+Right'), self, context=Qt.WidgetShortcut)
        move_up.activated.connect(self.move_bottom)  # 맨 아래로
        copy_sheet = QShortcut(QKeySequence('Ctrl+C'), self, context=Qt.WidgetShortcut)
        copy_sheet.activated.connect(self.copy_sheet)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)  # 오버라이드하면서 기본 메서드 재활용
        if e.key() == Qt.Key_Delete:  # 지우기
            self.rows_delete(self._rows_selected())
            self.resizeColumnsToContents()

    def move_up(self):
        sel = self._rows_selected()
        if sel:
            if not sel[0] == 0:
                self.rows_paste(sel[0] - 1, self.rows_cut(sel, up=True), up=True)

    def move_down(self):
        sel = self._rows_selected()
        if sel:
            if not sel[-1] == self.rowCount() - 1:
                self.rows_paste(sel[-1] + 2, self.rows_cut(sel, up=False), up=False)

    def move_top(self):
        if self._rows_selected():
            self.rows_paste(0, self.rows_cut(self._rows_selected(), up=True), up=True)

    def move_bottom(self):
        if self._rows_selected():
            self.rows_paste(self.rowCount(), self.rows_cut(self._rows_selected(), up=False), up=False)

    def _rows_selected(self):
        if self.selectedItems():
            return sorted(list({i.row() for i in self.selectedItems()}))  # set comprehension

    def rows_cut(self, rows_list, up):  # generator, table item -> table item
        rows_list.reverse()
        ii = 0
        for r in rows_list:
            yield [self.item(r + ii, c) for c in range(self.columnCount())]
            ii += 1 if up else 0
            self.removeRow(r + ii)  # 지우기

    def rows_paste(self, where_to, rows_gen, up):
        ii, n = 0, 0
        col_origin = self.currentColumn()
        for row in rows_gen:
            self.insertRow(where_to + ii)
            n += 1
            for c in range(len(row)):
                self.setItem(where_to + ii, c, QTableWidgetItem(row[c]))
            ii -= 0 if up else 1
        # current & selection
        if up:
            rng = QTableWidgetSelectionRange(where_to, 0, where_to + n - 1, self.columnCount() - 1)
        else:
            where_to -= 1
            rng = QTableWidgetSelectionRange(where_to - n + 1, 0, where_to, self.columnCount() - 1)
        self.setCurrentCell(where_to, col_origin)
        self.setRangeSelected(rng, True)

    def rows_delete(self, rows_list):
        if rows_list:
            if len(rows_list) == self.rowCount():
                self.setRowCount(0)
            else:
                col_origin = self.currentColumn()
                rows_list.reverse()
                # t = time.time()
                for r in rows_list:
                    self.removeRow(r)
                # print(time.time() - t)
                pos_after = rows_list[0] - len(rows_list)  # 뒤집었으니까 -1 아니라 0
                pos_after += 0 if self.rowCount() - 1 == pos_after else 1
                self.setCurrentCell(pos_after, col_origin)

    def rows_text_copy(self, rows_list=None):  # table item -> text
        if rows_list is None:
            rows_list = range(self.rowCount())
        for row in rows_list:
            yield [self.item(row, col).text() for col in range(self.columnCount())]

    def rows_text_insert(self, where_to=None, editable=None, clickable=None, alignment=None):  # text -> table item
        if where_to is None:
            where_to = self.rowCount()
        if editable is None:
            editable = self.col_editable
        if clickable is None:
            clickable = self.col_clickable
        if alignment is None:
            alignment = self.col_alignment
        n = 0
        while True:
            to_insert = (yield)
            if to_insert is None:  # 꼼수
                where_to = self.rowCount()
                n = 0
                continue
            self.insertRow(where_to + n)
            for col in range(self.columnCount()):
                item = QTableWidgetItem(to_insert[col])
                if not editable[col]:  # false 일때 플래그 제거
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                if not clickable[col]:
                    item.setFlags(item.flags() ^ Qt.ItemIsEnabled)
                if alignment[col]:
                    item.setTextAlignment(alignment[col])  # ex) Qt.AlignCenter
                self.setItem(where_to + n, col, item)
            n += 1

    @staticmethod
    def convert_table_to_str(list_2d):  # 2d array -> text
        return '\n'.join(['\t'.join([str(col) for col in row]) for row in list_2d])

    @staticmethod
    def convert_str_to_table(text):  # text -> 2d array
        return [col.split('\t') for col in text.split('\n')]

    def copy_sheet(self):
        if self.selectedItems():
            t = ''
            for i in self.selectedItems():
                if i.column() == self.columnCount() - 1:
                    t = f'{t}{i.text()}\n'
                else:
                    t = f'{t}{i.text()}\t'
            pyperclip.copy(t[:-1])
