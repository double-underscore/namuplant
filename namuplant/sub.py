from PySide2.QtWidgets import QDialog, QFileDialog, QSizePolicy, QHBoxLayout, QVBoxLayout, QGridLayout, QShortcut
from PySide2.QtWidgets import QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QCheckBox
from PySide2.QtWidgets import QRadioButton, QButtonGroup
from PySide2.QtWidgets import QTableWidget, QTableWidgetItem, QTableWidgetSelectionRange, QAbstractItemView, QHeaderView
from PySide2.QtGui import QIcon, QKeySequence, QFont, QTextCursor, QTextCharFormat, QColor
from PySide2.QtCore import Qt, Signal, Slot, QUrl, QSize
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
import pyperclip
import difflib
from . import core


class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel()
        self.label.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.input = QLineEdit()
        self.input.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_ok = NPButton('확인', 10, self)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = NPButton('취소', 10, self)
        self.btn_cancel.clicked.connect(self.reject)
        grid = QGridLayout()
        grid.addWidget(self.label, 0, 0, 1, 8)
        grid.addWidget(self.input, 1, 0, 1, 8)
        grid.addWidget(self.btn_ok, 2, 6, 1, 1)
        grid.addWidget(self.btn_cancel, 2, 7, 1, 1)
        self.setLayout(grid)
        self.setWindowIcon(QIcon('icon.png'))
        self.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

    def get_text(self, title, lbl):
        self.setWindowTitle(title)
        self.label.setText(lbl)
        self.input.clear()
        if self.exec_() == self.Accepted:
            return self.input.text(), True
        else:
            return '', False


class DDOSDialog(QDialog):
    ddos_checked = Signal()

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
        self.btn_zoom_in = NPButton('+', 9, self)
        self.btn_zoom_in.setMinimumWidth(30)
        self.btn_zoom_in.setMaximumWidth(50)
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out = NPButton('-', 9, self)
        self.btn_zoom_out.setMinimumWidth(30)
        self.btn_zoom_out.setMaximumWidth(50)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        self.btn = NPButton('완료', 10, self)
        self.btn.setMaximumWidth(200)
        self.btn.clicked.connect(self.accept)
        # self.btn.clicked.connect(self.test2)
        self.abc = False
        box_h = QHBoxLayout()
        box_h.addWidget(self.btn_zoom_in)
        box_h.addWidget(self.btn_zoom_out)
        box_h.addStretch(4)
        box_h.addWidget(self.btn)
        box_h.setStretchFactor(self.btn_zoom_in, 1)
        box_h.setStretchFactor(self.btn_zoom_out, 1)
        box_h.setStretchFactor(self.btn, 4)
        box_v = QVBoxLayout()
        box_v.addWidget(self.label)
        box_v.addWidget(self.browser)
        box_v.addLayout(box_h)
        box_v.setContentsMargins(8, 10, 8, 8)
        self.setLayout(box_v)
        # self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('reCAPTCHA')
        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.browser.setFocus()
        self.resize(480, 700)

    def zoom_in(self):
        self.zoom(True)

    def zoom_out(self):
        self.zoom(False)

    def zoom(self, b):
        if b:
            self.browser.setZoomFactor(self.browser.zoomFactor() + 0.25)
        else:
            self.browser.setZoomFactor(self.browser.zoomFactor() - 0.25)

    @Slot()
    def show_ddos(self):
        self.browser.load(QUrl(f'{core.SITE_URL}/404'))
        ok = self.exec_()
        if ok == QDialog.Accepted:
            self.ddos_checked.emit()


