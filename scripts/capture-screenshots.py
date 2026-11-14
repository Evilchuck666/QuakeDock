"""Capture the real desktop with isolated settings, without installing a game.

Run from the repository root: QT_QPA_PLATFORM=offscreen python scripts/capture-screenshots.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QToolButton

from quake_gui.window import MainWindow


def main():
    output = Path(__file__).resolve().parents[1] / "site/assets/screenshots"
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    with tempfile.TemporaryDirectory(prefix="quakedock-capture-") as temporary:
        settings = QSettings(str(Path(temporary) / "settings.ini"), QSettings.Format.IniFormat)
        for edition, folder in (("singleplayer", "Campaign"), ("multiplayer", "Multiplayer")):
            settings.setValue(f"directory/{edition}", f"/Games/Quake/{folder}")
        window = MainWindow(settings)
        window.resize(1120, 960)
        window.show()
        for edition, name in (("singleplayer", "campaign"), ("multiplayer", "multiplayer")):
            window.select_edition(edition)
            for button in window.findChildren(QToolButton):
                if button.text() == "Player settings":
                    button.setChecked(edition == "multiplayer")
            app.processEvents()
            if not window.grab().save(str(output / f"{name}.png")):
                raise RuntimeError(f"Could not save {name} screenshot")
        window.close()


if __name__ == "__main__":
    main()
