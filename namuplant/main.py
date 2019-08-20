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
from PySide2.QtWidgets import QTextBrowser
from PySide2.QtGui import QIcon, QColor, QFont, QKeySequence, QStandardItem, QStandardItemModel
from PySide2.QtCore import Qt, QUrl, QThread, QObject, Slot, Signal
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
# 내부
import core, storage  # from . 에러...

process = psutil.Process(os.getpid())

# todo 첫 편집 시 결과 미리보기 모드
# todo 미러 사이트를 통한 문서 필터링
# todo 목록 중복 제거
# todo if 편집


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet('font: 10pt \'맑은 고딕\';'
                           'color: #373a3c')
        self.main_widget = MainWidget()
        self.setCentralWidget(self.main_widget)
        self.resize(800, 800)
        self.setWindowTitle('namuplant')
        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # 액션
        act_test = QAction(QIcon('icon.png'), '실험', self)
        act_test.triggered.connect(self.action_test)
        act_image = QAction('이미지 업로드', self)
        act_image.triggered.connect(self.action_image)
        # 메뉴
        menu_bar = self.menuBar()
        menu_file = menu_bar.addMenu('&File')
        menu_file.addAction(act_test)
        menu_file.addAction(act_image)
        self.read_doc_list_csv()
        self.show()

    def read_doc_list_csv(self):
        reader = storage.read_list_csv('doc_list.csv')

        t_m = self.main_widget.tab_macro
        t_m.table_doc.insert_items(reader['doc'])
        t_m.edit_editor.table_edit.insert_items(reader['edit'])

    def write_doc_list_csv(self):
        t_m = self.main_widget.tab_macro
        docs = t_m.table_doc.rows_copy(range(t_m.table_doc.rowCount()))
        edits = t_m.edit_list_rearrange(t_m.edit_editor.table_edit.rows_copy(range(t_m.edit_editor.table_edit.rowCount())))

        storage.write_list_csv('doc_list.csv', docs, edits)

    def closeEvent(self, event):
        self.write_doc_list_csv()
        print('finished..')

    def action_test(self):
        print(process.memory_info().rss / 1024 / 1024)

    def action_image(self):
        name_list = QFileDialog.getOpenFileNames(self, '이미지 열기', './', '이미지 파일(*.jpg *.png *.gif *.JPG *.PNG *.GIF)')[0]
        self.main_widget.tab_macro.table_doc.insert_items(
            [[f'@{n}', f'파일:{n[n.rfind("/") + 1:n.rfind(".")]}.{n[n.rfind(".") + 1:].lower()}',
              f'{n[n.rfind("/") + 1:]}'] for n in name_list])


class CheckDdos(QDialog):

    def __init__(self):
        super().__init__()
        self.label = QLabel('reCAPTCHA 해결 후 완료 버튼을 눌러주세요.')
        self.browser = QWebEngineView()
        self.btn = QPushButton('완료')
        self.btn.clicked.connect(self.accept)

        box_v = QVBoxLayout()
        box_v.addWidget(self.label)
        box_v.addWidget(self.browser)
        box_v.addWidget(self.btn)
        self.setLayout(box_v)
        # self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('reCAPTCHA')
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(480, 600)


