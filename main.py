#!/usr/bin/env python3
"""
Personal VPN – Android App (Kivy)
Full GUI + domain‑fronted GAS‑CFW tunnel, all in one APK.

Author: Ehsan Poursamad
Thanks to: Aref.P
"""

import json, os, sys, io, re, threading, asyncio, logging, time, queue
from pathlib import Path

# We include the mhr-cfw modules from the 'src' folder
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, SRC_DIR)

import cert_installer, mitm, proxy_server, google_ip_scanner
from cert_installer import install_ca, uninstall_ca, is_ca_trusted
from mitm import CA_CERT_FILE
from proxy_server import ProxyServer
from google_ip_scanner import scan_sync

# -------------------------- Kivy imports --------------------------
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse
from kivy.uix.behaviors import ButtonBehavior
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.utils import platform
from kivy.uix.image import AsyncImage

# For Android foreground service
try:
    from jnius import autoclass
    PythonService = autoclass('org.kivy.android.PythonService')
    AndroidActivity = autoclass('org.kivy.android.PythonActivity')
    NotificationBuilder = autoclass('android.app.Notification$Builder')
    Context = autoclass('android.content.Context')
    Intent = autoclass('android.content.Intent')
    has_android = True
except:
    has_android = False

# -------------------------- Logging --------------------------
log_messages = []
MAX_LOG = 200

def gui_log(msg):
    log_messages.append(msg)
    if len(log_messages) > MAX_LOG:
        del log_messages[0]

class QueueHandler(logging.Handler):
    def emit(self, record):
        gui_log(self.format(record))

logging.basicConfig(level=logging.DEBUG, handlers=[QueueHandler()], format='%(asctime)s • %(levelname)-7s [%(name)-8s] %(message)s', datefmt='%H:%M:%S')

