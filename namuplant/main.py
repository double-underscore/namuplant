import sys
import os
import re
import time
import psutil
from urllib import parse
import pyperclip
import mouse
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QDialog, QAction, QShortcut, QPushButton, QLabel
from PySide2.QtWidgets import QComboBox, QSpinBox, QLineEdit, QTextEdit, QTabWidget, QSplitter, QVBoxLayout, QHBoxLayout
from PySide2.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QTableWidgetSelectionRange
from PySide2.QtWidgets import QTextBrowser, QFrame, QSizePolicy, QHeaderView, QFileDialog, QTableView
from PySide2.QtGui import QIcon, QColor, QFont, QKeySequence, QStandardItem, QStandardItemModel, QPixmap, QPalette
from PySide2.QtCore import Qt, QUrl, QThread, QObject, QSize, Signal, Slot, QAbstractItemModel, QModelIndex
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from namuplant import core, storage
process = psutil.Process(os.getpid())


def trace(func):
    def wrapper(self, *args, **kwargs):
        t1 = time.time()
        print(func.__name__, '시행 전 메모리:', process.memory_info().rss / 1024 / 1024)
        r = func(self, *args, **kwargs)
        print(func.__name__, '시행 후 메모리:', process.memory_info().rss / 1024 / 1024,
              '시행 소요 시간', time.time() - t1)
        return r

    return wrapper

# todo 미러 사이트를 통한 목록 필터링
# todo 목록 중복 제거
# todo 파일 문서명 일괄 변경 (접두 접미)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet('font: 10pt \'맑은 고딕\'; color: #373a3c;')
        self.resize(800, 800)
        # self.setWindowTitle('namuplant')
        self.setWindowIcon(QIcon('icon.png'))
        # 액션
        act_test = QAction('실험', self)
        act_test.triggered.connect(self.action_test)
        act_test2 = QAction('실험2', self)
        act_test2.triggered.connect(self.action_test2)
        act_memory = QAction('RAM', self)
        act_memory.triggered.connect(self.action_memory)
        # 메뉴
        menu_bar = self.menuBar()
        menu_bar.addAction(act_test)
        menu_bar.addAction(act_test2)
        menu_bar.addAction(act_memory)
        # menu_test = menu_bar.addMenu('&Test')
        # menu_test.addAction(act_test)
        # menu_memory = menu_bar.addMenu('&Memory')
        # menu_memory.addAction(act_memory)
        # 메인
        self.main_widget = MainWidget()
        self.setCentralWidget(self.main_widget)

        t = time.time()
        self.read_doc_list_csv_()
        print(time.time() - t)

    # def read_doc_list_csv(self):
    #     docs, edits = storage.read_list_csv('doc_list.csv')
    #     t_m = self.main_widget.tab_macro
    #     t_m.doc_board.table_doc.rows_insert(docs)
    #     t_m.doc_board.table_doc.after_insert()
    #     t_m.edit_editor.table_edit.rows_insert(edits)
    #     # t_m.doc_inventory.table_doc.setcurrent
    #
    # def write_doc_list_csv(self):
    #     t_m = self.main_widget.tab_macro
    #     docs = t_m.doc_board.table_doc.rows_copy_text()
    #     edits = t_m.edit_editor.table_edit.edits_copy()
    #     storage.write_list_csv('doc_list.csv', docs, edits)

    def read_doc_list_csv_(self):
        t_m = self.main_widget.tab_macro
        # doc
        wt = t_m.doc_board.table_doc.rows_text_insert()
        wt.send(None)
        for row in storage.read_csv_('doc_list.csv'):
            wt.send([row['code'], row['title'], row['error']])
        t_m.doc_board.table_doc.after_insert()
        # edit
        wt = t_m.edit_editor.table_edit.rows_text_insert()
        wt.send(None)
        for row in storage.read_csv_('edit_list.csv'):
            wt.send([row['index'], row['opt1'], row['opt2'], row['opt3'], row['opt4'], row['edit']])
        t_m.edit_editor.table_edit.resizeColumnsToContents()
        wt.close()

    def write_doc_list_csv_(self):
        t_m = self.main_widget.tab_macro
        # doc
        wc = storage.write_csv_('doc_list.csv', 'w', 'doc')
        wc.send(None)
        for row in t_m.doc_board.table_doc.rows_text_copy():
            wc.send({'code': row[0], 'title': row[1], 'error': row[2]})
        # edit
        wc = storage.write_csv_('edit_list.csv', 'w', 'edit')
        wc.send(None)
        for row in t_m.edit_editor.table_edit.rows_text_copy():
            wc.send({'index': row[0], 'opt1': row[1], 'opt2': row[2], 'opt3': row[3], 'opt4': row[4], 'edit': row[5]})
        wc.close()

    def closeEvent(self, event):
        self.write_doc_list_csv_()

    def action_test(self):
        # print('th_micro: ', self.main_widget.tab_macro.th_micro.isRunning())
        # print(process.memory_info().rss / 1024 / 1024)
        # self.main_widget.ddos_dialog.browser.load(QUrl('https://www.google.com/recaptcha/api2/demo'))
        # self.main_widget.ddos_dialog.browser.setHtml("<html><head></head><body><h1>정말 잘하셨어요</h1></body></html>")
        # self.main_widget.ddos_dialog.show()
        # self.main_widget.tab_macro.btn_get.setEnabled(False)
        self.main_widget.tab_macro.doc_board.table_doc.setRowCount(0)

    def action_test2(self):
        self.main_widget.tab_macro.doc_board.table_doc.clearContents()

    @classmethod
    def action_memory(cls):
        print(process.memory_info().rss / 1024 / 1024)


class DDOSDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.label = QLabel('reCAPTCHA 해결 후 완료 버튼을 눌러주세요.\n404 페이지가 로드되면 정상입니다.')
        self.label.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        QWebEngineProfile.defaultProfile().setHttpAcceptLanguage('ko')
        self.browser = QWebEngineView()
        self.browser.setStyleSheet('border: 1px solid gray;')
        self.browser.loadStarted.connect(self.test)
        # self.browser.loadFinished.connect(self.test2)
        self.btn = QPushButton('완료')
        self.btn.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn.clicked.connect(self.accept)
        # self.btn.clicked.connect(self.test2)
        self.abc = False
        box_v = QVBoxLayout()
        box_v.addWidget(self.label)
        box_v.addWidget(self.browser)
        box_v.addWidget(self.btn)
        box_v.setContentsMargins(3, 10, 3, 3)
        self.setLayout(box_v)
        # self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('reCAPTCHA')
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowMinimizeButtonHint)
        self.resize(480, 600)

    @Slot()
    def test(self):
        # self.abc = {True: False, False: True}[self.abc]
        print(self.abc)
        # self.browser.setHtml("<html><head></head><body><h1>ciao</h1></body></html>")


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        # label
        self.main_label = QLabel()
        self.main_label.setAlignment(Qt.AlignCenter)
        self.main_label.setStyleSheet('font: 10.5pt \'맑은 고딕\'')
        self.main_label.setWordWrap(True)
        # self.set_main_label('namuplant: a bot for namu.wiki')

        # self.tabs = QTabWidget()
        self.tab_macro = TabMacro()
        self.tab_macro.sig_main_label.connect(self.set_main_label)
        # self.tab_b = TabMicro()
        # self.tab_b.sig_main_label.connect(self.set_main_label)
        # self.tabs.addTab(self.tab_macro, '    Macro    ')
        # self.tabs.addTab(self.tab_b, '    Micro    ')

        box_v = QVBoxLayout()
        box_v.addWidget(self.main_label)
        box_v.addWidget(self.tab_macro)
        box_v.setStretchFactor(self.main_label, 1)
        box_v.setStretchFactor(self.tab_macro, 25)
        box_v.setContentsMargins(3, 3, 3, 3)
        self.setLayout(box_v)
        # ddos dialog connect
        self.ddos_dialog = DDOSDialog()
        self.tab_macro.req_get.sig_check_ddos.connect(self.show_ddos_dialog)
        self.tab_macro.iterate_post.sig_check_ddos.connect(self.show_ddos_dialog)
        self.tab_macro.micro_post.sig_check_ddos.connect(self.show_ddos_dialog)
        self.tab_macro.edit_editor.ss.sig_check_ddos.connect(self.show_ddos_dialog)

    @Slot(str)
    def set_main_label(self, t):
        self.main_label.setText(t)

    @Slot(object)
    def show_ddos_dialog(self, obj):
        self.ddos_dialog.browser.load(QUrl(f'{core.SITE_URL}/404'))
        ddd = self.ddos_dialog.exec_()
        if ddd == QDialog.Accepted:
            obj.is_ddos_checked = True


