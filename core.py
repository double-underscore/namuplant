import sys
import os
import re
import configparser
import time
import webbrowser
import csv
import winsound
import requests
from bs4 import BeautifulSoup
from urllib import parse
import pyperclip
import keyboard
import mouse
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import *
#  QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

LIST_FIELD = ['code', 'title', 'opt1', 'opt2', 'opt3', 'edit']
LOG_FIELD = ['code', 'title', 'opt1', 'opt2', 'opt3', 'edit', 'time', 'rev', 'error']


class Session(QObject):
    sig_check_ddos = pyqtSignal(object)

    def __init__(self):  # 반복 필요 없는 것
        super().__init__()
        # self.ddos_dialog = CheckDdos()
        # self.sig_is_ddos_checked.connect(self.receive_checked)
        self.is_checked = False
        self.config = configparser.ConfigParser()
        self.config.read('config.ini', encoding='utf-8')
        self.UMI = self.config['login']['UMI']
        self.UA = self.config['login']['UA']
        self.ID = self.config['login']['ID']
        self.PW = self.config['login']['PW']
        self.DELAY = float(self.config['setting']['DELAY'])
        # self.jar = requests.cookies.RequestsCookieJar()
        # self.jar.set('umi', self.UMI, domain='namu.wiki')
        self.URL_LOGIN = 'https://namu.wiki/member/login'

    def login(self):

        self.s = requests.Session()
        self.s.headers.update({'user-agent': self.UA})
        self.s.get('https://namu.wiki/edit/IMO')
        self.s.cookies.set('umi', self.UMI, domain='namu.wiki')
        soup = self.ddos_check(self.s.post, self.URL_LOGIN, headers=self.make_header(self.URL_LOGIN),
                               cookies=self.s.cookies, data={'username': self.ID, 'password': self.PW})
        info = soup.select('body > div.navbar-wrapper > nav > ul.nav.navbar-nav.pull-right >'
                           'li > div > div.dropdown-item.user-info > div > div')
        if info[1].text == 'Member':
            return f'login SUCCESS {info[0].text}'
        else:
            return 'login FAILURE'

    def ddos_check(self, funcs, url, **kwargs):
        while True:
            if 'file' in kwargs:
                r = funcs(url, headers=kwargs['headers'], cookies=kwargs['cookies'], data=kwargs['data'],
                          files=kwargs['files'])
            elif 'data' in kwargs:
                r = funcs(url, headers=kwargs['headers'], cookies=kwargs['cookies'], data=kwargs['data'])
            elif 'headers' in kwargs:
                r = funcs(url, headers=kwargs['headers'], cookies=kwargs['cookies'])
            else:
                r = funcs(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            if soup.title:
                if soup.title.text == '비정상적인 트래픽 감지':
                    self.is_checked = False
                    self.sig_check_ddos.emit(self)
                    while not self.is_checked:
                        time.sleep(0.5)
                    # webbrowser.open('https://namu.wiki/404')
                    # input('비정상적인 트래픽 감지. 캡차 해결 후 아무 키나 입력')
                    continue
                else:
                    return soup
            else:  # for raw page
                return soup

    @pyqtSlot(bool)
    def receive_checked(self, b):
        self.is_checked = b

    @classmethod
    def make_header(cls, url):
        return {'referer': url}


class ReqPost(Session):
    def __init__(self):
        super().__init__()
        # self.login()

    def post(self, doc_code, edit_list):
        doc_url = f'https://namu.wiki/edit/{doc_code}'
        soup = self.ddos_check(self.s.get, doc_url, headers=self.make_header(doc_url), cookies=self.s.cookies)  # 겟
        baserev = soup.find(attrs={'name': 'baserev'})['value']
        if self.is_over_perm(soup):
            error_log = '편집 권한이 없습니다.'
        elif self.is_not_exist(soup):
            error_log = '문서가 존재하지 않습니다.'
        else:
            doc_text = soup.textarea.contents[0]  # soup.find(attrs={'name': 'text'}).text
            identifier = soup.find(attrs={'name': 'identifier'})['value']
            if 'm:' + self.ID == identifier:
                pass
                # print('yes!') # 아니면 중단
            # 변경
            doc_some = self.find_replace(doc_text, edit_list)  # 0 텍스트 1 요약
            # 포0
            soup = self.ddos_check(self.s.post, doc_url, headers=self.make_header(doc_url), cookies=self.s.cookies)  # 포0
            if self.is_captcha(soup):
                return {'rerun': True}
            else:
                token = soup.find(attrs={'name': 'token'})['value']
                # 포1
                multidata = {'token': token, 'identifier': identifier, 'baserev': baserev, 'text': doc_some[0],
                             'log': doc_some[1], 'agree': 'Y'}
                soup = self.ddos_check(self.s.post, doc_url, headers=self.make_header(doc_url), cookies=self.s.cookies,
                                  data=multidata, files={'file': None})  # 포1
                # 오류메시지
                alert = soup.select('.alert-danger')
                if alert:  # 편집기 오류 메시지
                    winsound.Beep(500, 50)
                    error_log = alert[0].strong.next_sibling.strip()
                else:  # 성공
                    print('EDIT success')
                    error_log = ''
        return {'rerun': False, 'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                'rev': baserev, 'error': error_log}

    @classmethod
    def find_replace(cls, text, edit_list, title=''):
        find_temp = ''
        summary = ''
        option_temp = ''
        for edit in edit_list:  # 0 num, 1 opt1, 2 opt2, 3 opt3, 4 text
            if edit[1] == '모두':  # 문서 내 모든 텍스트
                if edit[2] == '찾기':
                    option_temp = edit[3]
                    find_temp = edit[4]
                elif edit[2] == '바꾸기':
                    if option_temp == '일반':
                        text = text.replace(find_temp, edit[4])
                    elif option_temp == '정규식':
                        text = re.sub(find_temp, edit[4], text)
                elif edit[2] == '넣기':
                    if edit[3] == '맨 앞':  # 맨 앞
                        text = f'{edit[4]}\n{text}'
                    elif edit[3] == '맨 뒤':  # 맨 뒤
                        text = f'{text}\n{edit[4]}'
            elif edit[1] == '요약':  # 편집요약
                summary = edit[4]
            elif edit[1] == '복구':  # 복구 옵션
                pass
        return [text, summary]

    @classmethod
    def is_captcha(cls, soup):
        element = soup.select('#recaptcha')
        if element:
            return True  # 캡챠 활성화됨
        else:
            return False

    @classmethod
    def is_over_perm(cls, soup):
        element = soup.select(
            'body > div.content-wrapper > article > div.alert.alert-danger.alert-dismissible.fade.in.edit-alert')
        if element:
            return True  # 편집 권한 없음
        else:
            return False

    @classmethod
    def is_not_exist(cls, soup):
        element = soup.select(
            '.wiki-inner-content > p')
        if element:
            return True  # 존재하지 않는 문서
        else:
            return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setStyleSheet('font: 10pt \'맑은 고딕\';'
                           'color: #373a3c')
        # self.setfont(QFont('Segoe UI', 10))
        self.main_widget = MainWidget()
        self.setCentralWidget(self.main_widget)
        self.setGeometry(960, 30, 960, 1020)  # X Y 너비 높이
        self.setWindowTitle('Actinidia')
        self.setWindowIcon(QIcon('icon.png'))
        # self.statusBar().showMessage('Ready')

        test_action = QAction(QIcon('icon.png'), 'aaaa', self)
        test_action.triggered.connect(self.test_act)
        test_action.setShortcut('Ctrl + Q')

        menu_bar = self.menuBar()
        # menu_bar.setNativeMenuBar(False)
        menu_file = menu_bar.addMenu('&File')
        menu_file.addAction(test_action)

        self.read_list_csv()
        self.show()

    def read_list_csv(self):
        lists = read_csv('doc_list.csv')
        doc_to_insert = []
        edit_to_insert = []
        num = 1
        order_done = set()
        t_m = self.main_widget.tab_macro
        for i in range(len(lists)):
            order_t = lists[i]['code']
            if '#' in order_t or '$' in order_t:  # 편집 지시자
                order = int(order_t[1:])
                if order in order_done:
                    if lists[i]['opt1']:  # 선두 아닌 일반
                        edit_to_insert.append(
                            [str(order), lists[i]['opt1'], lists[i]['opt2'], lists[i]['opt3'], lists[i]['edit']])
                    else:  # 중복 지시자
                        doc_to_insert.append([lists[i]['code'], lists[i]['title'], ''])
                else:
                    order_done.add(order)
                    edit_to_insert.append(
                        [str(order), lists[i]['opt1'], lists[i]['opt2'], lists[i]['opt3'], lists[i]['edit']])
                    if '#' in order_t:  # 지시자 있는 선두
                        doc_to_insert.append([lists[i]['code'], lists[i]['title'], ''])
            else:  # 문서
                doc_to_insert.append([lists[i]['code'], lists[i]['title'], ''])
        t_m.table_doc.insert_items(doc_to_insert)
        t_m.table_edit.insert_items(edit_to_insert)

    def write_list_csv(self):
        t_m = self.main_widget.tab_macro
        docs = t_m.table_doc.rows_copy(range(t_m.table_doc.rowCount()))
        edits = t_m.edit_list_rearrange(t_m.table_edit.rows_copy(range(t_m.table_edit.rowCount())))
        to_write = []
        order_done = set()
        for i in range(len(docs)):
            if '#' in docs[i][0]:  # 편집 지시자
                order = int(docs[i][0][1:])
                if order not in order_done:
                    for edit in edits[order - 1]:  # 아예 처음
                        to_write.append({'code': docs[i][0], 'title': docs[i][1],
                                        'opt1': edit[1], 'opt2': edit[2], 'opt3': edit[3], 'edit': edit[4]})
                    order_done.add(order)
                else:  # 중복
                    to_write.append({'code': docs[i][0], 'title': docs[i][1],
                                     'opt1': '', 'opt2': '', 'opt3': '', 'edit': ''})
            else:  # 문서
                to_write.append({'code': docs[i][0], 'title': docs[i][1],
                                 'opt1': '', 'opt2': '', 'opt3': '', 'edit': ''})
        if len(edits) > len(order_done):  # 편집 지시자 없는 edit
            for aaa in edits:
                if int(aaa[0][0]) not in order_done:
                    for edit in aaa:
                        to_write.append({'code': f'${edit[0]}', 'title': f'💡 편집사항 #{edit[0]} 💡',
                                         'opt1': edit[1], 'opt2': edit[2], 'opt3': edit[3], 'edit': edit[4]})

        write_csv('doc_list.csv', 'w', LIST_FIELD, to_write)

    def closeEvent(self, event):
        self.write_list_csv()
        print('finished..')

    def test_act(self):
        print('aaaa')

class CheckDdos(QDialog):

    def __init__(self):
        super().__init__()
        self.label = QLabel('비정상트래픽 갬-쥐')
        self.browser = QWebEngineView()
        self.btn = QPushButton('완료')
        self.btn.clicked.connect(self.accept)

        box_v = QVBoxLayout()
        box_v.addWidget(self.label)
        box_v.addWidget(self.browser)
        box_v.addWidget(self.btn)
        self.setLayout(box_v)
        # self.setWindowModality(Qt.ApplicationModal)
        self.setGeometry(960, 30, 480, 500)


class MainWidget(QWidget):
    sig_is_ddos_checked_get = pyqtSignal(bool)
    sig_is_ddos_checked_macro = pyqtSignal(bool)
    sig_is_ddos_checked_preview = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        # label
        self.main_label = QLabel('Actinidia v 0.01')
        self.main_label.setAlignment(Qt.AlignCenter)
        self.main_label.setStyleSheet('font: 11pt')

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
        box_v.setStretchFactor(self.tabs, 22)
        self.setLayout(box_v)

        self.ddos_dialog = CheckDdos()
        self.tab_macro.req_get.sig_check_ddos.connect(self.open_ddos_dialog)
        self.tab_macro.obj_macro.sig_check_ddos.connect(self.open_ddos_dialog)
        # self.tab_macro.raw_preview.sig_check_ddos.connect(self.open_ddos_dialog)

        # self.sig_is_ddos_checked_get.connect(self.tab_macro.req_get.receive_checked)
        # self.sig_is_ddos_checked_macro.connect(self.tab_macro.obj_macro.receive_checked)
        # self.sig_is_ddos_checked_preview.connect(self.tab_macro.raw_preview.receive_checked)

    @pyqtSlot(str)
    def set_main_label(self, t):
        self.main_label.setText(t)

    @pyqtSlot(object)
    def open_ddos_dialog(self, obj):
        self.ddos_dialog.browser.load(QUrl('https://namu.wiki/404'))
        ddd = self.ddos_dialog.exec_()
        if ddd == QDialog.Accepted:
            obj.is_checked = True


class TabMacro(QWidget):
    sig_main_label = pyqtSignal(str)
    send_doc_list = pyqtSignal(list)
    send_edit_list = pyqtSignal(list)
    send_speed = pyqtSignal(int)
    send_get_option = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        # table doc
        self.table_doc = TableDoc()
        self.table_doc.sig_main_label.connect(self.str_to_main)
        # preview
        self.raw_preview = RawPreview()
        self.table_doc.sig_preview.connect(self.raw_preview.receive_code)
        # table edit
        self.table_edit = TableEdit()
        self.table_edit.sig_insert.connect(self.table_doc.insert_edit_num)
        self.table_edit.setStyleSheet('font: 10pt \'Segoe UI\'')
        # second to last row: edit options
        self.spin_1 = QSpinBox()
        self.spin_1.setMinimum(1)
        self.spin_1.setStyleSheet('font: 11pt')
        self.combo_opt1 = QComboBox()
        self.combo_opt1_text = ['모두', '요약', '복구']
        self.combo_opt1.addItems(self.combo_opt1_text)
        self.combo_opt1.setStyleSheet('font: 11pt')
        self.combo_opt2 = QComboBox()
        self.combo_opt2_text = ['찾기', '바꾸기', '넣기']
        self.combo_opt2.addItems(self.combo_opt2_text)
        self.combo_opt2.setStyleSheet('font: 11pt')
        self.combo_opt3 = QComboBox()
        self.combo_opt3_1_text = ['일반', '정규식']
        self.combo_opt3_3_text = ['맨 앞', '맨 뒤']
        self.combo_opt3.addItems(self.combo_opt3_1_text)
        self.combo_opt3.setStyleSheet('font: 11pt')
        self.combo_opt1.currentIndexChanged.connect(self.combo_opt1_change)
        self.combo_opt2.currentIndexChanged.connect(self.combo_opt2_change)
        self.line_input = QLineEdit()
        self.line_input.setStyleSheet('font: 11pt \'Segoe UI\'')
        self.line_input.returnPressed.connect(self.add_to_edit)
        # last row: get link
        self.combo_get_activate = QComboBox(self)
        self.combo_get_activate.addItems(['右 ON', '右 OFF'])
        self.combo_get_activate.setCurrentIndex(1)
        self.combo_get_activate.setStyleSheet('font: 11pt')
        self.combo_get_option = QComboBox(self)
        self.combo_get_option.addItems(['1개', '역링크', '분류'])
        self.combo_get_option.setStyleSheet('font: 11pt')
        self.btn_test = QPushButton('test')
        # self.btn_test.clicked.connect(self.aaa)
        self.dos = CheckDdos()
        # last row: main work
        self.combo_speed = QComboBox(self)
        self.combo_speed.addItems(['고속', '저속'])
        self.combo_speed.setStyleSheet('font: 11pt')
        self.btn_do = QPushButton('시작', self)
        self.btn_do.setStyleSheet('font: 11pt')
        self.btn_do.clicked.connect(self.iterate_start)
        self.btn_pause = QPushButton('정지', self)
        self.btn_pause.setStyleSheet('font: 11pt')
        self.btn_pause.clicked.connect(self.thread_quit)
        self.btn_pause.setEnabled(False)
        # splitter left
        self.split_v = QSplitter(Qt.Vertical)
        self.split_v.addWidget(self.raw_preview)
        self.split_v.addWidget(self.table_edit)
        self.split_v.setStretchFactor(0, 4)
        self.split_v.setStretchFactor(1, 12)
        # splitter right
        self.split_h = QSplitter()
        self.split_h.addWidget(self.table_doc)
        self.split_h.addWidget(self.split_v)
        self.split_h.setStretchFactor(0, 2)
        self.split_h.setStretchFactor(1, 3)

        box_h1 = QHBoxLayout()
        box_h2 = QHBoxLayout()
        box_v = QVBoxLayout()

        box_h1.addWidget(self.spin_1)
        box_h1.addWidget(self.combo_opt1)
        box_h1.addWidget(self.combo_opt2)
        box_h1.addWidget(self.combo_opt3)
        box_h1.addWidget(self.line_input)
        box_h1.setStretchFactor(self.spin_1, 1)
        box_h1.setStretchFactor(self.combo_opt1, 1)
        box_h1.setStretchFactor(self.combo_opt2, 1)
        box_h1.setStretchFactor(self.combo_opt3, 1)
        box_h1.setStretchFactor(self.line_input, 6)

        box_h2.addWidget(self.combo_get_activate)
        box_h2.addWidget(self.combo_get_option)
        box_h2.addWidget(self.btn_test)
        box_h2.addStretch(4)
        box_h2.addWidget(self.combo_speed)
        box_h2.addWidget(self.btn_do)
        box_h2.addWidget(self.btn_pause)
        box_h2.setStretchFactor(self.combo_get_activate, 1)
        box_h2.setStretchFactor(self.combo_get_option, 1)
        box_h2.setStretchFactor(self.btn_test, 1)
        box_h2.setStretchFactor(self.combo_speed, 1)
        box_h2.setStretchFactor(self.btn_do, 1)
        box_h2.setStretchFactor(self.btn_pause, 1)

        box_v.addWidget(self.split_h)
        box_v.addLayout(box_h1)
        box_v.addLayout(box_h2)

        self.setLayout(box_v)
        self.init_req()

    def init_req(self):
        # thread get_click
        mouse.on_right_click(self.get_start)
        self.th_get = QThread()
        self.req_get = ReqGet()
        self.req_get.send_code_list.connect(self.table_doc.receive_codes)
        self.req_get.moveToThread(self.th_get)
        self.req_get.finished.connect(self.get_finish)
        self.th_get.started.connect(self.req_get.work)
        self.req_get.label_text.connect(self.str_to_main)
        self.send_get_option.connect(self.req_get.get_option)
        # thread iterate
        self.th_macro = QThread()
        self.obj_macro = Iterate()
        self.obj_macro.moveToThread(self.th_macro)
        self.obj_macro.finished.connect(self.iterate_finish)
        self.th_macro.started.connect(self.obj_macro.work)
        self.obj_macro.label_text.connect(self.str_to_main)
        self.obj_macro.doc_set_current.connect(self.table_doc.set_current)
        self.obj_macro.doc_remove.connect(self.table_doc.removeRow)
        self.obj_macro.doc_error.connect(self.table_doc.set_error)
        self.send_doc_list.connect(self.obj_macro.get_doc_list)
        self.send_edit_list.connect(self.obj_macro.get_edit_list)
        self.send_speed.connect(self.obj_macro.get_speed)

    @pyqtSlot()
    def thread_quit(self):
        aaa = self.th_macro.isRunning()
        bbb = self.th_get.isRunning()
        if self.th_macro.isRunning():
            self.obj_macro.is_quit = True
        elif self.th_get.isRunning():
            self.req_get.is_quit = True
        self.str_to_main('정지 버튼을 눌렀습니다.')

    @pyqtSlot()
    def get_start(self):
        if self.combo_get_activate.currentIndex() == 0:  # 우클릭 모드 ON
            self.send_get_option.emit(self.combo_get_option.currentIndex())
            self.btn_do.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.th_get.start()

    @pyqtSlot()
    def get_finish(self):
        self.th_get.quit()
        self.req_get.is_quit = False
        self.btn_do.setEnabled(True)
        self.btn_pause.setEnabled(False)

    @pyqtSlot()
    def iterate_start(self):
        self.send_doc_list.emit(self.table_doc.rows_copy(range(self.table_doc.rowCount())))
        self.send_edit_list.emit(self.edit_list_rearrange(self.table_edit.rows_copy(range(self.table_edit.rowCount()))))
        self.send_speed.emit(self.combo_speed.currentIndex())
        self.btn_do.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.th_macro.start()

    @pyqtSlot()
    def iterate_finish(self):
        self.th_macro.quit()
        self.obj_macro.is_quit = False
        self.btn_do.setEnabled(True)
        self.btn_pause.setEnabled(False)

    @pyqtSlot(int)
    def combo_opt1_change(self, i):
        if i == 0:  # 모두
            self.combo_opt2.setEnabled(True)
            self.combo_opt3.setEnabled(True)
        elif i == 1 or 2:  # 요약, 되돌리기
            self.combo_opt2.setEnabled(False)
            self.combo_opt3.setEnabled(False)

    @pyqtSlot(int)
    def combo_opt2_change(self, i):
        opt3 = self.combo_opt3.currentText()
        if i == 0 or i == 1:
            if opt3 in self.combo_opt3_3_text:
                self.combo_opt3.clear()
                self.combo_opt3.addItems(self.combo_opt3_1_text)
            if i == 0:  # 찾
                self.combo_opt3.setEnabled(True)
            elif i == 1:  # 바
                self.combo_opt3.setEnabled(False)
        elif i == 2:  # 넣기
            self.combo_opt3.setEnabled(True)
            self.combo_opt3.clear()
            self.combo_opt3.addItems(self.combo_opt3_3_text)

    @pyqtSlot()
    def add_to_edit(self):
        # 값 추출
        opt1 = self.combo_opt1.currentText()
        if self.combo_opt2.isEnabled():
            opt2 = self.combo_opt2.currentText()
        else:
            opt2 = ''
        if self.combo_opt3.isEnabled():
            opt3 = self.combo_opt3.currentText()
        else:
            opt3 = ''

        self.table_edit.insert_items([[str(self.spin_1.value()), opt1, opt2, opt3, self.line_input.text()]])

        # 입력 후
        self.line_input.clear()
        if opt1 == self.combo_opt1_text[0]:
            if opt2 == self.combo_opt2_text[1]:  # 바꾸기
                self.combo_opt2.setCurrentIndex(0)
            elif opt2 == self.combo_opt2_text[0]:  # 찾기
                self.combo_opt2.setCurrentIndex(1)

        # item0.setFlags(item0.flags() ^ Qt.ItemIsEditable)  # ^은 빼기 |은 더하기
        # item1.setFlags(item1.flags() ^ Qt.ItemIsEditable)
        # item2.setFlags(item2.flags() ^ Qt.ItemIsEditable)
        # item3.setFlags(item3.flags() ^ Qt.ItemIsEditable)

    @pyqtSlot(str)
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


class ReqGet(Session):
    send_code_list = pyqtSignal(list)
    label_text = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.s = requests.Session()
        self.is_quit = False
        # mouse.on_right_click(self.get_click)

    def work(self):
        code = self.get_url()
        codes = []
        if code:
            if self.option == 0:  # 1개
                code_unquote = parse.unquote(code)
                codes = [[code], f'\'{code_unquote}\' 문서를 목록에 추가했습니다.']
            elif self.option == 1:  # 역링크
                codes = self.get_xref(code)
            elif self.option == 2:  # 분류
                codes = self.get_cat(code)
                
            self.send_code_list.emit(codes[0])  # code list
            self.label_text.emit(codes[1])  # label
        else:
            self.label_text.emit('올바른 URL을 찾을 수 없습니다.')
            winsound.Beep(500, 50)
        self.finished.emit()

    def get_url(self):
        pyperclip.copy('')
        time.sleep(0.01)
        keyboard.send('e')
        time.sleep(0.01)
        pasted_url = pyperclip.paste()
        if pasted_url:
            return self.get_code(pasted_url)
        else:
            keyboard.send('esc')
            time.sleep(0.01)
            return ''

    @pyqtSlot(int)
    def get_option(self, option):
        self.option = option

    @classmethod
    def get_redirect(cls, url):
        pass

    @classmethod
    def get_code(cls, url):
        if url.find('https://namu.wiki/') >= 0:
            search = re.search('https://namu\.wiki/\w+/(.*?)($|#|\?)', url).group(1)
            if search:
                return search
            else:
                return ''
        else:
            return ''

    def get_xref(self, doc_code):
        total = 0
        doc_name = parse.unquote(doc_code)
        list_space = []
        list_ref = []
        soup = self.ddos_check(self.s.get, f'https://namu.wiki/xref/{doc_code}')
        spaces = soup.select(
            'body > div.content-wrapper > article > fieldset > form > div:nth-child(1) > select:nth-child(2) > option')
        for v in spaces:
            list_space.append(parse.quote(v.get('value')))
        for namespace in list_space:
            added = ''
            while True:
                if self.is_quit:
                    return [list_ref, f'정지 버튼을 눌러 중지되었습니다.'
                                      f'\n\'{doc_name}\'의 역링크 문서를 {total}개 가져왔습니다.']
                added_unquote = parse.unquote(added[6:])
                namespace_unquote = parse.unquote(namespace)
                self.label_text.emit(f'{doc_name}의 역링크 {namespace_unquote} 가져오는 중... ( +{total} )'
                                     f'\n{added_unquote}')
                soup = self.ddos_check(requests.get, f'https://namu.wiki/xref/{doc_code}?namespace={namespace}{added}')
                titles = soup.select('div > ul > li > a')  # 목록
                for v in titles:
                    if v.next_sibling[2:-1] != 'redirect':
                        list_ref.append(v.get('href')[3:])
                        total += 1
                btn = soup.select('body > div.content-wrapper > article > div > a')  # 앞뒤버튼
                added = btn[1].get('href')  # 뒤 버튼
                if not added:  # 없으면 다음 스페이스로
                    break
                else:
                    added = added[added.find('&from'):].replace('\'', '%27')  # '만 인코딩이 안 되어 있음
                    # re.sub('\?namespace=.*?(&from.*?)$', '\g<1>', aaa)
        return [list_ref, f'\'{doc_name}\'의 역링크 문서를 {total}개 가져왔습니다.']

    def get_cat(self, doc_code):
        total = 0
        n = 0
        doc_name = parse.unquote(doc_code)
        list_cat = []
        btn_done = 0
        added = ''
        soup = self.ddos_check(self.s.get, f'https://namu.wiki/w/{doc_code}')
        h2s = soup.select('h2.wiki-heading')
        divs = soup.select('body > div.content-wrapper > article > div.wiki-content.clearfix > div')
        for i in range(len(h2s)):
            h2s[i] = h2s[i].text[h2s[i].text.rfind(' ') + 1:]
        # divs 0 문서내용 1 문서수 2 목록 3 문서수 4 버튼(있으면) 5 목록 6 버튼(있으면) ....
        for i in range(len(divs)):
            is_list = divs[i].select('div > ul > li > a')
            is_btn = divs[i].select('a.btn')
            if is_btn:  # 버튼. 같은 버튼이 목록 앞뒤로 중복
                if btn_done == 0:
                    added = divs[i].select('a')[1].get('href')
                    btn_done = 1
                elif btn_done == 1:
                    btn_done = 0
            elif is_list:  # 목록
                namespace = h2s[n]
                n += 1
                self.label_text.emit(f'{doc_name}의 하위 {namespace} 가져오는 중... ( +{total} )\n')
                for v in is_list:  # 첫번째 페이지 획득
                    list_cat.append(v.get('href')[3:])
                    total += 1
                while True:  # 한 페이지
                    if self.is_quit:
                        return [list_cat, f'정지 버튼을 눌러 중지되었습니다.'
                                          f'\n\'{doc_name}\'에 분류된 문서를 {total}개 가져왔습니다.']
                    if added:
                        added_unquote = parse.unquote(added[added.find('&cfrom=') + 7:])
                        self.label_text.emit(f'\'{doc_name}\'의 하위 {namespace} 가져오는 중... ( +{total} )\n{added_unquote}')
                        soup_new = self.ddos_check(self.s.get, f'https://namu.wiki/w/{doc_code}{added}')
                        divs_new = soup_new.select('body > div.content-wrapper >'
                                                   'article > div.wiki-content.clearfix > div')
                        for v in divs_new[i].select('div > ul > li > a'):
                            list_cat.append(v.get('href')[3:])
                            total += 1
                        added = divs_new[i - 1].select('a')[1].get('href')  # 버튼에서 값 추출
                    else:
                        break
        return [list_cat, f'\'{doc_name}\'에 분류된 문서를 {total}개 가져왔습니다.']
    

class Iterate(ReqPost):
    label_text = pyqtSignal(str)
    doc_remove = pyqtSignal(int)
    doc_set_current = pyqtSignal(int)
    doc_error = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        logged_in = self.login()
        self.label_text.emit(logged_in)
        self.is_quit = False

    def work(self):
        edit_temp = []
        edit_row = 0
        deleted = 0
        deleted_temp = 0
        t1 = time.time()

        if len(self.doc_list) == 0 or len(self.edit_list) == 0:  # 값이 없음
            self.label_text.emit('작업을 시작할 수 없습니다. 목록을 확인해주세요.')
        else:
            self.label_text.emit('작업을 시작합니다.')
            if self.index_speed == 0:  # 고속이면
                is_delay = False
            else:
                is_delay = True
            # 본작업 루프 시작
            for i in range(len(self.doc_list)):  # 0 code, 1 title, 2 etc
                self.doc_set_current.emit(i - deleted)
                if self.is_quit:  # 정지 버튼 눌려있으면 중단
                    self.label_text.emit('작업이 정지되었습니다.')
                    break
                if '#' in self.doc_list[i][0]:  # 편집 지시자
                    if i > 0 and i - edit_row - 1 == deleted_temp:  # 해당 지시자 쓰는 문서 편집 모두 성공하면
                        self.doc_remove.emit(edit_row - deleted)  # 더는 쓸모 없으니까 지시자 지움
                        deleted += 1
                        deleted_temp = 0
                    edit_row = i
                    edit_num = int(self.doc_list[i][0][1:])
                    # edit_num = re.sub('#(\d+)', '\g<1>', self.doc_list[i][0])
                    self.label_text.emit(f'편집사항 {edit_num}번 진행 중입니다.')
                    edit_temp = self.edit_list[edit_num - 1]  # 순번이 1이면 0번 항목
                    edit_temp_to_write = []
                    for edit in edit_temp:
                        edit_temp_to_write.append({'code': self.doc_list[i][0], 'title': self.doc_list[i][1],
                                                   'opt1': edit[1], 'opt2': edit[2], 'opt3': edit[3],
                                                   'edit': edit[4], 'time': '', 'rev': '', 'error': ''})
                    write_csv('edit_log.csv', 'a', LOG_FIELD, edit_temp_to_write)
                elif '^' in self.doc_list[i][0]:  # 중단자
                    self.label_text.emit('작업이 중단되었습니다.')
                    self.doc_remove.emit(i - deleted)
                    break
                else:  # 문서
                    if i > 0:  # 목록 처음이 편집 지시자가 아닌 경우만
                        label = f'( {i + 1} / {len(self.doc_list)} ) {self.doc_list[i][1]}'
                        self.label_text.emit(label)
                        while True:
                            posted = self.post(self.doc_list[i][0], edit_temp)  # 포스트 실시
                            if posted['rerun']:  # 리캡챠 발생
                                # self.label_text.emit('reCAPTCHA 감지되었습니다.')
                                self.login()
                            else:
                                if is_delay:  # 저속 옵션
                                    t2 = time.time()
                                    waiting = self.DELAY - (t2 - t1)
                                    if waiting > 0:
                                        time.sleep(waiting)
                                    t1 = time.time()
                                if posted['error']:  # 에러 발생
                                    self.label_text.emit(f'{label}\n{posted["error"]}')
                                    self.doc_error.emit(i - deleted, posted['error'])
                                else:  # 정상
                                    self.doc_remove.emit(i - deleted)
                                    deleted += 1
                                    deleted_temp += 1
                                write_csv('edit_log.csv', 'a', LOG_FIELD,
                                          [{'code': self.doc_list[i][0], 'title': self.doc_list[i][1],
                                            'opt1': '', 'opt2': '', 'opt3': '', 'edit': '',
                                            'time': posted['time'], 'rev': posted['rev'], 'error': posted['error']}])
                                break
                    else:
                        self.label_text.emit('편집 사항이 존재하지 않습니다.')
                        break
                if i == len(self.doc_list) - 1:  # 마지막 행
                    if i - edit_row == deleted_temp:  # 해당 지시자 쓰는 문서 편집 모두 성공하면
                        self.doc_remove.emit(edit_row)  # 더는 쓸모 없으니까 지시자 지움
                    self.label_text.emit('작업이 모두 완료되었습니다.')
        self.finished.emit()

    @pyqtSlot(list)
    def get_doc_list(self, doc_list):
        self.doc_list = doc_list

    @pyqtSlot(list)
    def get_edit_list(self, edit_list):
        self.edit_list = edit_list

    @pyqtSlot(int)
    def get_speed(self, index):
        self.index_speed = index


class TableEnhanced(QTableWidget):
    # todo 행이 많을 때 속도 저하 문제
    sig_main_label = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setAlternatingRowColors(True)
        self.setGridStyle(Qt.DotLine)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.verticalHeader().setDefaultSectionSize(23)
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

    def rows_copy(self, rows_list):
        return [[self.item(r, c).text() for c in range(self.columnCount())] for r in rows_list]

    def rows_paste(self, copied_list, row_to_paste):
        start = time.time()
        copied_list.reverse()
        for i in range(len(copied_list)):
            self.insertRow(row_to_paste)
            for c in range(self.columnCount()):
                self.setItem(row_to_paste, c, QTableWidgetItem(copied_list[i][c]))
        print(time.time() - start)

    def rows_move(self, where_to):
        self.setUpdatesEnabled(False)
        col_origin = self.currentColumn()
        rows_selected = self.rows_selected()
        row_where_to = 0
        items = self.rows_copy(rows_selected)
        # 일단 지우고
        self.rows_delete(rows_selected)
        # 어디로 가야 하나
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
    sig_preview = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['코드', '표제어', '비고'])
        self.horizontalScrollBar().setVisible(True)
        self.hideColumn(0)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.setSortingEnabled(True)
        # self.set_data()

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
            self.sig_preview.emit(self.item(self.currentRow(), 0).text())

    @pyqtSlot(int, str)
    def set_error(self, row, text):
        self.setItem(row, 2, QTableWidgetItem(text))
        self.resizeColumnToContents(2)

    @pyqtSlot(int)
    def set_current(self, row):
        self.setCurrentCell(row, 1)

    @pyqtSlot(list)
    def receive_codes(self, code_list):
        self.insert_items([[code, parse.unquote(code), ''] for code in code_list])

    # @pyqtSlot(list)
    def insert_items(self, item_list):
        self.rows_paste(item_list, self.rowCount())
        self.setCurrentCell(self.rowCount() - 1, 1)
        self.resizeColumnToContents(1)
        if self.columnWidth(1) > 450:
            self.setColumnWidth(1, 450)
        self.resizeRowsToContents()

    @pyqtSlot(str)
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
    sig_insert = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['순', '1', '2', '3', '내용'])
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
        self.rows_paste(item_list, self.rowCount())
        # self.setCurrentCell(self.rowCount() - 1, 1)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class RawPreview(QTextEdit, Session):
    
    def __init__(self):
        super().__init__()
        self.setPlaceholderText('미리보기 화면')
        self.setReadOnly(True)
    
    @pyqtSlot(str)
    def receive_code(self, doc_code):
        soup = self.ddos_check(requests.get, f'https://namu.wiki/raw/{doc_code}')
        self.setText(soup.text)
        