# -------------------------- Bilingual texts --------------------------
T = {
    "en": {
        "title": "Personal VPN",
        "subtitle": "by Ehsan.P  /  Thanks to Aref.P",
        "connect": "Connect",
        "disconnect": "Disconnect",
        "status_off": "Disconnected",
        "status_connecting": "Connecting…",
        "status_on": "Connected",
        "export_log": "Export Log",
        "clear_log": "Clear",
        "settings": "Settings",
        "help": "Help",
        "help_text": (
            "📚 Deploy your Google Apps Script relay\n\n"
            "1. Go to https://script.google.com, create a project.\n"
            "2. Paste Code.gs and set AUTH_KEY.\n"
            "3. Deploy as Web App, copy Deployment ID.\n"
            "4. Enter that ID + Auth Key in Settings.\n"
            "5. Click Connect.\n\n"
            "Use Firefox with 'Use third party CA certificates' enabled.\n\n"
            "For mobile data: add proxy 127.0.0.1:8085 in APN settings."
        ),
        "rate_limit": "Rate limit detected! Re‑deploy script.",
        "exit": "Exit",
        "auth_key": "Auth Key",
        "script_id": "Script ID",
        "listen_host": "Listen Host",
        "listen_port": "Listen Port",
        "socks5_port": "Socks5 Port",
        "google_ip": "Google IP",
        "front_domain": "Front Domain",
        "lan_sharing": "LAN Sharing",
        "socks5_enabled": "Socks5 Enabled",
        "auto_proxy": "Auto proxy (Android not yet)",
        "save_config": "Save Config",
        "load_config": "Load Config",
        "validate": "Validate",
        "cert_install": "Install CA",
        "cert_uninstall": "Uninstall CA",
        "cert_check": "Check Trust",
        "cert_status": "Certificate: ",
        "scanner_scan": "Scan Google IPs",
        "scanner_set": "Set",
        "block_hosts": "Block data-heavy hosts",
        "block_apply": "Apply Blocker",
        "apn_settings": "Open APN Settings (for mobile proxy)",
        "apn_guide": "To set proxy on mobile data:\n- Tap 'Open APN Settings'\n- Edit your APN\n- Set Proxy: 127.0.0.1, Port: 8085\n- Save and select that APN.",
    },
    "fa": {
        "title": "Personal VPN",
        "subtitle": "ساخته احسان.پ  /  با تشکر از عارف.پ",
        "connect": "اتصال",
        "disconnect": "قطع",
        "status_off": "قطع",
        "status_connecting": "در حال اتصال…",
        "status_on": "متصل",
        "export_log": "خروجی گزارش",
        "clear_log": "پاک کردن",
        "settings": "تنظیمات",
        "help": "راهنما",
        "help_text": (
            "📚 راهنمای استقرار رله Google Apps Script\n\n"
            "۱. به script.google.com بروید، پروژه جدید بسازید.\n"
            "۲. Code.gs را جایگذاری و AUTH_KEY تنظیم کنید.\n"
            "۳. به عنوان Web App مستقر کنید، ID را کپی کنید.\n"
            "۴. ID و Auth Key را در تنظیمات وارد کنید.\n"
            "۵. اتصال بزنید.\n\n"
            "در Firefox گزینه 'Use third party CA certificates' را فعال کنید.\n\n"
            "برای اینترنت همراه: در APN پروکسی 127.0.0.1:8085 را اضافه کنید."
        ),
        "rate_limit": "محدودیت نرخ! اسکریپت جدید مستقر کنید.",
        "exit": "خروج",
        "auth_key": "Auth Key",
        "script_id": "Script ID",
        "listen_host": "Listen Host",
        "listen_port": "Listen Port",
        "socks5_port": "Socks5 Port",
        "google_ip": "Google IP",
        "front_domain": "Front Domain",
        "lan_sharing": "LAN Sharing",
        "socks5_enabled": "Socks5 Enabled",
        "auto_proxy": "Auto proxy (Android not yet)",
        "save_config": "ذخیره تنظیمات",
        "load_config": "بارگذاری",
        "validate": "بررسی",
        "cert_install": "نصب CA",
        "cert_uninstall": "حذف CA",
        "cert_check": "بررسی اعتماد",
        "cert_status": "گواهی: ",
        "scanner_scan": "اسکن IP گوگل",
        "scanner_set": "تنظیم",
        "block_hosts": "مسدود کردن هاست‌های پرمصرف",
        "block_apply": "اعمال",
        "apn_settings": "تنظیمات APN (پروکسی اینترنت همراه)",
        "apn_guide": "برای تنظیم پروکسی روی اینترنت همراه:\n- روی 'تنظیمات APN' بزنید\n- APN خود را ویرایش کنید\n- Proxy: 127.0.0.1, Port: 8085\n- ذخیره و انتخاب کنید.",
    }
}

