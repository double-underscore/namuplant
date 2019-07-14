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

# todo UI, 대량입력

LIST_FIELD = ['code', 'title', 'find', 'replace', 'option', 'summary']
LOG_FIELD = ['code', 'title', 'find', 'replace', 'option', 'summary', 'time', 'rev', 'error']

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


class Win:
    def __init__(self):
        pass

    def UI(self):
        pass


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
                'body > div.navbar-wrapper > nav > ul.nav.navbar-nav.pull-right > li > div > div.dropdown-item.user-info > div > div')[
            1].text == 'Member':
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
        # ['code', 'title', 'find', 'replace', 'option', 'summary', ///// 'time', 'rev', 'error']
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
            maintext = self.find_replace(maintext, doc_dict['find'], doc_dict['replace'], doc_dict['option'])
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
    def find_replace(text, text_find, text_replace, option):
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
            writer = csv.DictWriter(csvfile, LOG_FIELD)  # ['code', 'title', 'find', 'replace', 'option', 'summary', 'time', 'rev', 'error']
            writer.writerow({'code': log_dict['code'], 'title': log_dict['title'], 'find': log_dict['find'],
                             'replace': log_dict['replace'], 'option': log_dict['option'], 'summary': log_dict['summary'],
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
            writer = csv.DictWriter(csvfile, LIST_FIELD)  # ['code', 'title', 'find', 'replace', 'option', 'summary']
            writer.writerow({'code': doc_code, 'title': parse.unquote(doc_code)})

def read_list(): #csv 읽기 & 입력값 첨가
    list = []
    with open('doc_list.csv', 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dict_row = dict(row)
            dict_row['option'] = int(dict_row['option'])
            list.append(dict_row)
    return list

def deduplication(input):
    return list(set(input))


def do_edit_post():
    ttt = Req()
    ttt.login()
    ttt.edit_post(
        {'code': '%EB%82%98%EB%AC%B4%EC%9C%84%ED%82%A4:%EC%97%B0%EC%8A%B5%EC%9E%A5', 'find': '연습연', 'replace': 'test',
         'option': 9, 'summary': ''})


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
    # '''
    start_t = time.time()

    test_req = Req()
    test_req.login()
    test_req.iterate(read_list())
        # do_edit_post()
        # do_get_xref()
        # get_cat(test_code)

    end_t = time.time()
    print(end_t - start_t)
    # '''