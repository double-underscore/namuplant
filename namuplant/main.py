import os
import re
import time
import psutil
from urllib import parse
import mouse
from PySide2.QtWidgets import QMainWindow, QWidget, QDialog, QAction, QShortcut, QPushButton, QLabel, QLineEdit
from PySide2.QtWidgets import QComboBox, QSpinBox, QTextEdit, QPlainTextEdit
from PySide2.QtWidgets import QSplitter, QVBoxLayout, QHBoxLayout
from PySide2.QtWidgets import QTabWidget, QTableWidget, QTableWidgetItem
from PySide2.QtWidgets import QTextBrowser, QFrame, QSizePolicy, QHeaderView, QFileDialog, QInputDialog
from PySide2.QtGui import QIcon, QKeySequence, QPixmap, QTextCursor, QTextDocument
from PySide2.QtCore import Qt, QUrl, QThread, QObject, QSize, Signal, Slot

from . import core, sub, storage
from .__init__ import __version__
process = psutil.Process(os.getpid())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet('font: 10pt \'맑은 고딕\'; color: #373a3c;')
        self.resize(800, 800)
        self.setWindowTitle(f'namuplant {__version__}')
        self.setWindowIcon(QIcon('icon.png'))
        # 파일 메뉴
        act_load_doc_list = QAction('문서 열기', self)
        act_load_doc_list.triggered.connect(self.action_load_doc_list)
        act_load_edit_list = QAction('편집사항 열기', self)
        act_load_edit_list.triggered.connect(self.action_load_edit_list)
        act_save_doc_list = QAction('문서 따로 저장', self)
        act_save_doc_list.triggered.connect(self.action_save_doc_list)
        act_save_edit_list = QAction('편집사항 따로 저장', self)
        act_save_edit_list.triggered.connect(self.action_save_edit_list)
        act_name_edit = QAction('이미지 표제어 변경', self)
        act_name_edit.triggered.connect(self.action_name_edit)
        # 설정 메뉴
        self.act_on_top = QAction('항상 위', self)
        self.act_on_top.setCheckable(True)
        self.act_on_top.toggled.connect(self.action_on_top)
        self.act_auto_ins = QAction('편집사항 자동 추가', self)
        self.act_auto_ins.setCheckable(True)
        self.act_auto_ins.toggled.connect(self.action_auto_ins)
        act_config = QAction('개인정보', self)
        act_config.triggered.connect(self.action_config)
        act_memory = QAction('RAM', self)
        act_memory.triggered.connect(self.action_memory)
        # 실험 메뉴
        self.act_skip_review = QAction('미리보기 스킵', self)
        self.act_skip_review.setCheckable(True)
        self.act_skip_review.toggled.connect(self.action_skip_review)
        act_test = QAction('test1', self)
        act_test.triggered.connect(self.action_test)
        act_test2 = QAction('test2', self)
        act_test2.triggered.connect(self.action_test2)
        # 메뉴바
        menu_bar = self.menuBar()
        menu_file = menu_bar.addMenu('파일')
        menu_file.addActions([act_load_doc_list, act_load_edit_list, act_save_doc_list, act_save_edit_list])
        menu_file.addSeparator()
        menu_file.addActions([act_name_edit])
        menu_option = menu_bar.addMenu('설정')
        menu_option.addActions([self.act_on_top, self.act_auto_ins])
        menu_option.addSeparator()
        menu_option.addActions([act_config, act_memory])
        # menu_test = menu_bar.addMenu('테스트')
        # menu_test.addAction(self.act_skip_review)
        # menu_test.addSeparator()
        # menu_test.addActions([act_test, act_test2])
        # 메인 위젯 구동
        self.main_widget = MainWidget()
        self.setCentralWidget(self.main_widget)
        # 데이터 준비
        self.read_list_csv('doc', 'doc_list.csv')
        self.read_list_csv('edit', 'edit_list.csv')
        # 기타 옵션
        self.act_on_top.setChecked(int(self.main_widget.CONFIG['window']['ON_TOP']))
        self.act_auto_ins.setChecked(int(self.main_widget.CONFIG['window']['AUTO_INS']))

    def action_on_top(self, check):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, check)
        self.main_widget.CONFIG['window']['ON_TOP'] = int(check)
        self.main_widget.save_config()
        self.show()

    def action_auto_ins(self, check):
        self.main_widget.tab_macro.AUTO_INSERT = int(check)
        self.main_widget.CONFIG['window']['AUTO_INS'] = int(check)
        self.main_widget.save_config()

    def action_skip_review(self, check):
        self.main_widget.tab_macro.SKIP_REVIEW = int(check)
        self.main_widget.CONFIG['window']['SKIP_REVIEW'] = int(check)
        self.main_widget.save_config()

    def action_config(self):
        self.main_widget.config_dialog.show_config()

    def action_name_edit(self):
        self.main_widget.show_name_edit_dialog()

    def action_memory(self):
        self.main_widget.set_main_label(f'메모리 사용량: {round(process.memory_info().rss / 1024 / 1024, 2)}MB')

    def action_load_doc_list(self):
        self.load_list('doc')

    def action_load_edit_list(self):
        self.load_list('edit')

    def action_save_doc_list(self):
        self.save_list('doc')

    def action_save_edit_list(self):
        self.save_list('edit')

    def action_test(self):
        # t1 = time.time()
        # print(time.time() - t1)
        pass

    def action_test2(self):
        pass

    def closeEvent(self, event):
        self.write_list_csv('doc', 'doc_list.csv')
        self.write_list_csv('edit', 'edit_list.csv')
        self.main_widget.save_config()

    def read_list_csv(self, mode_1: str, file_dir, index=None):
        t_m = self.main_widget.tab_macro
        if mode_1 == 'doc':
            wt = t_m.doc_board.table_doc.rows_text_insert()
            cols = ['code', 'title', 'rev']
        elif mode_1 == 'edit':
            wt = t_m.edit_editor.table_edit.rows_text_insert()
            cols = ['index', 'opt1', 'opt2', 'opt3', 'opt4', 'edit']
        else:
            return
        wt.send(None)
        for row in storage.read_csv(file_dir):
            if index is None:
                wt.send([row[f'{v}'] for v in cols])
            else:
                if index in str(row):
                    wt.send([row[f'{v}'] for v in cols])
        if mode_1 == 'doc':
            t_m.doc_board.table_doc.after_insert()
        elif mode_1 == 'edit':
            t_m.edit_editor.table_edit.resizeColumnsToContents()
        wt.close()

    def write_list_csv(self, mode: str, file_dir):
        t_m = self.main_widget.tab_macro
        wc = storage.write_csv(file_dir, 'w', mode)
        wc.send(None)
        if mode == 'doc':
            tc = t_m.doc_board.table_doc.rows_text_copy()
            cols = ['code', 'title', 'error']
        elif mode == 'edit':
            tc = t_m.edit_editor.table_edit.rows_text_copy()
            cols = ['index', 'opt1', 'opt2', 'opt3', 'opt4', 'edit']
        else:
            return
        for row in tc:
            wc.send(dict(zip(cols, [row[i] for i in range(len(row))])))  # 핵심
        wc.close()

    def load_list(self, mode):
        name = {'doc': '문서', 'edit': '편집사항'}[mode]
        file_dir = QFileDialog.getOpenFileName(self, f'{name} 목록 불러오기', './', 'CSV 파일(*.csv)')[0]
        if file_dir:
            self.main_widget.set_main_label(f'{file_dir}\n{name} 목록을 불러오는 중입니다.')
            search, ok = QInputDialog.getText(self, '특정 로그 불러오기',
                                              f'특정 {name} 로그를 불러오는 경우 검색할 내용을 입력해주세요.', QLineEdit.Normal)
            if ok:
                try:
                    if search:
                        self.read_list_csv(mode, file_dir, search)
                    else:
                        self.read_list_csv(mode, file_dir)
                    self.main_widget.set_main_label(f'{file_dir}\n{name} 목록을 불러왔습니다.')
                except KeyError:
                    self.main_widget.set_main_label('목록 유형이 잘못되었습니다.')

    def save_list(self, mode):
        name = {'doc': '문서', 'edit': '편집사항'}[mode]
        file_dir = QFileDialog.getSaveFileName(self, f'{name} 목록 저장하기', './', 'CSV 파일(*.csv)')[0]
        if file_dir:
            self.main_widget.set_main_label(f'{file_dir}\n{name} 목록을 저장하는 중입니다.')
            self.write_list_csv(mode, file_dir)
            self.main_widget.set_main_label(f'{file_dir}\n{name} 목록을 저장했습니다.')


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.CONFIG = storage.read_config('config.ini')
        # label
        self.main_label = QLabel()
        self.main_label.setAlignment(Qt.AlignCenter)
        self.main_label.setMinimumHeight(40)
        self.main_label.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.main_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.main_label.setWordWrap(True)
        self.main_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.main_label.setOpenExternalLinks(True)
        #
        self.tab_macro = TabMacro()
        self.tab_macro.sig_main_label.connect(self.set_main_label)
        self.login_confirm()
        # dialogs
        self.config_dialog = sub.ConfigDialog(self.tab_macro.requester)
        self.config_dialog.load(self.CONFIG['login'], self.CONFIG['work'])
        self.config_dialog.dialog_closed.connect(self.config_changed)

        self.ddos_dialog = sub.DDOSDialog()
        self.tab_macro.requester.ddos_detected.connect(self.ddos_dialog.show_ddos)
        self.ddos_dialog.ddos_checked.connect(self.tab_macro.requester.ddos_checked)
        self.tab_macro.requester.timeout_detected.connect(self.timeout_text)

        self.name_edit_dialog = sub.NameEditDialog()
        self.name_edit_dialog.sig_name_edit.connect(self.tab_macro.doc_board.table_doc.edit_file_name)

        box_v = QVBoxLayout()
        box_v.addWidget(self.main_label)
        box_v.addWidget(self.tab_macro)
        box_v.setStretchFactor(self.main_label, 1)
        box_v.setStretchFactor(self.tab_macro, 25)
        box_v.setContentsMargins(5, 5, 5, 5)
        self.setLayout(box_v)

    @Slot(str)
    def set_main_label(self, t):
        self.main_label.setText(t)

    def login_confirm(self):
        self.tab_macro.requester.load_config(self.CONFIG['login'], self.CONFIG['work'])
        if self.tab_macro.requester.login():
            self.tab_macro.setEnabled(True)
            self.set_main_label(f'namuplant {__version__}')
            # icon = QPixmap('icon.png')
            # self.main_label.setPixmap(icon.scaled(50, 50, Qt.KeepAspectRatio))
        else:
            self.tab_macro.setEnabled(False)
            self.set_main_label(
                '주어진 정보로는 로그인 할 수 없습니다.\n메뉴의 \'설정-개인정보\'에서 로그인 정보를 입력하십시오.')

    @Slot(dict, dict)
    def config_changed(self, c_login, c_work):
        self.CONFIG['login'], self.CONFIG['work'] = c_login, c_work
        self.save_config()
        self.login_confirm()

    def show_name_edit_dialog(self):
        self.name_edit_dialog.show()

    def timeout_text(self):
        self.set_main_label('timeout!!!')
        print('timeout')

    def save_config(self):
        storage.write_config('config.ini', self.CONFIG)


