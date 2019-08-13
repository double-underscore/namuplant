import re
import time
import winsound
from PySide2.QtCore import QObject, Slot, Signal
import requests
from bs4 import BeautifulSoup
from urllib import parse
import pyperclip
import keyboard

from namuplant import storage

site_url = 'https://namu.wiki'


class SeedSession(QObject):
    sig_check_ddos = Signal(object)

    def __init__(self):  # 반복 필요 없는 것
        super().__init__()
        self.is_checked = False
        self.CONFIG = storage.read_setting('config.ini')
        self.URL_LOGIN = f'{site_url}/member/login'

    def login(self):
        self.s = requests.Session()
        self.s.headers.update({'user-agent': self.CONFIG['UA']})
        self.ddos_check(f'{site_url}/edit/%EB%82%98%EB%AC%B4%EC%9C%84%ED%82%A4:%EB%8C%80%EB%AC%B8', funcs=self.s.get)
        self.s.cookies.set('umi', self.CONFIG['UMI'], domain=f'.{site_url[8:]}')
        soup = self.ddos_check(self.URL_LOGIN, funcs=self.s.post, headers=self.make_header(self.URL_LOGIN),
                               cookies=self.s.cookies, data={'username': self.CONFIG['ID'], 'password': self.CONFIG['PW']})
        info = soup.select('body > div.navbar-wrapper > nav > ul.nav.navbar-nav.pull-right >'
                           'li > div > div.dropdown-item.user-info > div > div')
        if info[1].text == 'Member':
            return f'login SUCCESS {info[0].text}'
        else:
            return 'login FAILURE'

    def ddos_check(self, url, funcs=requests.get, **kwargs):
        while True:
            if 'files' in kwargs:
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
                    continue
                else:
                    return soup
            else:  # for raw page
                return soup

    @Slot(bool)
    def receive_checked(self, b):
        self.is_checked = b

    @classmethod
    def make_header(cls, url):
        return {'referer': url}