class ConfigDialog(QDialog):
    config_changed = Signal()

    def __init__(self, requester, config, parent=None):
        super().__init__(parent)
        self.requester = requester
        self.requester.pin_needed.connect(self.input_pin)
        self.requester.umi_made.connect(self.write_umi)
        self.requester.msg_passed.connect(self.error_msg)
        self.config = config
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
        self.lbl_msg = QLabel('')
        self.line_id = QLineEdit()
        self.line_pw = QLineEdit()
        self.line_pw.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.line_umi = QLineEdit()
        self.line_umi.setPlaceholderText('로그인 시 자동 입력')
        self.line_ua = QLineEdit()
        self.line_delay = QDoubleSpinBox()
        self.line_delay.setMinimum(3)
        self.line_delay.setDecimals(1)
        self.line_delay.setSuffix('초')
        self.line_delay.setSingleStep(0.1)
        self.btn_save = NPButton('저장', 10, self)
        self.btn_save.clicked.connect(self.save)
        self.btn_cancel = NPButton('취소', 10, self)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_get_umi = NPButton('로그인', 10, self)
        self.btn_get_umi.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.btn_get_umi.clicked.connect(self.get_umi)
        grid = QGridLayout()
        grid.addWidget(self.lbl_id, 0, 0, 1, 1)
        grid.addWidget(self.line_id, 0, 1, 1, 6)
        grid.addWidget(self.lbl_pw, 1, 0, 1, 1)
        grid.addWidget(self.line_pw, 1, 1, 1, 6)
        grid.addWidget(self.btn_get_umi, 0, 7, 2, 2)
        grid.addWidget(self.lbl_umi, 2, 0, 1, 1)
        grid.addWidget(self.line_umi, 2, 1, 1, 8)
        grid.addWidget(self.lbl_ua, 3, 0, 1, 1)
        grid.addWidget(self.line_ua, 3, 1, 1, 8)
        grid.addWidget(self.lbl_delay, 4, 0, 1, 1)
        grid.addWidget(self.line_delay, 4, 1, 1, 8)
        grid.addWidget(self.lbl_msg, 5, 0, 1, 4)
        grid.addWidget(self.btn_save, 5, 5, 1, 2)
        grid.addWidget(self.btn_cancel, 5, 7, 1, 2)
        self.setLayout(grid)
        self.input_dialog = InputDialog(self)
        self.input_dialog.input.setInputMask('999999')
        self.setWindowTitle('개인정보')
        self.setWindowIcon(QIcon('icon.png'))
        self.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.c_login, self.c_work = {}, {}

    @Slot(str)
    def error_msg(self, t):
        self.lbl_msg.setText(t)

    def load(self):
        self.line_id.setText(self.config.c['login']['ID'])
        self.line_pw.setText(self.config.c['login']['PW'])
        self.line_umi.setText(self.config.c['login']['UMI'])
        self.line_ua.setText(self.config.c['login']['UA'])
        self.line_ua.setCursorPosition(0)
        self.line_delay.setValue(float(self.config.c['work']['DELAY']))
        self.lbl_msg.clear()
        ok = self.exec_()
        if ok == QDialog.Accepted:
            self.config_changed.emit()

    def save(self):
        self.config.save(
            login={'ID': self.line_id.text().strip(), 'PW': self.line_pw.text().strip(),
                   'UMI': self.line_umi.text().strip(), 'UA': self.line_ua.text().strip()},
            delay=self.line_delay.value()
        )
        self.accept()

    def get_umi(self):
        self.lbl_msg.setText('로그인 시도...')
        self.line_umi.clear()
        self.input_dialog.input.clear()
        self.requester.init_login(self.line_id.text().strip(), self.line_pw.text().strip())

    @Slot(str)
    def write_umi(self, umi):
        self.line_umi.setText(umi)

    @Slot(str)
    def input_pin(self, mail):
        pin, ok = self.input_dialog.get_text('로그인 PIN 입력', f'이메일({mail})로 전송된 PIN을 입력해주세요.')
        if ok:
            if pin:
                self.requester.typed_pin = pin
            else:
                self.requester.typed_pin = 'nothing'
        else:
            self.requester.typed_pin = 'deny'