class TabMacro(QWidget):
    sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        self.requester = core.Requester()
        # define main widgets
        self.doc_board = DocBoard()
        self.tabs_viewer = TabViewers()
        self.edit_editor = EditEditor(self.requester)
        # define main tools
        self.req_get = core.ReqGet(self.requester, self.doc_board.table_doc.rows_text_insert())
        self.iterate_post = core.Iterate(self.requester)
        self.micro_post = core.Micro(self.requester)
        # last row: get link
        self.btn_get = QPushButton('右 OFF', self)
        self.btn_get.setCheckable(True)
        self.btn_get.toggled.connect(self.btn_get_toggle)
        self.btn_get.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_get.setMinimumWidth(70)
        self.btn_get.setMaximumWidth(100)
        # last row: main work
        self.cmb_speed = QComboBox(self)
        self.cmb_speed.addItems(['고속', '저속'])
        self.cmb_speed.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_speed.setMinimumWidth(70)
        self.cmb_speed.setMaximumWidth(100)
        self.cmb_speed.currentIndexChanged.connect(self.iterate_speed_change)
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
        # split_h.setStyleSheet("""
        #     QSplitter::handle {
        #         background-color: darkcyan;
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
        box_last_row.addWidget(self.cmb_speed)
        box_last_row.addWidget(self.btn_do)
        box_last_row.addWidget(self.btn_pause)
        box_last_row.setStretchFactor(self.btn_get, 1)
        box_last_row.setStretchFactor(self.cmb_speed, 1)
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
        self.doc_board.sig_main_label.connect(self.str_to_main)
        self.doc_board.table_doc.sig_main_label.connect(self.str_to_main)
        self.doc_board.table_doc.sig_doc_viewer.connect(self.micro_view)
        self.doc_board.cmb_option.currentIndexChanged.connect(self.btn_get_enable)
        self.tabs_viewer.sig_main_label.connect(self.str_to_main)
        self.edit_editor.table_edit.sig_insert_edit_sign.connect(self.doc_board.table_doc.insert_edit_sign)
        self.btn_do.clicked.connect(self.iterate_start)
        self.btn_pause.clicked.connect(self.thread_quit)
        # thread get_click
        mouse.on_right_click(self.get_start)
        self.th_get = QThread()
        self.AUTO_INSERT = 0
        self.req_get.finished.connect(self.get_finish)
        self.req_get.label_shown.connect(self.str_to_main)
        # self.req_get.send_code_list.connect(self.doc_board.table_doc.receive_codes_get)
        self.doc_board.doc_code_typed.connect(self.get_by_input)
        self.req_get.moveToThread(self.th_get)
        self.th_get.started.connect(self.req_get.work)
        # thread iterate
        self.th_iterate = QThread()
        self.SKIP_REVIEW = 0
        self.iterate_post.finished.connect(self.iterate_finish)
        self.iterate_post.label_shown.connect(self.str_to_main)
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
        self.micro_post.finished.connect(self.micro_finish)
        self.micro_post.label_shown.connect(self.str_to_main)
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
        if i == 4:
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
            self.req_get.option = self.doc_board.cmb_option.currentIndex()
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
            self.req_get.option = self.doc_board.cmb_option.currentIndex()
            self.th_get.start()
    @Slot()
    def get_finish(self):
        self.th_get.quit()
        # print(time.time() - self.t1)
        self.doc_board.table_doc.resizeColumnsToContents()
        self.doc_board.table_doc.setCurrentCell(self.doc_board.table_doc.rowCount() - 1, 1)
        # self.doc_board.table_doc.setFocus()
        self.req_get.is_quit = False
        self.btn_do.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_get.setEnabled(True)
        if self.AUTO_INSERT and self.req_get.total:
            self.edit_editor.auto_add_edit(self.doc_board.cmb_option.currentText(), parse.unquote(self.req_get.code))

    @Slot()
    def iterate_start(self):
        self.btn_do.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.iterate_post.doc_list = [row for row in self.doc_board.table_doc.rows_text_copy()]
        # self.iterate_post.doc_list = self.doc_board.table_doc.rows_text_copy_list()
        self.iterate_post.edit_dict = self.edit_editor.table_edit.edits_copy()
        self.iterate_post.index_speed = self.cmb_speed.currentIndex()
        self.iterate_post.diff_done = 3 if self.SKIP_REVIEW else 1
        self.th_iterate.start()

    @Slot()
    def iterate_finish(self):
        self.th_iterate.quit()
        self.tabs_viewer.close_diff(9)
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
        edit_list = self.edit_editor.table_edit.edits_copy(str(self.tabs_viewer.doc_viewer.spin.value()))
        v = self.tabs_viewer.doc_viewer.viewer
        v.selectAll()
        before = v.textCursor().selection().toPlainText()
        v.insertPlainText(self.micro_post.apply(before, edit_list))
        v.moveCursor(QTextCursor.Start)
        v.setFocus()

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


