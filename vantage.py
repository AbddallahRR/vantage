#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import subprocess
import glob
import os
import re
import threading

APP_NAME = "Lenovo Vantage"
APP_VERSION = "2.0"

VPC_DEVICES = glob.glob("/sys/bus/platform/devices/VPC2004:*")
VPC = VPC_DEVICES[0] if VPC_DEVICES else None
PLATFORM_PROFILE = "/sys/firmware/acpi/platform_profile"

_touchpad_id = None


def get_touchpad_id():
    global _touchpad_id
    if _touchpad_id is not None:
        return _touchpad_id
    try:
        r = subprocess.run(["xinput", "list"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.split('\n'):
            if 'Touchpad' in line:
                m = re.search(r'id=(\d+)', line)
                if m:
                    _touchpad_id = m.group(1)
                    return _touchpad_id
    except:
        pass
    return None


def read_sysfs(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except:
        return None


def cmd_exists(cmd):
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0


def module_exists(mod):
    return subprocess.run(["modinfo", "-n", mod], capture_output=True).returncode == 0


def sysfs_on_off(path):
    if not path: return None
    v = read_sysfs(path)
    if v == "1": return "On"
    if v == "0": return "Off"
    return None


def sysfs_on_off_inverted(path):
    if not path: return None
    v = read_sysfs(path)
    if v == "0": return "On"
    if v == "1": return "Off"
    return None


HELPER = "/usr/lib/vantage/vantage-helper.sh"


def run_helper(action, arg=None):
    cmd = ["sudo", HELPER, action]
    if arg:
        cmd.append(arg)
    try:
        return subprocess.run(cmd, timeout=30).returncode == 0
    except:
        return False


def run_cmd(cmd, timeout=10):
    try:
        return subprocess.run(cmd, timeout=timeout).returncode == 0
    except:
        return False


class FeatureRow(Gtk.ListBoxRow):
    def __init__(self, name, icon, status_fn, action_fn,
                 control_type='switch', opts=None, available_fn=None):
        super().__init__()
        self._status_fn = status_fn
        self._action_fn = action_fn
        self._control_type = control_type
        self._updating = False

        available = available_fn() if available_fn else True

        self.set_property("activatable", False)
        self.set_can_focus(False)

        box = Gtk.Box(spacing=10, margin_start=12, margin_end=12,
                      margin_top=10, margin_bottom=10)

        lbl_icon = Gtk.Label()
        lbl_icon.set_markup(f'<span size="x-large">{icon}</span>')
        box.pack_start(lbl_icon, False, False, 0)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)

        lbl_name = Gtk.Label(label=name, xalign=0)
        lbl_name.set_markup(f'<b>{name}</b>')
        info.pack_start(lbl_name, False, False, 0)

        self.lbl_status = Gtk.Label(xalign=0)
        self.lbl_status.get_style_context().add_class("dim-label")
        info.pack_start(self.lbl_status, False, False, 0)

        box.pack_start(info, True, True, 0)

        if control_type == 'switch':
            self.ctrl = Gtk.Switch(valign=Gtk.Align.CENTER)
            self.ctrl.connect("notify::active", self._on_switch)
        elif control_type == 'combo':
            self.ctrl = Gtk.ComboBoxText(valign=Gtk.Align.CENTER)
            for o in (opts or []):
                self.ctrl.append_text(o)
            self.ctrl.connect("changed", self._on_combo)

        box.pack_end(self.ctrl, False, False, 0)
        self.add(box)

        if not available:
            self.set_sensitive(False)
            self.lbl_status.set_text("Not available")

        self.show_all()

    def refresh(self):
        if not self.get_sensitive():
            return
        try:
            status = self._status_fn()
            if status is None:
                self.lbl_status.set_text("Error")
                return
            self.lbl_status.set_text(status)
            self._updating = True
            if self._control_type == 'switch':
                active = status.lower() in ('on', 'active', 'enabled')
                self.ctrl.set_active(active)
            elif self._control_type == 'combo':
                model = self.ctrl.get_model()
                found = False
                norm = status.lower().replace('-', ' ')
                for i in range(len(model)):
                    opt_text = model[i][0]
                    if opt_text.lower() == status.lower() or opt_text.lower() == norm:
                        self.ctrl.set_active(i)
                        found = True
                        break
                if not found:
                    self._updating = False
                    return
            self._updating = False
        except Exception:
            self.lbl_status.set_text("Error")
            self._updating = False

    def _run_action(self, action):
        def task():
            ok = self._action_fn(action)
            GLib.idle_add(self.refresh)
            if not ok:
                GLib.idle_add(self._show_error, f"Failed: {self._get_name()} → {action}")
        threading.Thread(target=task, daemon=True).start()

    def _get_name(self):
        return self.get_children()[0].get_children()[1].get_children()[0].get_text()

    def _show_error(self, msg):
        w = self.get_toplevel()
        if hasattr(w, 'show_message'):
            w.show_message(msg, Gtk.MessageType.ERROR)

    def _on_switch(self, sw, pspec):
        if self._updating:
            return
        action = "On" if sw.get_active() else "Off"
        self._run_action(action)

    def _on_combo(self, combo):
        if self._updating:
            return
        action = combo.get_active_text()
        if action:
            self._run_action(action)


class VantageWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=APP_NAME)
        self.set_default_size(440, 460)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("lenovo-vantage")

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if os.path.exists(icon_path):
            self.set_icon_from_file(icon_path)

        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = APP_NAME

        btn_refresh = Gtk.Button.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        btn_refresh.set_tooltip_text("Refresh status")
        btn_refresh.connect("clicked", self._on_refresh)
        hb.pack_end(btn_refresh)

        btn_about = Gtk.Button.new_from_icon_name("help-about-symbolic", Gtk.IconSize.BUTTON)
        btn_about.set_tooltip_text("About")
        btn_about.connect("clicked", self._show_about)
        hb.pack_end(btn_about)

        self.set_titlebar(hb)

        self.infobar = Gtk.InfoBar()
        self.infobar.set_show_close_button(True)
        self.infobar.connect("response", lambda w, r: w.hide())
        self.infobar_label = Gtk.Label()
        self.infobar.get_content_area().add(self.infobar_label)
        self.infobar.set_no_show_all(True)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.get_style_context().add_class("boxed-list")

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.listbox)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(self.infobar, False, False, 0)
        vbox.pack_start(scrolled, True, True, 0)
        self.add(vbox)

        self.rows = []
        self._build_features()

        css = b"""
        .boxed-list {
            border: 1px solid alpha(currentColor, 0.15);
            border-radius: 8px;
            margin: 6px;
        }
        .boxed-list row {
            border-bottom: 1px solid alpha(currentColor, 0.08);
            padding: 2px 0;
        }
        .boxed-list row:last-child { border-bottom: none; }
        .dim-label { opacity: 0.65; font-size: 0.85em; }
        window { background: @theme_bg_color; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._on_refresh()
        GLib.timeout_add_seconds(5, self._on_refresh)

    def _build_features(self):
        vpc_path = VPC

        def vpc_file(name):
            return os.path.join(vpc_path, name) if vpc_path else None

        cons_path = vpc_file("conservation_mode")
        usb_path = vpc_file("usb_charging")
        fn_path = vpc_file("fn_lock")

        features = []
        features.append(("Conservation Mode", "🔋",
            lambda p=cons_path: sysfs_on_off(p),
            lambda a: run_helper("conservation-on" if a == "On" else "conservation-off"),
            'switch', None,
            lambda p=cons_path: p is not None and os.path.exists(p)))

        features.append(("Always-On USB", "🔌",
            lambda p=usb_path: sysfs_on_off(p),
            lambda a: run_helper("usb-on" if a == "On" else "usb-off"),
            'switch', None,
            lambda p=usb_path: p is not None and os.path.exists(p)))

        features.append(("Fan Mode", "🌡\uFE0F",
            self._get_fan_status,
            self._set_fan_mode,
            'combo', ["Low Power", "Balanced", "Performance"],
            lambda: os.path.exists(PLATFORM_PROFILE)))

        features.append(("FN Lock", "⌨\uFE0F",
            lambda p=fn_path: sysfs_on_off_inverted(p),
            lambda a: run_helper("fn-on" if a == "On" else "fn-off"),
            'switch', None,
            lambda p=fn_path: p is not None and os.path.exists(p)))

        features.append(("Camera", "📷",
            self._get_camera_status,
            self._toggle_camera,
            'switch', None,
            lambda: module_exists("uvcvideo")))

        features.append(("Microphone", "🎤",
            self._get_mic_status,
            self._toggle_mic,
            'switch', None,
            lambda: cmd_exists("pactl")))

        features.append(("Touchpad", "🖱",
            self._get_touchpad_status,
            self._toggle_touchpad,
            'switch', None,
            lambda: get_touchpad_id() is not None))

        features.append(("WiFi", "🌐",
            self._get_wifi_status,
            self._toggle_wifi,
            'switch', None,
            lambda: cmd_exists("nmcli")))

        for f in features:
            row = FeatureRow(f[0], f[1], f[2], f[3], f[4], f[5], f[6])
            self.listbox.add(row)
            self.rows.append(row)

    def _get_fan_status(self):
        v = read_sysfs(PLATFORM_PROFILE)
        if v is None:
            return None
        mapping = {"low-power": "Low Power", "balanced": "Balanced",
                   "performance": "Performance", "custom": "Custom"}
        return mapping.get(v, v.title())

    def _get_camera_status(self):
        r = subprocess.run(["lsmod"], capture_output=True, text=True, timeout=5)
        return "On" if "uvcvideo" in r.stdout else "Off"

    def _get_mic_status(self):
        r = subprocess.run(["pactl", "get-source-mute", "@DEFAULT_SOURCE@"],
                          capture_output=True, text=True, timeout=5)
        return "Muted" if "yes" in r.stdout else "Active"

    def _get_touchpad_status(self):
        tid = get_touchpad_id()
        if not tid:
            return None
        r = subprocess.run(["xinput", "--list-props", tid],
                          capture_output=True, text=True, timeout=5)
        for line in r.stdout.split('\n'):
            if "Device Enabled" in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    v = parts[-1].strip()
                    return "On" if v == "1" else "Off"
        return None

    def _get_wifi_status(self):
        r = subprocess.run(["nmcli", "radio", "wifi"],
                          capture_output=True, text=True, timeout=5)
        return "On" if r.stdout.strip() == "enabled" else "Off"

    def _set_fan_mode(self, mode):
        mapping = {"Low Power": "low-power", "Balanced": "balanced",
                   "Performance": "performance"}
        val = mapping.get(mode, mode.lower())
        return run_helper("fan", val)

    def _toggle_camera(self, action):
        return run_helper("camera-on" if action == "On" else "camera-off")

    def _toggle_mic(self, action):
        if action == "Off":
            return run_cmd(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "1"])
        return run_cmd(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "0"])

    def _toggle_touchpad(self, action):
        tid = get_touchpad_id()
        if not tid:
            return False
        if action == "On":
            return run_cmd(["xinput", "enable", tid])
        return run_cmd(["xinput", "disable", tid])

    def _toggle_wifi(self, action):
        if action == "On":
            return run_cmd(["nmcli", "radio", "wifi", "on"])
        return run_cmd(["nmcli", "radio", "wifi", "off"])

    def _on_refresh(self, *args):
        for row in self.rows:
            row.refresh()
        return True

    def show_message(self, text, msg_type=Gtk.MessageType.INFO):
        self.infobar.set_message_type(msg_type)
        self.infobar_label.set_text(text)
        self.infobar.show_all()
        self.infobar_label.show()
        GLib.timeout_add_seconds(4, lambda: self.infobar.hide())

    def _show_about(self, *args):
        dlg = Gtk.AboutDialog(transient_for=self, modal=True)
        dlg.set_program_name(APP_NAME)
        dlg.set_version(APP_VERSION)
        dlg.set_comments("Hardware control panel for Lenovo laptops")
        dlg.set_copyright("Based on vantage.sh by Nizam & Lanchon")
        dlg.set_license_type(Gtk.License.GPL_2_0)
        dlg.set_website("https://github.com/niizam/vantage")
        dlg.set_logo_icon_name("lenovo-vantage")
        dlg.run()
        dlg.destroy()


class VantageApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="io.github.niizam.vantage", flags=0)

    def do_activate(self):
        win = VantageWindow(self)
        win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)


if __name__ == "__main__":
    app = VantageApp()
    app.run()
