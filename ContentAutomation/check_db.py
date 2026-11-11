import os
import shutil
import sqlite3
import tempfile

db_candidates = [
    r"E:\Omniroute\VoiceStudio\omnivoice.db",
    r"E:\Omniroute\openstudio\VoiceStudio\omnivoice.db",
    r"E:\Omniroute\openstudio\VoiceStudio\tests\fixtures\omnivoice_data\omnivoice.db",
]

db_path = next((p for p in db_candidates if os.path.exists(p)), None)
print("Database found:", db_path)

if db_path:
    # Use temporary copy to avoid database locks from active VoiceStudio process
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        shutil.copy2(db_path, tmp_path)
        conn = sqlite3.connect(tmp_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print("Tables in omnivoice.db:", tables)

        target_table = "voice_profiles" if "voice_profiles" in tables else ("profiles" if "profiles" in tables else None)
        if target_table:
            cur.execute(f"PRAGMA table_info({target_table})")
            cols = [r[1] for r in cur.fetchall()]
            print(f"\nColumns in '{target_table}':", cols)

            cols_to_select = [c for c in ["id", "name", "kind", "language", "ref_audio_path"] if c in cols]
            cur.execute(f"SELECT {', '.join(cols_to_select)} FROM {target_table}")
            rows = cur.fetchall()
            print(f"\nVoice Profiles found ({len(rows)}):")
            for r in rows:
                print("  " + " | ".join(f"{c}: {val}" for c, val in zip(cols_to_select, r)))
        conn.close()
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
