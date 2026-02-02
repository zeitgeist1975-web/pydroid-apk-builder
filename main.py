import os
import threading
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.utils import platform # 플랫폼 확인용

# 안드로이드 빌드 환경일 때만 권한 모듈 임포트
if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
    except ImportError:
        pass

import PyPDF2
from deep_translator import GoogleTranslator

def get_korean_font():
    paths = ["/storage/emulated/0/Download/font.ttf", "/system/fonts/NanumGothic.ttf", 
             "/system/fonts/NotoSansCJK-Regular.ttc", "/system/fonts/DroidSansFallback.ttf"]
    for p in paths:
        if os.path.exists(p): return p
    return 'Roboto'

KOREAN_FONT = get_korean_font()

class MedicalKivyTranslator(App):
    def build(self):
        # [수정] 앱 시작 시 권한 요청 (안드로이드 환경에서만 실행)
        if platform == 'android':
            try:
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            except Exception as e:
                print(f"Permission Error: {e}")

        self.kmle_db = {"체포": "정지(Arrest)", "심장 체포": "심정지", "문화": "배양"}
        self.download_path = "/storage/emulated/0/Download"
        self.translator = GoogleTranslator(source='en', target='ko')
        self.is_typing = False
        
        root = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # 1. 상단 설정
        top_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=200, spacing=10)
        try:
            pdf_files = [f for f in os.listdir(self.download_path) if f.lower().endswith('.pdf')]
        except: pdf_files = []
        if not pdf_files: pdf_files = ['PDF 파일 없음']

        self.file_spinner = Spinner(
            text='번역할 PDF 선택', values=pdf_files, 
            size_hint_y=None, height=85, font_name=KOREAN_FONT, font_size='17sp'
        )
        self.filename_input = TextInput(
            text="result_KO.pdf", multiline=False, 
            size_hint_y=None, height=85, font_name=KOREAN_FONT, font_size='17sp',
            padding=[15, 28, 15, 10], cursor_color=(0, 0.5, 0.8, 1)
        )
        top_layout.add_widget(self.file_spinner)
        top_layout.add_widget(self.filename_input)
        root.add_widget(top_layout)

        # 2. 프로그레스바
        progress_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=55, spacing=10)
        self.pb = ProgressBar(max=100, value=0, size_hint_y=None, height=45)
        self.percent_label = Label(text="0.0%", size_hint_x=0.25, font_size='22sp', bold=True)
        progress_box.add_widget(self.pb)
        progress_box.add_widget(self.percent_label)
        root.add_widget(progress_box)

        # 3. 상하 대조 창
        self.eng_label = Label(text="", size_hint_y=None, font_size='14sp', halign='left', valign='top', padding=(15, 15), color=(0.8, 0.8, 0.8, 1))
        self.eng_label.bind(size=lambda s, w: s.setter('text_size')(s, (w[0], None)))
        self.eng_scroll = ScrollView(size_hint_y=0.45)
        self.eng_scroll.add_widget(self.eng_label)
        root.add_widget(self.eng_scroll)
        
        self.kor_label = Label(text="", size_hint_y=None, font_size='14sp', font_name=KOREAN_FONT, halign='left', valign='top', padding=(15, 15), color=(0, 0.8, 1, 1))
        self.kor_label.bind(size=lambda s, w: s.setter('text_size')(s, (w[0], None)))
        self.kor_scroll = ScrollView(size_hint_y=0.45)
        self.kor_scroll.add_widget(self.kor_label)
        root.add_widget(self.kor_scroll)

        # 4. 버튼
        self.btn = Button(text="의학 번역 시작", size_hint_y=None, height=95, font_name=KOREAN_FONT, font_size='20sp', background_color=(0, 0.5, 0.9, 1))
        self.btn.bind(on_press=self.start_thread)
        root.add_widget(self.btn)

        return root

    def start_thread(self, instance):
        if self.file_spinner.text in ('번역할 PDF 선택', 'PDF 파일 없음'): return
        self.btn.disabled = True
        self.eng_label.text = ""
        self.kor_label.text = ""
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        try:
            input_file = os.path.join(self.download_path, self.file_spinner.text)
            reader = PyPDF2.PdfReader(input_file)
            total_pages = len(reader.pages)
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text: continue
                sentences = [s.strip() for s in text.replace('\n', ' ').split('. ') if len(s) > 5]
                
                for j, sent in enumerate(sentences):
                    translated = self.translator.translate(sent)
                    for w, c in self.kmle_db.items():
                        translated = translated.replace(w, c)
                    
                    prog = ((i / total_pages) + (j / len(sentences) / total_pages)) * 100
                    self.is_typing = True
                    Clock.schedule_once(lambda dt, s=sent, t=translated, p=prog: self.run_typing_sync(s, t, p))
                    while self.is_typing:
                        time.sleep(0.005)
            
            Clock.schedule_once(lambda dt: self.complete())
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.kor_label, 'text', f"Error: {e}"))

    def run_typing_sync(self, eng, kor, prog):
        e_text = f"• {eng}\n\n"
        k_text = f"• {kor}\n\n"
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
                self.percent_label.text = f"{prog:.1f}%"
        label.text += char
        if len(label.text) > 5000: label.text = label.text[-4500:]
        label.height = max(label.texture_size[1], scroll.height)
        scroll.scroll_y = 0
        if is_last: self.is_typing = False

    def complete(self):
        self.btn.disabled = False
        self.btn.text = "번역 및 파일 저장 완료"
        self.pb.value = 100
        self.percent_label.text = "100.0%"

if __name__ == "__main__":
    MedicalKivyTranslator().run()
