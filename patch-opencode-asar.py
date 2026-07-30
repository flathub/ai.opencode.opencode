#!/usr/bin/env python3
"""
Disable the OpenCode Electron app's self-updater inside a Flatpak, in place.

Sets UPDATER_ENABLED = false in out/main/index.js inside app.asar. This is a
same-length text replacement, so the asar binary is patched directly without
extract/repack (which would drop the app.asar.unpacked native-module
metadata). The asar header, all offsets, and the unpacked entries are
preserved byte-for-byte.

Flatpak provides updates via the OS updater (GNOME Software / KDE Discover /
flatpak update); the electron-updater self-updater can't install into the
read-only /app anyway, so it must be disabled. Upstream issue:
https://github.com/anomalyco/opencode/issues/39670

Usage: patch-opencode-asar.py <path/to/app.asar>
"""
import os
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path/to/app.asar>", file=sys.stderr)
        sys.exit(2)

    asar_path = sys.argv[1]
    if not os.environ.get("FLATPAK_ID"):
        print("FLATPAK_ID is not set; expected to be run inside flatpak-builder", file=sys.stderr)
        sys.exit(1)

    with open(asar_path, "rb") as f:
        data = f.read()

    # out/main/index.js: `const UPDATER_ENABLED = app.isPackaged && CHANNEL !== "dev";`
    # Replace the RHS with `false` plus a comment, padded to the same byte
    # length so the asar layout (offsets, unpacked entries) is unchanged.
    old = b'app.isPackaged && CHANNEL !== "dev"'
    new = b'false/*packed&&CHANNEL!=="dev"*/'.ljust(len(old), b" ")
    if len(old) != len(new):
        raise SystemExit(f"length mismatch: {len(old)} vs {len(new)}")
    count = data.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly 1 occurrence of UPDATER_ENABLED, found {count}")
    data = data.replace(old, new, 1)

    with open(asar_path, "wb") as f:
        f.write(data)

    print(f"patched {asar_path}: UPDATER_ENABLED = false")


if __name__ == "__main__":
    main()