class TableDoc(sub.TableEnhanced):
    sig_doc_viewer = Signal(str)

    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setGridStyle(Qt.DotLine)
        self.cellDoubleClicked.connect(self.view_doc)
        self.setHorizontalHeaderLabels(['코드', '표제어', '비고'])
        self.horizontalHeader().setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.horizontalHeader().setMinimumSectionSize(34)
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().sectionClicked.connect(self.sort)
        self.horizontalHeader().sectionDoubleClicked.connect(self.dedupl)
        # self.horizontalHeader().sectionResized.connect(self.resize_section)
        self.verticalHeader().setStyleSheet('font: 7pt \'맑은 고딕\'')
        self.horizontalScrollBar().setVisible(True)
        # self.setSortingEnabled(True)
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
            insert.send(['!', '⌛ 정지 ⌛', ''])
            # self.rows_insert([['!', '⌛ 정지 ⌛', '']], where_to=self.currentRow())
            self.setCurrentCell(self.currentRow() - 1, 1)

    @Slot(int, int)
    def view_doc(self, row, _):
        self.sig_doc_viewer.emit(self.item(row, 0).text())

    @Slot(int, str)
    def set_error(self, row, text):
        self.edit_item_text(row, 2, self.item(row, 2).flags(), text)

    @Slot(int)
    def set_current(self, row):
        self.setCurrentCell(row, 1)

    def edit_item_text(self, row, col, flag, new_text):
        new_item = QTableWidgetItem(new_text)
        new_item.setFlags(flag)
        self.setItem(row, col, new_item)
        self.resizeColumnToContents(col)

    def after_insert(self):
        self.resizeColumnsToContents()
        if self.columnWidth(1) > 450:
            self.setColumnWidth(1, 450)

    @Slot(int)
    def dedupl(self, _):
        temp = set()
        rows_list = []
        ii = 0
        for row in self.rows_text_copy():
            code = row[0]
            if code in temp:
                rows_list.append(ii)
            else:
                temp.add(code)
            ii += 1
        self.rows_delete(rows_list)
        if len(rows_list) == 0:
            self.sig_main_label.emit('중복되는 표제어가 존재하지 않습니다.')
        else:
            self.sig_main_label.emit(f'중복되는 표제어를 {len(rows_list)}개 제거했습니다.')
        self.selectionModel().clearSelection()
        self.scrollToTop()

    @Slot(int)
    def sort(self, _):
        self.sortItems(0, Qt.AscendingOrder)

    @Slot(str, int)
    def edit_file_name(self, t, opt):
        if self._rows_selected():
            for row in self._rows_selected():
                old = self.item(row, 1).text()
                if old[0:3] == '파일:':
                    if opt == 0:  # 접두 0
                        new = f'파일:{t}{old[3:]}'
                    else:  # 접미 1
                        new = f'{old[:-4]}{t}{old[old.rfind("."):]}'
                    self.edit_item_text(row, 1, self.item(row, 1).flags(), new)

    @Slot(str)
    def insert_edit_sign(self, edit_index):
        where_to = self.currentRow()
        if where_to == -1:
            where_to = 0
        # elif edit_num == 1 and self.item(0, 0).text()[0] != '#':
        #     where_to = 0
        insert = self.rows_text_insert(where_to=where_to)
        insert.send(None)
        insert.send([f'#{edit_index}', f'💡 편집사항 #{edit_index} 💡', ''])
        # self.rows_insert([[f'#{edit_num}', f'💡 편집사항 #{edit_num} 💡', '']], where_to=where_to)
        self.resizeColumnsToContents()
        self.setCurrentCell(self.currentRow() - 1, 1)
        self.setFocus()

    @Slot()
    def insert_edit_1(self):
        self.insert_edit_sign('1')

    @Slot()
    def insert_edit_2(self):
        self.insert_edit_sign('2')

    @Slot()
    def insert_edit_3(self):
        self.insert_edit_sign('3')

    @Slot()
    def insert_edit_4(self):
        self.insert_edit_sign('4')

    @Slot()
    def insert_edit_5(self):
        self.insert_edit_sign('5')

    @Slot()
    def insert_edit_6(self):
        self.insert_edit_sign('6')

    @Slot()
    def insert_edit_7(self):
        self.insert_edit_sign('7')

    @Slot()
    def insert_edit_8(self):
        self.insert_edit_sign('8')

    @Slot()
    def insert_edit_9(self):
        self.insert_edit_sign('9')

    @Slot(int, int)
    def resize_to_splitter(self, w, _):
        pass
        # vh = self.verticalHeader().width()
        # vs = {True: self.verticalScrollBar().width(), False: 0}[self.verticalScrollBar().isVisible()]
        # if vh + vs + self.columnWidth(1) + self.columnWidth(2) > w:  # 축소
        #     self.setColumnWidth(1, w - vh - vs)

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