class TabMacro(QWidget):
    sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        self.doc_board = DocBoard()
        self.tabs_viewer = TabViewers()
        self.edit_editor = EditEditor()
        # last row: get link
        self.btn_get = QPushButton('右 OFF', self)
        self.btn_get.setCheckable(True)
        self.btn_get.toggled.connect(self.btn_get_toggle)
        self.btn_get.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_get.setMinimumWidth(70)
        self.btn_get.setMaximumWidth(100)
        # last row: main work
        self.combo_speed = QComboBox(self)
        self.combo_speed.addItems(['고속', '저속'])
        self.combo_speed.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_speed.setMinimumWidth(70)
        self.combo_speed.setMaximumWidth(100)
        self.combo_speed.currentIndexChanged.connect(self.iterate_speed_change)
        # todo 스피드 옵션 이터레이트 즉시 반응
        self.btn_do = QPushButton('시작', self)
        self.btn_do.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_do.setMinimumWidth(72)
        self.btn_do.setMaximumWidth(100)
        self.btn_pause = QPushButton('정지', self)
        self.btn_pause.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_pause.setMinimumWidth(72)
        self.btn_pause.setMaximumWidth(100)
        self.btn_pause.setEnabled(False)
        # splitter left
        split_v = QSplitter(Qt.Vertical)
        split_v.addWidget(self.tabs_viewer)
        split_v.addWidget(self.edit_editor)
        split_v.setStretchFactor(0, 1)
        split_v.setStretchFactor(1, 1)
        split_v.setMinimumSize(200, 265)
        # splitter right
        split_h = QSplitter()
        # split_h.setframe
        # split_h.setStyleSheet("""
        #     QSplitter::handle {
        #         background-color: silver;
        #     }
        #     """)
        split_h.addWidget(self.doc_board)
        split_h.addWidget(split_v)
        split_h.setStretchFactor(0, 1)
        split_h.setStretchFactor(1, 1)
        split_h.splitterMoved.connect(self.doc_board.table_doc.resize_to_splitter)

        # box last row
        box_last_row = QHBoxLayout()
        box_last_row.addWidget(self.btn_get)
        box_last_row.addStretch(6)
        box_last_row.addWidget(self.combo_speed)
        box_last_row.addWidget(self.btn_do)
        box_last_row.addWidget(self.btn_pause)
        box_last_row.setStretchFactor(self.btn_get, 1)
        box_last_row.setStretchFactor(self.combo_speed, 1)
        box_last_row.setStretchFactor(self.btn_do, 1)
        box_last_row.setStretchFactor(self.btn_pause, 1)
        box_last_row.setContentsMargins(0, 0, 0, 0)
        # box vertical
        box_v = QVBoxLayout()
        box_v.addWidget(split_h)
        box_v.addLayout(box_last_row)
        box_v.setContentsMargins(2, 2, 2, 2)
        self.setLayout(box_v)
        # widget connect
        self.doc_board.table_doc.sig_main_label.connect(self.str_to_main)
        self.doc_board.table_doc.sig_doc_viewer.connect(self.micro_view)
        self.doc_board.combo_option.currentIndexChanged.connect(self.btn_get_enable)
        self.tabs_viewer.sig_main_label.connect(self.str_to_main)
        self.edit_editor.table_edit.sig_insert.connect(self.doc_board.table_doc.insert_edit_num)
        self.btn_do.clicked.connect(self.iterate_start)
        self.btn_pause.clicked.connect(self.thread_quit)
        # thread get_click
        mouse.on_right_click(self.get_start)
        self.th_get = QThread()
        self.req_get = core.ReqGet(self.doc_board.table_doc.rows_text_insert())
        self.req_get.finished.connect(self.get_finish)
        self.req_get.sig_label_text.connect(self.str_to_main)
        # self.req_get.send_code_list.connect(self.doc_board.table_doc.receive_codes_get)
        self.doc_board.sig_doc_code.connect(self.get_by_input)
        self.req_get.moveToThread(self.th_get)
        self.th_get.started.connect(self.req_get.work)
        # thread iterate
        self.th_iterate = QThread()
        self.iterate_post = core.Iterate()
        self.iterate_post.finished.connect(self.iterate_finish)
        self.iterate_post.sig_label_text.connect(self.str_to_main)
        self.iterate_post.sig_doc_remove.connect(self.doc_board.table_doc.removeRow)
        self.iterate_post.sig_doc_set_current.connect(self.doc_board.table_doc.set_current)
        self.iterate_post.sig_doc_error.connect(self.doc_board.table_doc.set_error)
        self.iterate_post.sig_view_diff.connect(self.tabs_viewer.show_diff)
        self.iterate_post.sig_enable_pause.connect(self.iterate_enable_pause)
        self.tabs_viewer.sig_diff_done.connect(self.iterate_post.receive_diff_done)
        self.iterate_post.moveToThread(self.th_iterate)
        self.th_iterate.started.connect(self.iterate_post.work)
        # thread micro
        self.th_micro = QThread()
        self.micro_post = core.Micro()
        self.micro_post.finished.connect(self.micro_finish)
        self.micro_post.sig_label_text.connect(self.str_to_main)
        self.micro_post.sig_text_view.connect(self.tabs_viewer.doc_viewer.set_text_view)
        self.micro_post.sig_text_edit.connect(self.tabs_viewer.doc_viewer.set_text_edit)
        self.micro_post.sig_image_view.connect(self.tabs_viewer.show_image)
        self.micro_post.sig_enable_iterate.connect(self.micro_enable_iterate)
        self.micro_post.sig_view_diff.connect(self.tabs_viewer.show_diff_micro)
        self.tabs_viewer.sig_diff_micro_done.connect(self.micro_post.receive_diff_done)
        self.tabs_viewer.doc_viewer.btn_edit.clicked.connect(self.micro_edit)
        self.tabs_viewer.doc_viewer.btn_close.clicked.connect(self.micro_close)
        self.tabs_viewer.doc_viewer.btn_apply.clicked.connect(self.micro_apply)
        self.tabs_viewer.doc_viewer.btn_post.clicked.connect(self.micro_text_post)
        self.tabs_viewer.doc_viewer.btn_cancel.clicked.connect(self.micro_back)
        self.th_micro.started.connect(self.micro_post.work)
        self.micro_post.moveToThread(self.th_micro)

    @Slot(str)
    def str_to_main(self, t):
        self.sig_main_label.emit(t)

    @Slot(bool)
    def btn_get_toggle(self, b):
        self.btn_get.setText({True: '右 ON', False: '右 OFF'}[b])

    @Slot(int)
    def btn_get_enable(self, i):
        if i == 3:
            self.btn_get.setEnabled(False)
        else:
            self.btn_get.setEnabled(True)

    @Slot()
    def thread_quit(self):
        if self.th_iterate.isRunning():
            self.iterate_post.is_quit = True
        elif self.th_get.isRunning():
            self.req_get.is_quit = True
        self.str_to_main('정지 버튼을 눌렀습니다.')

    @Slot()
    def get_start(self):
        if self.btn_get.isEnabled() and self.btn_get.isChecked():  # 우클릭 모드 ON
            self.btn_get.setEnabled(False)  # 동시 실행 방지
            self.req_get.mode = 1
            self.btn_do.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.req_get.option = self.doc_board.combo_option.currentIndex()
            self.th_get.start()

    @Slot(str)
    def get_by_input(self, code):
        if self.btn_get.isEnabled():
            # self.t1 = time.time()
            self.btn_get.setEnabled(False)  # 동시 실행 방지
            self.req_get.mode = 0
            self.req_get.code = code
            self.btn_do.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.req_get.option = self.doc_board.combo_option.currentIndex()
            self.th_get.start()

    @Slot()
    def get_finish(self):
        self.th_get.quit()
        # print(time.time() - self.t1)
        self.doc_board.table_doc.resizeColumnsToContents()
        self.doc_board.table_doc.setCurrentCell(self.doc_board.table_doc.rowCount() - 1, 1)
        self.doc_board.table_doc.setFocus()
        self.req_get.is_quit = False
        self.btn_do.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_get.setEnabled(True)

    @Slot()
    def iterate_start(self):
        self.btn_do.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.iterate_post.doc_list = self.doc_board.table_doc.rows_copy_text()
        self.iterate_post.edit_list = self.edit_editor.table_edit.edits_copy()
        self.iterate_post.index_speed = self.combo_speed.currentIndex()
        self.iterate_post.diff_done = 1
        self.th_iterate.start()

    @Slot()
    def iterate_finish(self):
        self.th_iterate.quit()
        self.iterate_post.is_quit = False
        self.btn_do.setEnabled(True)
        self.btn_pause.setEnabled(False)

    @Slot(bool)
    def iterate_enable_pause(self, b):
        self.btn_pause.setEnabled(b)

    @Slot(int)
    def iterate_speed_change(self, i):
        if self.th_iterate.isRunning():
            self.iterate_post.index_speed = i

    @Slot(str)
    def micro_view(self, doc_code):
        if not self.th_micro.isRunning():
            self.micro_post.doc_code = doc_code  # 여기서 doc_code 지정
            self.micro_post.mode = 0
            self.tabs_viewer.setCurrentWidget(self.tabs_viewer.doc_viewer)
            self.th_micro.start()

    @Slot()
    def micro_close(self):
        self.tabs_viewer.doc_viewer.quit_edit(True)
        self.str_to_main('문서를 닫았습니다.')

    @Slot()
    def micro_edit(self):
        self.micro_post.mode = 1
        self.th_micro.start()

    @Slot()
    def micro_apply(self):
        edit_list = self.edit_editor.table_edit.edits_copy_one(self.tabs_viewer.doc_viewer.spin.value() - 1)
        text = self.tabs_viewer.doc_viewer.viewer.toPlainText()
        self.tabs_viewer.doc_viewer.viewer.setPlainText(self.micro_post.apply(text, edit_list))

    @Slot()
    def micro_text_post(self):
        self.micro_post.text = self.tabs_viewer.doc_viewer.viewer.toPlainText()
        self.micro_post.do_post = True

    @Slot()
    def micro_back(self):
        self.micro_post.do_cancel = True
        self.micro_post.do_post = True

    @Slot()
    def micro_finish(self):
        code = self.micro_post.doc_code
        if self.micro_post.mode == 1:
            self.tabs_viewer.doc_viewer.quit_edit(False)
        self.th_micro.quit()
        if self.micro_post.mode == 1:
            time.sleep(0.01)
            self.micro_view(code)

    @Slot(bool)
    def micro_enable_iterate(self, b):
        self.btn_do.setEnabled(b)


