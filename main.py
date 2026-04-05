import random
import os
from datetime import datetime
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, Select, Label, TextArea
from textual.containers import Vertical, VerticalScroll, Horizontal
from textual import on

# Setup Cache Directory
CACHE_DIR = Path.home() / ".cache" / "raptui"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_dictionary():
    paths = ["/usr/share/dict/words", "/usr/share/dict/american-english"]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                return [w.strip().lower() for w in f.readlines() if len(w.strip()) > 3]
    return ["flow", "rhythm", "beat", "rhyme", "street", "mic", "sound", "ground"]


DICTIONARY = load_dictionary()


class RapTuiApp(App):
    TITLE = "Rap TUI"

    BINDINGS = [
        ("escape", "exit_app", "Quit & Save"),
        ("ctrl+s", "toggle_settings", "Settings"),
        ("ctrl+n", "toggle_notebook", "Notebook"),
        ("ctrl+o", "save_lyrics", "Save Now"),
    ]

    CSS = """
    Screen { layers: base overlay; }
    #main_layout { width: 100%; height: 100%; }
    #game_container { align: center middle; width: 1fr; height: 100%; }
    
    #display_box {
        width: 60; height: 7;
        border: heavy $accent;
        content-align: center middle;
        margin-bottom: 1;
        background: $surface;
    }

    #main_input { width: 60; border: tall $primary; }

    #notebook_panel {
        width: 50; height: 100%;
        dock: right;
        border-left: double $secondary;
        background: $panel;
        display: none;
    }

    #notebook_title {
        padding: 1; background: $secondary;
        color: white; text-align: center; width: 100%;
    }

    #settings_pane {
        width: 40; height: auto;
        border: double $warning;
        padding: 1; background: $surface;
        display: none; position: absolute;
        offset-x: 10; offset-y: 5; layer: overlay;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main_layout"):
            with Vertical(id="game_container"):
                yield Static("Type a line to start the session!", id="display_box")
                yield Input(placeholder="Spit your bars...", id="main_input")

            with Vertical(id="notebook_panel"):
                yield Label("📓 NOTEBOOK (~/.cache/raptui/)", id="notebook_title")
                yield TextArea(id="lyrics_area")

        with VerticalScroll(id="settings_pane"):
            yield Label("[b]SETTINGS[/]", id="settings_title")
            yield Label("Rhyme Length:")
            yield Input("2", id="rhyme_len_input")
            yield Label("Theme:")
            yield Select(
                [("Default", "default"), ("Dark", "dark")],
                value="default",
                id="theme_select",
            )
        yield Footer()

    def action_save_lyrics(self) -> str:
        """Saves lyrics to ~/.cache/raptui/raptui-note-YYYYMMDD-HHMMSS.txt"""
        lyrics = self.query_one("#lyrics_area", TextArea).text
        if not lyrics.strip():
            return None

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = CACHE_DIR / f"raptui-note-{timestamp}.txt"

        with open(filename, "w") as f:
            f.write(lyrics)

        self.notify(f"Saved to {filename.name}", title="Backup Successful")
        return str(filename)

    def action_exit_app(self) -> None:
        """Saves one last time before closing."""
        self.action_save_lyrics()
        self.exit()

    def action_toggle_settings(self) -> None:
        pane = self.query_one("#settings_pane")
        pane.display = not pane.display
        (
            self.query_one("#rhyme_len_input").focus()
            if pane.display
            else self.query_one("#main_input").focus()
        )

    def action_toggle_notebook(self) -> None:
        note = self.query_one("#notebook_panel")
        note.display = not note.display
        (
            self.query_one("#lyrics_area").focus()
            if note.display
            else self.query_one("#main_input").focus()
        )

    @on(Input.Submitted, "#main_input")
    def process_bar(self, event: Input.Submitted):
        line = event.value.strip()
        if not line:
            return

        try:
            r_len = int(self.query_one("#rhyme_len_input").value)
        except:
            r_len = 2

        words = line.split()
        if words:
            suffix = words[-1].strip(".,!?;:")[-r_len:]
            matches = [w for w in DICTIONARY if w.endswith(suffix.lower())]
            suggestion = random.choice(matches) if matches else "No match"
            self.query_one("#display_box").update(
                f"Rhyme with: [b cyan]{suffix}[/]\nSuggestion: [b yellow]{suggestion}[/]"
            )
        event.input.value = ""


if __name__ == "__main__":
    RapTuiApp().run()