class NameEditDialog(QDialog):
    sig_name_edit = Signal(str, int)

    def __init__(self):
        super().__init__()
        self.cmb_option = QComboBox(self)
        self.cmb_option.addItems(['접두', '접미'])
        self.cmb_option.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_option.setMinimumWidth(70)
        self.cmb_option.setMaximumWidth(100)
        self.line_text = NPLine()
        self.line_text.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_ok = NPButton('실행', 10, self)
        self.btn_ok.clicked.connect(self.emit_sig_name_edit)

        box_h = QHBoxLayout()
        box_h.addWidget(self.line_text)
        box_h.addWidget(self.cmb_option)
        box_h.addWidget(self.btn_ok)
        box_h.setStretchFactor(self.cmb_option, 1)
        box_h.setStretchFactor(self.line_text, 4)
        box_h.setStretchFactor(self.btn_ok, 1)
        # box_h.setContentsMargins(3, 3, 3, 3)
        self.setLayout(box_h)
        self.setWindowTitle('선택한 이미지 파일 표제어 일괄 변경')
        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        # self.resize(300, 40)

    def emit_sig_name_edit(self):
        self.sig_name_edit.emit(self.line_text.text(), self.cmb_option.currentIndex())


class FileDialog(QFileDialog):
    def __init__(self):
        super().__init__()

    def get_open_image(self):
        self.setAcceptMode(self.AcceptOpen)
        self.setFileMode(self.ExistingFiles)
        self.setNameFilter('이미지 파일(*.jpg *.png *.gif *.JPG *.PNG *.GIF)')
        self.setWindowTitle('이미지 열기')
        if self.exec_():
            return self.selectedFiles()

    def get_open_csv(self):
        self.setAcceptMode(self.AcceptOpen)
        self.setFileMode(self.ExistingFile)
        self.setNameFilter('CSV 파일(*.csv)')
        self.setWindowTitle('목록 불러오기')
        if self.exec_():
            return self.selectedFiles()

    def get_save_csv(self):
        self.setAcceptMode(self.AcceptSave)
        self.setFileMode(self.AnyFile)
        self.setNameFilter('CSV 파일(*.csv)')
        self.setWindowTitle('목록 저장하기')
        if self.exec_():
            return self.selectedFiles()


class NPButton(QPushButton):
    def __init__(self, label, size, parent=None):
        super().__init__(parent)
        self.setText(label)
        self.setStyleSheet(f'font: {size}pt \'맑은 고딕\'')
        self.setMinimumWidth(70)
        self.setMaximumWidth(120)


class NPLine(QLineEdit):
    focused = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

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


class NPTable(QTableWidget):
    sig_main_label = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
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
            self.sig_main_label.emit('선택된 문서를 목록에서 제거하였습니다.')
            # self.resizeColumnsToContents()

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


