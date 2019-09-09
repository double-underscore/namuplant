import sys
import os
import re
import time
import psutil
from urllib import parse
import mouse
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QDialog, QAction, QShortcut, QPushButton, QLabel
from PySide2.QtWidgets import QComboBox, QSpinBox, QLineEdit, QTextEdit, QTabWidget, QSplitter, QVBoxLayout, QHBoxLayout
from PySide2.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QTableWidgetSelectionRange, QFileDialog
from PySide2.QtWidgets import QTextBrowser, QFrame, QSizePolicy, QStatusBar
from PySide2.QtGui import QIcon, QColor, QFont, QKeySequence, QStandardItem, QStandardItemModel
from PySide2.QtCore import Qt, QUrl, QThread, QObject, Slot, Signal
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet('font: 10pt \'맑은 고딕\';'
                           'color: #373a3c')
        self.resize(800, 800)
        # self.setWindowTitle('namuplant')
        # self.setWindowIcon(QIcon('icon.png'))
        # 액션
        act_image = QAction('이미지 업로드', self)
        act_image.triggered.connect(self.action_image)
        act_test = QAction(QIcon('icon.png'), '실험', self)
        act_test.triggered.connect(self.action_test)
        act_memory = QAction('점유 메모리', self)
        act_memory.triggered.connect(self.action_memory)
        # 메뉴
        menu_bar = self.menuBar()
        menu_file = menu_bar.addMenu('&File')
        menu_file.addAction(act_image)
        menu_file.addAction(act_memory)
        menu_file.addAction(act_test)
        # 메인
        self.main_widget = MainWidget()
        self.setCentralWidget(self.main_widget)



        self.read_doc_list_csv()
        self.show()

    def read_doc_list_csv(self):
        docs, edits = storage.read_list_csv('doc_list.csv')
        t_m = self.main_widget.tab_macro
        t_m.doc_inventory.table_doc.insert_items(docs, [False, False, False])
        t_m.edit_editor.table_edit.insert_items(edits)
        # t_m.doc_inventory.table_doc.setcurrent

    def write_doc_list_csv(self):
        t_m = self.main_widget.tab_macro
        docs = t_m.doc_inventory.table_doc.rows_copy_text(range(t_m.doc_inventory.table_doc.rowCount()))
        edits = t_m.edit_editor.table_edit.edits_copy()

        storage.write_list_csv('doc_list.csv', docs, edits)

    def closeEvent(self, event):
        self.write_doc_list_csv()

    def action_test(self):
        # print('th_micro: ', self.main_widget.tab_macro.th_micro.isRunning())
        # print(process.memory_info().rss / 1024 / 1024)
        # self.main_widget.ddos_dialog.browser.load(QUrl('https://m.naver.com'))
        # self.main_widget.ddos_dialog.show()
        pass

    @classmethod
    def action_memory(cls):
        print(process.memory_info().rss / 1024 / 1024)

    def action_image(self):
        name_list = QFileDialog.getOpenFileNames(self, '이미지 열기', './', '이미지 파일(*.jpg *.png *.gif *.JPG *.PNG *.GIF)')[0]
        t_d = self.main_widget.tab_macro.doc_inventory.table_doc
        t_d.insert_items([[f'@{n}',
                          f'파일:{n[n.rfind("/") + 1:n.rfind(".")]}.{n[n.rfind(".") + 1:].lower()}',
                          f'{n[n.rfind("/") + 1:]}'] for n in name_list
                          ],
                         [False, True, False])


class CheckDdos(QDialog):

    def __init__(self):
        super().__init__()
        self.label = QLabel('reCAPTCHA 해결 후 완료 버튼을 눌러주세요.')
        self.label.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.browser = QWebEngineView()

        self.btn = QPushButton('완료')
        self.btn.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn.clicked.connect(self.accept)

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
        self.ddos_dialog = CheckDdos()
        self.tab_macro.req_get.sig_check_ddos.connect(self.show_ddos_dialog)
        self.tab_macro.iterate_post.sig_check_ddos.connect(self.show_ddos_dialog)
        self.tab_macro.micro_post.sig_check_ddos.connect(self.show_ddos_dialog)
        self.tab_macro.edit_editor.ss.sig_check_ddos.connect(self.show_ddos_dialog)

    @Slot(str)
    def set_main_label(self, t):
        self.main_label.setText(t)

    @Slot(object)
    def show_ddos_dialog(self, obj):
        self.ddos_dialog.browser.load(QUrl(f'{core.site_url}/404'))
        ddd = self.ddos_dialog.exec_()
        if ddd == QDialog.Accepted:
            obj.is_ddos_checked = True


