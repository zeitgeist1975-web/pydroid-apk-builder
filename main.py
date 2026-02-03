# main.py

import os
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
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.text import LabelBase

if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
    except ImportError:
        pass

def safe_import():
    try:
        global PyPDF2
        import PyPDF2
        return True, "PyPDF2 loaded"
    except Exception as e:
        return False, str(e)

def translate_text(text, target='ko'):
    try:
        base_url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'en',
            'tl': target,
            'dt': 't',
            'q': text
        }
        url = base_url + '?' + urllib.parse.urlencode(params)
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=10)
        result = json.loads(response.read().decode('utf-8'))
        
        translated = ''
        for sentence in result[0]:
            if sentence[0]:
                translated += sentence[0]
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def register_korean_font():
    """안드로이드 시스템 한글 폰트 찾아서 등록"""
    font_paths = [
        "/system/fonts/NanumGothic.ttf",
        "/system/fonts/NotoSansCJK-Regular.ttc",
        "/system/fonts/DroidSansFallback.ttf",
        "/system/fonts/NotoSansKR-Regular.otf"
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                LabelBase.register(name='Korean', fn_regular=font_path)
                print(f"Korean font registered: {font_path}")
                return 'Korean'
            except Exception as e:
                print(f"Font register error: {e}")
                continue
    
    print("No Korean font found, using default")
    return 'Roboto'

KOREAN_FONT = register_korean_font()

class MedicalKivyTranslator(App):
    def build(self):
        self.kmle_db = {"체포": "정지(Arrest)", "심장 체포": "심정지", "문화": "배양"}
        self.download_path = "/storage/emulated/0/Download"
        self.is_typing = False
        self.libs_loaded = False
        
        root = BoxLayout(orientation='vertical', padding=15, spacing=10)

        top_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=200, spacing=10)
        
        self.file_spinner = Spinner(text='Loading...', values=['Wait'], size_hint_y=None, height=85, font_name=KOREAN_FONT, font_size='17sp')
        self.file_spinner.bind(on_press=self.refresh_files)
        self.filename_input = TextInput(text="result_KO.pdf", multiline=False, size_hint_y=None, height=85, font_name=KOREAN_FONT, font_size='17sp', padding=[15, 28, 15, 10], cursor_color=(0, 0.5, 0.8, 1))
        top_layout.add_widget(self.file_spinner)
        top_layout.add_widget(self.filename_input)
        root.add_widget(top_layout)

        progress_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=55, spacing=10)
        self.pb = ProgressBar(max=100, value=0, size_hint_y=None, height=45)
        self.percent_label = Label(text="0.0%", size_hint_x=0.25, font_name=KOREAN_FONT, font_size='22sp', bold=True)
        progress_box.add_widget(self.pb)
        progress_box.add_widget(self.percent_label)
        root.add_widget(progress_box)

        self.eng_label = Label(text="", size_hint_y=None, font_size='14sp', halign='left', valign='top', padding=(15, 15), color=(0.8, 0.8, 0.8, 1))
        self.eng_label.bind(size=lambda s, w: s.setter('text_size')(s, (w[0], None)))
        self.eng_scroll = ScrollView(size_hint_y=0.45)
        self.eng_scroll.add_widget(self.eng_label)
        root.add_widget(self.eng_scroll)
        
        self.kor_label = Label(text="초기화 중...", size_hint_y=None, font_size='14sp', font_name=KOREAN_FONT, halign='left', valign='top', padding=(15, 15), color=(0, 0.8, 1, 1))
        self.kor_label.bind(size=lambda s, w: s.setter('text_size')(s, (w[0], None)))
        self.kor_scroll = ScrollView(size_hint_y=0.45)
        self.kor_scroll.add_widget(self.kor_label)
        root.add_widget(self.kor_scroll)

        self.btn = Button(text="의학 번역 시작", size_hint_y=None, height=95, font_name=KOREAN_FONT, font_size='20sp', background_color=(0, 0.5, 0.9, 1))
        self.btn.bind(on_press=self.start_thread)
        root.add_widget(self.btn)

        Clock.schedule_once(lambda dt: self.init_app(), 0.5)

        return root

    def init_app(self):
        def initialize():
            if platform == 'android':
                try:
                    request_permissions([
                        Permission.READ_EXTERNAL_STORAGE,
                        Permission.WRITE_EXTERNAL_STORAGE,
                        Permission.INTERNET
                    ])
                    time.sleep(2)
                except Exception as e:
                    print(f"Permission error: {e}")
            
            success, msg = safe_import()
            self.libs_loaded = success
            
            Clock.schedule_once(lambda dt: self.update_after_init(success, msg))
        
        threading.Thread(target=initialize, daemon=True).start()

    def update_after_init(self, success, msg):
        if success:
            self.kor_label.text = msg + " - 파일 확인 중..."
            Clock.schedule_once(lambda dt: self.refresh_files(None), 0.5)
        else:
            self.file_spinner.text = '라이브러리 오류'
            self.file_spinner.values = ['재빌드 필요']
            self.kor_label.text = f'실패: {msg}'

    def refresh_files(self, instance):
        """파일 목록 새로고침"""
        def load_files():
            pdf_files = []
            error_msg = ""
            
            try:
                if not os.path.exists(self.download_path):
                    error_msg = f"경로 없음: {self.download_path}"
                elif not os.access(self.download_path, os.R_OK):
                    error_msg = "읽기 권한 없음"
                else:
                    all_files = os.listdir(self.download_path)
                    for f in all_files:
                        if f.lower().endswith('.pdf'):
                            pdf_files.append(f)
                    pdf_files.sort()
                    
                    if not pdf_files:
                        error_msg = f"PDF 없음: {self.download_path}"
            except Exception as e:
                error_msg = f"오류: {str(e)}"
            
            Clock.schedule_once(lambda dt: self.update_file_list(pdf_files, error_msg))
        
        threading.Thread(target=load_files, daemon=True).start()

    def update_file_list(self, pdf_files, error_msg):
        if pdf_files:
            self.file_spinner.text = 'PDF 선택'
            self.file_spinner.values = pdf_files
            self.kor_label.text = f'준비 완료 - {len(pdf_files)}개 PDF 발견'
        else:
            self.file_spinner.text = 'PDF 없음'
            self.file_spinner.values = ['탭하여 새로고침']
            self.kor_label.text = error_msg if error_msg else 'PDF 파일 없음'

    def start_thread(self, instance):
        if not self.libs_loaded:
            self.kor_label.text = "PyPDF2 로드 안됨"
            return
        if self.file_spinner.text in ('PDF 선택', 'Loading...', 'PDF 없음', '라이브러리 오류'):
            self.kor_label.text = "먼저 PDF 파일을 선택하세요 (스피너 탭하여 새로고침)"
            return
            
        self.btn.disabled = True
        self.eng_label.text = ""
        self.kor_label.text = "번역 시작 중..."
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        try:
            input_file = os.path.join(self.download_path, self.file_spinner.text)
            reader = PyPDF2.PdfReader(input_file)
            total_pages = len(reader.pages)
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text:
                    continue
                clean_text = text.replace(chr(10), ' ')
                sentence_list = clean_text.split('. ')
                sentences = [s.strip() for s in sentence_list if len(s) > 5]
                
                for j, sent in enumerate(sentences):
                    translated = translate_text(sent, 'ko')
                    for w, c in self.kmle_db.items():
                        translated = translated.replace(w, c)
                    
                    prog = ((i / total_pages) + (j / len(sentences) / total_pages)) * 100
                    self.is_typing = True
                    Clock.schedule_once(lambda dt, s=sent, t=translated, p=prog: self.run_typing_sync(s, t, p))
                    while self.is_typing:
                        time.sleep(0.005)
            
            Clock.schedule_once(lambda dt: self.complete())
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.kor_label, 'text', "오류: " + str(e)))

    def run_typing_sync(self, eng, kor, prog):
        newline = chr(10)
        e_text = "• " + eng + newline + newline
        k_text = "• " + kor + newline + newline
        for idx, char in enumerate(e_text):
            Clock.schedule_once(lambda dt, c=char: self.update_ui('eng', c), idx * 0.001)
        delay = len(e_text) * 0.001
        for idx, char in enumerate(k_text):
            last = (idx == len(k_text) - 1)
            Clock.schedule_once(lambda dt, c=char, l=last, p=prog: self.update_ui('kor', c, l, p), delay + (idx * 0.002))

    def update_ui(self, target, char, is_last=False, prog=None):
        if target == 'eng':
            label, scroll = self.eng_label, self.eng_scroll
        else:
            label, scroll = self.kor_label, self.kor_scroll
            if prog:
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
        self.btn.text = "번역 및 파일 저장 완료"
        self.pb.value = 100
        self.percent_label.text = "100.0%"

if __name__ == "__main__":
    MedicalKivyTranslator().run()
