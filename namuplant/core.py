import re
import time
import winsound
from PySide2.QtCore import QObject, Slot, Signal
import requests
from bs4 import BeautifulSoup
from urllib import parse
import pyperclip
import keyboard
import difflib
from . import storage
SITE_URL = 'https://namu.wiki'

# todo 디도스 체크시 간헐적으로 정상 수행됐으면서 오류 띄우는 문제


def shorten(n: int, c='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'):
    t = ''
    while True:
        n, m = divmod(n, len(c))
        t = f'{c[m]}{t}'
        if n <= m:
            break
    return t


class SeedSession(QObject):
    sig_check_ddos = Signal(object)
    sig_label_text = Signal(str)

    def __init__(self):  # 반복 필요 없는 것
        super().__init__()
        self.is_ddos_checked = False
        self.URL_LOGIN = f'{SITE_URL}/member/login'
        self.s = requests.Session()

    def load_config(self, config):
        # config = storage.read_config('config.ini')
        self.INFO = config['login']
        self.DELAY = float(config['work']['DELAY'])

    def login(self):
        self.s = requests.Session()
        self.s.headers.update({'user-agent': self.INFO['UA']})
        self.request_soup('get', f'{SITE_URL}/edit/%EB%82%98%EB%AC%B4%EC%9C%84%ED%82%A4:%EB%8C%80%EB%AC%B8')
        self.s.cookies.set('umi', self.INFO['UMI'], domain=f'.{SITE_URL[8:]}')
        soup = self.request_soup('post', self.URL_LOGIN,
                                 data={'username': self.INFO['ID'], 'password': self.INFO['PW']})
        member = soup.select('nav > ul > li > div > div > div')
        if member[1].text == 'Member':
            print(f'login SUCCESS {member[0].text}')
        else:
            print('login FAILURE')

    def request_soup(self, method, url, **kwargs):  # 디도스 검사 리퀘스트
        # func = self.s.post if func == 'post' else self.s.get
        while True:
            try:
                r = self.s.request(method, url, headers={'referer': url}, cookies=self.s.cookies, timeout=5, **kwargs)
                # r = func(url, headers={'referer': url}, cookies=self.s.cookies, timeout=5, **kwargs)
                print(r.status_code)
                if r.status_code == 429:  # too many requests
                    self.is_ddos_checked = False
                    self.sig_check_ddos.emit(self)
                    while not self.is_ddos_checked:
                        time.sleep(0.1)
                    continue
                else:
                    return BeautifulSoup(r.text, 'html.parser')
            except requests.exceptions.Timeout:
                winsound.Beep(500, 50)

    # def requester(self):
    #     soup = ''
    #     while True:
    #         url, func, kwargs = (yield soup)
    #         soup = self.request_soup(url, func, **kwargs)


