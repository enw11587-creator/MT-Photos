package com.emily.mtphotos;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteStatement;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Database-level people album merges for MT Photos.
 *
 * Compatible with the APK's existing schema:
 * person(id INTEGER PRIMARY KEY, name TEXT NOT NULL DEFAULT '')
 * face(uri TEXT, person INTEGER, vector BLOB, left REAL, top REAL, right REAL,
 *      bottom REAL, PRIMARY KEY(uri, person)).
 *
 * Call on a worker thread. Never delete the underlying photo or the photo
 * scan checkpoint from the photo table.
 */
public final class PeopleMerger {
    private PeopleMerger() {}

    /** Merge one person into another. Returns false for a no-op or missing person. */
    public static boolean merge(SQLiteDatabase db, long targetId, long sourceId) {
        if (targetId == sourceId) return false;
        db.beginTransaction();
        try {
            if (!exists(db, targetId) || !exists(db, sourceId)) return false;

            // Preserve any distinct face samples, ignoring duplicate
            // (uri, person) pairs that are already held by the target.
            db.execSQL(
                "INSERT OR IGNORE INTO face " +
                "(uri, person, vector, left, top, right, bottom) " +
                "SELECT uri, ?, vector, left, top, right, bottom " +
                "FROM face WHERE person = ?",
                new Object[] { targetId, sourceId });

            // Both person records can contain a name; prefer target's chosen
            // label, but retain source's label if target is currently unnamed.
            String targetName = nameOf(db, targetId);
            String sourceName = nameOf(db, sourceId);
            if (targetName.trim().isEmpty() && !sourceName.trim().isEmpty()) {
                db.execSQL("UPDATE person SET name = ? WHERE id = ?",
                           new Object[] { sourceName, targetId });
            }
            db.execSQL("DELETE FROM face WHERE person = ?", new Object[] { sourceId });
            db.execSQL("DELETE FROM person WHERE id = ?", new Object[] { sourceId });
            db.setTransactionSuccessful();
            return true;
        } finally {
            db.endTransaction();
        }
    }

    /**
     * Merge people whose user-assigned names match, ignoring case and extra
     * surrounding whitespace. Blank names never auto-merge.
     * Returns the number of deleted duplicate person records.
     */
    public static int mergeSameNames(SQLiteDatabase db) {
        List<Person> people = new ArrayList<>();
        try (Cursor c = db.rawQuery(
                "SELECT id, name FROM person ORDER BY id", null)) {
            while (c.moveToNext()) {
                people.add(new Person(c.getLong(0), c.getString(1)));
            }
        }
        Map<String, Long> targets = new LinkedHashMap<>();
        int merged = 0;
        for (Person person : people) {
            String normalized = person.name.trim().toLowerCase(Locale.ROOT);
            if (normalized.isEmpty()) continue;
            Long target = targets.get(normalized);
            if (target == null) {
                targets.put(normalized, person.id);
            } else if (merge(db, target, person.id)) {
                merged++;
            }
        }
        return merged;
    }

    private static boolean exists(SQLiteDatabase db, long id) {
        try (Cursor c = db.rawQuery(
                "SELECT 1 FROM person WHERE id = ?",
                new String[]{String.valueOf(id)})) {
            return c.moveToFirst();
        }
    }

    private static String nameOf(SQLiteDatabase db, long id) {
        try (Cursor c = db.rawQuery(
                "SELECT name FROM person WHERE id = ?",
                new String[]{String.valueOf(id)})) {
            return c.moveToFirst() && !c.isNull(0) ? c.getString(0) : "";
        }
    }

    private static final class Person {
        final long id;
        final String name;
        Person(long id, String name) {
            this.id = id;
            this.name = name == null ? "" : name;
        }
    }
}