class ReqPost(SeedSession):
    def __init__(self):
        super().__init__()
        # self.login()

    def post(self, doc_code, edit_list):
        doc_url = f'{site_url}/edit/{doc_code}'
        soup = self.ddos_check(doc_url, funcs=self.s.get, headers=self.make_header(doc_url), cookies=self.s.cookies)  # 겟
        baserev = soup.find(attrs={'name': 'baserev'})['value']
        if self.is_over_perm(soup):
            error_log = '편집 권한이 없습니다.'
        elif self.is_not_exist(soup):
            error_log = '문서가 존재하지 않습니다.'
        else:
            doc_text = soup.textarea.contents[0]  # soup.find(attrs={'name': 'text'}).text
            identifier = soup.find(attrs={'name': 'identifier'})['value']
            if f'm:{self.CONFIG["ID"]}' == identifier:
                pass
            # 변경
            doc_some = self.find_replace(doc_text, edit_list, parse.unquote(doc_code))  # 0 텍스트 1 요약
            # 포0
            soup = self.ddos_check(doc_url, funcs=self.s.post, headers=self.make_header(doc_url),
                                   cookies=self.s.cookies)  # 포0
            if self.is_captcha(soup):  # 서버 말고 편집창에 뜨는 리캡차
                return {'rerun': True}
            else:
                token = soup.find(attrs={'name': 'token'})['value']
                # 포1
                multi_data = {'token': token, 'identifier': identifier, 'baserev': baserev, 'text': doc_some[0],
                              'log': doc_some[1], 'agree': 'Y'}
                soup = self.ddos_check(doc_url, funcs=self.s.post, headers=self.make_header(doc_url), cookies=self.s.cookies,
                                       data=multi_data, files={'file': None})  # 포1
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
    def is_captcha(cls, soup):
        element = soup.select('#recaptcha')
        if element:
            return True  # 편집창 캡차 활성화됨
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

    @classmethod
    def find_replace(cls, text, edit_list, title=''):
        find_temp = ''
        summary = ''
        option_temp = ''
        for edit in edit_list:  # 0 num, 1 opt1, 2 opt2, 3 opt3, 4 text
            if edit[1] == '일반':  # 문서 내 모든 텍스트
                if edit[2] == '찾기':
                    option_temp = edit[3]
                    find_temp = edit[4]
                elif edit[2] == '바꾸기':
                    if option_temp == '일반':
                        text = text.replace(find_temp, edit[4])
                    elif option_temp == '정규식':
                        text = re.sub(find_temp, edit[4], text)
                elif edit[2] == '넣기':
                    if edit[3] == '맨 앞':
                        text = f'{edit[4]}\n{text}'
                    elif edit[3] == '맨 뒤':
                        text = f'{text}\n{edit[4]}'
                    elif edit[3] == '분류':
                        text = re.sub(r'(\[\[분류:.*?\]\].*?)(\n|$)', rf'\g<1>{edit[4]}\g<2>', text)
            elif edit[1] == '기타':
                pass
            elif edit[1] == '요약':  # 편집요약
                summary = edit[4]
            elif edit[1] == '복구':  # 복구 옵션
                pass
        return [text, summary]

    @classmethod
    def convert_title_hangul(cls, title):
        t = ord(title[0])
        j = ''
        if 44032 <= t < 45208:
            j = 'ㄱ'
        elif 45208 <= t < 45796:
            j = 'ㄴ'
        elif 45796 <= t < 46972:
            j = 'ㄷ'
        elif 46972 <= t < 47560:
            j = 'ㄹ'
        elif 47560 <= t < 48148:
            j = 'ㅁ'
        elif 48148 <= t < 49324:
            j = 'ㅂ'
        elif 49324 <= t < 50500:
            j = 'ㅅ'
        elif 50500 <= t < 51088:
            j = 'ㅇ'
        elif 51088 <= t < 52264:
            j = 'ㅈ'
        elif 52264 <= t < 52852:
            j = 'ㅊ'
        elif 52852 <= t < 53440:
            j = 'ㅋ'
        elif 53440 <= t < 54028:
            j = 'ㅌ'
        elif 54028 <= t < 54616:
            j = 'ㅍ'
        elif 54616 <= t < 55204:
            j = 'ㅎ'
        return j

    def upload(self, file_dir, doc_name, edit_list):
        doc_url = f'{site_url}/Upload'
        data = {'cite': '', 'date': '', 'author': '', 'etc': '', 'explain': '', 'lic': '제한적 이용', 'cat': ''}
        summary = f'파일 {file_dir[file_dir.rfind("/") + 1:]}을 올림'
        for edit in edit_list:
            if edit[1] == '파일':
                if edit[2] == '본문':
                    if edit[3] == '출처':
                        data['cite'] = edit[4]
                    elif edit[3] == '날짜':
                        data['date'] = edit[4]
                    elif edit[3] == '저작자':
                        data['author'] = edit[4]
                    elif edit[3] == '기타':
                        data['etc'] = edit[4]
                    elif edit[3] == '설명':
                        data['explain'] = edit[4]
                elif edit[2] == '분류':
                    data['cat'] = edit[4]
                elif edit[2] == '라이선스':
                    data['lic'] = edit[4]
            elif edit[1] == '요약':
                summary = edit[4]
        text = f'[include(틀:이미지 라이선스/{data["lic"]})]\n[[분류:{data["cat"]}]]' \
               f'\n[목차]\n\n== 기본 정보 ==\n|| 출처 || {data["cite"]} ||\n|| 날짜 || {data["date"]} ||' \
               f'\n|| 저작자 || {data["author"]} ||\n|| 저작권 || {data["lic"]} ||\n|| 기타 || {data["etc"]} ||' \
               f'\n\n== 이미지 설명 ==\n{data["explain"]}'
        multi_data = {'baserev': '0', 'identifier': f'm:{self.CONFIG["ID"]}', 'document': doc_name, 'log': summary, 'text': text}
        with open(file_dir, 'rb') as f:
            soup = self.ddos_check(doc_url, funcs=self.s.post, headers=self.make_header(doc_url), cookies=self.s.cookies,
                                   data=multi_data, files={'file': f})
        if self.is_captcha(soup):
            return {'rerun': True}
        else:
            alert = soup.select('.alert-danger')
            if alert:  # 편집기 오류 메시지
                winsound.Beep(500, 50)
                error_log = alert[0].strong.next_sibling.strip()
            else:  # 성공
                print('UPLOAD success')
                error_log = ''
            return {'rerun': False, 'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                    'rev': '0', 'error': error_log}

    @classmethod
    def is_file_exist(cls, soup):
        element = soup.select('article > div > div > a')
        if element:
            if element[0].text == '[더보기]':
                return True
        return False


class ReqGet(SeedSession):
    send_code_list = Signal(list)
    label_text = Signal(str)
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.s = requests.Session()
        self.is_quit = False
        self.option = 0

    def work(self):
        code = self.get_url()
        codes = []
        print('self option at work', self.option)
        if code:
            if self.option == 0:  # 1개
                code_unquote = parse.unquote(code)
                codes = [[code], f'\'{code_unquote}\' 문서를 목록에 추가했습니다.']
            elif self.option == 1:  # 역링크
                codes = self.get_xref(code)
            elif self.option == 2:  # 분류
                if parse.unquote(code)[:3] == '분류:':
                    codes = self.get_cat(code)
                else:
                    codes = [[], '해당 문서는 분류 문서가 아닙니다.']
                    winsound.Beep(500, 50)
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

    @classmethod
    def get_redirect(cls, url):
        pass

    @classmethod
    def get_code(cls, url):
        if url.find(site_url) >= 0:
            search = re.search(rf'{site_url}/\w+/(.*?)($|#|\?)', url).group(1)
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
        soup = self.ddos_check(f'{site_url}/xref/{doc_code}', funcs=self.s.get)
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
                soup = self.ddos_check(f'{site_url}/xref/{doc_code}?namespace={namespace}{added}', funcs=self.s.get)
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
        return [list_ref, f'\'{doc_name}\'의 역링크 문서를 {total}개 가져왔습니다.']

    def get_cat(self, doc_code):
        total = 0
        n = 0
        doc_name = parse.unquote(doc_code)
        list_cat = []
        btn_done = 0
        added = ''
        soup = self.ddos_check(f'{site_url}/w/{doc_code}', funcs=self.s.get)
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
                        soup_new = self.ddos_check(f'{site_url}/w/{doc_code}{added}', funcs=self.s.get)
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
    label_text = Signal(str)
    doc_remove = Signal(int)
    doc_set_current = Signal(int)
    doc_error = Signal(int, str)
    finished = Signal()

    def __init__(self):
        super().__init__()
        logged_in = self.login()
        self.label_text.emit(logged_in)
        self.is_quit = False
        self.doc_list = []
        self.edit_list = []
        self.index_speed = 0

    def work(self):
        edit_temp = []
        edit_row = 0
        deleted = 0
        deleted_temp = 0
        t1 = time.time()
        total = len(self.doc_list)
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
                if self.doc_list[i][0][0] == '#':  # 편집 지시자
                    if i > 0 and i - edit_row - 1 == deleted_temp:  # 해당 지시자 쓰는 문서 편집 모두 성공하면
                        self.doc_remove.emit(edit_row - deleted)  # 더는 쓸모 없으니까 지시자 지움
                        deleted += 1
                        deleted_temp = 0
                    edit_row = i
                    edit_num = int(self.doc_list[i][0][1:])
                    # edit_num = re.sub(r'#(\d+)', '\g<1>', self.doc_list[i][0])
                    self.label_text.emit(f'편집사항 {edit_num}번 진행 중입니다.')
                    edit_temp = self.edit_list[edit_num - 1]  # 순번이 1이면 0번 항목
                    edit_temp_to_write = []
                    for edit in edit_temp:
                        edit_temp_to_write.append({'code': self.doc_list[i][0], 'title': self.doc_list[i][1],
                                                   'opt1': edit[1], 'opt2': edit[2], 'opt3': edit[3],
                                                   'edit': edit[4], 'time': '', 'rev': '', 'error': ''})
                    storage.write_csv('edit_log.csv', 'a', storage.LOG_FIELD, edit_temp_to_write)
                elif self.doc_list[i][0][0] == '^':  # 중단자
                    self.label_text.emit('작업이 중단되었습니다.')
                    self.doc_remove.emit(i - deleted)
                    break
                else:  # 문서, 파일
                    if i > 0:  # 목록 처음이 편집 지시자가 아닌 경우만
                        label = f'( {i + 1} / {total} ) {self.doc_list[i][1]}'
                        self.label_text.emit(label)
                        while True:
                            if self.doc_list[i][0][0] == '@':  # 파일. 0번열의 0번째 문자가 @
                                posted = self.upload(self.doc_list[i][0][1:], self.doc_list[i][1], edit_temp)
                            else:  # 문서
                                posted = self.post(self.doc_list[i][0], edit_temp)  # 포스트 실시
                            if posted['rerun']:  # 편집창 리캡챠 발생
                                self.login()
                            else:
                                if is_delay:  # 저속 옵션
                                    t2 = time.time()
                                    waiting = self.CONFIG['DELAY'] - (t2 - t1)
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
                                storage.write_csv('edit_log.csv', 'a', storage.LOG_FIELD,
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