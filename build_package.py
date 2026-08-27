# -*- coding: utf-8 -*-
"""Build the job-search plugin into a handoff zip.

Run from anywhere:  python build_package.py

Why this exists rather than a one-line Compress-Archive: Windows PowerShell writes
backslash separators into zip entry names, which is out of spec and fails to extract
correctly on macOS and Linux. Most recipients are not on Windows.
"""
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "bishop")
ROOT = "bishop"          # top-level folder inside the zip
OUT = os.path.join(HERE, "bishop.zip")

SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache"}
SKIP_EXTS = {".pyc", ".pyo"}


def build():
    if not os.path.isdir(PLUGIN):
        sys.exit("no plugin directory at %s" % PLUGIN)

    manifest = os.path.join(PLUGIN, ".claude-plugin", "plugin.json")
    if not os.path.isfile(manifest):
        sys.exit("missing manifest: %s" % manifest)

    if os.path.exists(OUT):
        os.remove(OUT)

    written = []
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(PLUGIN):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for fn in sorted(filenames):
                if os.path.splitext(fn)[1] in SKIP_EXTS:
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, PLUGIN).replace(os.sep, "/")
                z.write(full, ROOT + "/" + rel)
                written.append(rel)

    # The LICENSE lives at the repo root so GitHub picks it up, and a copy sits
    # inside the plugin dir because a marketplace install copies only that dir.
    # The walk above already bundled the inner copy, so this only checks that
    # both exist and that they agree. A licence grant that ships in one place
    # and not the other is the failure worth catching here.
    root_lic = os.path.join(HERE, "LICENSE")
    plugin_lic = os.path.join(PLUGIN, "LICENSE")
    if not os.path.isfile(root_lic):
        sys.exit("no LICENSE at repo root; the package must ship one")
    if not os.path.isfile(plugin_lic):
        sys.exit("no LICENSE in %s; marketplace installs copy only the plugin dir" % PLUGIN)
    if open(root_lic, "rb").read() != open(plugin_lic, "rb").read():
        sys.exit("the two LICENSE copies disagree; make them identical")

    with zipfile.ZipFile(OUT) as z:
        assert not [n for n in z.namelist() if "\\" in n], "backslash entry names"
        assert z.testzip() is None, "zip failed integrity check"

    print("built %s (%.1f KB, %d files)" % (os.path.basename(OUT), os.path.getsize(OUT) / 1024.0, len(written)))
    for rel in written:
        print("  " + rel)


if __name__ == "__main__":
    build()

