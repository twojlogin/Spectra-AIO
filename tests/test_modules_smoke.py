import importlib
import pkgutil
import backend.modules as modules_pkg


def test_all_modules_importable():
    errors = []
    for m in pkgutil.iter_modules(modules_pkg.__path__):
        if m.name.startswith("_"):
            continue
        try:
            importlib.import_module(f"backend.modules.{m.name}")
        except Exception as e:
            errors.append(f"{m.name}: {e}")
    assert errors == [], "Import errors:\\n" + "\\n".join(errors)