class TabMacro(QWidget):
    sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        self.doc_inventory = DocInventory()
        self.tabs_viewer = TabViewers()
        self.edit_editor = EditEditor()
        # last row: get link
        self.combo_get_activate = QComboBox(self)
        self.combo_get_activate.addItems(['右 ON', '右 OFF'])
        self.combo_get_activate.setCurrentIndex(1)
        self.combo_get_activate.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_get_activate.setMaximumWidth(100)
        # last row: main work
        self.combo_speed = QComboBox(self)
        self.combo_speed.addItems(['고속', '저속'])
        self.combo_speed.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_speed.setMaximumWidth(100)
        self.combo_speed.currentIndexChanged.connect(self.iterate_speed_change)
        # todo 스피드 옵션 이터레이트 즉시 반응 - 작동 확인 필요
        self.btn_do = QPushButton('시작', self)
        self.btn_do.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_do.setMaximumWidth(100)
        self.btn_pause = QPushButton('정지', self)
        self.btn_pause.setStyleSheet('font: 10pt \'맑은 고딕\'')
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
        split_h.setStyleSheet("""
            QSplitter::handle {
                background-color: #eeeedd;
                }
            """)
        split_h.addWidget(self.doc_inventory)
        split_h.addWidget(split_v)
        split_h.setStretchFactor(0, 1)
        split_h.setStretchFactor(1, 1)

        # box last row
        box_last_row = QHBoxLayout()
        box_last_row.addWidget(self.combo_get_activate)
        box_last_row.addStretch(6)
        box_last_row.addWidget(self.combo_speed)
        box_last_row.addWidget(self.btn_do)
        box_last_row.addWidget(self.btn_pause)
        box_last_row.setStretchFactor(self.combo_get_activate, 1)
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
        self.doc_inventory.table_doc.sig_main_label.connect(self.str_to_main)
        self.doc_inventory.table_doc.sig_doc_viewer.connect(self.micro_view)
        self.tabs_viewer.doc_viewer.sig_main_label.connect(self.str_to_main)
        self.edit_editor.table_edit.sig_insert.connect(self.doc_inventory.table_doc.insert_edit_num)
        self.btn_do.clicked.connect(self.iterate_start)
        self.btn_pause.clicked.connect(self.thread_quit)
        # thread get_click
        mouse.on_right_click(self.get_start)
        self.th_get = QThread()
        self.req_get = core.ReqGet()
        self.req_get.finished.connect(self.get_finish)
        self.req_get.sig_label_text.connect(self.str_to_main)
        self.req_get.send_code_list.connect(self.doc_inventory.table_doc.receive_codes_get)
        self.doc_inventory.sig_doc_code.connect(self.get_by_input)
        self.req_get.moveToThread(self.th_get)
        self.th_get.started.connect(self.req_get.work)
        # thread iterate
        self.th_iterate = QThread()
        self.iterate_post = core.Iterate()
        self.iterate_post.finished.connect(self.iterate_finish)
        self.iterate_post.sig_label_text.connect(self.str_to_main)
        self.iterate_post.sig_doc_remove.connect(self.doc_inventory.table_doc.removeRow)
        self.iterate_post.sig_doc_set_current.connect(self.doc_inventory.table_doc.set_current)
        self.iterate_post.sig_doc_error.connect(self.doc_inventory.table_doc.set_error)
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
        self.micro_post.sig_enable_iterate.connect(self.micro_enable_iterate)
        self.micro_post.sig_view_diff.connect(self.tabs_viewer.show_diff_micro)
        self.tabs_viewer.sig_diff_micro_done.connect(self.micro_post.receive_diff_done)
        self.tabs_viewer.doc_viewer.btn_edit.clicked.connect(self.micro_edit)
        self.tabs_viewer.doc_viewer.btn_apply.clicked.connect(self.micro_apply)
        self.tabs_viewer.doc_viewer.btn_post.clicked.connect(self.micro_text_post)
        self.tabs_viewer.doc_viewer.btn_cancel.clicked.connect(self.micro_back)
        self.th_micro.started.connect(self.micro_post.work)
        self.micro_post.moveToThread(self.th_micro)

    @Slot(str)
    def str_to_main(self, t):
        self.sig_main_label.emit(t)

    @Slot()
    def thread_quit(self):
        if self.th_iterate.isRunning():
            self.iterate_post.is_quit = True
        elif self.th_get.isRunning():
            self.req_get.is_quit = True
        self.str_to_main('정지 버튼을 눌렀습니다.')

    @Slot()
    def get_start(self):
        if self.combo_get_activate.currentIndex() == 0:  # 우클릭 모드 ON
            self.req_get.mode = 1
            self.btn_do.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.req_get.option = self.doc_inventory.combo_option.currentIndex()
            self.th_get.start()

    @Slot(str)
    def get_by_input(self, code):
        self.req_get.mode = 0
        self.req_get.code = code
        self.btn_do.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.req_get.option = self.doc_inventory.combo_option.currentIndex()
        self.th_get.start()

    @Slot()
    def get_finish(self):
        self.th_get.quit()
        self.req_get.is_quit = False
        self.btn_do.setEnabled(True)
        self.btn_pause.setEnabled(False)

    @Slot()
    def iterate_start(self):
        self.btn_do.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.iterate_post.doc_list = self.doc_inventory.table_doc.rows_copy_text(
            range(self.doc_inventory.table_doc.rowCount()))
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
    def micro_edit(self):
        self.micro_post.mode = 1
        self.th_micro.start()

    @Slot()
    def micro_apply(self):
        edit_list = self.edit_editor.table_edit.edits_copy_one(self.tabs_viewer.doc_viewer.spin.value() - 1)
        text = self.tabs_viewer.doc_viewer.viewer.toPlainText()
        self.tabs_viewer.doc_viewer.viewer.setText(self.micro_post.apply(text, edit_list))

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
            self.tabs_viewer.doc_viewer.quit_edit()
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
        # self.verticalHeader().setSectionsClickable(False)

        self.shortcuts()

    def keyPressEvent(self, e):
        # todo 목록에 있는 거 지우면 미리보기도 없애기
        super().keyPressEvent(e)  # 오버라이드하면서 기본 메서드 재활용

        if e.key() == Qt.Key_Return:
            self.sig_main_label.emit(self.currentItem().text())

        elif e.key() == Qt.Key_Home:
            self.test()

        elif e.key() == Qt.Key_Delete:  # 지우기
            self.setUpdatesEnabled(False)
            col_origin = self.currentColumn()
            rows_selected = self.rows_selected()
            if rows_selected:
                # self.sig_deleted_rows.emit(rows_selected)
                self.rows_delete(rows_selected)
                pos_after = rows_selected[-1] - len(rows_selected)
                added = 0 if self.rowCount() - 1 == pos_after else 1
                self.setCurrentCell(pos_after + added, col_origin)
            self.setUpdatesEnabled(True)

    def shortcuts(self):
        move_up = QShortcut(QKeySequence('Ctrl+Shift+Up'), self, context=Qt.WidgetShortcut)
        move_up.activated.connect(self.method_move_up)  # 한 칸 위로
        move_down = QShortcut(QKeySequence('Ctrl+Shift+Down'), self, context=Qt.WidgetShortcut)
        move_down.activated.connect(self.method_move_down)  # 한 칸 아래로
        move_up = QShortcut(QKeySequence('Ctrl+Shift+Left'), self, context=Qt.WidgetShortcut)
        move_up.activated.connect(self.method_move_top)  # 맨 위로
        move_up = QShortcut(QKeySequence('Ctrl+Shift+Right'), self, context=Qt.WidgetShortcut)
        move_up.activated.connect(self.method_move_bottom)  # 맨 아래로

    def method_move_up(self):
        self.rows_move(1)

    def method_move_down(self):
        self.rows_move(2)

    def method_move_top(self):
        self.rows_move(3)

    def method_move_bottom(self):
        self.rows_move(4)

    def rows_selected(self):
        col_origin = self.currentColumn()
        if self.selectedItems():
            return sorted([i.row() for i in self.selectedItems() if i.column() == col_origin])

    def rows_delete(self, rows_list):
        deleted = 0
        if rows_list:
            for r in rows_list:
                self.removeRow(r - deleted)
                deleted += 1

    def rows_copy_text(self, rows_list):  # table item -> text
        return [[self.item(r, c).text() for c in range(self.columnCount())] for r in rows_list]

    def rows_copy_item(self, rows_list):  # table item -> table item
        return [[self.item(r, c) for c in range(self.columnCount())] for r in rows_list]

    def rows_paste(self, copied_list, row_to_paste):  # to be deprecated
        copied_list.reverse()
        for i in range(len(copied_list)):
            self.insertRow(row_to_paste)
            for c in range(self.columnCount()):
                self.setItem(row_to_paste, c, QTableWidgetItem(copied_list[i][c]))

    def test(self):
        # a = [self.item(0, 0), self.item(0, 1), self.item(0, 2)]
        # self.insertRow(self.rowCount())
        # for i in range(len(a)):
        #     self.setItem(self.rowCount() - 1, i, a[i])
        s = self.item(0, 1)
        self.setItem(1, 1, QTableWidgetItem(s))

    def rows_paste_item(self, copied_item_list, row_to_paste):  # table item -> table item
        copied_item_list.reverse()
        for i in range(len(copied_item_list)):
            self.insertRow(row_to_paste)
            for c in range(self.columnCount()):
                self.setItem(row_to_paste, c, copied_item_list[i][c])

    def rows_insert(self, copied_text_list, col_editable, row_to_insert):  # text -> table item
        # todo 테이블 열별 editable
        copied_text_list.reverse()
        for i in range(len(copied_text_list)):
            self.insertRow(row_to_insert)
            for c in range(self.columnCount()):
                item = QTableWidgetItem(copied_text_list[i][c])
                if not col_editable[c]:  # false면 플래그 제거
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.setItem(row_to_insert, c, item)

    def rows_move(self, where_to):
        self.setUpdatesEnabled(False)
        col_origin = self.currentColumn()
        rows_selected = self.rows_selected()
        row_where_to = 0
        items = self.rows_copy_text(rows_selected)
        # 일단 지우고
        self.rows_delete(rows_selected)
        # 이동할 위치
        if where_to == 1:  # 한 칸 위로
            if rows_selected[0] == 0:  # 첫 줄이었으면
                row_where_to = 0
            else:
                row_where_to = rows_selected[0] - 1
        elif where_to == 2:  # 한 칸 아래로
            row_last = rows_selected[-1]
            if row_last - len(rows_selected) == self.rowCount() - 1:  # 마지막 줄이었으면
                row_where_to = self.rowCount()  # - 1 - deletes['deleted']
            else:
                row_where_to = row_last + 2 - len(rows_selected)
        elif where_to == 3:  # 맨 위로
            row_where_to = 0
        elif where_to == 4:  # 맨 아래로
            row_where_to = self.rowCount()
        # 새로운 current cell과 selection
        self.rows_paste(items, row_where_to)
        if where_to == 1 or where_to == 3:
            self.setCurrentCell(row_where_to, col_origin)
        elif where_to == 2 or where_to == 4:
            self.setCurrentCell(row_where_to + len(rows_selected) - 1, col_origin)
        range_to_select = QTableWidgetSelectionRange(row_where_to, 0,
                                                     row_where_to + len(rows_selected) - 1, self.columnCount() - 1)
        self.setRangeSelected(range_to_select, True)
        self.setUpdatesEnabled(True)