class ViewDiff(QDialog):

    def __init__(self):
        super().__init__()
        self.browser = QTextBrowser()
        self.btn_yes = QPushButton('실행')
        self.btn_yes_group = QPushButton('그룹 실행')
        self.btn_yes_whole = QPushButton('전체 실행')
        self.btn_no = QPushButton('건너뛰기')
        self.btn_quit = QPushButton('중단')
        self.btn_yes.clicked.connect(self.yes_clicked)
        self.btn_yes_group.clicked.connect(self.yes_group_clicked)
        self.btn_yes_whole.clicked.connect(self.yes_whole_clicked)
        self.btn_no.clicked.connect(self.no_clicked)
        self.btn_quit.clicked.connect(self.quit_clicked)
        # box: buttons
        box_h = QHBoxLayout()
        box_h.addWidget(self.btn_yes)
        box_h.addWidget(self.btn_yes_group)
        box_h.addWidget(self.btn_yes_whole)
        box_h.addWidget(self.btn_no)
        box_h.addWidget(self.btn_quit)
        box_h.setStretchFactor(self.btn_yes, 1)
        box_h.setStretchFactor(self.btn_yes_group, 1)
        box_h.setStretchFactor(self.btn_yes_whole, 1)
        box_h.setStretchFactor(self.btn_no, 1)
        box_h.setStretchFactor(self.btn_quit, 1)
        # vertical
        box_v = QVBoxLayout()
        box_v.addWidget(self.browser)
        box_v.addLayout(box_h)
        self.setLayout(box_v)
        self.setWindowTitle('변경 사항 미리보기')
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(800, 600)

    @Slot()
    def yes_clicked(self):
        self.done(1)

    @Slot()
    def yes_group_clicked(self):
        self.done(2)

    @Slot()
    def yes_whole_clicked(self):
        self.done(3)

    @Slot()
    def no_clicked(self):
        self.done(4)

    @Slot()
    def quit_clicked(self):
        self.done(5)


class MainWidget(QWidget):
    sig_is_ddos_checked_get = Signal(bool)
    sig_is_ddos_checked_macro = Signal(bool)
    sig_is_ddos_checked_preview = Signal(bool)

    def __init__(self):
        super().__init__()
        # label
        self.main_label = QLabel('namuplant: a bot for namu.wiki')
        self.main_label.setAlignment(Qt.AlignCenter)
        self.main_label.setStyleSheet('font: 10.5pt')

        self.tabs = QTabWidget()
        self.tab_macro = TabMacro()
        self.tab_macro.sig_main_label.connect(self.set_main_label)
        self.tab_b = TabMicro()
        self.tab_b.sig_main_label.connect(self.set_main_label)
        self.tabs.addTab(self.tab_macro, '    Macro    ')
        self.tabs.addTab(self.tab_b, '    Micro    ')

        box_v = QVBoxLayout()
        box_v.addWidget(self.main_label)
        box_v.addWidget(self.tabs)
        box_v.setStretchFactor(self.main_label, 1)
        box_v.setStretchFactor(self.tabs, 25)
        self.setLayout(box_v)

        self.ddos_dialog = CheckDdos()
        self.tab_macro.req_get.sig_check_ddos.connect(self.show_ddos_dialog)
        self.tab_macro.iterate_post.sig_check_ddos.connect(self.show_ddos_dialog)

        self.diff_dialog = ViewDiff()
        self.tab_macro.iterate_post.sig_view_diff.connect(self.show_diff_dialog)


    @Slot(str)
    def set_main_label(self, t):
        self.main_label.setText(t)

    @Slot(object)
    def show_ddos_dialog(self, obj):
        self.ddos_dialog.browser.load(QUrl(f'{core.site_url}/404'))
        ddd = self.ddos_dialog.exec_()
        if ddd == QDialog.Accepted:
            obj.is_ddos_checked = True

    @Slot(str)
    def show_diff_dialog(self, t):
        self.diff_dialog.browser.setHtml(t)
        done = self.diff_dialog.exec_()
        self.tab_macro.iterate_post.diff_done = done


