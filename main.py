from datetime import datetime
import os
from pathlib import Path
import random
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input, Label, Select, Static, TextArea

import pronouncing

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
        ("ctrl+n", "toggle_notebook", "Notebook (Toggle)"),
        ("ctrl+r", "toggle_rhymes", "Rhymes (Toggle)"),
        ("ctrl+o", "save_lyrics", "Save Now"),
    ]

    CSS = """
    Screen { layers: base overlay; }
    #main_layout { width: 100%; height: 100%; }
    #game_container { align: center middle; width: 1fr; height: 100%; }
    
    #display_box {
        width: 60; height: 8;
        border: heavy $accent;
        content-align: center middle;
        margin-bottom: 1;
        background: $surface;
    }

    #main_input { width: 60; border: tall $primary; }

    #notebook_panel, #rhymes_panel {
        width: 35; height: 100%;
        dock: right;
        border-left: double $secondary;
        background: $panel;
        display: none; /* Hidden by default */
    }

    #rhymes_panel { border-left: double $accent; }

    .pane_title {
        padding: 1; background: $secondary;
        color: white; text-align: center; width: 100%;
        margin-bottom: 1;
    }

    #rhyme_list_view { padding: 1; color: $text; }

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
                yield Static("Spit a line to generate rhymes!", id="display_box")
                yield Input(placeholder="Type your bars here...", id="main_input")

            # Rhyme Results Pane (Hidden by default)
            with Vertical(id="rhymes_panel"):
                yield Label("🔥 ALL RHYMES", classes="pane_title")
                with VerticalScroll():
                    yield Static("", id="rhyme_list_view")

            # Notebook Pane (Hidden by default)
            with Vertical(id="notebook_panel"):
                yield Label("📓 NOTEBOOK", classes="pane_title")
                yield TextArea(id="lyrics_area")

        with VerticalScroll(id="settings_pane"):
            yield Label("[b]SETTINGS[/]", id="settings_title")
            yield Label("Fallback Length:")
            yield Input("2", id="rhyme_len_input")
            yield Select(
                [("Default", "default"), ("Dark", "dark")],
                value="default",
                id="theme_select",
            )
        yield Footer()

    def action_toggle_rhymes(self) -> None:
        pane = self.query_one("#rhymes_panel")
        pane.display = not pane.display
        if pane.display:
            self.notify("Rhyme Pane Visible (Ctrl+R to hide)")

    def action_toggle_notebook(self) -> None:
        pane = self.query_one("#notebook_panel")
        pane.display = not pane.display
        if pane.display:
            self.query_one("#lyrics_area").focus()

    def action_exit_app(self) -> None:
        self.exit()

    @on(Input.Submitted, "#main_input")
    def process_bar(self, event: Input.Submitted):
        line = event.value.strip()
        if not line:
            return

        words = line.split()
        if words:
            last_word = words[-1].strip(".,!?;:").lower()
            rhymes = pronouncing.rhymes(last_word)

            if rhymes:
                rhymes.sort()
                # Pick 3 random examples for the main display
                examples = random.sample(rhymes, min(3, len(rhymes)))
                ex_str = ", ".join([f"[b yellow]{ex}[/]" for ex in examples])

                # Update sidebar list
                full_list = "\n".join([f"• {r}" for r in rhymes])
                self.query_one("#rhyme_list_view").update(full_list)

                # Update main display
                self.query_one("#display_box").update(
                    f"Word: [b cyan]{last_word}[/]\n"
                    f"Found: {len(rhymes)} total rhymes\n\n"
                    f"Examples: {ex_str}"
                )
            else:
                # Fallback logic
                try:
                    r_len = int(self.query_one("#rhyme_len_input").value)
                except:
                    r_len = 2
                suffix = last_word[-r_len:] if len(last_word) >= r_len else last_word
                matches = sorted(
                    list(
                        set(
                            [
                                w
                                for w in DICTIONARY
                                if w.endswith(suffix) and w != last_word
                            ]
                        )
                    )
                )

                if matches:
                    examples = random.sample(matches, min(3, len(matches)))
                    ex_str = ", ".join([f"[b yellow]{ex}[/]" for ex in examples])
                    self.query_one("#rhyme_list_view").update(
                        "\n".join([f"• {m}" for m in matches])
                    )
                    self.query_one("#display_box").update(
                        f"Word: [b cyan]{last_word}[/] (Fallback)\n"
                        f"Matches: {len(matches)}\n\n"
                        f"Examples: {ex_str}"
                    )
                else:
                    self.query_one("#display_box").update(
                        f"No matches for [b red]{last_word}[/]"
                    )

        event.input.value = ""


if __name__ == "__main__":
    RapTuiApp().run()