class NPTextEdit(QTextEdit):
    sig_size = Signal(QSize)

    def __init__(self, bg_color='white', parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.textChanged.connect(self.resize_editor)
        self.document().documentLayout().documentSizeChanged.connect(self.resize_editor)
        self.setStyleSheet(f"""
            QTextEdit{{
                font: 9pt \'맑은 고딕\';
                background-color: {bg_color};
                selection-background-color: cadetblue; 
                selection-color: white;
                border: 0;}}
            QTextEdit:Focus{{
                selection-background-color: darkcyan; 
                selection-color: white;}}
            """)

    def resize_editor(self):
        h = self.document().size().height()
        margin = self.document().documentMargin()
        self.setMinimumHeight(h + 2 * margin)
        self.setMaximumHeight(h + 2 * margin)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.sig_size.emit(QSize(self.sizeHint().width(), self.maximumHeight()))


class DiffTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setColumnCount(4)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setMinimumSectionSize(10)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 컬러 세트
        color_sub = QColor()
        color_sub.setNamedColor('#ffaaaa')
        color_add = QColor()
        color_add.setNamedColor('#aaffaa')
        self.fmt_sub = QTextCharFormat()
        self.fmt_sub.setBackground(color_sub)
        self.fmt_add = QTextCharFormat()
        self.fmt_add.setBackground(color_add)
        self.a = ''
        self.b = ''

    def _make_table(self, a, b):
        self.setRowCount(0)
        al, bl = [], []
        bn = 1
        for ar, br, flag in difflib._mdiff(a.splitlines(keepends=True), b.splitlines(keepends=True), context=2):
            if flag is None:
                self.insertRow(self.rowCount())
                self.setItem(self.rowCount() - 1, 0, self._table_item())
                self.setItem(self.rowCount() - 1, 1, self._table_item('...'))
                self.setItem(self.rowCount() - 1, 2, self._table_item('...'))
                self.setItem(self.rowCount() - 1, 3, self._table_item('(생략)', center=False))
            else:
                an, at = ar
                bn, bt = br
                if flag:
                    if type(an) is int:
                        al.append([str(an), at])
                    if type(bn) is int:
                        bl.append([str(bn), bt])
                else:
                    self._insert_merged(al, bl)  # flag가 True일 때 모아둔 al, bl을 표에 실제 입력
                    al, bl = [], []
                    self.insertRow(self.rowCount())
                    self.setItem(self.rowCount() - 1, 0, self._table_item())
                    self.setItem(self.rowCount() - 1, 1, self._table_item(str(an)))
                    self.setItem(self.rowCount() - 1, 2, self._table_item(str(bn)))
                    self.setItem(self.rowCount() - 1, 3,
                                 self._table_item((lambda x: x[:-1] if x.endswith('\n') else x)(at), center=False))
        self._insert_merged(al, bl)
        if self.rowCount() == 0:
            self.insertRow(0)
            self.setItem(0, 3, self._table_item('변경 사항이 없습니다.', False))
        elif type(bn) is int and bn < len(b.splitlines()):  # 맨 마지막에 생략 표시가 자동으로 안 됨
            self.insertRow(self.rowCount())
            self.setItem(self.rowCount() - 1, 0, self._table_item())
            self.setItem(self.rowCount() - 1, 1, self._table_item('...'))
            self.setItem(self.rowCount() - 1, 2, self._table_item('...'))
            self.setItem(self.rowCount() - 1, 3, self._table_item('(생략)', center=False))

    @staticmethod
    def _table_item(text='', center=True):
        item = QTableWidgetItem(text)
        font = QFont()
        if center:  # 행번호
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.NoItemFlags)
            item.setFont(font)
            font.setPointSize(7)
        else:
            item.setFlags(Qt.NoItemFlags)
            item.setFont(font)
            font.setPointSize(9)
        return item

    def _insert_merged(self, al, bl):
        if al:
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 1, self._table_item('\n'.join(map(lambda x: x[0], al))))
            self.setItem(row, 2, self._table_item())
            self.setItem(row, 3, self._table_item())
            editor = NPTextEdit(bg_color='#ffeef0')
            editor.sig_size.connect(self.item(row, 3).setSizeHint)
            self._highlight(editor, ''.join(map(lambda x: x[1], al)), self.fmt_sub, self.fmt_sub)
            self.setCellWidget(row, 3, editor)
            if not bl:
                self.setItem(row, 0, self._table_item())
                self.setCellWidget(row, 0, QCheckBox(checked=True))
                self.cellWidget(row, 3).setReadOnly(True)
        if bl:
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 1, self._table_item())
            self.setItem(row, 2, self._table_item('\n'.join(map(lambda x: x[0], bl))))
            self.setItem(row, 3, self._table_item())
            editor = NPTextEdit(bg_color='#e6ffed')
            editor.sig_size.connect(self.item(row, 3).setSizeHint)
            self._highlight(editor, ''.join(map(lambda x: x[1], bl)), self.fmt_add, self.fmt_add)
            self.setCellWidget(row, 3, editor)
            if not al:
                self.setCellWidget(row, 0, QCheckBox(checked=True))
        if al and bl:  # 변경 시 radio button 필요
            group = QButtonGroup(self)
            group.setExclusive(True)
            ar = QRadioButton()
            br = QRadioButton(checked=True)
            group.addButton(ar)
            group.addButton(br)
            self.setCellWidget(self.rowCount() - 2, 0, ar)
            self.setCellWidget(self.rowCount() - 1, 0, br)

    @staticmethod
    def _get_pos_list(t: str):
        start, end, n, lst = 0, 0, 0, []
        while True:
            start = t.find('\0', n)
            end = t.find('\1', n)
            if start == -1:
                break
            else:
                lst.append((t[start + 1], start, end))
                n = end + 1
        return lst

    def _highlight(self, editor: QTextEdit, text: str, fmt: QTextCharFormat, fmt_chg: QTextCharFormat):
        cursor = QTextCursor(editor.textCursor())
        if text.endswith('\n'):
            text = text[:-1]
        elif text.endswith('\n\1'):
            text = text[:-2] + '\1'
        pos_list = self._get_pos_list(text)
        text = text.replace('\0+', '').replace('\0-', '').replace('\0^', '').replace('\1', '')
        editor.setPlainText(text)
        n = 0
        for tag, start, end in pos_list:
            if not end == start + 2:
                cursor.setPosition(start - n)
                cursor.setPosition(end - n - 2, QTextCursor.KeepAnchor)
                if tag == '^':
                    cursor.mergeCharFormat(fmt_chg)
                else:
                    cursor.mergeCharFormat(fmt)
            n += 3

    def _retrieve(self):
        i = 0
        n = self.rowCount()
        lines = []
        while i < n:
            widget_a = self.cellWidget(i, 0)
            if type(widget_a) is QRadioButton:
                widget_b = self.cellWidget(i + 1, 0)
                if type(widget_b) is QRadioButton:
                    b_num = self.item(i + 1, 2).text()
                    if '\n' in b_num:
                        lines.append((int(b_num[:b_num.find('\n')]), int(b_num[b_num.rfind('\n') + 1:]), 0,
                                      self.cellWidget(i + int(widget_b.isChecked()), 3).toPlainText()))
                    else:
                        lines.append((int(b_num), int(b_num), 0,
                                      self.cellWidget(i + int(widget_b.isChecked()), 3).toPlainText()))
                    i += 1
            elif type(widget_a) is QCheckBox:
                text = self.cellWidget(i, 3).toPlainText()
                if self.item(i, 1).text():  # 삭제
                    if not widget_a.isChecked():
                        if n == 1:  # 완전 삭제
                            lines.append((1, None, 1, text))
                        elif i == n - 1:  # 마지막
                            b_num = self.item(i - 1, 2).text()
                            lines.append((int(b_num) + 1, None, 1, text))
                        else:
                            b_num = self.item(i + 1, 2).text()
                            lines.append((int(b_num), None, 1, text))
                elif self.item(i, 2).text():  # 추가
                    mode = 0 if widget_a.isChecked() else -1
                    b_num = self.item(i, 2).text()
                    if '\n' in b_num:
                        lines.append((int(b_num[:b_num.find('\n')]), int(b_num[b_num.rfind('\n') + 1:]), mode, text))
                    else:
                        lines.append((int(b_num), int(b_num), mode, text))
            i += 1
        return lines

    @staticmethod
    def _assemble(b, ln_list):
        bs = b.splitlines(keepends=True)
        n = 0
        for s, e, m, t in ln_list:
            t = t + '\n'
            if m == 0:  # 일반적인 RadioButton
                del bs[s - 1 - n:e - n]
                bs.insert(s - 1 - n, t)
                n += e - s
            elif m == 1:
                bs.insert(s - 1 - n, t)
                n -= 1
            elif m == -1:
                del bs[s - 1 - n:e - n]
                n += e - s + 1
        return ''.join(bs)
        # return (lambda x: x[:-1] if x.endswith('\n') else x)(''.join(bs))

    def make_diff(self, a: str = None, b: str = None):
        if a is not None:
            self.a = a
        if b is not None:
            self.b = b
        self._make_table(self.a, self.b)

    def refresh_diff(self):
        self.make_diff(b=self.current_text())

    def current_text(self):
        return self._assemble(self.b, self._retrieve())