class TableEnhanced(QTableWidget):
    sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        self.setAlternatingRowColors(True)
        self.setGridStyle(Qt.DotLine)
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
            col_origin = self.currentColumn()
            rows_list.reverse()
            t = time.time()
            for r in rows_list:
                self.removeRow(r)
            print(time.time() - t)
            pos_after = rows_list[0] - len(rows_list)  # 뒤집었으니까 -1 아니라 0
            pos_after += 0 if self.rowCount() - 1 == pos_after else 1
            self.setCurrentCell(pos_after, col_origin)

    # def rows_insert(self, text_list_2d, where_to=None, editable=None, clickable=None, alignment=None):
    #     if where_to is None:
    #         where_to = self.rowCount()
    #     if editable is None:
    #         editable = self.col_editable
    #     if clickable is None:
    #         clickable = self.col_clickable
    #     if alignment is None:
    #         alignment = self.col_alignment
    #     text_list_2d.reverse()
    #     for i in range(len(text_list_2d)):
    #         self.insertRow(where_to)
    #         for c in range(self.columnCount()):
    #             item = QTableWidgetItem(text_list_2d[i][c])
    #             if not editable[c]:  # false 일때 플래그 제거
    #                 item.setFlags(item.flags() ^ Qt.ItemIsEditable)
    #             if not clickable[c]:
    #                 item.setFlags(item.flags() ^ Qt.ItemIsEnabled)
    #             if alignment[c]:
    #                 item.setTextAlignment(alignment[c])  # ex) Qt.AlignCenter
    #             self.setItem(where_to, c, item)
    #     self.resizeColumnsToContents()

    def rows_copy_text(self, rows_list=None):  # table item -> text
        if rows_list is None:
            rows_list = range(self.rowCount())
        return [[self.item(r, c).text() for c in range(self.columnCount())] for r in rows_list]

    def rows_text_copy(self, rows_list=None):  # table item -> text
        if rows_list is None:
            rows_list = range(self.rowCount())
        for row in rows_list:
            # self.horizontalHeaderItem(0).text()
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

    @classmethod
    def convert_table_to_str(cls, list_2d):  # 2d array -> text
        return '\n'.join(['\t'.join([str(col) for col in row]) for row in list_2d])

    @classmethod
    def convert_str_to_table(cls, text):  # text -> 2d array
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


class TableDoc(TableEnhanced):
    sig_doc_viewer = Signal(str)

    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['코드', '표제어', '비고'])
        self.horizontalHeader().setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.horizontalHeader().setMinimumSectionSize(34)
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().sectionResized.connect(self.resize_section)
        self.verticalHeader().setStyleSheet('font: 7pt \'맑은 고딕\'')
        self.horizontalScrollBar().setVisible(True)
        self.hideColumn(0)
        self.col_editable = (False, False, False)
        self.col_clickable = (False, True, True)
        self.col_alignment = (False, False, False)

    def shortcuts(self):
        super().shortcuts()
        a1 = QShortcut(QKeySequence('Alt+1'), self, context=Qt.WidgetShortcut)
        a1.activated.connect(self.insert_edit_1)
        a2 = QShortcut(QKeySequence('Alt+2'), self, context=Qt.WidgetShortcut)
        a2.activated.connect(self.insert_edit_2)
        a3 = QShortcut(QKeySequence('Alt+3'), self, context=Qt.WidgetShortcut)
        a3.activated.connect(self.insert_edit_3)
        a4 = QShortcut(QKeySequence('Alt+4'), self, context=Qt.WidgetShortcut)
        a4.activated.connect(self.insert_edit_4)
        a5 = QShortcut(QKeySequence('Alt+5'), self, context=Qt.WidgetShortcut)
        a5.activated.connect(self.insert_edit_5)
        a6 = QShortcut(QKeySequence('Alt+6'), self, context=Qt.WidgetShortcut)
        a6.activated.connect(self.insert_edit_6)
        a7 = QShortcut(QKeySequence('Alt+7'), self, context=Qt.WidgetShortcut)
        a7.activated.connect(self.insert_edit_7)
        a8 = QShortcut(QKeySequence('Alt+8'), self, context=Qt.WidgetShortcut)
        a8.activated.connect(self.insert_edit_8)
        a9 = QShortcut(QKeySequence('Alt+9'), self, context=Qt.WidgetShortcut)
        a9.activated.connect(self.insert_edit_9)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)  # 오버라이드하면서 기본 메서드 재활용
        if e.key() == Qt.Key_Insert:
            insert = self.rows_text_insert(where_to=self.currentRow())
            insert.send(None)
            insert.send(['^', '⌛ 정지 ⌛', ''])
            # self.rows_insert([['^', '⌛ 정지 ⌛', '']], where_to=self.currentRow())
            self.setCurrentCell(self.currentRow() - 1, 1)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.sig_doc_viewer.emit(self.item(self.currentRow(), 0).text())
        elif e.button() == Qt.RightButton:
            pass

    @Slot(int, str)
    def set_error(self, row, text):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.setItem(row, 2, item)
        self.resizeColumnToContents(2)

    @Slot(int)
    def set_current(self, row):
        self.setCurrentCell(row, 1)

    # @Slot(list)
    # def receive_codes_get(self, code_list):  # code list 1d -> code list 2d
    #     if code_list:
    #         self.rows_insert([[code, parse.unquote(code), ''] for code in code_list])
    #         self.after_insert()
    #         self.setCurrentCell(self.rowCount() - 1, 1)
    #         self.setFocus()

    def after_insert(self):
        self.resizeColumnsToContents()
        if self.columnWidth(1) > 450:
            self.setColumnWidth(1, 450)

    @Slot(int)
    def insert_edit_num(self, edit_num):
        where_to = self.currentRow()
        if where_to == -1:
            where_to = 0
        # elif edit_num == 1 and self.item(0, 0).text()[0] != '#':
        #     where_to = 0
        insert = self.rows_text_insert(where_to=where_to)
        insert.send(None)
        insert.send([f'#{edit_num}', f'💡 편집사항 #{edit_num} 💡', ''])
        # self.rows_insert([[f'#{edit_num}', f'💡 편집사항 #{edit_num} 💡', '']], where_to=where_to)
        self.resizeColumnsToContents()
        self.setCurrentCell(self.currentRow() - 1, 1)
        self.setFocus()

    @Slot()
    def insert_edit_1(self):
        self.insert_edit_num(1)

    @Slot()
    def insert_edit_2(self):
        self.insert_edit_num(2)

    @Slot()
    def insert_edit_3(self):
        self.insert_edit_num(3)

    @Slot()
    def insert_edit_4(self):
        self.insert_edit_num(4)

    @Slot()
    def insert_edit_5(self):
        self.insert_edit_num(5)

    @Slot()
    def insert_edit_6(self):
        self.insert_edit_num(6)

    @Slot()
    def insert_edit_7(self):
        self.insert_edit_num(7)

    @Slot()
    def insert_edit_8(self):
        self.insert_edit_num(8)

    @Slot()
    def insert_edit_9(self):
        self.insert_edit_num(9)

    @classmethod
    def dedup(cls, x):
        # return dict.fromkeys(x)
        return list(set(x))

    @Slot(int, int)
    def resize_to_splitter(self, w, _):
        # pass
        vh = self.verticalHeader().width()
        vs = {True: self.verticalScrollBar().width(), False: 0}[self.verticalScrollBar().isVisible()]
        if vh + vs + self.columnWidth(1) + self.columnWidth(2) > w:  # 축소
            self.setColumnWidth(1, w - vh - vs)

        # elif vh + vs + self.columnWidth(1) + self.columnWidth(2) < w:  # 확대
        #     self.setColumnWidth(1, w - vh - vs - self.columnWidth(2) - 2)

    @Slot(int, int, int)
    def resize_section(self, i, ow, nw):
        pass
        # print(i, ow, nw, self.width())
        # vh = self.verticalHeader().width()
        # vs = {True: self.verticalScrollBar().width(), False: 0}[self.verticalScrollBar().isVisible()]

        # print(i, nw - ow, self.columnWidth(1), self.columnWidth(2))

    #     vh, vs = self.verticalHeader().width(), self.verticalScrollBar().width()
    #     if i == 1:
    #         if vh + vs + self.columnWidth(1) + self.columnWidth(2) > self.width():
    #             self.setColumnWidth(1, ow)
    #         else:
    #             self.setColumnWidth(2, self.columnWidth(2) - (nw - ow))
    #         # print(i, vh, vs, self.columnWidth(1), self.columnWidth(2), self.width())


