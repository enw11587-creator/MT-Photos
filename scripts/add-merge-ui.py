#!/usr/bin/env python3
"""Add a clear, manual merge flow to MT Photos without changing stored data."""
from pathlib import Path

p = Path("app/src/main/java/com/emily/mtphotos/GalleryActivity.java")
s = p.read_text(encoding="utf-8")

old = 'mergeButton = button("Merge with another person", this::chooseMerge);'
new = 'mergeButton = button("Merge People", this::chooseMerge);'
assert s.count(old) == 1, "Could not identify merge button"
s = s.replace(old, new)

old = '''mergeButton.setVisibility(album == null ? View.GONE : View.VISIBLE);
        mergeButton.setEnabled(!scanning && albums.size() > 1);'''
new = '''mergeButton.setVisibility(people && albums.size() > 1 ? View.VISIBLE : View.GONE);
        mergeButton.setEnabled(!scanning && albums.size() > 1);
        mergeButton.setText(album == null ? "Merge People" : "Merge with another person");'''
assert s.count(old) == 1, "Could not find merge visibility"
s = s.replace(old, new)

begin = s.index("    private void chooseMerge() {")
end = s.index("    private void changePerson(", begin)
replacement = '''    private void chooseMerge() {
        if (scanning || albums.size() < 2) {
            toast("Scan at least two people before merging.");
            return;
        }
        PeopleStore.Album current = currentAlbum();
        if (current == null) {
            pickPerson(null, this::pickMergeTarget);
        } else {
            pickMergeTarget(current);
        }
    }

    private interface AlbumChoice {
        void choose(PeopleStore.Album album);
    }

    private void pickPerson(Long exclude, AlbumChoice action) {
        List<PeopleStore.Album> choices = new ArrayList<>();
        for (PeopleStore.Album candidate : albums) {
            if (exclude == null || candidate.id() != exclude) choices.add(candidate);
        }
        if (choices.isEmpty()) {
            toast("No other people to merge.");
            return;
        }
        GridView chooser = new GridView(this);
        chooser.setNumColumns(2);
        chooser.setVerticalSpacing(dp(8));
        chooser.setHorizontalSpacing(dp(8));
        Tiles adapter = new Tiles();
        List<Tile> items = new ArrayList<>();
        for (PeopleStore.Album candidate : choices) {
            items.add(new Tile(candidate.cover().photo(), candidate));
        }
        adapter.items = items;
        chooser.setAdapter(adapter);
        AlertDialog picker = new AlertDialog.Builder(this)
                .setTitle(exclude == null ? "Choose the first person" : "Choose the other person")
                .setView(chooser)
                .setNegativeButton("Cancel", null)
                .create();
        chooser.setOnItemClickListener((parent, view, position, id) -> {
            PeopleStore.Album chosen = choices.get(position);
            picker.dismiss();
            action.choose(chosen);
        });
        picker.show();
    }

    private void pickMergeTarget(PeopleStore.Album source) {
        pickPerson(source.id(), target -> {
            String name = !target.name().isEmpty() ? target.name() : source.name();
            String display = name.isEmpty() ? "Unnamed person" : name;
            new AlertDialog.Builder(this)
                    .setTitle("Merge these two people?")
                    .setMessage("Combine both photo groups under \\u201c" + display
                            + "\\u201d? This cannot be undone here. Your original photos stay on your phone.")
                    .setNegativeButton("Cancel", null)
                    .setPositiveButton("Merge", (dialog, which) ->
                            changePerson(source.id(), target.id(), null))
                    .show();
        });
    }

'''
s = s[:begin] + replacement + s[end:]
p.write_text(s, encoding="utf-8")
gradle = Path("app/build.gradle")
g = gradle.read_text(encoding="utf-8")
assert "versionCode 2" in g
gradle.write_text(g.replace("versionCode 2", "versionCode 3").replace("versionName '1.1-beta'", "versionName '1.2-beta'"), encoding="utf-8")
print("MT Photos: main People merge action added; existing database unchanged")
