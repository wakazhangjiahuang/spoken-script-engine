#!/usr/bin/env python3
"""Use the runtime's existing CJK font; no downloads or package installs."""
import json,tempfile
from pathlib import Path
from xml.sax.saxutils import escape
import pymupdf
root=Path(tempfile.mkdtemp(prefix='spoken-engine-font-'));fonts=root/'font-assets';fonts.mkdir();cache=root/'font-cache';cache.mkdir()
f=pymupdf.Font(fontname='cjk');(fonts/'DroidSansFallback.ttf').write_bytes(f.buffer)
config='''<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
 <include ignore_missing="yes">/etc/fonts/fonts.conf</include>
 <dir>FONT_DIR</dir>
 <cachedir>CACHE_DIR</cachedir>
 <alias><family>Carlito</family><prefer><family>Droid Sans Fallback</family><family>DejaVu Sans</family></prefer></alias>
</fontconfig>
'''.replace('FONT_DIR',escape(str(fonts))).replace('CACHE_DIR',escape(str(cache)))
p=root/'fonts.conf';p.write_text(config)
print(json.dumps({'directory':str(root),'fontconfig_file':str(p),'font_source':'existing PyMuPDF Font(cjk).buffer','font_name':f.name}))