class TableEdit(TableEnhanced):
    sig_insert = Signal(int)

    def __init__(self):
        super().__init__()
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(['순', '1', '2', '3', '4', '내용'])
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.resizeColumnsToContents()
        # self.resizeRowsToContents()
        # self.sizePolicy().setVerticalStretch(7)
        # self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.col_editable = (True, False, False, False, False, True)
        self.col_clickable = (True, True, True, True, True, True)
        self.col_alignment = (Qt.AlignCenter, False, False, False, False, False, False)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)  # 오버라이드하면서 기본 메서드 재활용

        if e.key() == Qt.Key_Insert:
            self.sig_insert.emit(int(self.item(self.currentRow(), 0).text()))

    @classmethod
    def edit_list_rearrange(cls, lists):  # 이중 리스트를 삼중 리스트로 변환
        edit_list = []
        for edit in lists:
            order = int(edit[0])
            while len(edit_list) < order:
                edit_list.append([])
            edit_list[order - 1].append(edit)
        return edit_list

    # @classmethod
    # def edit_list_do_dict(cls, edit_2d):
    #     list_a = []
    #     for edit in edit_2d:
    #         []
    #     pass

    def edits_copy(self):
        return self.edit_list_rearrange(self.rows_copy_text())

    def edits_copy_one(self, pick):
        return self.edit_list_rearrange(self.rows_copy_text())[pick]


class LineEnhanced(QLineEdit):
    focused = Signal()

    def __init__(self):
        super().__init__()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self.focused.emit()

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_Up:
            self.undo()
        elif e.key() == Qt.Key_Down:
            self.redo()


class DocBoard(QWidget):
    sig_doc_code = Signal(str)

    def __init__(self):
        super().__init__()
        self.table_doc = TableDoc()
        self.combo_option = QComboBox(self)
        self.combo_option.addItems(['1개', '역링크', '분류', '이미지'])
        self.combo_option.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_option.currentIndexChanged.connect(self.combo_option_change)
        # self.name_input = QLineEdit()
        self.name_input = LineEnhanced()
        self.name_input.setMinimumWidth(100)
        self.name_input.setPlaceholderText('입력하여 문서 추가')
        self.name_input.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.name_input.returnPressed.connect(self.insert)
        self.name_input.focused.connect(self.invoke_insert_file)
        # self.name_input.textChanged.connect(self.invoke_insert_file)
        box_h = QHBoxLayout()
        box_h.addWidget(self.combo_option)
        box_h.addWidget(self.name_input)
        box_v = QVBoxLayout()
        box_v.addLayout(box_h)
        box_v.addWidget(self.table_doc)
        box_v.setContentsMargins(0, 0, 0, 0)
        self.setLayout(box_v)

    @Slot()
    def insert(self):
        self.sig_doc_code.emit(parse.quote(self.name_input.text()))
        self.name_input.clear()

    @Slot()
    def invoke_insert_file(self):
        if self.combo_option.currentIndex() == 3:
            self.insert_file()

    @Slot(int)
    def combo_option_change(self, i):
        if i == 3:
            self.name_input.setPlaceholderText('클릭하여 파일 불러오기')
        else:
            self.name_input.setPlaceholderText('입력하여 문서 추가')

        if i == 2:  # 분류
            if not self.name_input.text()[0:3] == '분류:':
                self.name_input.setText(f'분류:{self.name_input.text()}')
        else:
            if self.name_input.text() == '분류:':
                self.name_input.clear()

    def insert_file(self):
        insert = self.table_doc.rows_text_insert(editable=[False, True, False])
        insert.send(None)
        name_list = QFileDialog.getOpenFileNames(self, '이미지 열기', './',
                                                 '이미지 파일(*.jpg *.png *.gif *.JPG *.PNG *.GIF)')[0]
        for n in name_list:
            insert.send([f'@{n}', f'파일:{n[n.rfind("/") + 1:n.rfind(".")]}.{n[n.rfind(".") + 1:].lower()}', ''])
        self.table_doc.resizeColumnsToContents()
        self.table_doc.setCurrentCell(self.table_doc.rowCount() - 1, 1)
        self.table_doc.setFocus()