class ReqPost(SeedSession):
    sig_view_diff = Signal(str)

    def __init__(self):
        super().__init__()
        # self.edit_list = []
        self.diff_done = 1

    def get_text(self, doc_code):
        doc_url = f'{SITE_URL}/edit/{doc_code}'
        text = ''
        error_log = ''
        while True:
            soup = self.request_soup('get', doc_url)
            baserev = soup.find(attrs={'name': 'baserev'})['value']
            identifier = soup.find(attrs={'name': 'identifier'})['value']
            if identifier == f'm:{self.INFO["ID"]}':  # 로그인 안 되어 있으면 로그인
                break
            else:
                self.login()
        if baserev == '0':
            error_log = '문서가 존재하지 않습니다.'
        else:
            if self.is_over_perm(soup):
                error_log = '편집 권한이 없습니다.'
            if soup.textarea.contents:
                text = soup.textarea.contents[0]  # soup.find(attrs={'name': 'text'}).text

        return text, baserev, identifier, error_log

    def diff(self, before, after):
        if self.diff_done == 1 or self.diff_done == 4:
            self.diff_done = 0
            self.sig_view_diff.emit(self.diff_html(before, after))
            while self.diff_done == 0:  # 외부에서 diff_done 결정
                time.sleep(0.1)
        #
        if self.diff_done == 4:
            error_log = '편집을 적용하지 않았습니다.'
        elif self.diff_done == 5:
            error_log = '편집을 중단했습니다.'
        else:
            error_log = ''
        return error_log

    def post(self, doc_code, text, rev, identifier, summary=''):
        # identifier, baserev, text, error, log
        doc_url = f'{SITE_URL}/edit/{doc_code}'
        while True:
            soup = self.request_soup('post', doc_url)  # 가짜 포스트
            if self.is_captcha(soup):  # 서버 말고 편집창에 뜨는 리캡차
                self.login()
            else:
                break
        token = soup.find(attrs={'name': 'token'})['value']
        # 진짜 포스트
        soup = self.request_soup(
            'post', doc_url,
            data={'identifier': identifier, 'baserev': rev, 'text': text, 'log': summary, 'token': token, 'agree': 'Y'},
            files={'file': None})
        # 오류메시지
        error_log = self.has_alert(soup)
        return error_log

    @staticmethod
    def time_doc_log():
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    @staticmethod
    def time_edit_log(index):
        index = str(index)
        if '_' in index:
            index = index[index.rfind('_') + 1:]
        new = shorten(int(time.time()))
        return f'{new}_{index}'

    @Slot(int)
    def receive_diff_done(self, i):
        self.diff_done = i

    @staticmethod
    def is_captcha(soup):
        if '"captcha":true' in soup.text:
            return True  # 편집창 캡차 활성화됨
        else:
            return False

    @staticmethod
    def has_alert(soup):
        alert = soup.select('article > div > div.a.e')
        if alert:  # 편집기 오류 메시지
            winsound.Beep(500, 50)
            return alert[0].span.text  # 경고 문구
        else:
            return ''

    @staticmethod
    def is_over_perm(soup):
        if 'readonly' in soup.textarea.attrs:
            return True  # 편집 권한 없음
        else:
            return False

    @staticmethod
    def is_exist_edit(soup):  # /edit/
        if soup.small.text == '(새 문서 생성)':
            return False  # 존재하지 않는 문서
        else:
            return True

    @staticmethod
    def find_replace(edit_list):
        text, summary = '', ''
        comp, subs = [], []
        for edit in edit_list:  # 사전 컴파일 & 분석
            if edit[1] == '문서':
                if edit[2] == '수정':
                    if edit[3] == '텍스트':
                        if edit[4] == '찾기':
                            comp.append(edit[5])
                        elif edit[4] == '바꾸기':
                            subs.append(edit[5])
                        elif edit[4] == '지우기':
                            comp.append(edit[5])
                            subs.append('')
                    elif edit[3] == '정규식':
                        if edit[4] == '찾기':
                            comp.append(re.compile(edit[5]))
                        elif edit[4] == '바꾸기':
                            subs.append(edit[5])
                        elif edit[4] == '지우기':
                            comp.append(re.compile(edit[5]))
                            subs.append('')
                    elif edit[3] == '분류:':
                        if edit[4] == '찾기':
                            comp.append(re.compile(rf'\[\[분류: ?{re.escape(edit[5])}(?P<blur>#blur)?\]\]'))
                        elif edit[4] == '바꾸기':
                            subs.append(rf'[[분류:{edit[5]}\g<blur>]]')
                        elif edit[4] == '지우기':
                            comp.append(re.compile(rf'\[\[분류: ?{re.escape(edit[5])}.*?\]\]'))
                            subs.append('')
                    elif edit[3] == '링크':
                        if edit[4] == '찾기':
                            comp.append(
                                re.compile(rf'(?P<b>(?P<a>\|\|)?(?(a)|\|))?\[\[{re.escape(edit[5])}'
                                           rf'((?P<c>\||#)|(?P<f>\]))(?P<d>(.|\n)*?)(?P<e>(?(a)|(?(b)\]\]|))(?(f)\]|\]\]))'))
                        elif edit[4] == '바꾸기':
                            if '|' in edit[5]:  # a -> a|b
                                tmp_a = edit[5][:edit[5].find('|')]
                                tmp_b = edit[5][edit[5].find('|') + 1:]
                                subs.append(rf'\g<b>[[{tmp_a}\g<c>\g<d>|{tmp_b}\g<f>\g<e>')
                                # [[a|b|c]]인 경우
                                comp.append(
                                    re.compile(rf'\[\[{re.escape(tmp_a)}(?P<a>|#.*?)(?P<b>\|.*?)\|{re.escape(tmp_b)}\]\]'))
                                subs.append(rf'[[{tmp_a}\g<a>\g<b>]]')
                            else:  # a -> b
                                subs.append(rf'\g<b>[[{edit[5]}\g<c>\g<d>\g<f>\g<e>')
                                # [[a|a]]인 경우
                                comp.append(re.compile(rf'\[\[{re.escape(edit[5])}(?P<a>|#.*?)\|{re.escape(edit[5])}\]\]'))
                                subs.append(rf'[[{edit[5]}\g<a>]]')
                        elif edit[4] == '지우기':
                            comp.append(
                                re.compile(rf'(?P<b>(?P<a>\|\|)?(?(a)|\|))?\[\[{re.escape(edit[5])}'
                                           rf'(\||(?P<f>\])|#)(.|\n)*?(?P<c>(?(a)|(?(b)\]\]|)))(?(f)\]|\]\])'))
                            subs.append(r'\g<a>\g<c>')
                    elif edit[3] == '포함':
                        if edit[4] == '찾기':
                            comp.append(re.compile(rf'\[(?i:include)\({re.escape(edit[5])}(?P<after>.*?\)\])'))
                        elif edit[4] == '바꾸기':
                            subs.append(rf'[include({edit[5]}\g<after>')
                        elif edit[4] == '지우기':
                            comp.append(re.compile(rf'\[(?i:include)\({re.escape(edit[5])}.*?\)\]( +)?(\n|$)'))
                            subs.append('')
                elif edit[2] == '삽입':
                    if edit[4] == '맨 앞':
                        comp.append(re.compile(r'^'))
                        subs.append(f'{edit[5]}\n')
                    elif edit[4] == '맨 뒤':
                        comp.append(re.compile(r'$'))
                        subs.append(f'\n{edit[5]}')
                    elif edit[4] == '분류 뒤':
                        pass
            elif edit[1] == '요약':
                summary = edit[5]
        while True:
            text = (yield text, summary)
            for i in range(len(comp)):
                if type(comp[i]) is re.Pattern:  # 정규식
                    try:
                        text = comp[i].sub(subs[i], text)
                    except re.error:
                        continue
                else:
                    text = text.replace(comp[i], subs[i])

    def get_acl(self):
        pass

    @staticmethod
    def diff_html(before, after):
        return difflib.HtmlDiff().make_file(before.splitlines(keepends=True),
                                            after.splitlines(keepends=True),
                                            context=True, numlines=2, charset='utf-8') \
            .replace('&nbsp;', ' ') \
            .replace('<td nowrap="nowrap">', '<td>') \
            .replace('table.diff {font-family:Courier; border:medium;}',
                     'table.diff {border:medium; width:100%; word-break:break-all; word-wrap:break-word;'
                     'padding:0px; line-height:150%; font-size:10pt;}') \
            .replace('.diff_header {text-align:right}',
                     '.diff_header {text-align:right; vertical-align:top;'
                     'word-break:normal; word-wrap:normal;}'
                     '\n\t\t\t.diff_none {background-color:#eeeedd; text-align:right;}') \
            .replace('<tbody>', '') \
            .replace('</tbody>', '\t<tr><td class="diff_none"></td><td class="diff_none">...</td>'
                                 '<td class="diff_none"></td>'
                                 '<td class="diff_none"> </td><td class="diff_none">...</td>'
                                 '<td class="diff_none"></td></tr>') \
            .replace('<td>', '<td width="45%">', 2) \
            .replace('No Differences Found', '변경 사항 없음') \
            .replace('Legends', '색인')

    @staticmethod
    def korean_consonant(text):
        share = (ord(text[0]) - 44032) // 588
        consonant = ['ㄱ', 'ㄱ', 'ㄴ', 'ㄷ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅂ', 'ㅅ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅈ', 'ㅊ',
                     'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        if 0 <= share <= 18:
            return consonant[share]

    @staticmethod
    def is_file_exist(soup):
        element = soup.select('article > div > a')
        if element:
            if element[0].text == '[더보기]':
                return True
        return False


class Iterate(ReqPost):
    sig_doc_remove = Signal(int)
    sig_doc_set_current = Signal(int)
    sig_doc_error = Signal(int, str)
    sig_enable_pause = Signal(bool)
    finished = Signal()

    def __init__(self):
        super().__init__()
        # logged_in = self.login()
        # self.sig_label_text.emit(logged_in)
        self.is_quit = False
        self.doc_list = []  # main.iterate_start
        self.edit_dict = {}
        self.index_speed = 0

    def work(self):
        edit_index = 0
        edit_row, deleted, deleted_temp = 0, 0, 0
        edit_log_index, upload_t, upload_s = '', '', ''
        t1 = time.time()
        total = len(self.doc_list)
        if len(self.doc_list) == 0 or len(self.edit_dict) == 0:  # 값이 없음
            self.sig_label_text.emit('작업을 시작할 수 없습니다. 목록을 확인해주세요.')
        else:
            doc_logger = storage.write_csv('doc_log.csv', 'a', 'doc')
            doc_logger.send(None)
            edit_logger = storage.write_csv('edit_log.csv', 'a', 'edit')
            edit_logger.send(None)
            self.sig_label_text.emit('작업을 시작합니다.')
            # 본작업 루프 시작
            for i in range(len(self.doc_list)):  # 0 code, 1 title, 2 etc
                self.sig_doc_set_current.emit(i - deleted)
                if self.is_quit:  # 정지 버튼 눌려있으면 중단
                    self.sig_label_text.emit('작업이 정지되었습니다.')
                    break
                if self.doc_list[i][0][0] == '#':  # 편집 지시자
                    if i > 0 and i - edit_row - 1 == deleted_temp:  # 해당 지시자 쓰는 문서 편집 모두 성공하면
                        self.sig_doc_remove.emit(edit_row - deleted)  # 더는 쓸모 없으니까 지시자 지움
                        deleted += 1
                        deleted_temp = 0
                    if self.diff_done == 2:  # 그룹 실행의 편집 그룹이 종료되어 초기화. 모두 실행(3)은 초기화 안 함
                        self.diff_done = 1
                    edit_row = i
                    edit_index = self.doc_list[i][0][1:]  # 편집사항 순번
                    self.sig_label_text.emit(f'편집사항 {edit_index}번 진행 중입니다.')
                    upload_t, upload_s = '', ''
                    if self.edit_dict[edit_index][0][1] == '파일':  # 업로드 시에는 반드시 요약보다 파일이 앞에 와야 됨
                        upload_t, upload_s = self.upload_text(self.edit_dict[edit_index])  # 파일 문서 텍스트, 요약
                    else:
                        replacer = self.find_replace(self.edit_dict[edit_index])
                        replacer.send(None)
                    edit_log_index = self.time_edit_log(edit_index)
                    for row in self.edit_dict[edit_index]:
                        edit_logger.send({'index': edit_log_index,
                                          'opt1': row[1], 'opt2': row[2], 'opt3': row[3], 'opt4': row[4], 'edit': row[5]})
                elif self.doc_list[i][0][0] == '!':  # 중단자
                    self.sig_label_text.emit('작업이 중단되었습니다.')
                    self.sig_doc_remove.emit(i - deleted)
                    break
                else:  # 문서, 파일
                    if i > 0:  # 목록 처음이 편집 지시자가 아닌 경우만
                        label = f'( {i + 1} / {total} ) {self.doc_list[i][1]}'
                        self.sig_label_text.emit(label)

                        if self.doc_list[i][0][0] == '$':  # 파일. 0번열의 0번째 문자가 $
                            post_error = self.upload(self.doc_list[i][0][1:], self.doc_list[i][1], upload_t, upload_s)
                            doc_logger.send({'code': self.doc_list[i][0], 'title': self.doc_list[i][1],
                                             'rev': f'r0', 'time': self.time_doc_log(),
                                             'index': edit_log_index, 'error': post_error})
                        else:  # 문서
                            if self.edit_dict[edit_index][0][1] == '복구':
                                post_error = self.revert(self.doc_list[i][0], self.edit_dict[edit_index],
                                                         self.doc_list[i][2])
                                post_rev = 'evert'
                            else:  # 편집
                                post_rev, post_error = self.edit(self.doc_list[i][0], self.doc_list[i][1], replacer)

                            doc_logger.send({'code': self.doc_list[i][0], 'title': self.doc_list[i][1],
                                             'rev': f'r{post_rev}', 'time': self.time_doc_log(),
                                             'index': edit_log_index, 'error': post_error})
                        if self.index_speed == 1:  # 저속 옵션
                            t2 = time.time()
                            waiting = self.DELAY - (t2 - t1)
                            if waiting > 0:
                                time.sleep(waiting)
                            t1 = time.time()
                        if post_error:  # 에러 발생
                            self.sig_label_text.emit(f'{label}\n{post_error}')
                            self.sig_doc_error.emit(i - deleted, post_error)
                        else:  # 정상
                            self.sig_doc_remove.emit(i - deleted)
                            deleted += 1
                            deleted_temp += 1
                        if self.diff_done == 5:
                            self.sig_label_text.emit('편집 비교 중 작업을 중단하였습니다.')
                            break
                    else:
                        self.sig_label_text.emit('첫 행에 편집 사항이 지정되어있지 않습니다.')
                        break
                if i == len(self.doc_list) - 1:  # 마지막 행
                    if i - edit_row == deleted_temp:  # 해당 지시자 쓰는 문서 편집 모두 성공하면
                        self.sig_doc_remove.emit(edit_row)  # 더는 쓸모 없으니까 지시자 지움
                    self.sig_label_text.emit('작업이 모두 완료되었습니다.')
            doc_logger.close()
            edit_logger.close()
        self.finished.emit()

    def edit(self, doc_code, doc_name, replacer):
        # 획득
        text_before, baserev, identifier, error = self.get_text(doc_code)
        # data = self.get_text(doc_code)  # identifier, baserev, text, error
        if not error:  # 권한 X, 문서 X
            # 변경
            # text_after, summary = self.find_replace(text_before, edit_list, doc_name)
            text_after, summary = replacer.send(text_before)
            # 비교
            self.sig_enable_pause.emit(False)
            error = self.diff(text_before, text_after)
            self.sig_enable_pause.emit(True)
            if not error:  # 건너 뜀, 중단함
                # 전송
                error = self.post(doc_code, text_after, baserev, identifier, summary)  # 서버 오류 메시지
        return baserev, error

    def revert(self, doc_code, edit_list, rev_on_doc):
        rev, summary, error_log = '', '', ''
        for edit in edit_list:
            if edit[1] == '복구':
                if edit[4] == '로그':
                    if rev_on_doc[0] == 'r' and rev_on_doc[1:].isdigit():
                        rev = rev_on_doc[1:]
                else:  # '지정'
                    rev = edit[5]
            elif edit[1] == '요약':
                summary = edit[5]
        if not rev:
            error_log = '되돌릴 리비전이 지정되어 있지 않습니다.'
        else:
            while True:
                soup = self.request_soup('post', f'{SITE_URL}/revert/{doc_code}',
                                         data={'rev': rev, 'identifier': f'm:{self.INFO["ID"]}', 'log': summary})
                print(soup.text)
                if soup.h1.text == '오류':
                    error_temp = soup.select('article > div')[0].text
                    if error_temp == 'reCAPTCHA 인증이 실패했습니다.':  # 로그인 확인용
                        self.login()
                    else:
                        error_log = error_temp
                        break
                else:
                    break
        return error_log

    def upload(self, file_dir, doc_name, text, summary):
        doc_url = f'{SITE_URL}/Upload'
        if not summary:
            summary = f'파일 {file_dir[file_dir.rfind("/") + 1:]}을 올림'
        multi_data = {'baserev': '0', 'identifier': f'm:{self.INFO["ID"]}', 'document': doc_name, 'log': summary,
                      'text': text}
        try:
            with open(file_dir, 'rb') as f:
                while True:
                    soup = self.request_soup('post', doc_url, data=multi_data, files={'file': f})
                    if self.is_captcha(soup):
                        self.login()
                    else:
                        break
            error_log = self.has_alert(soup)
        except FileNotFoundError:
            winsound.Beep(500, 50)
            error_log = '파일을 찾을 수 없습니다.'
        # self.post_log(file_dir, doc_name, '0', error_log)
        return error_log

    @staticmethod
    def upload_text(edit_list, summary=''):
        data = {'cite': '', 'date': '', 'author': '', 'etc': '', 'explain': '', 'lic': '제한적 이용', 'cat': ''}
        for edit in edit_list:
            if edit[1] == '파일':
                if edit[3] == '본문':
                    if edit[4] == '출처':
                        data['cite'] = edit[5]
                    elif edit[4] == '날짜':
                        data['date'] = edit[5]
                    elif edit[4] == '저작자':
                        data['author'] = edit[5]
                    elif edit[4] == '기타':
                        data['etc'] = edit[5]
                    elif edit[4] == '설명':
                        data['explain'] = edit[5]
                elif edit[3] == '분류:':
                    data['cat'] = edit[5]
                elif edit[3] == '라이선스':
                    data['lic'] = edit[5]
            elif edit[1] == '요약':
                summary = edit[5]
        return f'[include(틀:이미지 라이선스/{data["lic"]})]\n[[분류:{data["cat"]}]]' \
               f'\n[목차]\n\n== 기본 정보 ==\n|| 출처 || {data["cite"]} ||\n|| 날짜 || {data["date"]} ||' \
               f'\n|| 저작자 || {data["author"]} ||\n|| 저작권 || {data["lic"]} ||\n|| 기타 || {data["etc"]} ||' \
               f'\n\n== 이미지 설명 ==\n{data["explain"]}', summary


class Micro(ReqPost):
    sig_do_edit = Signal(str)
    sig_text_view = Signal(str, str, bool)
    sig_image_view = Signal(str)
    sig_text_edit = Signal(str)
    sig_enable_iterate = Signal(bool)
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.data = {}
        self.edits = []
        self.doc_code = ''
        self.text = ''
        self.do_post = False
        self.do_cancel = False
        self.mode = 0

    def work(self):
        if self.mode == 0:
            self.view()
        elif self.mode == 1:
            self.edit()

    def view(self):
        editable = False
        doc_name = parse.unquote(self.doc_code)
        if self.doc_code[0] == '$':  # 파일
            if len(doc_name) > 50:
                doc_name = f'...{doc_name[-50:]}'
            label = f'\'{doc_name[1:]}\' 파일을 열람중입니다.'
            self.sig_image_view.emit(self.doc_code[1:])
        else:
            if self.doc_code[0] == '#':  # 편집 지시자
                label = f'{doc_name[1:]}번 편집사항을 열람 중입니다.'
                text = f'{doc_name[1:]}번 편집사항'
            elif self.doc_code[0] == '!':  # 중단자
                label = '중단점을 열람 중입니다.'
                text = '중단점'
            else:  # 문서
                text, _, _, _ = self.get_text(self.doc_code)
                # data = self.get_text(self.doc_code)
                if text:
                    label = f'<a href=\"{SITE_URL}/w/{self.doc_code}\">{doc_name}</a> 문서를 열람 중입니다.'
                    editable = True
                else:  # 문서 존재 X
                    label = f'\'{doc_name}\' 문서는 존재하지 않습니다.'
                    text = '존재하지 않는 문서입니다.'
            self.sig_text_view.emit(self.doc_code, text, editable)
        self.sig_label_text.emit(label)
        self.finished.emit()

    def edit(self):
        # todo 편집 루프 제네레이터로 변경
        # todo 비교 시 취소하면 편집 종료되는 문제

        self.do_post = False
        self.do_cancel = False
        text_before, baserev, identifier, error = self.get_text(self.doc_code)
        # data = self.get_text(self.doc_code)
        doc_name = parse.unquote(self.doc_code)
        if error:  # 권한 X
            self.sig_label_text.emit(f'<a href=\"{SITE_URL}/w/{self.doc_code}\">{doc_name}</a> 문서를 편집할 권한이 없습니다.')
        else:
            self.sig_enable_iterate.emit(False)
            self.sig_text_edit.emit(text_before)
            self.sig_label_text.emit(f'<a href=\"{SITE_URL}/w/{self.doc_code}\">{doc_name}</a> 문서를 편집 중입니다.')
            while not self.do_post:
                time.sleep(0.1)
            if self.do_cancel:
                error = '편집을 취소했습니다.'
            else:
                # 비교
                error = self.diff(text_before, self.text)
                if not error:
                    # 전송
                    doc_logger = storage.write_csv('doc_log.csv', 'a', 'doc')
                    doc_logger.send(None)
                    error = self.post(self.doc_code, self.text, baserev, identifier)
                    doc_logger.send({'code': self.doc_code, 'title': doc_name, 'rev': f'r{baserev}',
                                     'time': self.time_doc_log(), 'index': '', 'error': error})
                    doc_logger.close()
            self.sig_enable_iterate.emit(True)
        self.finished.emit()

    def apply(self, text_before, edit_list):
        replacer = self.find_replace(edit_list)
        replacer.send(None)
        text_after, _ = replacer.send(text_before)
        return text_after
        # error = self.diff(text_before, text_after)
        # if error:
        #     return text_before
        # else:
        #     return text_after


class ReqGet(SeedSession):
    send_code_list = Signal(list)
    finished = Signal()

    def __init__(self, doc_insert):
        super().__init__()
        self.is_quit = False
        self.option = 0
        self.mode = 0  # 직접 입력
        self.code = ''
        self.doc_insert = doc_insert

    def work(self):
        if self.mode == 1:  # 클릭 얻기
            self.code = self.copy_url()
        self.doc_insert.send(None)
        if self.code:  # 직접 입력은 외부에서 조달
            if self.option == 0:  # 1개
                code = self.get_one(self.code)
                if code:
                    self.doc_insert.send([code, parse.unquote(code), ''])
            elif self.option == 1:  # 역링크
                for code in self.get_backlink(self.code):
                    self.doc_insert.send([code, parse.unquote(code), ''])
            elif self.option == 2:  # 분류
                if parse.unquote(self.code)[:3] == '분류:':
                    for code in self.get_cat(self.code):
                        self.doc_insert.send([code, parse.unquote(code), ''])
                else:
                    self.sig_label_text.emit('해당 문서는 분류 문서가 아닙니다.')
                    winsound.Beep(500, 50)
            elif self.option == 3:  # 파일
                if self.mode == 1:
                    self.sig_label_text.emit('이미지 파일은 우클릭으로 추가할 수 없습니다.')
                    winsound.Beep(500, 50)
        else:
            self.sig_label_text.emit('올바른 URL을 찾을 수 없습니다.')
            winsound.Beep(500, 50)
        self.finished.emit()

    def copy_url(self):
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

    @staticmethod
    def is_exist_read(soup):  # /w/
        if soup.select('article > div > p'):
            return False  # 존재하지 않는 문서
        else:
            return True

    @staticmethod
    def get_redirect(url):
        pass

    @staticmethod
    def get_code(url):
        if url.find(SITE_URL) >= 0:
            search = re.search(rf'{SITE_URL}/\w+/(.*?)($|#|\?)', url).group(1)
            if search:
                return search
            else:
                return ''
        else:
            return ''

    def get_one(self, doc_code):  # 존재여부 검사
        doc_name = parse.unquote(doc_code)
        if self.is_exist_read(self.request_soup('get', f'{SITE_URL}/w/{doc_code}')):
            self.sig_label_text.emit(f'\'{doc_name}\' 문서를 목록에 추가했습니다.')
            return doc_code
        else:
            self.sig_label_text.emit(f'\'{doc_name}\' 문서는 존재하지 않습니다.')

    def get_backlink(self, doc_code):
        total = 0
        doc_name = parse.unquote(doc_code)
        soup = self.request_soup('get', f'{SITE_URL}/backlink/{doc_code}')
        for namespace in list(map(lambda x: parse.quote(x.get('value')), soup.select('select:nth-child(2) > option'))):
            tail = ''
            while True:
                if self.is_quit:
                    self.sig_label_text.emit(f'정지 버튼을 눌러 중지되었습니다.'
                                             f'\n\'{doc_name}\'의 역링크 문서를 {total}개 가져왔습니다.')
                    return
                self.sig_label_text.emit(f'{doc_name}의 역링크 {parse.unquote(namespace)} 가져오는 중... ( +{total} )'
                                         f'\n{parse.unquote(tail[5:-1])}')
                # soup = self.request_soup(f'{SITE_URL}/backlink/{doc_code}?namespace={namespace}{added}', 'get')
                soup = self.request_soup('get', f'{SITE_URL}/backlink/{doc_code}?{tail}namespace={namespace}&flag=0')
                for v in soup.select('article > div > div > div > ul > li > a'):  # 표제어 목록
                    if not v.next_sibling[2:-1] == 'redirect':
                        yield v.get('href')[3:]
                        total += 1
                tail = soup.select('article > div > div > a')[3].get('href')  # 앞뒤 버튼 중 뒤 버튼
                if not tail:  # 없으면 다음 스페이스로
                    break
                else:
                    tail = tail[tail.find('?from=') + 1:tail.find('&') + 1]
                    # added = added[added.find('?from'):].replace('\'', '%27')
        self.sig_label_text.emit(f'\'{doc_name}\'의 역링크 문서를 {total}개 가져왔습니다.')

    def get_cat(self, doc_code):
        total = 0
        doc_name = parse.unquote(doc_code)
        soup = self.request_soup('get', f'{SITE_URL}/w/{doc_code}')
        spaces = soup.select('.cl')
        for i in range(len(spaces)):
            name = (lambda x: x[x.rfind(' ') + 1:])(spaces[i].select('h2')[0].text)
            self.sig_label_text.emit(f'{doc_name}의 하위 {name} 가져오는 중... ( +{total} )\n')
            for v in spaces[i].select('ul > li > a'):
                yield v.get('href')[3:]
                total += 1
            if spaces[i].select('div > div > a'):  # 다음 버튼
                tail = (lambda x: x[x.find('?namespace='):])(spaces[i].select('div > div > a')[1].get('href'))
                while True:
                    if self.is_quit:
                        self.sig_label_text.emit(f'정지 버튼을 눌러 중지되었습니다.'
                                                 f'\n\'{doc_name}\'에 분류된 문서를 {total}개 가져왔습니다.')
                        return
                    else:
                        new_soup = self.request_soup('get', f'{SITE_URL}/w/{doc_code}{tail}')
                        for v in new_soup.select('.cl')[i].select('ul > li > a'):
                            yield v.get('href')[3:]
                            total += 1
                        tail = (lambda x: '' if x is None else x[x.find('?namespace='):])(
                            new_soup.select('.cl')[i].select('div > div > a')[1].get('href'))
                        if not tail:
                            break
        self.sig_label_text.emit(f'\'{doc_name}\'에 분류된 문서를 {total}개 가져왔습니다.')