class TabMacro(QWidget):
    sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        # table doc
        self.table_doc = TableDoc()
        self.table_doc.sig_main_label.connect(self.str_to_main)
        # viewer package
        self.doc_viewer = DocViewer()
        self.table_doc.sig_viewer.connect(self.doc_viewer.receive_code)
        # edit package
        self.edit_editor = EditEditor()
        self.edit_editor.table_edit.sig_insert.connect(self.table_doc.insert_edit_num)
        # last row: get link
        self.combo_get_activate = QComboBox(self)
        self.combo_get_activate.addItems(['右 ON', '右 OFF'])
        self.combo_get_activate.setCurrentIndex(1)
        self.combo_get_activate.setStyleSheet('font: 10.5pt')
        self.combo_get_option = QComboBox(self)
        self.combo_get_option.addItems(['1개', '역링크', '분류'])
        self.combo_get_option.setStyleSheet('font: 10.5pt')
        # last row: main work
        self.combo_speed = QComboBox(self)
        self.combo_speed.addItems(['고속', '저속'])
        self.combo_speed.setStyleSheet('font: 10.5pt')
        self.btn_do = QPushButton('시작', self)
        self.btn_do.setStyleSheet('font: 10.5pt')
        self.btn_do.clicked.connect(self.iterate_start)
        self.btn_pause = QPushButton('정지', self)
        self.btn_pause.setStyleSheet('font: 10.5pt')
        self.btn_pause.clicked.connect(self.thread_quit)
        self.btn_pause.setEnabled(False)

        # splitter left
        self.split_v = QSplitter(Qt.Vertical)
        self.split_v.addWidget(self.doc_viewer)
        self.split_v.addWidget(self.edit_editor)
        self.split_v.setStretchFactor(0, 1)
        self.split_v.setStretchFactor(1, 1)
        # splitter right
        self.split_h = QSplitter()
        # self.split_h.setStyleSheet("""
        #     QSplitter::handle {
        #         background-color: #cccccc;
        #         }
        #     """)
        self.split_h.addWidget(self.table_doc)
        self.split_h.addWidget(self.split_v)
        self.split_h.setStretchFactor(0, 2)
        self.split_h.setStretchFactor(1, 3)

        box_last_row = QHBoxLayout()
        box_v = QVBoxLayout()

        box_last_row.addWidget(self.combo_get_activate)
        box_last_row.addWidget(self.combo_get_option)
        box_last_row.addStretch(5)
        box_last_row.addWidget(self.combo_speed)
        box_last_row.addWidget(self.btn_do)
        box_last_row.addWidget(self.btn_pause)
        box_last_row.setStretchFactor(self.combo_get_activate, 1)
        box_last_row.setStretchFactor(self.combo_get_option, 1)
        box_last_row.setStretchFactor(self.combo_speed, 1)
        box_last_row.setStretchFactor(self.btn_do, 1)
        box_last_row.setStretchFactor(self.btn_pause, 1)

        box_v.addWidget(self.split_h)
        box_v.addLayout(box_last_row)

        self.setLayout(box_v)
        self.init_req()

    @Slot(str)
    def str_to_main(self, t):
        self.sig_main_label.emit(t)

    @classmethod
    def edit_list_rearrange(cls, lists):  # 이중 리스트를 삼중 리스트로 변환
        edit_list = []
        for edit in lists:
            order = int(edit[0])
            while len(edit_list) < order:
                edit_list.append([])
            edit_list[order - 1].append(edit)
        return edit_list

    def init_req(self):
        # thread get_click
        mouse.on_right_click(self.get_start)
        self.th_get = QThread()
        self.req_get = core.ReqGet()
        self.req_get.finished.connect(self.get_finish)
        self.req_get.label_text.connect(self.str_to_main)
        self.req_get.send_code_list.connect(self.table_doc.receive_codes)
        self.req_get.moveToThread(self.th_get)
        self.th_get.started.connect(self.req_get.work)
        # thread iterate
        self.th_macro = QThread()
        self.iterate_post = core.Iterate()
        self.iterate_post.finished.connect(self.iterate_finish)
        self.iterate_post.label_text.connect(self.str_to_main)
        self.iterate_post.doc_set_current.connect(self.table_doc.set_current)
        self.iterate_post.doc_remove.connect(self.table_doc.removeRow)
        self.iterate_post.doc_error.connect(self.table_doc.set_error)
        self.iterate_post.moveToThread(self.th_macro)
        self.th_macro.started.connect(self.iterate_post.work)

    @Slot()
    def thread_quit(self):
        if self.th_macro.isRunning():
            self.iterate_post.is_quit = True
        elif self.th_get.isRunning():
            self.req_get.is_quit = True
        self.str_to_main('정지 버튼을 눌렀습니다.')

    @Slot()
    def get_start(self):
        if self.combo_get_activate.currentIndex() == 0:  # 우클릭 모드 ON
            self.btn_do.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.req_get.option = self.combo_get_option.currentIndex()
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
        self.iterate_post.doc_list = self.table_doc.rows_copy(range(self.table_doc.rowCount()))
        self.iterate_post.edit_list = self.edit_list_rearrange(
            self.edit_editor.table_edit.rows_copy(range(self.edit_editor.table_edit.rowCount()))
        )
        self.iterate_post.index_speed = self.combo_speed.currentIndex()
        self.iterate_post.diff_done = 1
        self.th_macro.start()

    @Slot()
    def iterate_finish(self):
        self.th_macro.quit()
        self.iterate_post.is_quit = False
        self.btn_do.setEnabled(True)
        self.btn_pause.setEnabled(False)


