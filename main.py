import json
import os
import time
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

AUDIO = ["*.mp3", "*.wav", "*.ogg", "*.m4a"]
PAD_NAMES = ["DJ AMON", "FIRE", "HORN", "SIREN"]
START_DIR = "/storage/emulated/0"


def fmt(sec):
    m, s = divmod(int(max(sec, 0)), 60)
    return "%d:%02d" % (m, s)


def start_folder():
    return START_DIR if os.path.isdir(START_DIR) else "/"


def app_dir():
    return App.get_running_app().user_data_dir


def rec_folder():
    folder = os.path.join(app_dir(), "DJ_Mixes")
    os.makedirs(folder, exist_ok=True)
    return folder


def save_file():
    return os.path.join(app_dir(), "dj_data.json")


def load_data():
    try:
        with open(save_file()) as f:
            return json.load(f)
    except Exception:
        return {}


def save_data(data):
    try:
        with open(save_file(), "w") as f:
            json.dump(data, f)
    except Exception:
        pass


class Deck(BoxLayout):
    def __init__(self, name, **kwargs):
        super().__init__(orientation="vertical", spacing=4, padding=4, **kwargs)
        self.name = name
        self.playlist = []
        self.index = -1
        self.sound = None
        self.playing = False
        self.saved_pos = 0
        self.started = 0
        self.gain = 1.0

        self.add_widget(Label(text="DECK " + name, size_hint_y=0.1))

        self.track = Label(text="No track", size_hint_y=0.15,
                           halign="center", shorten=True,
                           shorten_from="right", font_size="13sp")
        self.track.bind(size=lambda i, v: setattr(i, "text_size", v))
        self.add_widget(self.track)

        self.info = Label(text="0:00 / 0:00", size_hint_y=0.1,
                          font_size="13sp")
        self.add_widget(self.info)

        row1 = BoxLayout(size_hint_y=0.2, spacing=4)
        b_prev = Button(text="Prev")
        b_prev.bind(on_press=self.prev_track)
        self.play_btn = Button(text="Play")
        self.play_btn.bind(on_press=self.toggle)
        b_next = Button(text="Next")
        b_next.bind(on_press=self.next_track)
        row1.add_widget(b_prev)
        row1.add_widget(self.play_btn)
        row1.add_widget(b_next)
        self.add_widget(row1)

        row2 = BoxLayout(size_hint_y=0.2, spacing=4)
        b_add = Button(text="Add songs")
        b_add.bind(on_press=self.add_songs)
        b_rs = Button(text="Restart")
        b_rs.bind(on_press=self.restart)
        row2.add_widget(b_add)
        row2.add_widget(b_rs)
        self.add_widget(row2)

        self.add_widget(Label(text="Volume", size_hint_y=0.07,
                              font_size="12sp"))
        self.volume = Slider(min=0, max=1, value=0.8, size_hint_y=0.18)
        self.volume.bind(value=lambda i, v: self.apply_volume())
        self.add_widget(self.volume)

        Clock.schedule_interval(self.tick, 0.5)

    def apply_volume(self):
        if self.sound:
            self.sound.volume = self.volume.value * self.gain

    def load_index(self, i, play=False):
        if not self.playlist:
            return
        i = i % len(self.playlist)
        s = SoundLoader.load(self.playlist[i])
        if not s:
            self.track.text = "Cannot load file"
            return
        if self.sound:
            self.sound.stop()
        self.sound = s
        self.index = i
        self.saved_pos = 0
        self.playing = False
        self.play_btn.text = "Play"
        self.apply_volume()
        self.track.text = "%d/%d  %s" % (
            i + 1, len(self.playlist), os.path.basename(self.playlist[i]))
        if play:
            self.play()

    def play(self):
        if not self.sound:
            return
        self.sound.play()
        if self.saved_pos:
            self.sound.seek(self.saved_pos)
        self.playing = True
        self.started = time.time()
        self.play_btn.text = "Pause"

    def pause(self):
        if not self.sound:
            return
        self.saved_pos = self.sound.get_pos()
        self.sound.stop()
        self.playing = False
        self.play_btn.text = "Play"

    def toggle(self, *a):
        if self.playing:
            self.pause()
        else:
            self.play()

    def restart(self, *a):
        self.saved_pos = 0
        if self.sound and self.playing:
            self.sound.seek(0)

    def next_track(self, *a):
        if self.playlist:
            self.load_index(self.index + 1, play=self.playing)

    def prev_track(self, *a):
        if self.playlist:
            self.load_index(self.index - 1, play=self.playing)

    def add_songs(self, *a):
        chooser = FileChooserListView(path=start_folder(), multiselect=True,
                                      filters=AUDIO)
        box = BoxLayout(orientation="vertical")
        box.add_widget(chooser)
        btn = Button(text="Add selected", size_hint_y=0.12)
        box.add_widget(btn)
        popup = Popup(title="Deck " + self.name, content=box,
                      size_hint=(0.95, 0.95))

        def add(*x):
            for p in chooser.selection:
                if os.path.isfile(p):
                    self.playlist.append(p)
            popup.dismiss()
            if self.sound is None and self.playlist:
                self.load_index(0)

        btn.bind(on_press=add)
        popup.open()

    def tick(self, dt):
        if not self.sound:
            return
        pos = self.sound.get_pos() if self.playing else self.saved_pos
        self.info.text = "%s / %s" % (fmt(pos), fmt(self.sound.length or 0))
        if (self.playing and self.sound.state != "play"
                and time.time() - self.started > 1.5):
            self.playing = False
            self.play_btn.text = "Play"
            self.load_index(self.index + 1, play=True)


