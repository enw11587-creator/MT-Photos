from pathlib import Path
p = Path("app/src/main/java/com/emily/mtphotos/GalleryActivity.java")
s = p.read_text()
old = """        try {
            Map<Long, float[]> samples = store.exemplars();"""
new = """        try {
            updated = store.albums(snapshot);
            List<PeopleStore.Album> saved = updated;
            runOnUiThread(() -> {
                if (!isDestroyed() && photos.equals(snapshot)) {
                    albums = saved;
                    render(false);
                }
            });
            Map<Long, float[]> samples = store.exemplars();"""
assert s.count(old) == 1
s = s.replace(old, new)
old = '            outcome = "Face scanning stopped. Tap Scan photos for people to retry.";'
new = '''            try { updated = store.albums(snapshot); }
            catch (RuntimeException readError) {
                Log.e("MTPhotos", "Saved groups could not be read", readError);
            }
            outcome = "Scanning stopped. Saved groups are still available. Tap Scan photos for people to retry.";'''
assert s.count(old) == 1
s = s.replace(old, new)
p.write_text(s)
g = Path("app/build.gradle")
s = g.read_text().replace("versionCode 3", "versionCode 4").replace("versionName '1.2-beta'", "versionName '1.3-beta'")
g.write_text(s)