class TableDoc(TableEnhanced):
    sig_doc_viewer = Signal(str)

    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['코드', '표제어', '비고'])
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setStyleSheet('font: 7pt \'맑은 고딕\'')
        self.horizontalScrollBar().setVisible(True)
        self.hideColumn(0)
        # self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)  # 오버라이드하면서 기본 메서드 재활용

        if e.key() == Qt.Key_Insert:
            r = self.currentRow()
            self.insert_items([['^', '⌛ 정지 ⌛', '']], [False, False, False], r)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.sig_doc_viewer.emit(self.item(self.currentRow(), 0).text())
        elif e.button() == Qt.RightButton:
            pass

    @Slot(int, str)
    def set_error(self, row, text):
        self.setItem(row, 2, QTableWidgetItem(text))
        self.resizeColumnToContents(2)

    @Slot(int)
    def set_current(self, row):
        self.setCurrentCell(row, 1)

    @Slot(list)
    def receive_codes_get(self, code_list):  # code list 1d -> code list 2d
        if code_list:
            self.insert_items([[code, parse.unquote(code), ''] for code in code_list],
                              [False, False, False])

    def insert_items(self, list_2d, col_editable, row_to_insert=0):
        if not row_to_insert:
            row_to_insert = self.rowCount()
        self.rows_insert(list_2d, col_editable, row_to_insert)
        # self.setCurrentCell(row_to_insert - 1, 1)
        self.resizeColumnToContents(1)
        if self.columnWidth(1) > 450:
            self.setColumnWidth(1, 450)

    @Slot(str)
    def insert_edit_num(self, edit_num):
        row_insert = self.currentRow()
        if row_insert == -1:
            row_insert = 0
        elif int(edit_num) == 1 and self.item(0, 0).text()[0] != '#':
            row_insert = 0
        self.insertRow(row_insert)
        self.setItem(row_insert, 0, QTableWidgetItem(f'#{edit_num}'))
        self.setItem(row_insert, 1, QTableWidgetItem(f'💡 편집사항 #{edit_num} 💡'))
        self.setItem(row_insert, 2, QTableWidgetItem(''))
        self.resizeColumnToContents(1)

    @classmethod
    def dedup(cls, x):
        # return dict.fromkeys(x)
        return list(set(x))