class Mixer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.score = 0.0
        self.msg = "Welcome DJ"
        self.recorder = None
        self.rec_path = ""
        self.rec_start = 0
        self.pad_paths = [None] * 4
        self.pad_sounds = [None] * 4

        decks = BoxLayout(size_hint_y=0.55)
        self.a = Deck("A")
        self.b = Deck("B")
        decks.add_widget(self.a)
        decks.add_widget(self.b)
        self.add_widget(decks)

        self.add_widget(Label(text="Crossfader  A <---> B", size_hint_y=0.04,
                              font_size="12sp"))
        self.cross = Slider(min=0, max=1, value=0.5, size_hint_y=0.07)
        self.cross.bind(value=self.on_cross)
        self.add_widget(self.cross)

        pads = BoxLayout(size_hint_y=0.1, spacing=4)
        self.pad_btns = []
        for i, n in enumerate(PAD_NAMES):
            b = Button(text=n, font_size="12sp")
            b.bind(on_press=lambda inst, i=i: self.pad_press(i))
            pads.add_widget(b)
            self.pad_btns.append(b)
        self.add_widget(pads)

        tools = BoxLayout(size_hint_y=0.1, spacing=4)
        self.rec_btn = ToggleButton(text="REC", font_size="13sp")
        self.rec_btn.bind(state=self.on_rec)
        self.assign = ToggleButton(text="Change pad", font_size="13sp")
        rank = Button(text="RANKING", font_size="13sp")
        rank.bind(on_press=self.open_rank)
        tools.add_widget(self.rec_btn)
        tools.add_widget(self.assign)
        tools.add_widget(rank)
        self.add_widget(tools)

        self.status = Label(text="", size_hint_y=0.06, font_size="12sp")
        self.add_widget(self.status)

        self.on_cross(None, 0.5)
        Clock.schedule_once(lambda dt: self.load_pads(), 1)
        Clock.schedule_interval(self.second, 1)

    def on_cross(self, inst, x):
        self.a.gain = min(1.0, 2 * (1 - x))
        self.b.gain = min(1.0, 2 * x)
        self.a.apply_volume()
        self.b.apply_volume()

    # ---------- pads ----------
    def load_pads(self):
        paths = load_data().get("pads", [None] * 4)
        for i in range(4):
            if i < len(paths) and paths[i] and os.path.isfile(paths[i]):
                self.set_pad(i, paths[i], save=False)

    def set_pad(self, i, path, save=True):
        s = SoundLoader.load(path)
        if not s:
            self.msg = "Cannot load that sound"
            return
        self.pad_paths[i] = path
        self.pad_sounds[i] = s
        self.pad_btns[i].background_color = (0.2, 1, 0.3, 1)
        if save:
            d = load_data()
            d["pads"] = self.pad_paths
            save_data(d)
            self.msg = PAD_NAMES[i] + " pad ready"

    def pad_press(self, i):
        if self.assign.state == "down" or not self.pad_sounds[i]:
            self.assign.state = "normal"
            self.choose_sample(i)
            return
        s = self.pad_sounds[i]
        s.stop()
        s.volume = 1.0
        s.play()
        self.score += 2

    def choose_sample(self, i):
        chooser = FileChooserListView(path=start_folder(), filters=AUDIO)
        box = BoxLayout(orientation="vertical")
        box.add_widget(chooser)
        rec_b = Button(text="Open my recordings folder", size_hint_y=0.12)
        box.add_widget(rec_b)
        popup = Popup(title="Pick sound for " + PAD_NAMES[i],
                      content=box, size_hint=(0.95, 0.95))

        def go_rec(*x):
            try:
                chooser.path = rec_folder()
            except Exception:
                pass

        def picked(inst, sel, touch):
            if sel and os.path.isfile(sel[0]):
                self.set_pad(i, sel[0])
                popup.dismiss()

        rec_b.bind(on_press=go_rec)
        chooser.bind(on_submit=picked)
        popup.open()

    # ---------- recording ----------
    def on_rec(self, inst, state):
        if state == "down":
            if not self.start_rec():
                inst.state = "normal"
        else:
            self.stop_rec()

    def start_rec(self):
        try:
            from jnius import autoclass
            MediaRecorder = autoclass("android.media.MediaRecorder")
            Source = autoclass("android.media.MediaRecorder$AudioSource")
            OutFmt = autoclass("android.media.MediaRecorder$OutputFormat")
            Enc = autoclass("android.media.MediaRecorder$AudioEncoder")

            self.rec_path = os.path.join(
                rec_folder(), time.strftime("mix_%Y%m%d_%H%M%S.m4a"))

            r = MediaRecorder()
            r.setAudioSource(Source.MIC)
            r.setOutputFormat(OutFmt.MPEG_4)
            r.setAudioEncoder(Enc.AAC)
            r.setOutputFile(self.rec_path)
            r.prepare()
            r.start()
            self.recorder = r
            self.rec_start = time.time()
            self.msg = "Recording..."
            return True
        except Exception as e:
            self.recorder = None
            self.msg = "Rec failed: " + str(e).replace("\n", " ")[:90]
            return False

    def stop_rec(self):
        r = self.recorder
        self.recorder = None
        self.rec_btn.text = "REC"
        if not r:
            return
        try:
            r.stop()
            r.release()
            self.score += 10
            self.msg = "Saved in DJ_Mixes"
        except Exception:
            self.msg = "Recording too short"

    # ---------- ranking ----------
    def board_text(self, data):
        scores = data.get("scores", {})
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:10]
        if not top:
            return "No scores yet.\nSave yours to start!"
        lines = []
        for n, (name, pts) in enumerate(top):
            lines.append("%d.  %s  -  %d pts" % (n + 1, name, pts))
        return "\n".join(lines)

    def open_rank(self, *a):
        data = load_data()
        box = BoxLayout(orientation="vertical", spacing=8, padding=8)
        box.add_widget(Label(text="Your score: %d pts" % int(self.score),
                             size_hint_y=0.1))
        name_in = TextInput(text=data.get("name", ""), hint_text="DJ name",
                            multiline=False, size_hint_y=0.12)
        box.add_widget(name_in)
        board = Label(text=self.board_text(data), size_hint_y=0.5)
        box.add_widget(board)
        save_btn = Button(text="Save my score", size_hint_y=0.14)
        close_btn = Button(text="Close", size_hint_y=0.12)
        box.add_widget(save_btn)
        box.add_widget(close_btn)
        popup = Popup(title="DJ RANKING", content=box, size_hint=(0.92, 0.85))

        def save(*x):
            name = name_in.text.strip() or "DJ"
            d = load_data()
            sc = d.get("scores", {})
            sc[name] = max(sc.get(name, 0), int(self.score))
            d["scores"] = sc
            d["name"] = name
            save_data(d)
            board.text = self.board_text(d)

        save_btn.bind(on_press=save)
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def second(self, dt):
        if self.a.playing or self.b.playing:
            self.score += 0.2
        if self.recorder:
            self.rec_btn.text = "REC " + fmt(time.time() - self.rec_start)
        self.status.text = "%s  |  Score %d" % (self.msg, int(self.score))


class DJApp(App):
    title = "DJ Amon Mixer"

    def build(self):
        try:
            return Mixer()
        except Exception:
            sv = ScrollView()
            lab = Label(text=traceback.format_exc(), font_size="12sp",
                        size_hint_y=None, halign="left", valign="top")
            lab.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
            lab.bind(texture_size=lambda i, s: setattr(i, "height", s[1]))
            sv.add_widget(lab)
            return sv

    def on_start(self):
        if platform == "android":
            try:
                from android.permissions import request_permissions, Permission
                perms = [Permission.RECORD_AUDIO]
                for name in ("READ_MEDIA_AUDIO", "READ_EXTERNAL_STORAGE"):
                    if hasattr(Permission, name):
                        perms.append(getattr(Permission, name))
                request_permissions(perms)
            except Exception:
                pass


if __name__ == "__main__":
    DJApp().run()
