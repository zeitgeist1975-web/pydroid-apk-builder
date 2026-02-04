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
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.text import LabelBase

# 파이드로이드3 환경 감지
def is_pydroid3():
    return 'pydroid3' in sys.executable.lower() or 'ru.iiec.pydroid3' in sys.executable

# APK 환경에서만 권한 관련 import
if platform == 'android' and not is_pydroid3():
    try:
        from android.permissions import request_permissions, Permission, check_permission
        from jnius import autoclass
        Environment = autoclass('android.os.Environment')
        Build = autoclass('android.os.Build')
        ANDROID_PERMISSIONS = True
    except:
        ANDROID_PERMISSIONS = False
        Environment = None
        Build = None
else:
    ANDROID_PERMISSIONS = False
    Environment = None
    Build = None

def safe_import():
    try:
        global PyPDF2
        import PyPDF2
        return True, "OK"
    except Exception as e:
        return False, str(e)

def translate_text(text, target='ko'):
    try:
        base_url = "https://translate.googleapis.com/translate_a/single"
        params = {'client': 'gtx', 'sl': 'en', 'tl': target, 'dt': 't', 'q': text}
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
    except:
        return text

def register_fonts():
    paths = ["/system/fonts/NanumGothic.ttf", "/system/fonts/NotoSansCJK-Regular.ttc", 
             "/system/fonts/DroidSansFallback.ttf", "/system/fonts/NotoSansKR-Regular.otf"]
    for p in paths:
        if os.path.exists(p):
            try:
                LabelBase.register(name='KoreanFont', fn_regular=p)
                return True
            except:
                continue
    return False