class TableEdit(sub.TableEnhanced):
    sig_insert_edit_sign = Signal(str)

    def __init__(self):
        super().__init__()
        self.setColumnCount(6)
        self.setGridStyle(Qt.DashLine)
        self.cellDoubleClicked.connect(self.emit_edit_sign)
        self.setHorizontalHeaderLabels(['순', '1', '2', '3', '4', '내용'])
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.resizeColumnsToContents()
        # self.resizeRowsToContents()
        # self.sizePolicy().setVerticalStretch(7)
        # self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cellChanged.connect(self.after_item_edit)
        self.col_editable = (True, True, True, True, True, True)
        self.col_clickable = (True, True, True, True, True, True)
        self.col_alignment = (Qt.AlignCenter, False, False, False, False, False, False)

    def after_item_edit(self, _, c):
        self.resizeColumnToContents(c)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)  # 오버라이드하면서 기본 메서드 재활용

        if e.key() == Qt.Key_Insert:
            self.sig_insert_edit_sign.emit(self.item(self.currentRow(), 0).text())

    @Slot(int, int)
    def emit_edit_sign(self, row, _):
        self.sig_insert_edit_sign.emit(self.item(row, 0).text())

    def edits_copy(self, pick=''):
        temp = {}
        for row in self.rows_text_copy():
            index = row[0]
            if index not in temp:  # 없으면
                temp.setdefault(index, [])
            temp[index].append(row)
        if pick == '':  # 전체
            return temp
        else:
            return temp[pick]


