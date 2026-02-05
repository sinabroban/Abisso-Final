# ⚡ 초간단 시작 가이드

## 📦 이 폴더 내용

```
ESSENTIAL_FILES/
├── app.py              ← 메인 프로그램 (이것만 있으면 작동!)
├── requirements.txt    ← 필요한 라이브러리 목록
└── README.md          ← 이 파일
```

---

## 🎯 3단계로 시작하기

### ✅ 1단계: 깃허브에서 app.py 수정

1. **본인 깃허브 저장소 접속**
   - 예: `https://github.com/본인아이디/저장소이름`

2. **app.py 파일 클릭**

3. **우측 상단 ✏️ 연필 아이콘 클릭**

4. **기존 내용 전체 삭제**
   - `Ctrl + A` → `Delete`

5. **이 폴더의 app.py 파일 열기**
   - 메모장이나 VSCode로 열기
   - `Ctrl + A` (전체 선택)
   - `Ctrl + C` (복사)

6. **깃허브에 붙여넣기**
   - `Ctrl + V`

7. **맨 아래 "Commit changes" 버튼 클릭**

---

### ✅ 2단계: requirements.txt 수정

1. **깃허브에서 requirements.txt 파일 클릭**

2. **✏️ 연필 아이콘 클릭**

3. **기존 내용 삭제**

4. **이 폴더의 requirements.txt 내용 복사**

5. **깃허브에 붙여넣기**

6. **"Commit changes" 버튼 클릭**

---

### ✅ 3단계: 완료! 

1-2분 후 자동으로 재배포됩니다.

본인 앱 주소로 접속하세요:
- 예: `https://본인앱이름.streamlit.app`

---

## 💡 파일 여는 방법

### Windows
1. 파일 우클릭
2. **"연결 프로그램" → "메모장"** 선택
3. `Ctrl + A` (전체 선택)
4. `Ctrl + C` (복사)

### Mac
1. 파일 우클릭
2. **"다음으로 열기" → "텍스트 편집기"** 선택
3. `Cmd + A` (전체 선택)
4. `Cmd + C` (복사)

---

## 📝 requirements.txt 내용

이게 전부입니다! 그냥 이대로 복사하세요:

```
streamlit==1.29.0
pandas==2.1.4
numpy==1.26.2
plotly==5.18.0
pyupbit==0.2.33
pybithumb==1.0.21
python-dotenv==1.0.0
```

---

## 🆘 문제 해결

### "파일을 찾을 수 없습니다"

깃허브에 app.py가 없으면:

1. 깃허브 저장소에서 **"Add file"** 클릭
2. **"Create new file"** 선택
3. 파일 이름에 `app.py` 입력
4. 내용 붙여넣기
5. **"Commit new file"** 클릭

### "배포가 안 됩니다"

1-2분 기다린 후:

1. [Streamlit Cloud](https://share.streamlit.io/) 접속
2. 본인 앱 찾기
3. **"Reboot app"** 클릭

### "오류가 뜹니다"

1. requirements.txt가 정확한지 확인
2. app.py가 완전히 복사되었는지 확인
3. 깃허브에서 파일 다시 확인

---

## 🎁 추가 파일 (선택사항)

`crypto-trading-bot` 폴더에 더 많은 파일이 있습니다:

- `.streamlit/config.toml` ← 디자인 설정
- `README.md` ← 상세 설명
- `.gitignore` ← Git 제외 파일

**나중에 필요하면** 같은 방법으로 추가하세요!

---

## ✨ 완료 후 확인사항

앱이 정상 작동하면:

- ✅ 업비트/빗썸 선택 가능
- ✅ 실시간 차트 표시
- ✅ 매매 신호 확인 가능
- ✅ 테스트 모드로 시작 가능

---

## 🚀 다음 단계

1. **테스트 모드로 먼저 사용**
   - 신호 확인
   - 전략 이해

2. **API 키 발급** (실거래 시)
   - 업비트: https://upbit.com → 마이페이지 → API 관리
   - 빗썸: https://www.bithumb.com → 마이페이지 → API 관리

3. **소액으로 시작**
   - 10만원 이하 권장
   - 손절 3% 설정

---

**화이팅! 🎉**

궁금한 점이 있으면 `crypto-trading-bot/README.md` 파일을 확인하세요!