class MedicalKivyTranslator(App):
    def build(self):
        self.kmle_db = {"체포": "정지(Arrest)", "심장 체포": "심정지", "문화": "배양"}
        self.download_path = "/storage/emulated/0/Download"
        self.is_typing = False
        self.libs_loaded = False
        self.font_loaded = register_fonts()
        self.is_pydroid = is_pydroid3()
        
        root = BoxLayout(orientation='vertical', padding=15, spacing=10)
        top_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=200, spacing=10)
        
        fn = 'KoreanFont' if self.font_loaded else 'Roboto'
        
        init_text = 'Initializing...' if self.is_pydroid else 'Requesting permissions...'
        self.file_spinner = Spinner(text=init_text, values=['Wait'], 
                                   size_hint_y=None, height=85, font_name=fn, font_size='17sp')
        self.file_spinner.bind(on_press=self.refresh_files)
        
        self.filename_input = TextInput(text="result_KO.pdf", multiline=False, 
                                       size_hint_y=None, height=85, font_name=fn, 
                                       font_size='17sp', padding=[15, 28, 15, 10])
        top_layout.add_widget(self.file_spinner)
        top_layout.add_widget(self.filename_input)
        root.add_widget(top_layout)

        pb_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=55, spacing=10)
        self.pb = ProgressBar(max=100, value=0, size_hint_y=None, height=45)
        self.percent_label = Label(text="0.0%", size_hint_x=0.25, font_name=fn, 
                                  font_size='22sp', bold=True)
        pb_box.add_widget(self.pb)
        pb_box.add_widget(self.percent_label)
        root.add_widget(pb_box)

        self.eng_label = Label(text="", size_hint_y=None, font_size='14sp', 
                              halign='left', valign='top', padding=(15, 15), 
                              color=(0.8, 0.8, 0.8, 1))
        self.eng_label.bind(size=lambda s, w: s.setter('text_size')(s, (w[0], None)))
        self.eng_scroll = ScrollView(size_hint_y=0.45)
        self.eng_scroll.add_widget(self.eng_label)
        root.add_widget(self.eng_scroll)
        
        self.kor_label = Label(text="Loading...", size_hint_y=None, 
                              font_size='14sp', font_name=fn, halign='left', 
                              valign='top', padding=(15, 15), color=(0, 0.8, 1, 1))
        self.kor_label.bind(size=lambda s, w: s.setter('text_size')(s, (w[0], None)))
        self.kor_scroll = ScrollView(size_hint_y=0.45)
        self.kor_scroll.add_widget(self.kor_label)
        root.add_widget(self.kor_scroll)

        self.btn = Button(text="Start Translation", size_hint_y=None, height=95, 
                         font_name=fn, font_size='20sp', background_color=(0, 0.5, 0.9, 1))
        self.btn.bind(on_press=self.start_thread)
        root.add_widget(self.btn)

        if self.is_pydroid:
            Clock.schedule_once(lambda dt: self.init_app(), 0.3)
        else:
            Clock.schedule_once(lambda dt: self.request_permissions(), 0.5)
        
        return root

    def request_permissions(self):
        if ANDROID_PERMISSIONS:
            perms = [Permission.INTERNET, Permission.READ_EXTERNAL_STORAGE, 
                    Permission.WRITE_EXTERNAL_STORAGE]
            
            try:
                if Build and Build.VERSION.SDK_INT >= 30:
                    perms.append(Permission.MANAGE_EXTERNAL_STORAGE)
            except:
                pass
            
            self.kor_label.text = "Requesting storage permissions..."
            
            try:
                request_permissions(perms)
                Clock.schedule_once(lambda dt: self.check_permissions(), 4)
            except Exception as e:
                self.kor_label.text = "Permission request failed"
                Clock.schedule_once(lambda dt: self.init_app(), 1)
        else:
            Clock.schedule_once(lambda dt: self.init_app(), 0.5)

    def check_permissions(self):
        has_perm = False
        
        if ANDROID_PERMISSIONS:
            try:
                has_perm = check_permission(Permission.READ_EXTERNAL_STORAGE)
            except:
                has_perm = True
        else:
            has_perm = True
        
        if has_perm:
            self.kor_label.text = "Permissions OK. Loading library..."
            Clock.schedule_once(lambda dt: self.init_app(), 0.5)
        else:
            msg1 = "Permission denied!"
            msg2 = "Enable Storage in Settings"
            self.kor_label.text = msg1 + chr(10) + msg2
            self.file_spinner.text = 'No Permission'

    def init_app(self):
        def initialize():
            success, msg = safe_import()
            self.libs_loaded = success
            Clock.schedule_once(lambda dt: self.after_init(success))
        threading.Thread(target=initialize, daemon=True).start()

    def after_init(self, success):
        if success:
            self.kor_label.text = "Library loaded. Searching PDFs..."
            Clock.schedule_once(lambda dt: self.refresh_files(None), 0.5)
        else:
            self.file_spinner.text = 'Library Error'
            self.kor_label.text = 'PyPDF2 load failed'

    def refresh_files(self, instance):
        def load():
            files = []
            paths = ["/storage/emulated/0/Download", "/sdcard/Download", 
                    "/storage/sdcard0/Download"]
            found = None
            
            for p in paths:
                try:
                    if os.path.exists(p) and os.access(p, os.R_OK):
                        all_f = os.listdir(p)
                        temp = [f for f in all_f if f.lower().endswith('.pdf')]
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
            self.file_spinner.text = 'Select PDF'
            self.file_spinner.values = files
            n = str(len(files))
            t1 = "Ready! Found " + n + " PDFs"
            t2 = "Path: " + self.download_path
            self.kor_label.text = t1 + chr(10) + t2
        else:
            self.file_spinner.text = 'No PDF'
            self.file_spinner.values = ['Tap to refresh']
            msg1 = "No PDF found"
            msg2 = "Check /Download/ folder"
            self.kor_label.text = msg1 + chr(10) + msg2

    def start_thread(self, instance):
        if not self.libs_loaded:
            self.kor_label.text = "Library not loaded"
            return
        if self.file_spinner.text in ('Select PDF', 'Initializing...', 'Requesting permissions...', 'No PDF', 'Library Error', 'No Permission'):
            self.kor_label.text = "Select PDF first"
            return
        
        self.btn.disabled = True
        self.eng_label.text = ""
        self.kor_label.text = "Starting..."
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
                clean = txt.replace(chr(10), ' ')
                sents = [s.strip() for s in clean.split('. ') if len(s) > 5]
                
                for j, sent in enumerate(sents):
                    trans = translate_text(sent, 'ko')
                    for w, c in self.kmle_db.items():
                        trans = trans.replace(w, c)
                    
                    prog = ((i / total) + (j / len(sents) / total)) * 100
                    self.is_typing = True
                    Clock.schedule_once(lambda dt, s=sent, t=trans, p=prog: self.type_sync(s, t, p))
                    while self.is_typing:
                        time.sleep(0.005)
            
            Clock.schedule_once(lambda dt: self.complete())
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.kor_label, 'text', "Error: " + str(e)))

    def type_sync(self, eng, kor, prog):
        nl = chr(10)
        et = "• " + eng + nl + nl
        kt = "• " + kor + nl + nl
        for i, c in enumerate(et):
            Clock.schedule_once(lambda dt, ch=c: self.update_ui('eng', ch), i * 0.001)
        d = len(et) * 0.001
        for i, c in enumerate(kt):
            last = (i == len(kt) - 1)
            Clock.schedule_once(lambda dt, ch=c, l=last, p=prog: self.update_ui('kor', ch, l, p), d + (i * 0.002))

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
        self.btn.text = "Complete!"
        self.pb.value = 100
        self.percent_label.text = "100.0%"

if __name__ == "__main__":
    MedicalKivyTranslator().run()
