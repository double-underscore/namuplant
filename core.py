import requests
from bs4 import BeautifulSoup
from urllib import parse
import os
import re
import configparser
import time
import webbrowser
import csv
import winsound
import pyperclip
import keyboard
import mouse
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont, QKeySequence, QDropEvent
from PyQt5.QtCore import *

LIST_FIELD = ['code', 'title', 'option', 'find', 'replace', 'summary']
LOG_FIELD = ['code', 'title', 'option', 'find', 'replace', 'summary', 'time', 'rev', 'error']
COMBO_1 = ['모두', '복구', '요약']
COMBO_2 = ['찾기', '바꾸기', '넣기']
COMBO_3_1 = ['일반', '정규식']
COMBO_3_2 = []
COMBO_3_3 = ['맨 앞', '맨 뒤']


def ddos_check(funcs, url, **kwargs):
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
        if soup.title.text == '비정상적인 트래픽 감지':
            webbrowser.open('https://namu.wiki/404')
            input('ddos 감지. 캡차 해결 후 아무 키나 입력')
            continue
        else:
            return soup


class Req:  # 로그인이 필요한 작업
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini', encoding='utf-8')
        self.umi = self.config['login']['umi']
        self.ua = self.config['login']['ua']
        self.id = self.config['login']['id']
        self.pw = self.config['login']['pw']
        self.interval = float(self.config['setting']['interval'])
        self.logindata = {
            'username': self.id,
            'password': self.pw
        }
        self.loginurl = 'https://namu.wiki/member/login'
        # self.jar = requests.cookies.RequestsCookieJar()
        # self.jar.set('umi', self.umi, domain='namu.wiki')

    def test(self):
        pass

    def login(self):
        self.s = requests.Session()
        self.s.headers.update({'user-agent': self.ua})
        self.s.get('https://namu.wiki/edit/IMO')
        self.s.cookies.set('umi', self.umi, domain='namu.wiki')
        soup = ddos_check(self.s.post, self.loginurl, headers=self.make_header(self.loginurl), cookies=self.s.cookies,
                          data=self.logindata)
        # r = self.s.post(self.loginurl, headers=self.make_header(self.loginurl), cookies=self.s.cookies, data=self.logindata)
        if soup.select(
                'body > div.navbar-wrapper > nav > ul.nav.navbar-nav.pull-right > li > div > '
                'div.dropdown-item.user-info > div > div')[1].text == 'Member':
            print('login SUCCESS')
        else:
            print('login FAILURE')


    def iterate(self, doc_list, iter_option= 0):
        n = len(doc_list)
        i = 0
        while i < n:
            start_time = time.time()
            is_done = self.edit_post(doc_list[i])
            if is_done:
                i += 1
                if iter_option > 0:
                    end_time = time.time()
                    wait_time = end_time - start_time
                    if wait_time > 0:
                        time.sleep(wait_time)
            else:
                self.login() # 리캡챠 발생


    def edit_post(self, doc_dict):
        # ['code', 'title', 'option', 'find', 'replace', summary', ///// 'time', 'rev', 'error']
        # 겟
        doc_url = 'https://namu.wiki/edit/' + doc_dict['code']
        soup = ddos_check(self.s.get, doc_url, headers=self.make_header(doc_url), cookies=self.s.cookies)  # 겟
        baserev = soup.find(attrs={'name': 'baserev'})['value']
        if is_over_perm(soup):
            error_log = '편집 권한이 없습니다.'
        elif is_not_exist(soup):
            error_log = '문서가 존재하지 않습니다.'
        else:
            maintext = soup.textarea.contents[0]  # soup.find(attrs={'name': 'text'}).text
            identifier = soup.find(attrs={'name': 'identifier'})['value']
            if 'm:' + self.id == identifier:
                pass
                # print('yes!') # 아니면 중단
            # 변경
            maintext = self.find_replace(maintext, doc_dict['option'], doc_dict['find'], doc_dict['replace'])
            # 포0
            soup = ddos_check(self.s.post, doc_url, headers=self.make_header(doc_url), cookies=self.s.cookies)  # 포0
            if is_captcha(soup):
                return False
            else:
                token = soup.find(attrs={'name': 'token'})['value']
                # 포1
                multidata = {'token': token, 'identifier': identifier, 'baserev': baserev, 'text': maintext,
                             'log': doc_dict['summary'], 'agree': 'Y'}
                soup = ddos_check(self.s.post, doc_url, headers=self.make_header(doc_url), cookies=self.s.cookies,
                                  data=multidata, files={'file': None})  # 포1
                # 오류메시지
                alert = soup.select('.alert-danger')
                if alert:  # 편집기 오류 메시지
                    winsound.Beep(500, 50)
                    error_log = alert[0].strong.next_sibling.strip()
                else:  # 성공
                    print('EDIT success')
                    error_log = ''
        # 로그 기록
        doc_dict['time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        doc_dict['rev'] = baserev
        doc_dict['error'] = error_log
        self.append_log(doc_dict)
        return True # 재시도 필요 없음

    @staticmethod
    def make_header(url):
        return {'referer': url}

    @staticmethod
    def find_replace(text, option, text_find, text_replace):
        if option == 0:  # 일반 찾아바꾸기
            return text.replace(text_find, text_replace)
        elif option == 1:  # 정규식
            return re.sub(text_find, text_replace, text)
        elif option == 2:  # 맨 뒤에 추가하기
            return text + '\n' + text_replace
        elif option == 9:  # 테스트
            return text

    @staticmethod
    def append_log(log_dict):
        with open('edit_log.csv', 'a', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, LOG_FIELD)
            writer.writerow({'code': log_dict['code'], 'title': log_dict['title'], 'option': log_dict['option'],
                             'find': log_dict['find'], 'replace': log_dict['replace'], 'summary': log_dict['summary'],
                             'time': log_dict['time'], 'rev': log_dict['rev'], 'error': log_dict['error']})


def is_captcha(soup):
    element = soup.select('#recaptcha')
    if element:
        return True  # 캡챠 활성화됨
    else:
        return False


def is_over_perm(soup):
    element = soup.select(
        'body > div.content-wrapper > article > div.alert.alert-danger.alert-dismissible.fade.in.edit-alert')
    if element:
        return True  # 편집 권한 없음
    else:
        return False


def is_not_exist(soup):
    element = soup.select(
        '.wiki-inner-content > p')
    if element:
        return True  # 존재하지 않는 문서
    else:
        return False


def get_xref(doc_code):
    spacelist = []
    reflist = []
    soup = ddos_check(requests.get, f'https://namu.wiki/xref/{doc_code}')
    spaces = soup.select(
        'body > div.content-wrapper > article > fieldset > form > div:nth-child(1) > select:nth-child(2) > option')  # 네임스페이스
    for v in spaces:
        spacelist.append(parse.quote(v.get('value')))
    for v in spacelist:
        added = ''
        namespace = v
        while True:
            print(len(reflist))
            soup = ddos_check(requests.get, f'https://namu.wiki/xref/{doc_code}?namespace={namespace}{added}')
            titles = soup.select('div > ul > li > a')  # 목록
            for v in titles:
                if v.next_sibling[2:-1] != 'redirect':
                    reflist.append(v.get('href')[3:])
            btn = soup.select('body > div.content-wrapper > article > div > a')  # 앞뒤버튼
            added = btn[1].get('href')  # 뒤 버튼
            if added == None:  # 없으면 다음 스페이스로
                break
            else:
                added = added[added.find('&from'):].replace('\'', '%27')  # '만 인코딩이 안 되어 있음
                # re.sub('\?namespace=.*?(&from.*?)$', '\g<1>', aaa)
    append_list(reflist)


def get_cat(doc_code):
    catlist = []
    donebtn = 0
    added = ''
    soup = ddos_check(requests.get, f'https://namu.wiki/w/{doc_code}')
    divs = soup.select('body > div.content-wrapper > article > div.wiki-content.clearfix > div')
    for i in range(len(divs)):
        islist = divs[i].select('div > ul > li > a')
        isbtn = divs[i].select('a.btn')
        if isbtn:
            if donebtn == 0:
                added = divs[i].select('a')[1].get('href')
                donebtn = 1
            elif donebtn == 1:
                donebtn = 0
        elif islist:
            for v in islist:  # 기본 페이지
                catlist.append(v.get('href')[3:])
            while True:
                if added:
                    newsoup = ddos_check(requests.get, f'https://namu.wiki/w/{doc_code}{added}')
                    newdivs = newsoup.select('body > div.content-wrapper > article > div.wiki-content.clearfix > div')
                    for v in newdivs[i].select('div > ul > li > a'):
                        catlist.append(v.get('href')[3:])
                    added = newdivs[i - 1].select('a')[1].get('href')  # 버튼에서 값 추출
                else:
                    break
    append_list(catlist)


def append_list(code_list):
    for doc_code in code_list:
        with open('doc_list.csv', 'a', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, LIST_FIELD) # ['code', 'title', 'option', 'find', 'replace', 'summary']
            writer.writerow({'code': doc_code, 'title': parse.unquote(doc_code)})

def read_list(): #csv 읽기 & 입력값 첨가
    list = []
    with open('doc_list.csv', 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dict_row = dict(row)
            if dict_row['option']:
                dict_row['option'] = int(dict_row['option'])
            list.append(dict_row)
    return list


def deduplication(input):
    return list(set(input))


def check_setting():
    if not os.path.isfile('config.ini'):  # 최초 생성
        config = configparser.ConfigParser()
        config['login'] = {'umi': '', 'ua': '', 'id': '', 'pw': ''}
        config['setting'] = {'interval': 3}
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    if not os.path.isfile('doc_list.csv'):  # 최초 생성
        with open('doc_list.csv', 'w', encoding='utf-8', newline='') as csvfile:
            csv.DictWriter(csvfile, LIST_FIELD).writeheader()
    if not os.path.isfile('edit_log.csv'):  # 최초 생성
        with open('edit_log.csv', 'w', encoding='utf-8', newline='') as csvfile:
            csv.DictWriter(csvfile, LOG_FIELD).writeheader()
            # ['code', 'title', 'option', 'find', 'replace', 'summary', 'time', 'rev', 'error']


def get_click():
    is_ctrl = keyboard.is_pressed('ctrl')
    if is_ctrl:
        pyperclip.copy('')
        keyboard.block_key('ctrl')
        keyboard.release('ctrl')
        time.sleep(0.03)
        keyboard.send('e')
        time.sleep(0.01)
        pasted_url = pyperclip.paste()
        if pasted_url:
            keyboard.unblock_key('ctrl')
            code = get_code(pasted_url)
            if code:
                # append_list([code])
                get_xref(code)
            else:
                winsound.Beep(500, 50)
        else:
            keyboard.send('esc')
            time.sleep(0.02)
            keyboard.unblock_key('ctrl')
            winsound.Beep(500, 50)


def get_code(url):
    if url.find('https://namu.wiki/') >= 0:
        search = re.search('https://namu\.wiki/\w+/(.*?)($|#|\?)', url).group(1)
        if search:
            return search
        else:
            return False
    else:
        return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setStyleSheet('font: 10pt \'Segoe UI\'')
        # self.setfont(QFont('Segoe UI', 10))
        main_widget = MainWidget()
        self.setCentralWidget(main_widget)
        self.setGeometry(960, 30, 960, 1020)  # X Y 너비 높이
        self.setWindowTitle('Actinidia')
        self.setWindowIcon(QIcon('icon.png'))
        # self.statusBar().showMessage('Ready')

        test_action = QAction(QIcon('icon.png'), 'aaaa', self)
        test_action.triggered.connect(self.test)
        test_action.setShortcut('Ctrl + Q')

        menu_bar = self.menuBar()
        # menu_bar.setNativeMenuBar(False)
        menu_file = menu_bar.addMenu('&File')
        menu_file.addAction(test_action)

        self.show()

    def test(self):
        print('aaaaaaaa')


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        # label
        self.main_label = QLabel('Actinidia v 0.01')
        self.main_label.setAlignment(Qt.AlignCenter)
        self.main_label.setStyleSheet('font: 11pt')
        # QDial().setValue()

        self.tabs = QTabWidget()
        tab_a = TabMacro()
        tab_b = TabMicro()
        tab_a.sig_test.connect(self.set_main_label)
        tab_a.sig_test.connect(self.set_main_label)
        self.tabs.addTab(tab_a, '    Macro    ')
        self.tabs.addTab(tab_b, '    Micro    ')

        box_v = QVBoxLayout()
        box_v.addWidget(self.main_label)
        box_v.addWidget(self.tabs)
        self.setLayout(box_v)

    @pyqtSlot(str)
    def set_main_label(self, t):
        self.main_label.setText(t)


class TabMacro(QWidget):
    sig_test = pyqtSignal(str)
    sig_table_doc_main_label = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()
        # self.keyPressEvent()

    def initUI(self):
        # self.setStyleSheet('background-color: #f0f0f0')
        # table doc
        self.table_doc = TableDoc()
        self.table_doc.sig_main_label.connect(self.str_to_main)

        #textbrowser
        self.text_editor = QTextBrowser()
        self.text_editor.setDisabled(True)
        # table edit
        self.table_edit = TableEdit()

        # second to last row
        self.spin_1 = QSpinBox()
        self.spin_1.setMinimum(1)
        self.spin_1.setStyleSheet('font: 11pt')
        self.combo_opt1 = QComboBox()
        self.combo_opt1.addItems(COMBO_1)
        self.combo_opt1.setStyleSheet('font: 11pt')
        self.combo_opt2 = QComboBox()
        self.combo_opt2.addItems(COMBO_2)
        self.combo_opt2.setStyleSheet('font: 11pt')
        self.combo_opt3 = QComboBox()
        self.combo_opt3.addItems(COMBO_3_1)
        self.combo_opt3.setStyleSheet('font: 11pt')
        self.combo_opt1.currentIndexChanged.connect(self.combo_opt1_change)
        self.combo_opt2.currentIndexChanged.connect(self.combo_opt2_change)
        self.line_input = QLineEdit()
        self.line_input.setStyleSheet('font: 11pt')
        self.line_input.returnPressed.connect(self.add_to_edit)

        # last row
        self.combo_speed = QComboBox(self)
        self.combo_speed.setStyleSheet('background-color: rgb(190, 190, 190);'
                                       'color: black;'
                                       'padding-left: 10px;'
                                       'padding-right: 30px;'
                                       'border-style: solid;'
                                       'border-width: 0px')
        self.combo_speed.addItem('고속')
        self.combo_speed.addItem('저속')
        self.btn_do = QPushButton('시작', self)
        # self.btn_do.clicked().connect(self.table_edit_add_new_row)
        self.btn_pause = QPushButton('정지', self)

        self.split_v = QSplitter(Qt.Vertical)
        self.split_v.addWidget(self.text_editor)
        self.split_v.addWidget(self.table_edit)
        self.split_v.setStretchFactor(0, 4)
        self.split_v.setStretchFactor(1, 12)

        self.split_h = QSplitter()
        self.split_h.addWidget(self.table_doc)
        self.split_h.addWidget(self.split_v)
        self.split_h.setStretchFactor(0, 2)
        self.split_h.setStretchFactor(1, 3)

        box_h1 = QHBoxLayout()
        box_h2 = QHBoxLayout()
        box_v = QVBoxLayout()

        # box_h1.addStretch(2)
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

        box_h2.addWidget(self.combo_speed)
        box_h2.addStretch(3)
        box_h2.addWidget(self.btn_do)
        box_h2.addWidget(self.btn_pause)

        box_v.addWidget(self.split_h)
        box_v.addLayout(box_h1)
        box_v.addLayout(box_h2)

        self.setLayout(box_v)

    @pyqtSlot(int)
    def combo_opt1_change(self, i):
        if i == 0: # 모두
            self.combo_opt2.setEnabled(True)
            self.combo_opt3.setEnabled(True)
        elif i == 1 or 2: # 되돌리기, 요약
            self.combo_opt2.setEnabled(False)
            self.combo_opt3.setEnabled(False)

    @pyqtSlot(int)
    def combo_opt2_change(self, i):
        opt3 = self.combo_opt3.currentText()
        if i == 0 or i == 1:
            if opt3 in COMBO_3_3:
                self.combo_opt3.clear()
                self.combo_opt3.addItems(COMBO_3_1)
            if i == 0:  # 찾
                self.combo_opt3.setEnabled(True)
            elif i == 1:  # 바
                self.combo_opt3.setEnabled(False)
        elif i == 2:  # 넣기
            self.combo_opt3.setEnabled(True)
            self.combo_opt3.clear()
            self.combo_opt3.addItems(COMBO_3_3)

    @pyqtSlot(int, int)
    def table_edit_add_new_row(self, r, c): # 시그널 슬롯 예시
        rows_total = self.table_edit.rowCount()
        if r == rows_total - 1:
            self.table_edit.insertRow(rows_total)
        self.str_to_main('동동이') # sig_test 라는 시그널을 뱉음
        # self.table_edit.setItem()
        # self.table_edit.item

    @pyqtSlot()
    def add_to_edit(self):
        # 값 추출
        order = self.spin_1.value()
        opt1 = self.combo_opt1.currentIndex()
        opt2 = self.combo_opt2.currentIndex()
        opt3 = self.combo_opt3.currentIndex()
        text = self.line_input.text()
        rows_total = self.table_edit.rowCount()

        item0 = QTableWidgetItem(str(order))
        item1 = QTableWidgetItem(COMBO_1[opt1])
        if self.combo_opt2.isEnabled():
            item2 = QTableWidgetItem(COMBO_2[opt2])
        else:
            item2 = QTableWidgetItem('')
        if self.combo_opt3.isEnabled():
            if opt2 == 0:
                item3 = QTableWidgetItem(COMBO_3_1[opt3])
            elif opt2 == 2:
                item3 = QTableWidgetItem(COMBO_3_3[opt3])
        else:
            item3 = QTableWidgetItem('')

        item0.setFlags(item0.flags() ^ Qt.ItemIsEditable) # ^은 빼기 |은 더하기
        item1.setFlags(item1.flags() ^ Qt.ItemIsEditable)
        item2.setFlags(item2.flags() ^ Qt.ItemIsEditable)
        item3.setFlags(item3.flags() ^ Qt.ItemIsEditable)

        # 값 입력
        self.table_edit.setRowCount(rows_total + 1)
        self.table_edit.setItem(rows_total, 0, item0)
        self.table_edit.setItem(rows_total, 1, item1)
        self.table_edit.setItem(rows_total, 2, item2)
        self.table_edit.setItem(rows_total, 3, item3)
        self.table_edit.setItem(rows_total, 4, QTableWidgetItem(text))
        self.table_edit.resizeColumnsToContents()
        self.table_edit.resizeRowsToContents()
        # 입력 후
        self.line_input.clear()
        if opt1 == 0:
            if opt2 == 1: # 바꾸기
                self.combo_opt2.setCurrentIndex(0)
            elif opt2 == 0:  # 찾기
                self.combo_opt2.setCurrentIndex(1)

    @pyqtSlot(str)
    def str_to_main(self, t):
        self.sig_test.emit(t)


class TableDoc(QTableWidget):
    sig_main_label = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['코드', '표제어', '비고'])
        self.horizontalScrollBar().setVisible(True)
        self.setAlternatingRowColors(True)
        self.setGridStyle(Qt.DotLine)
        self.hideColumn(0)
        self.verticalHeader().setDefaultSectionSize(23)
        # self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        # self.setSortingEnabled(True)
        self.set_data()
        self.shortcuts()

    def keyPressEvent(self, e):
        super().keyPressEvent(e) # 오버라이드하면서 기본 메서드 재활용

        if e.key() == Qt.Key_Return:
            self.sig_main_label.emit(self.currentItem().text())

        elif e.key() == Qt.Key_Delete: # 지우기
            self.setUpdatesEnabled(False)
            col_origin = self.currentColumn()
            rows_selected = self.rows_selected()
            if rows_selected:
                self.rows_delete(rows_selected)
                aaa = rows_selected[len(rows_selected) - 1] - len(rows_selected)
                if aaa + 1 == self.rowCount(): # 마지막 줄이면
                    added = 0
                else:
                    added = 1
                self.setCurrentCell(aaa + added, col_origin)
            self.setUpdatesEnabled(True)

    def shortcuts(self):
        move_up = QShortcut(QKeySequence('Ctrl+Shift+Up'), self, context=Qt.WidgetShortcut)
        move_up.activated.connect(self.method_move_up) # 한 칸 위로
        move_down = QShortcut(QKeySequence('Ctrl+Shift+Down'), self, context=Qt.WidgetShortcut)
        move_down.activated.connect(self.method_move_down) # 한 칸 아래로
        move_up = QShortcut(QKeySequence('Ctrl+Shift+Left'), self, context=Qt.WidgetShortcut)
        move_up.activated.connect(self.method_move_top) # 맨 위로
        move_up = QShortcut(QKeySequence('Ctrl+Shift+Right'), self, context=Qt.WidgetShortcut)
        move_up.activated.connect(self.method_move_bottom) # 맨 아래로

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
        # rows_list = self.rows_selected()
        item = []
        item_list = []
        if rows_list:
            for r in rows_list:
                for c in range(self.columnCount()):
                    item.append(self.item(r, c).text())
                item_list.append(item)
                item = []
        return item_list

    def rows_paste(self, copied_list, row_to_paste):
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
        # 어디로 가야 하나
        if where_to == 1: # 한 칸 위로
            if rows_selected[0] == 0: # 첫 줄이었으면
                row_where_to = 0
            else:
                row_where_to = rows_selected[0] - 1
        elif where_to == 2: # 한 칸 아래로
            row_last = rows_selected[len(rows_selected) - 1]
            if row_last - len(rows_selected) == self.rowCount() - 1: # 마지막 줄이었으면
                row_where_to = self.rowCount()  # - 1 - deletes['deleted']
            else:
                row_where_to = row_last + 2 - len(rows_selected)
        elif where_to == 3: # 맨 위로
            row_where_to = 0
        elif where_to == 4:  # 맨 아래로
            row_where_to = self.rowCount()
        # 새로운 current cell과 selection
        self.rows_paste(items, row_where_to)
        if where_to == 1 or where_to == 3:
            self.setCurrentCell(row_where_to, col_origin)
        elif where_to == 2 or where_to == 4:
            self.setCurrentCell(row_where_to + len(rows_selected) - 1, col_origin)
        aaaa = QTableWidgetSelectionRange(row_where_to, 0, row_where_to + len(rows_selected) - 1,
                                          self.columnCount() - 1)
        self.setRangeSelected(aaaa, True)
        self.setUpdatesEnabled(True)

    def set_data(self):
        start_time = time.time()
        doc_list = read_list()
        doc_num = len(doc_list)
        self.setRowCount(doc_num)
        for i in range(doc_num):
            item_code = QTableWidgetItem(doc_list[i]['code'])
            # item_code.setFlags(item_code.flags() ^ Qt.ItemIsEditable)
            item_title = QTableWidgetItem(doc_list[i]['title'])
            item_title.setFlags(item_title.flags() ^ Qt.ItemIsEditable)
            self.setItem(i, 0, item_code)
            self.setItem(i, 1, item_title)
            self.setItem(i, 2, QTableWidgetItem(''))
            # self.setItem(i, 2, QTableWidgetItem(doc_list[i]['option']))
            # self.setItem(i, 3, QTableWidgetItem(doc_list[i]['find']))
            # self.setItem(i, 4, QTableWidgetItem(doc_list[i]['replace']))
            # self.setItem(i, 5, QTableWidgetItem(doc_list[i]['summary']))
            # self.setItem(i, 6, QTableWidgetItem(doc_list[i]['error']))
        self.resizeColumnToContents(1)
        # self.resizeRowsToContents()
        # self.setColumnWidth()
        end_time = time.time()
        loading = end_time - start_time
        print(f'총 {loading}초 {doc_num}개 문서\n문서당 {loading / doc_num}초')
        print(self.rowCount())


class TableEdit(QTableWidget):
    sig_main_label = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['순', '1', '2', '3', '내용'])
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setGridStyle(Qt.DotLine)
        self.resizeColumnsToContents()
        self.verticalHeader().setDefaultSectionSize(23)
        # self.resizeRowsToContents()
        # self.sizePolicy().setVerticalStretch(7)
        # self.setEditTriggers(QAbstractItemView.NoEditTriggers)


class TabMicro(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        label_info = QLabel('언젠가 예정')
        box_v = QVBoxLayout()
        box_v.addWidget(label_info)
        self.setLayout(box_v)


if __name__ == '__main__':
    check_setting()
    mouse.on_right_click(get_click) ###

    # test_find = input('뭘 찾아서')
    # test_find = ''
    # test_replace = input('뭘 바꾸고')
    # test_replace = 'abcdefg'
    # test_option = input('어떻게')
    # test_option = 2
    # test_summary = ''
    # if test_option:

    '''
    start_t = time.time()

    test_req = Req()
    test_req.login()
    test_req.iterate(read_list())
        # do_edit_post()
        # do_get_xref()
        # get_cat(test_code)

    end_t = time.time()
    print(end_t - start_t)
    '''
    app = QApplication(sys.argv)
    win = MainWindow()
    sys.exit(app.exec_())