class TableEdit(TableEnhanced):
    sig_insert = Signal(str)

    def __init__(self):
        super().__init__()
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(['순', '1', '2', '3', '4', '내용'])
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.resizeColumnsToContents()

        # self.resizeRowsToContents()
        # self.sizePolicy().setVerticalStretch(7)
        # self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)  # 오버라이드하면서 기본 메서드 재활용

        if e.key() == Qt.Key_Insert:
            self.sig_insert.emit(self.item(self.currentRow(), 0).text())

    def insert_items(self, item_list):
        self.rows_paste(item_list, self.rowCount())  # ?
        self.setCurrentCell(self.rowCount() - 1, 1)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    @classmethod
    def edit_list_rearrange(cls, lists):  # 이중 리스트를 삼중 리스트로 변환
        edit_list = []
        for edit in lists:
            order = int(edit[0])
            while len(edit_list) < order:
                edit_list.append([])
            edit_list[order - 1].append(edit)
        return edit_list

    @classmethod
    def edit_list_do_dict(cls, edit_2d):
        list_a = []
        for edit in edit_2d:
            []
        pass

    def edits_copy(self):
        return self.edit_list_rearrange(self.rows_copy_text(range(self.rowCount())))

    def edits_copy_one(self, pick):
        return self.edit_list_rearrange(self.rows_copy_text(range(self.rowCount())))[pick]


