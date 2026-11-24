# Build on the target OS: python -m PyInstaller --noconfirm scripts/QuakeDock.spec
from pathlib import Path
import ast
import importlib
import sys
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH).resolve().parent
# PyInstaller can report missing imports as warnings and still produce an EXE.
# Check the build interpreter before touching an existing distribution.
required_modules = ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "tqdm", "certifi"]
if sys.platform == "win32":
    required_modules.append("winpty")
dependency_errors = []
for module in required_modules:
    try:
        importlib.import_module(module)
    except (ImportError, OSError) as error:
        dependency_errors.append(f"  {module}: {error}")
if dependency_errors:
    raise SystemExit(
        "Cannot build QuakeDock: missing or unusable GUI dependencies.\n"
        + "\n".join(dependency_errors)
        + f"\nBuild interpreter: {sys.executable}\n"
        + "Install scripts/requirements-build.txt with this same interpreter before building.\n"
        + "Use Python 3.13 to match the tested CI build environment.\n"
        + "See the Windows build commands in TECHNICAL_GUIDE.md."
    )
console_datas, console_binaries, console_imports = (
    collect_all("winpty") if sys.platform == "win32" else ([], [], [])
)
# The engine launchers ship as files and are loaded by path at runtime
# (quakedock.gui.library.load_launcher), so PyInstaller cannot see their imports.
launcher_imports = set()
for launcher in (root / "assets" / "scripts").glob("*/launcher.py"):
    for node in ast.walk(ast.parse(launcher.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            launcher_imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            launcher_imports.add(node.module)
analysis = Analysis(
    [str(root / "run.py")],
    pathex=[str(root / "src")],
    datas=[(str(root / "assets" / "cfg"), "assets/cfg"),
           (str(root / "assets" / "icons"), "assets/icons"),
           (str(root / "assets" / "links"), "assets/links"),
           (str(root / "assets" / "scripts"), "assets/scripts"),
           (str(root / "README.md"), "."),
           (str(root / "TECHNICAL_GUIDE.md"), ".")] + console_datas,
    binaries=console_binaries,
    hiddenimports=["certifi"] + sorted(launcher_imports) + console_imports,
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2"],
    noarchive=False,
)
if sys.platform == "linux":
    # The X11 companion uses private xkbcommon internals. Loading the host's
    # companion with a bundled core can crash in xkb_keymap_unref on Artix.
    # Keep both libraries together in the host desktop stack.
    analysis.binaries = [
        entry for entry in analysis.binaries
        if not Path(entry[0]).name.startswith(("libxkbcommon.so", "libxkbcommon-x11.so"))
    ]
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, analysis.binaries, analysis.datas, [],
    name="QuakeDock", debug=False, strip=False, upx=False,
    console=False, icon=str(root / "assets" / "icons" / "vkQuake.ico"),
)
# One executable on every platform. A macOS .app is a directory bundle,
# so do not wrap this Mach-O executable in BUNDLE.