# -------------------------- Circular Button --------------------------
class CircularButton(ButtonBehavior, Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (180, 180)
        self.radius = 90
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        with self.canvas:
            self.bg_color = Color(0.5, 0.5, 0.5, 1)  # grey
            self.ellipse = Ellipse(pos=self.pos, size=self.size)
    def _update_canvas(self, *args):
        self.ellipse.pos = self.pos
        self.ellipse.size = self.size
    def set_color(self, r, g, b, a=1):
        self.bg_color.rgba = (r, g, b, a)

# -------------------------- Main App --------------------------
class PersonalVPNApp(App):
    language = StringProperty("en")
    tunnel_running = BooleanProperty(False)
    status_text = StringProperty("Disconnected")
    button_text = StringProperty("Connect")

    def build(self):
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.proxy_thread = None
        self.loop = None
        self.server = None
        self.service = None
        return Builder.load_string(kv_string)

    def on_start(self):
        Clock.schedule_interval(self.update_logs, 1)
        self.load_config()
        # Start foreground service if on Android
        if has_android and not self.service:
            self.start_foreground_service()

    # ----- Foreground service -----
    def start_foreground_service(self):
        try:
            service_name = "com.ehsanpoursamad.personalvpn.ServiceProxy"
            self.service = PythonService()
            self.service.start(service_name, "Proxy running", "Tap to open app")
        except Exception as e:
            logging.error(f"Foreground service failed: {e}")

    def stop_foreground_service(self):
        if self.service:
            self.service.stop()
            self.service = None

    # ----- Tunnel control -----
    def toggle_tunnel(self):
        if self.tunnel_running:
            self.stop_tunnel()
        else:
            self.start_tunnel()

    def start_tunnel(self):
        if self.tunnel_running:
            return
        try:
            cfg = self._read_config()
        except:
            self.show_msg("Error", "Invalid config")
            return
        if not cfg.get("auth_key") or not (cfg.get("script_id") or cfg.get("script_ids")):
            self.show_msg("Missing", "Auth Key and Script ID required")
            return
        self.tunnel_running = True
        self.status_text = T[self.language]["status_connecting"]
        self.button_text = T[self.language]["disconnect"]
        self.root.ids.connect_btn.set_color(0, 0.8, 0, 1)  # green
        self.proxy_thread = threading.Thread(target=self._run_proxy, args=(cfg,), daemon=True)
        self.proxy_thread.start()

    def _run_proxy(self, config):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        try:
            self.server = ProxyServer(config)
            loop.run_until_complete(self.server.start())
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.getLogger("Tunnel").error(f"Fatal: {e}")
        finally:
            self.server = None
            self.loop = None
            self.tunnel_running = False
            self.status_text = T[self.language]["status_off"]
            self.button_text = T[self.language]["connect"]
            Clock.schedule_once(lambda dt: self._update_button_ui(), 0)

    def _update_button_ui(self):
        self.root.ids.connect_btn.set_color(0.5, 0.5, 0.5, 1)  # grey
        self.root.ids.status_label.text = self.status_text
        self.root.ids.connect_btn_label.text = self.button_text

    def stop_tunnel(self):
        if not self.tunnel_running or self.loop is None:
            return
        async def _cancel():
            tasks = [t for t in asyncio.all_tasks(self.loop) if t is not asyncio.current_task()]
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            self.loop.stop()
        asyncio.run_coroutine_threadsafe(_cancel(), self.loop)
        self.tunnel_running = False
        self.status_text = T[self.language]["status_off"]
        self.button_text = T[self.language]["connect"]
        self._update_button_ui()

    # ----- Config -----
    def _read_config(self):
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except:
            return {}

    def load_config(self, *args):
        cfg = self._read_config()
        for key, widget_id in [("auth_key", "auth_key"), ("script_id", "script_id"),
                               ("listen_host", "listen_host"), ("listen_port", "listen_port"),
                               ("socks5_port", "socks5_port"), ("google_ip", "google_ip"),
                               ("front_domain", "front_domain")]:
            val = cfg.get(key, "")
            self.root.ids[widget_id].text = str(val)
        self.root.ids.lan_sharing.active = cfg.get("lan_sharing", False)
        self.root.ids.socks5_enabled.active = cfg.get("socks5_enabled", True)
        self.root.ids.block_enabled.active = bool(cfg.get("block_hosts", []))
        block_hosts = "\n".join(cfg.get("block_hosts", []))
        self.root.ids.block_hosts.text = block_hosts
        self._update_cert_status()

    def save_config(self, *args):
        cfg = {
            "auth_key": self.root.ids.auth_key.text.strip(),
            "script_id": self.root.ids.script_id.text.strip(),
            "listen_host": self.root.ids.listen_host.text.strip(),
            "listen_port": int(self.root.ids.listen_port.text.strip() or 8085),
            "socks5_port": int(self.root.ids.socks5_port.text.strip() or 1080),
            "google_ip": self.root.ids.google_ip.text.strip(),
            "front_domain": self.root.ids.front_domain.text.strip(),
            "lan_sharing": self.root.ids.lan_sharing.active,
            "socks5_enabled": self.root.ids.socks5_enabled.active,
            "mode": "apps_script",
            "block_hosts": self.root.ids.block_hosts.text.strip().splitlines() if self.root.ids.block_enabled.active else [],
        }
        with open(self.config_path, "w") as f:
            json.dump(cfg, f, indent=2)
        self.show_msg("Saved", "Configuration saved")

    def validate_config(self, *args):
        cfg = {
            "auth_key": self.root.ids.auth_key.text.strip(),
            "script_id": self.root.ids.script_id.text.strip(),
        }
        if not cfg["auth_key"]:
            self.show_msg("Error", "Auth Key missing")
        elif not cfg["script_id"]:
            self.show_msg("Error", "Script ID missing")
        else:
            self.show_msg("OK", "Configuration seems valid")

    # ----- Certificate -----
    def cert_install(self):
        threading.Thread(target=lambda: self._cert_action("install")).start()
    def cert_uninstall(self):
        threading.Thread(target=lambda: self._cert_action("uninstall")).start()
    def cert_check(self):
        threading.Thread(target=lambda: self._cert_action("check")).start()
    def _cert_action(self, action):
        try:
            if action == "install":
                ok = install_ca(CA_CERT_FILE)
                msg = "CA installed" if ok else "CA install failed"
            elif action == "uninstall":
                ok = uninstall_ca(CA_CERT_FILE)
                msg = "CA removed" if ok else "CA removal failed"
            else:
                trusted = is_ca_trusted(CA_CERT_FILE)
                msg = f"Trusted: {trusted}"
            self.show_msg("Certificate", msg)
        except Exception as e:
            self.show_msg("Error", str(e))
        finally:
            self._update_cert_status()
    def _update_cert_status(self):
        if os.path.exists(CA_CERT_FILE):
            trusted = is_ca_trusted(CA_CERT_FILE)
            status = T[self.language]["cert_status"] + ("Trusted" if trusted else "Not trusted")
        else:
            status = T[self.language]["cert_status"] + "Missing"
        self.root.ids.cert_status_label.text = status

    # ----- Scanner -----
    def scan_ips(self):
        threading.Thread(target=self._scan_thread, daemon=True).start()
    def _scan_thread(self):
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()
        try:
            scan_sync(self.root.ids.front_domain.text.strip() or "www.google.com")
            output = mystdout.getvalue()
        except Exception as e:
            output = f"Scan error: {e}"
        finally:
            sys.stdout = old_stdout
        ips = []
        for line in output.splitlines():
            parts = line.strip().split()
            if parts and re.match(r"\d+\.\d+\.\d+\.\d+", parts[0]):
                ips.append((parts[0], parts[1] if len(parts)>1 else "?"))
        def update_ui(dt):
            grid = self.root.ids.scan_results
            grid.clear_widgets()
            if not ips:
                grid.add_widget(Label(text="No IPs found"))
                return
            for ip, lat in ips:
                grid.add_widget(Label(text=f"{ip} ({lat})"))
                btn = Button(text=T[self.language]["scanner_set"], size_hint_x=None, width=80)
                btn.bind(on_press=lambda x, ip=ip: self._set_ip(ip))
                grid.add_widget(btn)
        Clock.schedule_once(update_ui, 0)
    def _set_ip(self, ip):
        self.root.ids.google_ip.text = ip

    # ----- Data blocker -----
    def apply_blocker(self):
        self.save_config()

    # ----- Log viewer -----
    def update_logs(self, dt):
        self.root.ids.log_label.text = "\n".join(log_messages)
    def export_log(self):
        content = "\n".join(log_messages)
        from kivy.utils import platform
        if platform == "android":
            from jnius import cast
            from android.storage import primary_external_storage_path
            path = os.path.join(primary_external_storage_path(), "Download", "vpn_log.txt")
            with open(path, "w") as f:
                f.write(content)
            self.show_msg("Exported", f"Log saved to {path}")
        else:
            with open("vpn_log.txt", "w") as f:
                f.write(content)
            self.show_msg("Exported", "Log saved to vpn_log.txt")
    def clear_log(self):
        log_messages.clear()
        self.root.ids.log_label.text = ""

    # ----- APN helper -----
    def open_apn_settings(self):
        try:
            Intent = autoclass('android.content.Intent')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            intent = Intent(Intent.ACTION_MAIN)
            intent.setClassName("com.android.settings", "com.android.settings.ApnSettings")
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivity(intent)
        except:
            self.show_msg("Info", T[self.language]["apn_guide"])

    # ----- Language / Theme / Helpers -----
    def toggle_language(self, switch, value):
        self.language = "fa" if value else "en"
        self.refresh_texts()
    def toggle_theme(self, switch, value):
        Window.clearcolor = (0.1, 0.1, 0.1, 1) if value else (0.95, 0.95, 0.95, 1)
    def refresh_texts(self):
        root = self.root.ids
        root.connect_btn_label.text = T[self.language]["connect"] if not self.tunnel_running else T[self.language]["disconnect"]
        root.status_label.text = self.status_text
        root.help_text_label.text = T[self.language]["help_text"]
        root.subtitle_label.text = T[self.language]["subtitle"]
        # Settings labels
        for kid, lang_key in [
            ("auth_key_label", "auth_key"), ("script_id_label", "script_id"),
            ("listen_host_label", "listen_host"), ("listen_port_label", "listen_port"),
            ("socks5_port_label", "socks5_port"), ("google_ip_label", "google_ip"),
            ("front_domain_label", "front_domain"),
        ]:
            root[kid].text = T[self.language][lang_key]
    def show_msg(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.6, 0.4))
        popup.open()

