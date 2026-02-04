# main.py
import os
import sys
import threading
import time
import json
import urllib.request
import urllib.parse

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.text import LabelBase
from kivy.metrics import sp

# 파이드로이드3 환경 감지
def is_pydroid3():
    exe = (sys.executable or "").lower()
    return ("pydroid3" in exe) or ("ru.iiec.pydroid3" in exe)

# APK 환경에서만 권한 관련 import
ANDROID_PERMISSIONS = False
Environment = None
Build = None

if platform == "android" and not is_pydroid3():
    try:
        from android.permissions import request_permissions, Permission, check_permission
        from jnius import autoclass
        Environment = autoclass("android.os.Environment")
        Build = autoclass("android.os.Build")
        ANDROID_PERMISSIONS = True
    except Exception:
        pass

# 한글 폰트 등록
def register_fonts():
    paths = [
        "/system/fonts/NanumGothic.ttf",
        "/system/fonts/NotoSansCJK-Regular.ttc",
        "/system/fonts/DroidSansFallback.ttf",
        "/system/fonts/NotoSansKR-Regular.otf",
        "/system/fonts/DroidSans.ttf"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                LabelBase.register(name="KoreanFont", fn_regular=p)
                return True
            except:
                continue
    return False

# Spinner 드롭다운용 커스텀 옵션 (한글 폰트 적용)
class KSpinnerOption(SpinnerOption):
    pass

def safe_import():
    try:
        global PyPDF2
        import PyPDF2
        return True, "OK"
    except Exception as e:
        return False, str(e)

# 번역 함수 (실패 시 에러 메시지 포함)
def translate_text(text, target="ko"):
    try:
        base_url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": target,
            "dt": "t",
            "q": text
        }
        url = base_url + "?" + urllib.parse.urlencode(params)
        headers = {"User-Agent": "Mozilla/5.0"}
        
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=10)
        result = json.loads(response.read().decode("utf-8"))
        
        translated = ""
        if result and len(result) > 0:
            for sentence in result[0]:
                if sentence and len(sentence) > 0 and sentence[0]:
                    translated += sentence[0]
        
        if translated.strip():
            return translated
        else:
            return "[번역결과 비어있음] " + text
            
    except Exception as e:
        error_msg = str(e)[:70]
        return "[번역실패: " + error_msg + "] " + text