class DocBoard(QWidget):
    doc_code_typed = Signal(str)
    sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        self.table_doc = TableDoc()
        self.table_doc.setStyleSheet("""
            QTableWidget::item:selected{
                background-color: cadetblue;
                color: white;}
            QTableWidget::item:focus{
                background-color: darkcyan;
                color: white;}
            """)
        self.cmb_option = QComboBox(self)
        self.cmb_option.addItems(['1개', '역링크', '분류:', '사용자:', '이미지'])
        self.cmb_option.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_option.currentIndexChanged.connect(self.cmb_option_change)
        # self.name_input = QLineEdit()
        self.name_input = sub.LineEnhanced()
        self.name_input.setMinimumWidth(100)
        self.name_input.setPlaceholderText('입력하여 문서 추가')
        self.name_input.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.name_input.returnPressed.connect(self.insert)
        self.name_input.focused.connect(self.invoke_insert_file)
        # self.name_input.textChanged.connect(self.invoke_insert_file)
        box_h = QHBoxLayout()
        box_h.addWidget(self.cmb_option)
        box_h.addWidget(self.name_input)
        box_v = QVBoxLayout()
        box_v.addLayout(box_h)
        box_v.addWidget(self.table_doc)
        box_v.setContentsMargins(0, 0, 0, 0)
        self.setLayout(box_v)

    @Slot()
    def insert(self):
        if self.name_input.text():
            if self.cmb_option.currentIndex() == 2:  # 분류:
                self.doc_code_typed.emit(parse.quote(f'분류:{self.name_input.text()}'))
            else:
                self.doc_code_typed.emit(parse.quote(self.name_input.text()))
            self.name_input.clear()
        else:
            self.sig_main_label.emit('입력란이 비어있습니다.')

    @Slot()
    def invoke_insert_file(self):
        if self.cmb_option.currentIndex() == 4:
            self.insert_file()

    @Slot(int)
    def cmb_option_change(self, i):
        if i == 4:
            self.name_input.setPlaceholderText('클릭하여 파일 불러오기')
        else:
            self.name_input.setPlaceholderText('입력하여 문서 추가')

    def insert_file(self):
        insert = self.table_doc.rows_text_insert(editable=[False, True, False])
        insert.send(None)
        name_list = QFileDialog.getOpenFileNames(self, '이미지 열기', './',
                                                 '이미지 파일(*.jpg *.png *.gif *.JPG *.PNG *.GIF)')[0]
        for n in name_list:
            insert.send([f'${n}', f'파일:{n[n.rfind("/") + 1:n.rfind(".")]}.{n[n.rfind(".") + 1:].lower()}', ''])
        self.table_doc.resizeColumnsToContents()
        self.table_doc.setCurrentCell(self.table_doc.rowCount() - 1, 1)
        self.table_doc.setFocus()


class LineFind(sub.LineEnhanced):
    sig_find = Signal(str, int)

    def __init__(self):
        super().__init__()
        find_backward = QShortcut(QKeySequence('Shift+Return'), self, context=Qt.WidgetShortcut)
        find_backward.activated.connect(self.find_backward)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_Return:
            self.sig_find.emit(self.text(), 0)  # 전방 탐색

    def find_backward(self):
        self.sig_find.emit(self.text(), 1)  # 후방 탐색