# -------------------------- Kivy Language string --------------------------
kv_string = '''
#:import T __main__.T
BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        size_hint_y: None
        height: '70dp'
        BoxLayout:
            orientation: 'vertical'
            Label:
                text: "Personal VPN"
                font_size: '18sp'
                bold: True
            Label:
                id: subtitle_label
                text: T[app.language]['subtitle'] if app.language in T else 'by Ehsan.P'
                font_size: '12sp'
                color: 0.5,0.5,0.5,1
        BoxLayout:
            size_hint_x: None
            width: '150dp'
            Label:
                text: "Dark"
            Switch:
                id: theme_switch
                on_active: app.toggle_theme(*args)
            Label:
                text: "FA"
            Switch:
                id: lang_switch
                on_active: app.toggle_language(*args)
    TabbedPanel:
        id: main_tabs
        do_default_tab: False
        TabbedPanelItem:
            text: 'Dashboard'
            BoxLayout:
                orientation: 'vertical'
                FloatLayout:
                    size_hint_y: None
                    height: '200dp'
                    CircularButton:
                        id: connect_btn
                        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                        on_press: app.toggle_tunnel()
                    Label:
                        id: connect_btn_label
                        pos: connect_btn.pos[0] + 30, connect_btn.pos[1] + 70
                        text: app.button_text
                        font_size: '20sp'
                        color: 1,1,1,1
                Label:
                    id: status_label
                    text: app.status_text
                    font_size: '16sp'
                ScrollView:
                    Label:
                        id: log_label
                        text: 'Logs will appear here...'
                        size_hint_y: None
                        height: self.texture_size[1]
                        text_size: self.width, None
                        valign: 'top'
                BoxLayout:
                    size_hint_y: None
                    height: '48dp'
                    Button:
                        text: T[app.language]['export_log'] if app.language in T else 'Export'
                        on_release: app.export_log()
                    Button:
                        text: T[app.language]['clear_log'] if app.language in T else 'Clear'
                        on_release: app.clear_log()
                    Button:
                        text: T[app.language]['apn_settings'] if app.language in T else 'APN'
                        on_release: app.open_apn_settings()
        TabbedPanelItem:
            text: 'Settings'
            ScrollView:
                GridLayout:
                    cols: 1
                    size_hint_y: None
                    height: self.minimum_height
                    Label:
                        text: 'General'
                        bold: True
                    BoxLayout:
                        size_hint_y: None
                        height: '40dp'
                        Label:
                            id: auth_key_label
                            text: T[app.language]['auth_key'] if app.language in T else 'Auth Key'
                            size_hint_x: None
                            width: '150dp'
                        TextInput:
                            id: auth_key
                    BoxLayout:
                        size_hint_y: None
                        height: '40dp'
                        Label:
                            id: script_id_label
                            text: T[app.language]['script_id'] if app.language in T else 'Script ID'
                            size_hint_x: None
                            width: '150dp'
                        TextInput:
                            id: script_id
                    BoxLayout:
                        size_hint_y: None
                        height: '40dp'
                        Label:
                            id: listen_host_label
                            text: T[app.language]['listen_host'] if app.language in T else 'Listen Host'
                            size_hint_x: None
                            width: '150dp'
                        TextInput:
                            id: listen_host
                    BoxLayout:
                        size_hint_y: None
                        height: '40dp'
                        Label:
                            id: listen_port_label
                            text: T[app.language]['listen_port'] if app.language in T else 'Listen Port'
                            size_hint_x: None
                            width: '150dp'
                        TextInput:
                            id: listen_port
                    BoxLayout:
                        size_hint_y: None
                        height: '40dp'
                        Label:
                            id: socks5_port_label
                            text: T[app.language]['socks5_port'] if app.language in T else 'Socks5 Port'
                            size_hint_x: None
                            width: '150dp'
                        TextInput:
                            id: socks5_port
                    BoxLayout:
                        size_hint_y: None
                        height: '40dp'
                        Label:
                            id: google_ip_label
                            text: T[app.language]['google_ip'] if app.language in T else 'Google IP'
                            size_hint_x: None
                            width: '150dp'
                        TextInput:
                            id: google_ip
                    BoxLayout:
                        size_hint_y: None
                        height: '40dp'
                        Label:
                            id: front_domain_label
                            text: T[app.language]['front_domain'] if app.language in T else 'Front Domain'
                            size_hint_x: None
                            width: '150dp'
                        TextInput:
                            id: front_domain
                    BoxLayout:
                        size_hint_y: None
                        height: '40dp'
                        Label:
                            text: T[app.language]['lan_sharing'] if app.language in T else 'LAN Sharing'
                            size_hint_x: None
                            width: '150dp'
                        CheckBox:
                            id: lan_sharing
                    BoxLayout:
                        size_hint_y: None
                        height: '40dp'
                        Label:
                            text: T[app.language]['socks5_enabled'] if app.language in T else 'Socks5 Enabled'
                            size_hint_x: None
                            width: '150dp'
                        CheckBox:
                            id: socks5_enabled
                            active: True
                    BoxLayout:
                        size_hint_y: None
                        height: '48dp'
                        Button:
                            text: T[app.language]['load_config'] if app.language in T else 'Load Config'
                            on_release: app.load_config()
                        Button:
                            text: T[app.language]['save_config'] if app.language in T else 'Save Config'
                            on_release: app.save_config()
                        Button:
                            text: T[app.language]['validate'] if app.language in T else 'Validate'
                            on_release: app.validate_config()
                    Label:
                        text: 'Certificate'
                        bold: True
                    Label:
                        id: cert_status_label
                        text: 'Certificate: Unknown'
                    BoxLayout:
                        size_hint_y: None
                        height: '48dp'
                        Button:
                            text: T[app.language]['cert_install'] if app.language in T else 'Install CA'
                            on_release: app.cert_install()
                        Button:
                            text: T[app.language]['cert_uninstall'] if app.language in T else 'Uninstall CA'
                            on_release: app.cert_uninstall()
                        Button:
                            text: T[app.language]['cert_check'] if app.language in T else 'Check Trust'
                            on_release: app.cert_check()
                    Label:
                        text: 'Google IP Scanner'
                        bold: True
                    Button:
                        text: T[app.language]['scanner_scan'] if app.language in T else 'Scan'
                        on_release: app.scan_ips()
                    ScrollView:
                        size_hint_y: None
                        height: '100dp'
                        GridLayout:
                            id: scan_results
                            cols: 2
                            size_hint_y: None
                            height: self.minimum_height
                    Label:
                        text: 'Data Blocker'
                        bold: True
                    BoxLayout:
                        size_hint_y: None
                        height: '40dp'
                        Label:
                            text: T[app.language]['block_hosts'] if app.language in T else 'Block hosts'
                            size_hint_x: None
                            width: '150dp'
                        CheckBox:
                            id: block_enabled
                    TextInput:
                        id: block_hosts
                        text: "*.windowsupdate.com\\n*.windowsupdate.microsoft.com"
                        size_hint_y: None
                        height: '80dp'
                    Button:
                        text: T[app.language]['block_apply'] if app.language in T else 'Apply'
                        on_release: app.apply_blocker()
        TabbedPanelItem:
            text: 'Help'
            ScrollView:
                Label:
                    id: help_text_label
                    text: T[app.language]['help_text'] if app.language in T else 'Help'
                    size_hint_y: None
                    height: self.texture_size[1]
                    text_size: self.width, None
                    valign: 'top'
'''

if __name__ == "__main__":
    PersonalVPNApp().run()