class DocViewer(QWidget):
    # sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        # tab view
        self.tab_view = QWidget()
        self.combo_info = QComboBox()
        self.combo_info.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_info.setEditable(True)
        self.combo_info.setEnabled(False)
        self.combo_info.setInsertPolicy(QComboBox.NoInsert)
        self.btn_edit = QPushButton('편집', self)
        self.btn_edit.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_edit.setMaximumWidth(100)
        self.btn_edit.setEnabled(False)
        self.btn_close = QPushButton('닫기', self)
        self.btn_close.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_close.setMaximumWidth(100)
        self.btn_close.setEnabled(False)
        box_tab_view = QHBoxLayout()
        box_tab_view.addWidget(self.combo_info)
        box_tab_view.addWidget(self.btn_close)
        box_tab_view.addWidget(self.btn_edit)
        box_tab_view.setStretchFactor(self.combo_info, 5)
        box_tab_view.setStretchFactor(self.btn_close, 1)
        box_tab_view.setStretchFactor(self.btn_edit, 1)
        box_tab_view.setContentsMargins(0, 0, 0, 0)
        self.tab_view.setLayout(box_tab_view)
        # tab edit
        self.tab_edit = QWidget()
        self.spin = QSpinBox()
        self.spin.setMinimum(1)
        self.spin.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.spin.setMaximumWidth(100)
        self.btn_apply = QPushButton('적용', self)
        self.btn_apply.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_apply.setMaximumWidth(100)
        self.btn_cancel = QPushButton('취소', self)
        self.btn_cancel.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_cancel.setMaximumWidth(100)
        self.btn_post = QPushButton('전송', self)
        self.btn_post.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_post.setMaximumWidth(100)
        box_tab_edit = QHBoxLayout()
        box_tab_edit.addWidget(self.spin)
        box_tab_edit.addWidget(self.btn_apply)
        box_tab_edit.addStretch(3)
        box_tab_edit.addWidget(self.btn_cancel)
        box_tab_edit.addWidget(self.btn_post)
        box_tab_edit.setStretchFactor(self.spin, 1)
        box_tab_edit.setStretchFactor(self.btn_apply, 1)
        box_tab_edit.setStretchFactor(self.btn_cancel, 1)
        box_tab_edit.setStretchFactor(self.btn_post, 1)
        box_tab_edit.setContentsMargins(0, 0, 0, 0)
        self.tab_edit.setLayout(box_tab_edit)
        # tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.tab_view, '열람')
        self.tabs.addTab(self.tab_edit, '편집')
        self.tabs.tabBar().hide()
        self.tabs.setMaximumHeight(24)
        # viewer
        self.viewer = QTextEdit()
        self.viewer.setPlaceholderText('미리보기 화면')
        # self.viewer.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.viewer.setReadOnly(True)
        # box main
        box_v = QVBoxLayout()
        box_v.addWidget(self.tabs)
        box_v.addWidget(self.viewer)
        box_v.setContentsMargins(0, 0, 0, 0)
        box_v.setSpacing(5)
        self.setLayout(box_v)

    @Slot(str, str, bool)
    def set_text_view(self, code, text, editable):
        self.combo_info.clear()
        self.combo_info.setEnabled(editable)
        if self.combo_info.isEnabled():
            self.combo_info.addItem(parse.unquote(code))
            self.combo_info.addItems(self.get_info(text))
        self.btn_edit.setEnabled(editable)
        self.btn_close.setEnabled(True)
        self.viewer.setPlainText(text)

    @Slot(str)
    def set_text_edit(self, text):
        self.combo_info.clear()
        self.viewer.setReadOnly(False)
        self.tabs.setCurrentWidget(self.tab_edit)
        self.viewer.setPlainText(text)

    @Slot()
    def quit_edit(self, clear):
        self.viewer.setReadOnly(True)
        self.combo_info.clear()
        if clear:
            self.viewer.clear()
            self.combo_info.setEnabled(False)
            self.btn_edit.setEnabled(False)
            self.btn_close.setEnabled(False)
        self.tabs.setCurrentWidget(self.tab_view)

    @classmethod
    def get_info(cls, text):
        return re.findall(r'\[\[(분류: ?.*?)\]\]', text)