class DocViewer(QWidget):
    # sig_main_label = Signal(str)

    def __init__(self):
        super().__init__()
        # tab view
        self.tab_view = QWidget()
        self.cmb_info = QComboBox()
        self.cmb_info.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_info.setEditable(True)
        self.cmb_info.setEnabled(False)
        self.cmb_info.setInsertPolicy(QComboBox.NoInsert)
        self.btn_edit = QPushButton('편집', self)
        self.btn_edit.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_edit.setMaximumWidth(100)
        self.btn_edit.setEnabled(False)
        self.btn_close = QPushButton('닫기', self)
        self.btn_close.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.btn_close.setMaximumWidth(100)
        self.btn_close.setEnabled(False)
        box_tab_view = QHBoxLayout()
        box_tab_view.addWidget(self.cmb_info)
        box_tab_view.addWidget(self.btn_close)
        box_tab_view.addWidget(self.btn_edit)
        box_tab_view.setStretchFactor(self.cmb_info, 5)
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
        self.tabs.setMaximumHeight(self.cmb_info.height())  # 임시변통
        # viewer
        self.viewer = QPlainTextEdit()
        self.viewer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.viewer.setPlaceholderText('미리보기 화면')
        self.viewer.setStyleSheet("""
            QPlainTextEdit{
                selection-background-color: cadetblue; 
                selection-color: white;}
            QPlainTextEdit:Focus{
                selection-background-color: darkcyan; 
                selection-color: white;}        
            """)
        # self.viewer.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.viewer.setReadOnly(True)
        # finder
        self.find_input = LineFind()
        self.find_input.sig_find.connect(self.run_find)
        self.find_input.setPlaceholderText("찾기")
        self.find_input.setHidden(True)
        find_input_show = QShortcut(QKeySequence('Ctrl+F'), self, context=Qt.WidgetWithChildrenShortcut)
        find_input_show.activated.connect(self.show_find_input)  # 한 칸 위로
        # box main
        box_v = QVBoxLayout()
        box_v.addWidget(self.tabs)
        box_v.addWidget(self.find_input)
        box_v.addWidget(self.viewer)
        box_v.setContentsMargins(0, 0, 0, 0)
        self.setLayout(box_v)

    @Slot(str, str, bool)
    def set_text_view(self, code, text, editable):
        self.cmb_info.clear()
        self.cmb_info.setEnabled(editable)
        if self.cmb_info.isEnabled():
            self.cmb_info.addItem(parse.unquote(code))
            self.cmb_info.addItems(self.get_cat_from(text))
        self.btn_edit.setEnabled(editable)
        self.btn_close.setEnabled(True)
        self.viewer.setPlainText(text)

    @Slot(str)
    def set_text_edit(self, text):
        self.cmb_info.clear()
        self.viewer.setReadOnly(False)
        self.tabs.setCurrentWidget(self.tab_edit)
        self.viewer.setPlainText(text)

    @Slot()
    def quit_edit(self, clear):
        self.viewer.setReadOnly(True)
        self.cmb_info.clear()
        if clear:
            self.viewer.clear()
            self.find_input.setHidden(True)
            self.find_input.clear()
            self.cmb_info.setEnabled(False)
            self.btn_edit.setEnabled(False)
            self.btn_close.setEnabled(False)
        self.tabs.setCurrentWidget(self.tab_view)

    @staticmethod
    def get_cat_from(text):
        return list(map(lambda x: x[:-5] if x[-5:] == '#blur' else x, re.findall(r'\[\[(분류: ?.*?)\]\]', text)))

    @Slot()
    def show_find_input(self):
        # self.find_input.setHidden(not self.find_input.isHidden())
        if self.find_input.isHidden():
            self.find_input.setHidden(False)
            self.find_input.setFocus()
        else:
            self.find_input.setHidden(True)
            self.find_input.clear()

    @Slot(str, int)
    def run_find(self, text, order):
        if order == 0:
            order = QTextDocument.FindFlag()
        else:
            order = QTextDocument.FindBackward
        for i in range(2):
            if self.viewer.find(text, order):
                break
            else:
                if i == 0:
                    if order == 0:
                        self.viewer.moveCursor(QTextCursor.Start)
                    else:
                        self.viewer.moveCursor(QTextCursor.End)
                elif i == 1:
                    pass


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
        box_macro.addWidget(self.btn_no)
        box_macro.addWidget(self.btn_yes_group)
        box_macro.addWidget(self.btn_yes_whole)
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
        self.tabs.setMaximumHeight(self.btn_yes.height())
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 0;}
            """)

        # vertical
        box_v = QVBoxLayout()
        box_v.addWidget(self.browser)
        box_v.addWidget(self.tabs)
        box_v.setContentsMargins(0, 0, 0, 0)
        # box_v.setSpacing(5)
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
        # box_v.setSpacing(5)
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
        if done == 2 or done == 3 or done == 5 or done == 9:  # 비교 탭 다시 볼 필요 없음
            self.setCurrentWidget(self.doc_viewer)
            self.diff_viewer.browser.clear()
        if done != 9:
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
    def __init__(self, requester):
        super().__init__()
        self.requester = requester
        box_edit = QVBoxLayout()
        box_edit_combos = QHBoxLayout()
        # table edit
        self.table_edit = TableEdit()
        self.table_edit.setStyleSheet("""
            * {font: 10pt \'Segoe UI\'}
            QTableWidget::item:selected{
                background-color: cadetblue;
                color: white;}
            QTableWidget::item:focus{
                background-color: darkcyan;
                color: white;}
            """)
        # edit options
        self.spin_1 = QSpinBox()
        self.spin_1.setMinimum(1)
        self.spin_1.setStyleSheet('font: 10.5pt \'맑은 고딕\'')
        self.cmb_main = QComboBox()
        self.cmb_main.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_main.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_main.addItems(['문서', '파일', '요약', '복구'])
        self.cmb_main.currentTextChanged.connect(self.cmb_main_change)
        # cmb_main 문서
        self.cmb_doc = QComboBox()
        self.cmb_doc.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_doc.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_doc.addItems(['수정', '삽입'])
        self.cmb_doc.currentTextChanged.connect(self.cmb_doc_change)
        self.cmb_doc_by = QComboBox()
        self.cmb_doc_by.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_doc_by.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_doc_by.addItems(['텍스트', '정규식', '링크', '포함', '분류:'])
        self.cmb_doc_do = QComboBox()
        self.cmb_doc_do.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_doc_do.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_doc_do.addItems(['찾기', '바꾸기', '지우기'])
        self.cmb_doc_insert = QComboBox()
        self.cmb_doc_insert.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_doc_insert.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_doc_insert.addItems(['맨 위', '맨 아래', '분류 앞', '분류 뒤'])
        # cmb_main 파일
        self.cmb_file = QComboBox()
        self.cmb_file.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_file.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_file.addItems(['본문', '라이선스', '분류:'])
        self.cmb_file.currentTextChanged.connect(self.cmb_file_change)
        self.cmb_file_desc = QComboBox()
        self.cmb_file_desc.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_file_desc.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_file_desc.addItems(['설명', '출처', '날짜', '저작자', '기타'])
        lic, cat = self.cmb_image()
        self.cmb_file_lic = QComboBox()
        self.cmb_file_lic.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_file_lic.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_file_lic.view().setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.cmb_file_lic.view().setTextElideMode(Qt.ElideRight)
        self.cmb_file_lic.addItems(lic)
        self.cmb_file_lic.activated.connect(self.cmb_file_lic_change)
        self.cmb_file_cat = QComboBox()
        self.cmb_file_cat.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_file_cat.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_file_cat.view().setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.cmb_file_cat.view().setTextElideMode(Qt.ElideRight)
        self.cmb_file_cat.addItems(cat)
        self.cmb_file_cat.activated.connect(self.cmb_file_cat_change)
        # cmb_main 복구
        self.cmb_revert = QComboBox()
        self.cmb_revert.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_revert.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_revert.addItems(['직전', '지정'])
        self.cmb_revert.currentTextChanged.connect(self.cmb_revert_change)
        self.cmb_revert_before = QComboBox()
        self.cmb_revert_before.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_revert_before.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_revert_before.addItems(['현재', '마지막', '처음'])
        self.cmb_revert_to = QComboBox()
        self.cmb_revert_to.setStyleSheet('font: 10pt \'맑은 고딕\'')
        self.cmb_revert_to.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self.cmb_revert_to.addItems(['로그', '입력'])

        # space
        self.lbl_2 = QLabel()
        self.lbl_3 = QLabel()
        self.lbl_4 = QLabel()

        box_edit_combos.addWidget(self.spin_1)  # 0
        box_edit_combos.addWidget(self.cmb_main)  # 1
        box_edit_combos.addWidget(self.lbl_2)  # 2
        box_edit_combos.addWidget(self.cmb_doc)  # 2
        box_edit_combos.addWidget(self.lbl_3)  # 3
        box_edit_combos.addWidget(self.cmb_doc_by)  # 3
        box_edit_combos.addWidget(self.cmb_file)  # 3
        box_edit_combos.addWidget(self.cmb_revert)  # 3
        box_edit_combos.addWidget(self.lbl_4)  # 4
        box_edit_combos.addWidget(self.cmb_doc_do)  # 4
        box_edit_combos.addWidget(self.cmb_doc_insert)  # 4
        box_edit_combos.addWidget(self.cmb_file_desc)  # 4
        box_edit_combos.addWidget(self.cmb_file_lic)  # 4
        box_edit_combos.addWidget(self.cmb_file_cat)  # 4
        box_edit_combos.addWidget(self.cmb_revert_before)  # 4
        box_edit_combos.addWidget(self.cmb_revert_to)  # 4

        box_edit_combos.setStretchFactor(self.spin_1, 1)
        box_edit_combos.setStretchFactor(self.cmb_main, 1)
        box_edit_combos.setStretchFactor(self.cmb_doc, 1)
        box_edit_combos.setStretchFactor(self.cmb_doc_by, 1)
        box_edit_combos.setStretchFactor(self.cmb_doc_do, 1)
        box_edit_combos.setStretchFactor(self.cmb_doc_insert, 1)
        box_edit_combos.setStretchFactor(self.cmb_file, 1)
        box_edit_combos.setStretchFactor(self.cmb_file_desc, 1)
        box_edit_combos.setStretchFactor(self.cmb_file_lic, 1)
        box_edit_combos.setStretchFactor(self.cmb_file_cat, 1)
        box_edit_combos.setStretchFactor(self.cmb_revert, 1)
        box_edit_combos.setStretchFactor(self.cmb_revert_before, 1)
        box_edit_combos.setStretchFactor(self.cmb_revert_to, 1)
        box_edit_combos.setStretchFactor(self.lbl_2, 1)
        box_edit_combos.setStretchFactor(self.lbl_3, 1)
        box_edit_combos.setStretchFactor(self.lbl_4, 1)
        self.cmb_main.setCurrentIndex(2)
        self.cmb_main.setCurrentIndex(0)
        # input
        self.edit_input = sub.LineEnhanced()
        self.edit_input.setStyleSheet('font: 10.5pt \'Segoe UI\'')
        self.edit_input.returnPressed.connect(self.add_to_edit)
        box_edit.addWidget(self.table_edit)
        box_edit.addLayout(box_edit_combos)
        box_edit.addWidget(self.edit_input)
        box_edit.setContentsMargins(0, 0, 0, 0)
        box_edit.setSpacing(6)
        self.setLayout(box_edit)
        
    def show_cmb(self, visible):  # True 보이기 False 감추기 None 냅두기
        cmbs = (self.cmb_doc, self.cmb_doc_by, self.cmb_doc_do, self.cmb_doc_insert,
                self.cmb_file, self.cmb_file_desc, self.cmb_file_lic, self.cmb_file_cat,
                self.cmb_revert, self.cmb_revert_before, self.cmb_revert_to,
                self.lbl_2, self.lbl_3, self.lbl_4)
        for i in range(len(cmbs)):
            if visible[i] is not None:
                cmbs[i].setVisible(visible[i])

    @Slot(str)
    def cmb_main_change(self, t):
        if t == '문서':
            self.show_cmb([True, True, True, False, False, False, False, False, False, False, False, False, False, False])
            self.cmb_doc_change(self.cmb_doc.currentText())
        elif t == '파일':
            self.show_cmb([False, False, False, False, True, True, False, False, False, False, False, True, False, False])
            self.cmb_file_change(self.cmb_file.currentText())
        elif t == '요약':
            self.show_cmb([False, False, False, False, False, False, False, False, False, False, False, True, True, True])
        elif t == '복구':
            self.show_cmb([False, False, False, False, False, False, False, False, True, True, False, True, False, False])

    @Slot(str)
    def cmb_doc_change(self, t):
        if t == '수정':
            self.show_cmb([None, True, True, False, None, None, None, None, None, None, None, None, False, None])
        elif t == '삽입':
            self.show_cmb([None, False, False, True, None, None, None, None, None, None, None, None, True, None])

    @Slot(str)
    def cmb_file_change(self, t):
        if t == '본문':
            self.show_cmb([None, None, None, None, None, True, False, False, None, None, None, True, None, None])
        elif t == '라이선스':
            self.show_cmb([None, None, None, None, None, False, True, False, None, None, None, True, None, None])
        elif t == '분류:':
            self.show_cmb([None, None, None, None, None, False, False, True, None, None, None, True, None, None])
        self.edit_input.clear()

    @Slot(str)
    def cmb_revert_change(self, t):
        if t == '직전':
            self.show_cmb([None, None, None, None, None, None, None, None, None, True, False, True, None, None])
        elif t == '지정':
            self.show_cmb([None, None, None, None, None, None, None, None, None, False, True, True, None, None])

    @Slot(int)
    def cmb_file_lic_change(self, i):
        self.edit_input.setText(self.cmb_file_lic.itemText(i))

    @Slot(int)
    def cmb_file_cat_change(self, i):
        self.edit_input.setText(self.cmb_file_cat.itemText(i))

    def cmb_image(self):
        source = self.requester.s.get(f'{core.SITE_URL}/Upload').text
        lic = re.findall(r'\"title\":\"이미지 라이선스/(.*?)\"', source)
        lic.insert(0, lic.pop(-1))
        cat = re.findall(r'\"title\":\"(파일/.*?)\"', source)
        cat.remove('파일/미분류')
        cat.insert(0, '파일/미분류')
        return lic, cat

    @Slot()
    def add_to_edit(self, alt=''):
        string = self.edit_input.text()
        # 값 추출
        opt1 = self.cmb_main.currentText()
        opt2, opt3, opt4 = '', '', ''
        if opt1 == '문서':
            opt2 = self.cmb_doc.currentText()
            if opt2 == '수정':
                opt3 = self.cmb_doc_by.currentText()
                opt4 = self.cmb_doc_do.currentText()
            elif opt2 == '삽입':
                opt3 = ''
                opt4 = self.cmb_doc_insert.currentText()
        elif opt1 == '파일':
            opt2 = ''
            opt3 = self.cmb_file.currentText()
            if opt3 == '본문':
                opt4 = self.cmb_file_desc.currentText()
            elif opt3 == '라이선스':
                if not string:
                    string = self.cmb_file_lic.currentText()
                opt4 = ''
            elif opt3 == '분류:':
                if not string:
                    string = self.cmb_file_cat.currentText()
                opt4 = ''
        elif opt1 == '요약':
            opt2, opt3, opt4 = '', '', ''
        elif opt1 == '복구':
            opt2 = ''
            opt3 = self.cmb_revert.currentText()
            if opt3 == '직전':
                opt4 = self.cmb_revert_before.currentText()
            elif opt3 == '지정':
                opt4 = self.cmb_revert_to.currentText()
        # 스트링 예외
        if alt:
            string = alt
        elif opt4 == '로그' or opt4 == '현재':  # 복구 옵션 중 텍스트 입력칸 무시
            string = ''
        insert = self.table_edit.rows_text_insert()
        insert.send(None)
        insert.send([str(self.spin_1.value()), opt1, opt2, opt3, opt4, string])
        # self.table_edit.rows_insert([[str(self.spin_1.value()), opt1, opt2, opt3, opt4, self.edit_input.text()]])
        self.table_edit.resizeColumnsToContents()
        self.table_edit.setCurrentCell(self.table_edit.rowCount() - 1, 1)
        # 입력 후
        self.table_edit.sortItems(0, Qt.AscendingOrder)
        self.table_edit.setCurrentCell(self.table_edit.currentRow(), self.table_edit.currentColumn())
        self.edit_input.clear()
        if opt4 == '바꾸기':
            self.cmb_doc_do.setCurrentText('찾기')
        elif opt4 == '찾기':
            self.cmb_doc_do.setCurrentText('바꾸기')

    def auto_add_edit(self, option, name):
        if name.startswith('분류:'):
            name = name[3:]
        if name:
            if option == '역링크' or option == '분류:':
                if self.table_edit.rowCount() == 0:
                    self.spin_1.setValue(1)
                else:
                    ddd = self.table_edit.item(self.table_edit.rowCount() - 1, 0).text()
                    self.spin_1.setValue(int(ddd[ddd.rfind('_') + 1:]) + 1)
                self.cmb_main.setCurrentText('문서')
                self.cmb_doc.setCurrentText('수정')
                self.cmb_doc_do.setCurrentText('찾기')
                if option == '역링크':
                    self.cmb_doc_by.setCurrentText('링크')
                elif option == '분류:':
                    self.cmb_doc_by.setCurrentText('분류:')
                self.add_to_edit(alt=name)


def trace(func):
    def wrapper(self, *args, **kwargs):
        t1 = time.time()
        print(func.__name__, '시행 전 메모리:', process.memory_info().rss / 1024 / 1024)
        r = func(self, *args, **kwargs)
        print(func.__name__, '시행 후 메모리:', process.memory_info().rss / 1024 / 1024,
              '시행 소요 시간', time.time() - t1)
        return r

    return wrapper