class TableEnhanced(QTableWidget):
    sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        self.setAlternatingRowColors(True)
        self.setGridStyle(Qt.DotLine)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setDefaultSectionSize(23)
        # self.verticalHeader().setSectionsClickable(False)
        self.shortcuts()

    def keyPressEvent(self, e):
        super().keyPressEvent(e)  # 오버라이드하면서 기본 메서드 재활용

        if e.key() == Qt.Key_Return:
            self.sig_main_label.emit(self.currentItem().text())

        elif e.key() == Qt.Key_Delete:  # 지우기
            self.setUpdatesEnabled(False)
            col_origin = self.currentColumn()
            rows_selected = self.rows_selected()
            if rows_selected:
                self.rows_delete(rows_selected)
                aaa = rows_selected[-1] - len(rows_selected)
                if aaa + 1 == self.rowCount():  # 마지막 줄이면
                    added = 0
                else:
                    added = 1
                self.setCurrentCell(aaa + added, col_origin)
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
        rows_list = []
        col_origin = self.currentColumn()
        items = self.selectedItems()
        if items:
            for i in items:
                if i.column() == col_origin:
                    rows_list.append(i.row())
            rows_list.sort()
        return rows_list

    def rows_delete(self, rows_list):
        deleted = 0
        if rows_list:
            for r in rows_list:
                self.removeRow(r - deleted)
                deleted += 1

    def rows_copy(self, rows_list):  # paste보다 더 오래 걸림...
        return [[self.item(r, c).text() for c in range(self.columnCount())] for r in rows_list]

    def rows_paste(self, copied_list, row_to_paste):
        # 가장 시간이 많이 소요되는 구간
        copied_list.reverse()
        for i in range(len(copied_list)):
            self.insertRow(row_to_paste)
            for c in range(self.columnCount()):
                self.setItem(row_to_paste, c, QTableWidgetItem(copied_list[i][c]))

    def rows_move(self, where_to):
        self.setUpdatesEnabled(False)
        col_origin = self.currentColumn()
        rows_selected = self.rows_selected()
        row_where_to = 0
        items = self.rows_copy(rows_selected)
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
    sig_viewer = Signal(str)

    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['코드', '표제어', '비고'])
        self.horizontalScrollBar().setVisible(True)
        self.hideColumn(0)
        # self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)  # 오버라이드하면서 기본 메서드 재활용

        if e.key() == Qt.Key_Insert:
            r = self.currentRow()
            self.insertRow(r)
            self.setItem(r, 0, QTableWidgetItem('^'))
            self.setItem(r, 1, QTableWidgetItem('⌛ 정지 ⌛'))
            self.setItem(r, 2, QTableWidgetItem(''))

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.sig_viewer.emit(self.item(self.currentRow(), 0).text())
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
    def receive_codes(self, code_list):
        if code_list:
            self.insert_items([[code, parse.unquote(code), ''] for code in code_list])

    # @Slot(list)
    def insert_items(self, item_list):
        self.rows_paste(item_list, self.rowCount())
        self.setCurrentCell(self.rowCount() - 1, 1)
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

    def dedup(self, x):
        # return dict.fromkeys(x)
        return list(set(x))


