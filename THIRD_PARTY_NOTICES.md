# Third-party notices

FlatShot's Python runtime uses the following direct dependencies. They are not relicensed by FlatShot and remain subject to their own license terms.

| Component | Purpose | License | Project |
| --- | --- | --- | --- |
| Pillow | Image decoding, transformation, and encoding | HPND | https://python-pillow.org/ |
| NumPy | Numeric image operations | BSD-3-Clause | https://numpy.org/ |
| Pydantic | Data validation and settings models | MIT | https://docs.pydantic.dev/ |
| CPython 3.13 | Bundled Python interpreter and standard library | Python Software Foundation License 2.0 | https://www.python.org/ |
| PyInstaller 6.22.0 | Windows one-folder bootloader and freezing tool | GPL-2.0-or-later with the PyInstaller bootloader exception | https://pyinstaller.org/ |
| pywebview 6.2.1 | Native Windows webview host | BSD-3-Clause | https://pywebview.flowrl.com/ |
| pythonnet 3.1.0 | .NET interop used by pywebview on Windows | MIT | https://pythonnet.github.io/ |
| clr-loader 0.3.1 | .NET runtime loader used by pythonnet | MIT | https://github.com/pythonnet/clr-loader |
| Bottle 0.13.4 | HTTP support included by pywebview | MIT | https://bottlepy.org/ |
| proxy-tools 0.1.0 | Proxy helpers included by pywebview | MIT | https://github.com/ionelmc/python-proxy-tools |
| CFFI 2.1.1 / pycparser 3.0 | Native interface support used transitively | MIT-0 / BSD-3-Clause | https://cffi.readthedocs.io/ |

Frozen portable builds reproduce this notice and FlatShot's MIT license at the
archive root. They also collect the resolved CPython and package license texts
under `THIRD_PARTY_LICENSES/`; those upstream texts remain authoritative.
Maintainers should review the resolved dependency set before each public
release.

Unless a file states otherwise, repository-authored source code, documentation, and visual assets are provided under the repository's MIT License. No customer product images or third-party stock media should be committed.
