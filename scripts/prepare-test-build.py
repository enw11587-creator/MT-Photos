#!/usr/bin/env python3
"""Give the beta a distinct Android identity so it installs alongside the original."""
from pathlib import Path
gradle = Path("app/build.gradle")
text = gradle.read_text(encoding="utf-8")
original = "applicationId 'com.emily.mtphotos'"
assert text.count(original) == 1, "Expected the original application ID exactly once"
gradle.write_text(text.replace(original, "applicationId 'com.emily.mtphotos.mergepreview'"), encoding="utf-8")
manifest = Path("app/src/main/AndroidManifest.xml")
text = manifest.read_text(encoding="utf-8")
original = 'android:label="MT Photos"'
assert text.count(original) == 1, "Expected original app label exactly once"
manifest.write_text(text.replace(original, 'android:label="MT Photos Test"'), encoding="utf-8")
print("Test APK has separate package and app label; original remains untouched")