class DiffViewer(QWidget):
    sig_send_diff = Signal(int)
    sig_send_diff_micro = Signal(int)

    def __init__(self):
        super().__init__()
        self.browser = QTextBrowser()
        self.browser.setPlaceholderText('텍스트 비교')
        self.btn_yes = QPushButton('실행')
        self.btn_yes_group = QPushButton('그룹 실행')
        self.btn_yes_whole = QPushButton('전체 실행')
        self.btn_no = QPushButton('건너뛰기')
        self.btn_quit = QPushButton('중단')
        self.btn_yes_micro = QPushButton('실행')
        self.btn_no_micro = QPushButton('취소')
        self.btn_yes.clicked.connect(self.yes_clicked)
        self.btn_yes_group.clicked.connect(self.yes_group_clicked)
        self.btn_yes_whole.clicked.connect(self.yes_whole_clicked)
        self.btn_no.clicked.connect(self.no_clicked)
        self.btn_quit.clicked.connect(self.quit_clicked)
        self.btn_yes_micro.clicked.connect(self.yes_micro_clicked)
        self.btn_no_micro.clicked.connect(self.no_micro_clicked)
        # box: macro buttons
        box_macro = QHBoxLayout()
        box_macro.addWidget(self.btn_yes)
        box_macro.addWidget(self.btn_yes_group)
        box_macro.addWidget(self.btn_yes_whole)
        box_macro.addWidget(self.btn_no)
        box_macro.addWidget(self.btn_quit)
        box_macro.setStretchFactor(self.btn_yes, 1)
        box_macro.setStretchFactor(self.btn_yes_group, 1)
        box_macro.setStretchFactor(self.btn_yes_whole, 1)
        box_macro.setStretchFactor(self.btn_no, 1)
        box_macro.setStretchFactor(self.btn_quit, 1)
        box_macro.setContentsMargins(0, 0, 0, 0)
        # box: micro buttons
        box_micro = QHBoxLayout()
        box_micro.addWidget(self.btn_yes_micro)
        box_micro.addStretch(2)
        box_micro.addWidget(self.btn_no_micro)
        box_micro.addStretch(1)
        box_micro.setStretchFactor(self.btn_yes_micro, 1)
        box_micro.setStretchFactor(self.btn_no_micro, 1)
        box_micro.setContentsMargins(0, 0, 0, 0)
        # tabs
        self.tabs = QTabWidget()
        self.tab_macro = QWidget()
        self.tab_macro.setLayout(box_macro)
        self.tab_micro = QWidget()
        self.tab_micro.setLayout(box_micro)
        self.tabs.addTab(self.tab_macro, '')
        self.tabs.addTab(self.tab_micro, '')
        self.tabs.tabBar().hide()
        self.tabs.setMaximumHeight(24)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 0;}
            """)

        # vertical
        box_v = QVBoxLayout()
        box_v.addWidget(self.browser)
        box_v.addWidget(self.tabs)
        box_v.setContentsMargins(0, 0, 0, 0)
        box_v.setSpacing(5)
        self.setLayout(box_v)

    @Slot()
    def yes_clicked(self):
        self.sig_send_diff.emit(1)

    @Slot()
    def yes_group_clicked(self):
        self.sig_send_diff.emit(2)

    @Slot()
    def yes_whole_clicked(self):
        self.sig_send_diff.emit(3)

    @Slot()
    def no_clicked(self):
        self.sig_send_diff.emit(4)

    @Slot()
    def quit_clicked(self):
        self.sig_send_diff.emit(5)

    @Slot()
    def yes_micro_clicked(self):
        self.sig_send_diff_micro.emit(1)

    @Slot()
    def no_micro_clicked(self):
        self.sig_send_diff_micro.emit(4)


class ImgViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.line_info = QLineEdit()
        self.line_info.setReadOnly(True)
        self.line_info.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.line_info.setPlaceholderText('파일 경로')
        self.label_img = QLabel()
        self.label_img.setBaseSize(300, 200)
        self.label_img.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label_img.setAlignment(Qt.AlignCenter)
        self.label_img.setStyleSheet('border: 1px solid gray;')
        self.btn_close = QPushButton('닫기')
        self.btn_close.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_close.setMaximumWidth(100)
        box_h = QHBoxLayout()
        box_h.addWidget(self.line_info)
        box_h.addWidget(self.btn_close)
        box_h.setStretchFactor(self.line_info, 5)
        box_h.setStretchFactor(self.btn_close, 1)
        box_v = QVBoxLayout()
        box_v.addLayout(box_h)
        box_v.addWidget(self.label_img)
        box_v.setContentsMargins(0, 0, 0, 0)
        box_v.setSpacing(5)
        self.setLayout(box_v)


class TabViewers(QTabWidget):
    sig_main_label = Signal(str)
    sig_diff_done = Signal(int)
    sig_diff_micro_done = Signal(int)

    def __init__(self):
        super().__init__()
        self.doc_viewer = DocViewer()
        self.diff_viewer = DiffViewer()
        self.img_viewer = ImgViewer()
        self.addTab(self.doc_viewer, '보기')
        self.addTab(self.diff_viewer, '비교')
        self.addTab(self.img_viewer, '이미지')
        self.diff_viewer.sig_send_diff.connect(self.close_diff)
        self.diff_viewer.sig_send_diff_micro.connect(self.close_diff_micro)
        self.img_viewer.btn_close.clicked.connect(self.close_image)
        self.tabBar().hide()
        self.setStyleSheet("""
            QTabWidget::pane {
            border: 0;
            }
            """)

    @Slot(str)
    def show_diff(self, diff_html):
        self.diff_viewer.tabs.setCurrentWidget(self.diff_viewer.tab_macro)
        # self.diff_viewer.show_html(diff_html)
        self.diff_viewer.browser.setHtml(diff_html)
        self.setCurrentWidget(self.diff_viewer)

    @Slot(str)
    def show_diff_micro(self, diff_html):
        self.diff_viewer.tabs.setCurrentWidget(self.diff_viewer.tab_micro)
        # self.diff_viewer.show_html(diff_html)
        self.diff_viewer.browser.setHtml(diff_html)
        self.setCurrentWidget(self.diff_viewer)

    @Slot(int)
    def close_diff(self, done):
        if done == 2 or done == 3 or done == 5:  # 비교 탭 다시 볼 필요 없음
            self.setCurrentWidget(self.doc_viewer)
            self.diff_viewer.browser.clear()
        self.sig_diff_done.emit(done)
        # self.iterate_post.diff_done = done

    @Slot(int)
    def close_diff_micro(self, done):
        self.setCurrentWidget(self.doc_viewer)
        self.diff_viewer.browser.clear()
        self.sig_diff_micro_done.emit(done)

    @Slot(str)
    def show_image(self, f):
        self.img_viewer.btn_close.setEnabled(True)
        pic = QPixmap(f)
        if pic.isNull():
            self.img_viewer.line_info.setText(f'파일을 찾을 수 없습니다.')
            self.img_viewer.label_img.clear()
        else:
            self.img_viewer.line_info.setText(f)
            self.img_viewer.line_info.setCursorPosition(0)
            if pic.width() < self.width() and pic.height() < self.height() - 32:
                self.img_viewer.label_img.setPixmap(pic)
            else:
                self.img_viewer.label_img.setPixmap(pic.scaled(self.width(), self.height() - 32, Qt.KeepAspectRatio))
        if not self.currentWidget == self.img_viewer:
            self.setCurrentWidget(self.img_viewer)

    def close_image(self):
        self.img_viewer.line_info.clear()
        self.img_viewer.label_img.clear()
        self.img_viewer.btn_close.setEnabled(False)
        self.sig_main_label.emit('파일을 닫았습니다.')


class EditEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.ss = core.SeedSession()
        box_edit = QVBoxLayout()
        box_edit_combos = QHBoxLayout()
        # table edit
        self.table_edit = TableEdit()
        self.table_edit.setStyleSheet('font: 10pt \'Segoe UI\'')
        # edit options
        self.spin_1 = QSpinBox()
        self.spin_1.setMinimum(1)
        self.spin_1.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_opt1 = QComboBox()
        self.combo_opt1.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_opt1_text = ['일반', '파일', '기타', '요약', '복구']
        self.combo_opt1.addItems(self.combo_opt1_text)
        self.combo_opt2 = QComboBox()
        self.combo_opt2.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_opt2_text = ['', 'if', 'then']
        self.combo_opt2.addItems(self.combo_opt2_text)
        self.combo_opt2.setEnabled(False)
        self.combo_opt3 = QComboBox()
        self.combo_opt3.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_opt3_1_text = ['찾기', '바꾸기', '넣기']
        self.combo_opt3_2_text = ['본문', '라이선스', '분류']
        self.combo_opt3.addItems(self.combo_opt3_1_text)
        self.combo_opt4 = QComboBox()
        self.combo_opt4.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_opt4_1_1_text = ['텍스트', '정규식']
        self.combo_opt4_1_3_text = ['맨 앞', '맨 뒤', '분류']
        self.combo_opt4_2_1_text = ['설명', '출처', '날짜', '저작자', '기타']
        self.combo_opt4_2_2_text = []
        self.combo_opt4_2_3_text = []
        self.combo_opt4.addItems(self.combo_opt4_1_1_text)
        self.combo_opt1.currentTextChanged.connect(self.combo_opt1_change)
        self.combo_opt2.currentTextChanged.connect(self.combo_opt2_change)
        self.combo_opt3.currentTextChanged.connect(self.combo_opt3_change)
        self.combo_opt4.currentTextChanged.connect(self.combo_opt4_change)
        #
        box_edit_combos.addWidget(self.spin_1)
        box_edit_combos.addWidget(self.combo_opt1)
        box_edit_combos.addWidget(self.combo_opt2)
        box_edit_combos.addWidget(self.combo_opt3)
        box_edit_combos.addWidget(self.combo_opt4)
        box_edit_combos.setStretchFactor(self.spin_1, 1)
        box_edit_combos.setStretchFactor(self.combo_opt1, 1)
        box_edit_combos.setStretchFactor(self.combo_opt2, 1)
        box_edit_combos.setStretchFactor(self.combo_opt3, 1)
        box_edit_combos.setStretchFactor(self.combo_opt4, 1)
        #
        self.edit_input = LineEnhanced()
        self.edit_input.setStyleSheet('font: 10.5pt \'Segoe UI\'')
        self.edit_input.returnPressed.connect(self.add_to_edit)

        box_edit.addWidget(self.table_edit)
        box_edit.addLayout(box_edit_combos)
        box_edit.addWidget(self.edit_input)
        box_edit.setContentsMargins(0, 0, 0, 0)
        box_edit.setSpacing(5)
        self.setLayout(box_edit)

    @Slot(str)
    def combo_opt1_change(self, t):
        if t == '일반':  # 일반
            self.combo_opt3.setEnabled(True)
            self.combo_opt4.setEnabled(True)
            self.combo_opt3.clear()
            self.combo_opt3.addItems(self.combo_opt3_1_text)
        elif t == '파일':  # 파일
            lic, cat = self.combo_image()
            self.combo_opt4_2_2_text = lic  # 라이선스
            self.combo_opt4_2_3_text = cat  # 파일 분류
            self.combo_opt3.setEnabled(True)
            self.combo_opt4.setEnabled(True)
            self.combo_opt3.clear()
            self.combo_opt3.addItems(self.combo_opt3_2_text)
        elif t == '기타' or t == '요약' or t == '복구':
            self.combo_opt3.setEnabled(False)
            self.combo_opt4.setEnabled(False)
            self.combo_opt3.clear()
            self.combo_opt4.clear()

    @Slot(str)
    def combo_opt2_change(self, t):
        pass

    @Slot(str)
    def combo_opt3_change(self, t):
        if t == '찾기' or t == '바꾸기':
            self.combo_opt4.clear()
            self.combo_opt4.addItems(self.combo_opt4_1_1_text)
            if t == '찾기':
                self.combo_opt4.setEnabled(True)
            elif t == '바꾸기':
                self.combo_opt4.setEnabled(False)
        elif t == '넣기':
            self.combo_opt4.setEnabled(True)
            self.combo_opt4.clear()
            self.combo_opt4.addItems(self.combo_opt4_1_3_text)
        elif t == '본문':
            self.combo_opt4.clear()
            self.combo_opt4.addItems(self.combo_opt4_2_1_text)
            self.edit_input.clear()
        elif t == '라이선스':
            self.combo_opt4.clear()
            self.combo_opt4.addItems(self.combo_opt4_2_2_text)
        elif t == '분류':
            self.combo_opt4.clear()
            self.combo_opt4.addItems(self.combo_opt4_2_3_text)

    @Slot(str)
    def combo_opt4_change(self, t):
        opt3 = self.combo_opt3.currentText()
        if opt3 == '라이선스' or opt3 == '분류':
            self.edit_input.setText(t)

    def combo_image(self):
        soup = self.ss.request_soup(f'{core.SITE_URL}/Upload', 'get')
        lic = [t.text for t in soup.select('#licenseSelect > option')]
        lic.insert(0, lic.pop(-1))  # 제한적 이용 맨 앞으로
        cat = [t.attrs['value'][3:] for t in soup.select('#categorySelect > option')]
        return lic, cat

    @Slot()
    def add_to_edit(self):
        # 값 추출
        opt1 = self.combo_opt1.currentText()
        opt2 = self.combo_opt2.currentText()
        if self.combo_opt3.isEnabled():
            opt3 = self.combo_opt3.currentText()
        else:
            opt3 = ''
        if self.combo_opt4.isEnabled():
            if opt3 == '라이선스' or opt3 == '분류':
                opt4 = ''
            else:
                opt4 = self.combo_opt4.currentText()
        else:
            opt4 = ''
        insert = self.table_edit.rows_text_insert()
        insert.send(None)
        insert.send([str(self.spin_1.value()), opt1, opt2, opt3, opt4, self.edit_input.text()])
        # self.table_edit.rows_insert([[str(self.spin_1.value()), opt1, opt2, opt3, opt4, self.edit_input.text()]])
        self.table_edit.resizeColumnsToContents()
        self.table_edit.setCurrentCell(self.table_edit.rowCount() - 1, 1)
        # 입력 후
        self.edit_input.clear()
        if opt1 == '일반':
            if opt3 == '바꾸기':
                self.combo_opt3.setCurrentText('찾기')
            elif opt3 == '찾기':
                self.combo_opt3.setCurrentText('바꾸기')


if __name__ == '__main__':
    print(process.memory_info().rss / 1024 / 1024)
    storage.new_setting()
    app = QApplication(sys.argv)
    # app.setStyle('fusion')
    win = MainWindow()
    win.show()
    print(process.memory_info().rss / 1024 / 1024)
    sys.exit(app.exec_())
