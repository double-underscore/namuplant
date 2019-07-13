import requests, re, configparser, time, webbrowser
from bs4 import BeautifulSoup
from urllib import parse
# time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

# 컨트롤w - 선택 쉽게 해줌

def ddoscheck_(funcs, url, **kwargs):
    while True:
        if 'file' in kwargs:
            r = funcs(url, headers=kwargs['headers'], cookies=kwargs['cookies'], data=kwargs['data'], files=kwargs['files'])
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

class req: #로그인이 필요한 작업
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini', 'utf-8')
        self.umi = self.config['login']['umi']
        self.ua = self.config['login']['ua']
        self.id = self.config['login']['id']
        self.pw = self.config['login']['pw']
        self.logindata = {
            'username':self.id,
            'password':self.pw
        }
        self.loginurl = 'https://namu.wiki/member/login'
        # self.jar = requests.cookies.RequestsCookieJar()
        # self.jar.set('umi', self.umi, domain='namu.wiki')
        self.log = ''

        self.s = requests.Session()
        self.s.headers.update({'user-agent': self.ua})

    def login(self):
        self.s.get('https://namu.wiki/edit/IMO')
        self.s.cookies.set('umi', self.umi, domain='namu.wiki')
        soup = ddoscheck_(self.s.post, self.loginurl, headers=self.headermaker(self.loginurl), cookies=self.s.cookies, data=self.logindata )
        # r = self.s.post(self.loginurl, headers=self.headermaker(self.loginurl), cookies=self.s.cookies, data=self.logindata)
        if soup.select('body > div.navbar-wrapper > nav > ul.nav.navbar-nav.pull-right > li > div > div.dropdown-item.user-info > div > div')[1].text == 'Member':
            print('login SUCCESS')
        else:
            print('login FAILURE')

    def headermaker(self, url):
        return {'referer': url}

    def process(self, doccode, chanfrom, chanto):
        # 겟
        docediturl = 'https://namu.wiki/edit/' + doccode
        soup = ddoscheck_(self.s.get, docediturl, headers=self.headermaker(docediturl), cookies=self.s.cookies) # 겟
        maintext = soup.textarea.contents[0]# soup.find(attrs={'name': 'text'}).text
        baserev = soup.find(attrs={'name':'baserev'})['value']
        identifier = soup.find(attrs={'name':'identifier'})['value']
        if 'm:' + self.id == identifier:
            pass
            # print('yes!') # 아니면 중단
        # 변경
        maintext = self.edit(maintext, chanfrom, chanto, 0)
        # 포0
        soup = ddoscheck_(self.s.post, docediturl, headers=self.headermaker(docediturl), cookies=self.s.cookies) # 포0
        token = soup.find(attrs={'name':'token'})['value']
        # 포1
        multidata = {'token': token, 'identifier': identifier, 'baserev': baserev, 'text': maintext, 'log': self.log, 'agree':'Y'}
        soup = ddoscheck_(self.s.post, docediturl, headers=self.headermaker(docediturl), cookies=self.s.cookies, data = multidata, files = {'file': None}) # 포1
        print(soup.text.strip())
        # soup = BeautifulSoup(r.text, 'html.parser')

    def edit(self, text, chanfrom, chanto, opt):
        if opt == 0: # 일반
            return text.replace(chanfrom, chanto)
        elif opt == 1: # 정규식
            return re.sub(chanfrom, chanto, text)
        elif opt == 2: # 테스트
            return text + '플러스'

    def isperm(self, text):
        soup = BeautifulSoup(text, 'html.parser')
        perm = soup.select('body > div.content-wrapper > article > div.alert.alert-danger.alert-dismissible.fade.in.edit-alert')
        if len(perm): return True #권한 없음
        else: return False

class crawl:
    def __init__(self):
        pass
    def getref(self):
        pass

def getxref(doccode):
    spacelist = []
    reflist = []
    soup = ddoscheck_(requests.get, f'https://namu.wiki/xref/{doccode}')
    spaces = soup.select('body > div.content-wrapper > article > fieldset > form > div:nth-child(1) > select:nth-child(2) > option') # 네임스페이스
    for v in spaces:
        spacelist.append(parse.quote(v.get('value')))
    for v in spacelist:
        added =''
        namespace = v
        while True:
            print(len(reflist))
            soup = ddoscheck_(requests.get, f'https://namu.wiki/xref/{doccode}?namespace={namespace}{added}')
            titles = soup.select('div > ul > li > a') # 목록
            for v in titles:
                if v.next_sibling[2:-1] != 'redirect':
                    reflist.append(v.get('href')[3:])
            btn = soup.select('body > div.content-wrapper > article > div > a') # 앞뒤버튼
            added = btn[1].get('href') #뒤 버튼
            if added == None: #없으면 다음 스페이스로
                break
            else:
                added = added[added.find('&from'):].replace('\'', '%27') # '만 인코딩이 안 되어 있음
                # re.sub('\?namespace=.*?(&from.*?)$', '\g<1>', aaa)
    for v in reflist:
        print(parse.unquote(v))
    print(len(reflist))
    return reflist

def getcat(doccode):
    catlist = []
    donebtn = 0
    added = ''
    soup = ddoscheck_(requests.get, f'https://namu.wiki/w/{doccode}')
    divs = soup.select('body > div.content-wrapper > article > div.wiki-content.clearfix > div')
    for i in range(len(divs)):
        islist = divs[i].select('div > ul > li > a')
        isbtn = divs[i].select('a.btn')
        if len(isbtn):
            if donebtn == 0:
                added = divs[i].select('a')[1].get('href')
                donebtn = 1
            elif donebtn == 1:
                donebtn = 0
        elif len(islist):
            for v in islist: # 기본 페이지
                catlist.append(v.get('href')[3:])
            while True:
                if added:
                    newsoup = ddoscheck_(requests.get, f'https://namu.wiki/w/{doccode}{added}')
                    newdivs = newsoup.select('body > div.content-wrapper > article > div.wiki-content.clearfix > div')
                    for v in newdivs[i].select('div > ul > li > a'):
                        catlist.append(v.get('href')[3:])
                    added = newdivs[i-1].select('a')[1].get('href') # 버튼에서 값 추출
                else:
                    break
    for v in catlist:
        print(parse.unquote(v))
    print(len(catlist))
    # return catlist

def deduplication(input):
    return list(set(input))

def doedit():
    ttt = req()
    ttt.login()
    ttt.process('%EB%82%98%EB%AC%B4%EC%9C%84%ED%82%A4:%EC%97%B0%EC%8A%B5%EC%9E%A5', '연습연', 'test')

def dogetcat():
    aaa = input('분류 가져올 거 코드')
    if aaa:
        getcat(aaa)

if __name__ == '__main__':
    # pass
    startt = time.time()
    # doedit()
    # dogetxref()
    dogetcat()
    endt = time.time()
    print(endt - startt)