import random
import os
import httpx
from datetime import datetime
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, Select, Label, TextArea
from textual.containers import Vertical, VerticalScroll, Horizontal
from textual import on, work

# Setup Cache Directory
CACHE_DIR = Path.home() / ".cache" / "raptui"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class RapTuiApp(App):
    TITLE = "Rap TUI"

    BINDINGS = [
        ("escape", "exit_app", "Quit & Save"),
        ("ctrl+s", "toggle_settings", "Settings"),
        ("ctrl+n", "toggle_notebook", "Notebook"),
        ("ctrl+p", "save_lyrics", "Save Now"),
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
                yield Static(
                    "Enter a word to find a real rhyme via API!", id="display_box"
                )
                yield Input(placeholder="Spit your bars...", id="main_input")

            with Vertical(id="notebook_panel"):
                yield Label("📓 NOTEBOOK (API MODE)", id="notebook_title")
                yield TextArea(id="lyrics_area")

        with VerticalScroll(id="settings_pane"):
            yield Label("[b]SETTINGS[/]", id="settings_title")
            yield Label("Theme:")
            yield Select(
                [("Default", "default"), ("Dark", "dark")],
                value="default",
                id="theme_select",
            )
        yield Footer()

    @work(exclusive=True)
    async def fetch_rhyme(self, word: str):
        """Calls the Datamuse API asynchronously."""
        display = self.query_one("#display_box")
        display.update(f"Searching for rhymes for [b cyan]{word}[/]...")

        try:
            async with httpx.AsyncClient() as client:
                # 'rel_rhy' finds perfect rhymes
                response = await client.get(
                    f"https://api.datamuse.com/words?rel_rhy={word}", timeout=5.0
                )
                data = response.json()

            if data:
                # Pick a random rhyme from the top 10 results
                suggestion = random.choice(data[:10])["word"]
                display.update(
                    f"Rhyme with: [b cyan]{word}[/]\nSuggestion: [b yellow]{suggestion}[/]"
                )
            else:
                display.update(
                    f"No perfect rhyme for [b red]{word}[/].\nTry a different word!"
                )
        except Exception as e:
            display.update(f"[red]API Error: Check connection[/]")

    @on(Input.Submitted, "#main_input")
    def process_bar(self, event: Input.Submitted):
        line = event.value.strip()
        if not line:
            return

        words = line.split()
        if words:
            last_word = words[-1].strip(".,!?;:")
            # Trigger the background worker
            self.fetch_rhyme(last_word)

        event.input.value = ""

    # --- Saving & UI Logic ---
    def action_save_lyrics(self) -> None:
        lyrics = self.query_one("#lyrics_area", TextArea).text
        if not lyrics.strip():
            return

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = CACHE_DIR / f"raptui-note-{timestamp}.txt"
        filename.write_text(lyrics)
        self.notify(f"Saved to {filename.name}")

    def action_exit_app(self) -> None:
        self.action_save_lyrics()
        self.exit()

    def action_toggle_settings(self) -> None:
        pane = self.query_one("#settings_pane")
        pane.display = not pane.display

    def action_toggle_notebook(self) -> None:
        note = self.query_one("#notebook_panel")
        note.display = not note.display
        if note.display:
            self.query_one("#lyrics_area").focus()


if __name__ == "__main__":
    # You'll need to pip install httpx
    RapTuiApp().run()
