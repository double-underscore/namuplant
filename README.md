# namuplant
A bot for namu.wiki

by [double-underscore](https://github.com/double-underscore)

## 설치 및 설정
1. 기본
	1. Python 3.7.x. 설치  
	    * 경로에 한글이 있으면 오류가 발생하므로 모든 사용자용으로 설치할 것.
	2. 적절한 폴더에 프로젝트 클론  
	    * 공유 폴더에 설치하면 ID와 비밀번호가 유출될 가능성이 있으므로 피할 것.
	3. `requirements.txt`를 이용해 패키지 설치
		* 윈도우 탐색기에서 클론한 폴더에 들어간 다음 shift + 오른쪽 클릭 - 여기에서 PowerShell 열기
	    * `pip install -r requirements.txt`
	4. `run.py`(콘솔有) 또는 `run.pyw`(콘솔無) 실행
2. 로그인
	1. `설정 - 개인정보` 열기
	2. ID & 비밀번호 입력  
	    * `config.ini` 파일에 저장되므로 개인정보 유출 조심할 것.
	3. umi 쿠키 입력  
	    * umi 쿠키는 로그인 시 이메일 인증을 받으면 생성되는 쿠키로,  `EditThisCookie` 처럼 쿠키를 확인할 수 있게 해주는 확장프로그램을 이용하여 확인.
	4. User-Agents 입력  
	    * [사이트](https://developers.whatismybrowser.com/useragents/parse/?analyse-my-user-agent=yes)에서 복사하여 입력.
	5. 저장

## 사용법
1. 문서 목록 입력
    * 右 ON 상태에서 크롬 브라우저에서 문서 링크 우클릭 시 입력됨
    * 문서 제목 더블 클릭 시 RAW 확인 및 편집 가능
    * 열 제목 더블 클릭 시 중복 문서 제거
    * 이미지 파일의 경우 `F2`를 눌러 업로드될 문서명 편집 가능
    * `Ctrl + Shift + Up/Down`: 선택 문서 위 / 아래 이동
    * `Ctrl + Shift + Left/Right`: 선택 문서 맨 위 / 맨 아래 이동
2. 편집 지시사항 입력
    * 콤보 박스로 옵션 선택 후 내용을 입력하고 `Enter`시 입력
    * `찾기` 다음에는 `바꾸기` 필수
    * `F2`를 눌러 이미 입력된 지시사항 편집 가능
    * 더블 클릭시 문서 목록에 해당 편집 지시자 삽입
3. 문서 목록에 편집 지시자 삽입
    * 문서 목록에서 `Alt + 1~9` 눌러서 해당 번호 삽입 가능 
4. `시작`
    * 처음 실행 시 변경 사항 비교창에서 편집 지시사항을 제대로 작성하였는지 확인.
## 유의사항
* 마우스 우클릭을 통한 문서 입력은 크롬 브라우저에서만 가능.