class TableEdit(TableEnhanced):
    sig_insert = Signal(str)

    def __init__(self):
        super().__init__()
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(['순', '1', '2', '3', '4', '내용'])
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
        # self.setCurrentCell(self.rowCount() - 1, 1)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class DocViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.cats = QComboBox()
        # self.cat_viewer.setReadOnly(True)
        self.btn_test2 = QPushButton('시험 2', self)
        self.viewer = QTextEdit()
        self.viewer.setPlaceholderText('미리보기 화면')
        self.viewer.setReadOnly(True)
        self.ss = core.SeedSession()
        box_h = QHBoxLayout()
        box_v = QVBoxLayout()

        box_h.addWidget(self.cats)
        box_h.addWidget(self.btn_test2)
        box_h.setStretchFactor(self.cats, 4)
        box_h.setStretchFactor(self.btn_test2, 1)
        box_v.addLayout(box_h)
        box_v.addWidget(self.viewer)
        box_v.setContentsMargins(0, 0, 0, 0)

        self.setLayout(box_v)
        # self.setAutoFillBackground(True)

    @Slot(str)
    def receive_code(self, doc_code):
        self.cats.clear()
        if doc_code[0] == '@':  # 파일
            self.viewer.setText(f'이미지 파일 경로\n{doc_code[1:]}')
        elif doc_code[0] == '#':  # 편집 지시자
            self.viewer.setText(f'{doc_code} 편집사항')
        elif doc_code[0] == '^':  # 중단자
            self.viewer.setText('중단점')
        else:  # 문서
            soup = self.ss.ddos_check(f'{core.site_url}/raw/{doc_code}')
            if soup.title:
                if soup.h1.text.strip() == '문제가 발생했습니다!':
                    self.viewer.setText(soup.h2.text)
            else:  # raw는 title이 없음
                cat_list = re.findall(r'\[\[(분류: ?.*?)\]\]', soup.text)
                self.cats.addItems(cat_list)
                # self.cat_viewer.setText(f'({")(".join(cat)})')
                self.viewer.setText(soup.text)


class EditEditor(QWidget):
    def __init__(self):
        super().__init__()

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
        self.combo_opt3 = QComboBox()
        self.combo_opt3_1_text = ['찾기', '바꾸기', '넣기']
        self.combo_opt3_2_text = ['본문', '라이선스', '분류']
        self.combo_opt3.addItems(self.combo_opt3_1_text)
        self.combo_opt4 = QComboBox()
        self.combo_opt4_1_1_text = ['텍스트', '정규식']
        self.combo_opt4_1_3_text = ['맨 앞', '맨 뒤', '분류']
        self.combo_opt4_2_1_text = ['설명', '출처', '날짜', '저작자', '기타']
        self.image_text = self.combo_image()
        self.combo_opt4_2_2_text = self.image_text[0]  # 라이선스
        self.combo_opt4_2_3_text = self.image_text[1]  # 파일 분류
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

    @classmethod
    def combo_image(cls):
        s = core.SeedSession()
        soup = s.ddos_check(f'{core.site_url}/Upload')
        lic = [t.text for t in soup.select('#licenseSelect > option')]
        lic.insert(0, lic.pop(-1))
        cat = [t.attrs['value'][3:] for t in soup.select('#categorySelect > option')]
        return [lic, cat]

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


class TabMicro(QWidget):
    sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        label_info = QLabel('언젠가 예정')
        box_v = QVBoxLayout()
        box_v.addWidget(label_info)
        self.setLayout(box_v)


class WebView(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.load(QUrl(core.site_url))


if __name__ == '__main__':
    print(process.memory_info().rss / 1024 / 1024)
    storage.new_setting()
    # QWebEngineProfile.defaultProfile().setHttpAcceptLanguage('ko')
    app = QApplication(sys.argv)
    win = MainWindow()
    print(process.memory_info().rss / 1024 / 1024)
    sys.exit(app.exec_())