class MedicalKivyTranslator(App):
    def build(self):
        self.kmle_db = {
            "체포": "정지(Arrest)", 
            "심장 체포": "심정지", 
            "문화": "배양"
        }
        self.download_path = "/storage/emulated/0/Download"
        self.is_typing = False
        self.libs_loaded = False
        self.font_loaded = register_fonts()
        self.is_pydroid = is_pydroid3()
        
        # 폰트 설정
        fn = "KoreanFont" if self.font_loaded else "Roboto"
        
        root = BoxLayout(orientation="vertical", padding=15, spacing=10)
        top_layout = BoxLayout(orientation="vertical", size_hint_y=None, height=200, spacing=10)
        
        # 초기 텍스트
        init_text = "초기화 중..." if self.is_pydroid else "권한 요청 중..."
        
        # Spinner (파일 선택) - 20% 감소
        self.file_spinner = Spinner(
            text=init_text,
            values=["대기"],
            size_hint_y=None,
            height=85,
            font_name=fn,
            font_size=sp(19),  # 24 → 19
            option_cls=KSpinnerOption
        )
        # 드롭다운 항목에도 폰트 적용
        self.file_spinner.option_cls.font_name = fn
        self.file_spinner.option_cls.font_size = sp(18)  # 22 → 18
        self.file_spinner.bind(on_press=self.refresh_files)
        
        # 파일명 입력
        self.filename_input = TextInput(
            text="result_KO.pdf",
            multiline=False,
            size_hint_y=None,
            height=85,
            font_name=fn,
            font_size=sp(18),  # 22 → 18
            padding=[15, 28, 15, 10]
        )
        
        top_layout.add_widget(self.file_spinner)
        top_layout.add_widget(self.filename_input)
        root.add_widget(top_layout)

        # 진행률 표시
        pb_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=55, spacing=10)
        self.pb = ProgressBar(max=100, value=0, size_hint_y=None, height=45)
        self.percent_label = Label(
            text="0.0%",
            size_hint_x=0.25,
            font_name=fn,
            font_size=sp(22),  # 28 → 22
            bold=True
        )
        pb_box.add_widget(self.pb)
        pb_box.add_widget(self.percent_label)
        root.add_widget(pb_box)

        # 영문 표시 영역
        self.eng_label = Label(
            text="",
            size_hint_y=None,
            font_size=sp(14),  # 18 → 14
            font_name=fn,
            halign="left",
            valign="top",
            padding=(15, 15),
            color=(0.8, 0.8, 0.8, 1)
        )
        self.eng_label.bind(size=lambda s, w: s.setter("text_size")(s, (w[0], None)))
        self.eng_scroll = ScrollView(size_hint_y=0.45)
        self.eng_scroll.add_widget(self.eng_label)
        root.add_widget(self.eng_scroll)
        
        # 한글 번역 표시 영역
        self.kor_label = Label(
            text="로딩 중...",
            size_hint_y=None,
            font_size=sp(14),  # 18 → 14
            font_name=fn,
            halign="left",
            valign="top",
            padding=(15, 15),
            color=(0, 0.8, 1, 1)
        )
        self.kor_label.bind(size=lambda s, w: s.setter("text_size")(s, (w[0], None)))
        self.kor_scroll = ScrollView(size_hint_y=0.45)
        self.kor_scroll.add_widget(self.kor_label)
        root.add_widget(self.kor_scroll)

        # 번역 시작 버튼
        self.btn = Button(
            text="의학 번역 시작",
            size_hint_y=None,
            height=95,
            font_name=fn,
            font_size=sp(21),  # 26 → 21
            background_color=(0, 0.5, 0.9, 1)
        )
        self.btn.bind(on_press=self.start_thread)
        root.add_widget(self.btn)

        # 초기화
        if self.is_pydroid:
            Clock.schedule_once(lambda dt: self.init_app(), 0.3)
        else:
            Clock.schedule_once(lambda dt: self.request_permissions(), 0.5)
        
        return root

    def request_permissions(self):
        if ANDROID_PERMISSIONS:
            try:
                perms = [
                    Permission.INTERNET,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ]
                self.kor_label.text = "저장소 권한 요청 중..."
                request_permissions(perms)
                Clock.schedule_once(lambda dt: self.check_permissions(), 3)
            except Exception as e:
                self.kor_label.text = "권한요청 오류"
                Clock.schedule_once(lambda dt: self.init_app(), 1)
        else:
            Clock.schedule_once(lambda dt: self.init_app(), 0.5)

    def check_permissions(self):
        has_perm = True
        if ANDROID_PERMISSIONS:
            try:
                has_perm = check_permission(Permission.READ_EXTERNAL_STORAGE)
            except:
                has_perm = True
        
        if has_perm:
            self.kor_label.text = "권한 승인됨. 라이브러리 로딩 중..."
            Clock.schedule_once(lambda dt: self.init_app(), 0.5)
        else:
            self.kor_label.text = "권한 거부됨. 설정에서 저장소 권한 허용 필요"
            self.file_spinner.text = "권한 없음"

    def init_app(self):
        def initialize():
            success, msg = safe_import()
            self.libs_loaded = success
            Clock.schedule_once(lambda dt: self.after_init(success))
        threading.Thread(target=initialize, daemon=True).start()

    def after_init(self, success):
        if success:
            self.kor_label.text = "라이브러리 로드 완료. PDF 검색 중..."
            Clock.schedule_once(lambda dt: self.refresh_files(None), 0.5)
        else:
            self.file_spinner.text = "오류"
            self.kor_label.text = "PyPDF2 로드 실패"

    def refresh_files(self, instance):
        def load():
            files = []
            paths = [
                "/storage/emulated/0/Download",
                "/sdcard/Download",
                "/storage/sdcard0/Download",
                "/mnt/sdcard/Download"
            ]
            found = None
            
            for p in paths:
                try:
                    if os.path.exists(p) and os.access(p, os.R_OK):
                        all_f = os.listdir(p)
                        temp = [f for f in all_f if f.lower().endswith(".pdf")]
                        if temp:
                            files = temp
                            found = p
                            break
                except:
                    continue
            
            if files:
                files.sort()
                if found:
                    self.download_path = found
            
            Clock.schedule_once(lambda dt: self.update_list(files))
        
        threading.Thread(target=load, daemon=True).start()

    def update_list(self, files):
        if files:
            self.file_spinner.text = "PDF 선택"
            self.file_spinner.values = files
            # values 변경 후에도 드롭다운 폰트 유지
            fn = "KoreanFont" if self.font_loaded else "Roboto"
            self.file_spinner.option_cls.font_name = fn
            self.file_spinner.option_cls.font_size = sp(18)  # 22 → 18
            
            n = str(len(files))
            t1 = "준비 완료! " + n + "개 PDF 발견"
            t2 = "경로: " + self.download_path
            self.kor_label.text = t1 + chr(10) + t2
        else:
            self.file_spinner.text = "PDF 없음"
            self.file_spinner.values = ["탭하여 새로고침"]
            fn = "KoreanFont" if self.font_loaded else "Roboto"
            self.file_spinner.option_cls.font_name = fn
            self.file_spinner.option_cls.font_size = sp(18)  # 22 → 18
            
            msg1 = "PDF 파일을 찾을 수 없습니다"
            msg2 = "Download 폴더에 PDF를 넣고"
            msg3 = "새로고침하세요"
            self.kor_label.text = msg1 + chr(10) + msg2 + chr(10) + msg3

    def start_thread(self, instance):
        if not self.libs_loaded:
            self.kor_label.text = "라이브러리 로드가 안 됐습니다"
            return
        
        check_texts = [
            "PDF 선택",
            "초기화 중...",
            "권한 요청 중...",
            "PDF 없음",
            "오류",
            "권한 없음"
        ]
        if self.file_spinner.text in check_texts:
            self.kor_label.text = "먼저 PDF 파일을 선택하세요"
            return
        
        self.btn.disabled = True
        self.eng_label.text = ""
        self.kor_label.text = "번역 시작 중..."
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        try:
            fpath = os.path.join(self.download_path, self.file_spinner.text)
            reader = PyPDF2.PdfReader(fpath)
            total = len(reader.pages)
            
            for i, page in enumerate(reader.pages):
                txt = page.extract_text()
                if not txt:
                    continue
                    
                clean = txt.replace(chr(10), " ")
                sents = [s.strip() for s in clean.split(". ") if len(s) > 5]
                
                for j, sent in enumerate(sents):
                    trans = translate_text(sent, "ko")
                    
                    # 의학용어 교정
                    for w, c in self.kmle_db.items():
                        trans = trans.replace(w, c)
                    
                    prog = ((i / total) + (j / len(sents) / total)) * 100
                    self.is_typing = True
                    Clock.schedule_once(
                        lambda dt, s=sent, t=trans, p=prog: self.type_sync(s, t, p)
                    )
                    while self.is_typing:
                        time.sleep(0.005)
            
            Clock.schedule_once(lambda dt: self.complete())
            
        except Exception as e:
            err = "오류: " + str(e)[:100]
            Clock.schedule_once(lambda dt: setattr(self.kor_label, "text", err))
            Clock.schedule_once(lambda dt: setattr(self.btn, "disabled", False))

    def type_sync(self, eng, kor, prog):
        nl = chr(10)
        e_text = "• " + eng + nl + nl
        k_text = "• " + kor + nl + nl
        
        for i, c in enumerate(e_text):
            Clock.schedule_once(
                lambda dt, ch=c: self.update_ui("eng", ch),
                i * 0.001
            )
        
        delay = len(e_text) * 0.001
        for i, c in enumerate(k_text):
            last = (i == len(k_text) - 1)
            Clock.schedule_once(
                lambda dt, ch=c, l=last, p=prog: self.update_ui("kor", ch, l, p),
                delay + (i * 0.002)
            )

    def update_ui(self, target, char, is_last=False, prog=None):
        if target == "eng":
            label = self.eng_label
            scroll = self.eng_scroll
        else:
            label = self.kor_label
            scroll = self.kor_scroll
            if prog is not None:
                self.pb.value = prog
                self.percent_label.text = "{:.1f}%".format(prog)
        
        label.text += char
        
        if len(label.text) > 5000:
            label.text = label.text[-4500:]
        
        label.height = max(label.texture_size[1], scroll.height)
        scroll.scroll_y = 0
        
        if is_last:
            self.is_typing = False

    def complete(self):
        self.btn.disabled = False
        self.btn.text = "번역 완료!"
        self.pb.value = 100
        self.percent_label.text = "100.0%"


if __name__ == "__main__":
    MedicalKivyTranslator().run()