class TabMicro(QWidget):
    sig_main_label = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        label_info = QLabel('언젠가 예정')
        box_v = QVBoxLayout()
        box_v.addWidget(label_info)
        self.setLayout(box_v)


class WebView(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.load(QUrl('https://namu.wiki'))


# ==========

def write_csv(file_name, option, field, dict_list):
    with open(file_name, option, encoding='utf-8', newline='') as csv_file:
        if option == 'w':
            csv.DictWriter(csv_file, field).writeheader()
        writer = csv.DictWriter(csv_file, field)
        for dict_line in dict_list:
            writer.writerow(dict_line)


def read_csv(file_name):
    lists = []
    with open(file_name, 'r', encoding='utf-8', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            dict_row = dict(row)
            lists.append(dict_row)
    return lists


def check_setting():
    if not os.path.isfile('config.ini'):  # 최초 생성
        config = configparser.ConfigParser()
        config['login'] = {'UMI': '', 'UA': '', 'ID': '', 'PW': ''}
        config['setting'] = {'DELAY': 3}
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    if not os.path.isfile('doc_list.csv'):  # 최초 생성
        with open('doc_list.csv', 'w', encoding='utf-8', newline='') as csv_file:
            csv.DictWriter(csv_file, LIST_FIELD).writeheader()
    if not os.path.isfile('edit_log.csv'):  # 최초 생성
        with open('edit_log.csv', 'w', encoding='utf-8', newline='') as csv_file:
            csv.DictWriter(csv_file, LOG_FIELD).writeheader()

def test():
    pass

if __name__ == '__main__':
    check_setting()
    app = QApplication(sys.argv)
    win = MainWindow()
    sys.exit(app.exec_())