class DocInventory(QWidget):
    sig_doc_code = Signal(str)

    def __init__(self):
        super().__init__()
        self.table_doc = TableDoc()
        self.combo_option = QComboBox(self)
        self.combo_option.addItems(['1개', '역링크', '분류'])
        self.combo_option.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_option.currentTextChanged.connect(self.combo_option_change)

        self.name_input = QLineEdit()
        self.name_input.setMinimumWidth(100)
        self.name_input.setPlaceholderText('문서 추가')
        self.name_input.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.name_input.returnPressed.connect(self.insert)
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

    @Slot(str)
    def combo_option_change(self, t):
        if t == '분류':
            if not self.name_input.text()[0:3] == '분류:':
                self.name_input.setText(f'분류:{self.name_input.text()}')
        else:
            if self.name_input.text() == '분류:':
                self.name_input.clear()


class DocViewer(QWidget):
    sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        # tab view
        self.tab_view = QWidget()
        box_tab_view = QHBoxLayout()
        self.combo_info = QComboBox()
        self.combo_info.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.combo_info.setEnabled(False)
        self.btn_edit = QPushButton('편집', self)
        self.btn_edit.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_edit.setEnabled(False)
        box_tab_view.addWidget(self.combo_info)
        box_tab_view.addWidget(self.btn_edit)
        box_tab_view.setStretchFactor(self.combo_info, 4)
        box_tab_view.setStretchFactor(self.btn_edit, 1)
        box_tab_view.setContentsMargins(0, 0, 0, 0)
        self.tab_view.setLayout(box_tab_view)
        # tab edit
        self.tab_edit = QWidget()
        box_tab_edit = QHBoxLayout()
        self.spin = QSpinBox()
        self.spin.setMinimum(1)
        self.btn_apply = QPushButton('적용', self)
        self.btn_cancel = QPushButton('취소', self)
        self.btn_post = QPushButton('전송', self)
        box_tab_edit.addWidget(self.spin)
        box_tab_edit.addWidget(self.btn_apply)
        box_tab_edit.addStretch(1)
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
        self.tabs.addTab(self.tab_view, '')
        self.tabs.addTab(self.tab_edit, '')
        self.tabs.tabBar().hide()
        self.tabs.setMaximumHeight(24)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 0;
            }
            """)
        # viewer
        self.viewer = QTextEdit()
        self.viewer.setPlaceholderText('미리보기 화면')
        self.viewer.setReadOnly(True)
        # box main
        box_v = QVBoxLayout()
        box_v.addWidget(self.tabs)
        box_v.addWidget(self.viewer)
        box_v.setStretchFactor(self.tabs, 1)
        box_v.setStretchFactor(self.viewer, 9)
        box_v.setContentsMargins(0, 0, 0, 0)
        self.setLayout(box_v)

    @Slot(str, str, bool)
    def set_text_view(self, code, text, editable):
        self.combo_info.clear()
        self.combo_info.setEnabled(editable)
        if self.combo_info.isEnabled():
            self.combo_info.addItem(parse.unquote(code))
            self.combo_info.addItems(self.get_info(text))
        self.btn_edit.setEnabled(editable)
        self.viewer.setText(text)

    @Slot(str)
    def set_text_edit(self, text):
        self.combo_info.clear()
        self.viewer.setReadOnly(False)
        self.tabs.setCurrentWidget(self.tab_edit)
        self.viewer.setText(text)

    @Slot()
    def quit_edit(self):
        self.viewer.setReadOnly(True)
        self.combo_info.clear()
        # self.viewer.clear()
        # self.combo_info.setEnabled(False)
        # self.btn_edit.setEnabled(False)
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

    @Slot(str)
    def show_html(self, t):
        self.browser.setHtml(t)


class TabViewers(QTabWidget):
    sig_diff_done = Signal(int)
    sig_diff_micro_done = Signal(int)

    def __init__(self):
        super().__init__()
        self.doc_viewer = DocViewer()
        self.diff_viewer = DiffViewer()
        self.addTab(self.doc_viewer, '  보기  ')
        self.addTab(self.diff_viewer, '  비교  ')
        self.diff_viewer.sig_send_diff.connect(self.close_diff)
        self.diff_viewer.sig_send_diff_micro.connect(self.close_diff_micro)
        self.tabBar().hide()
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 0;}
            """)

    @Slot(str)
    def show_diff(self, diff_html):
        self.diff_viewer.tabs.setCurrentWidget(self.diff_viewer.tab_macro)
        self.diff_viewer.show_html(diff_html)
        self.setCurrentWidget(self.diff_viewer)

    @Slot(str)
    def show_diff_micro(self, diff_html):
        self.diff_viewer.tabs.setCurrentWidget(self.diff_viewer.tab_micro)
        self.diff_viewer.show_html(diff_html)
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
        self.combo_opt1 = QComboBox()
        self.combo_opt1_text = ['일반', '파일', '기타', '요약', '복구']
        self.combo_opt1.addItems(self.combo_opt1_text)
        self.combo_opt2 = QComboBox()
        self.combo_opt2_text = ['', 'if', 'then']
        self.combo_opt2.addItems(self.combo_opt2_text)
        self.combo_opt2.setEnabled(False)
        self.combo_opt3 = QComboBox()
        self.combo_opt3_1_text = ['찾기', '바꾸기', '넣기']
        self.combo_opt3_2_text = ['본문', '라이선스', '분류']
        self.combo_opt3.addItems(self.combo_opt3_1_text)
        self.combo_opt4 = QComboBox()
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
        self.edit_input = QLineEdit()
        self.edit_input.setStyleSheet('font: 10.5pt \'Segoe UI\'')
        self.edit_input.returnPressed.connect(self.add_to_edit)

        box_edit.addWidget(self.table_edit)
        box_edit.addLayout(box_edit_combos)
        box_edit.addWidget(self.edit_input)
        box_edit.setContentsMargins(0, 0, 0, 0)
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
        soup = self.ss.ddos_check(f'{core.site_url}/Upload', 'get')
        lic = [t.text for t in soup.select('#licenseSelect > option')]
        lic.insert(0, lic.pop(-1))
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
        self.table_edit.insert_items([[str(self.spin_1.value()), opt1, opt2, opt3, opt4, self.edit_input.text()]])
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
    # QWebEngineProfile.defaultProfile().setHttpAcceptLanguage('ko')
    app = QApplication(sys.argv)
    win = MainWindow()
    print(process.memory_info().rss / 1024 / 1024)
    sys.exit(app.exec_())
