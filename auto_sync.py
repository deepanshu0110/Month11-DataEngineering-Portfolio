"""
auto_sync_month11.py
=====================================================================
Watchdog-based auto-sync for Month11-DataEngineering-Portfolio.

Behavior (matches your established convention from prior months):
  - Watches the repo folder for any file change (create/modify/delete/move)
  - Debounces for 3 seconds — if you save 5 files in a row, it waits
    until things go quiet for 3s before doing anything, so you don't
    get a commit-per-keystroke
  - Auto-rebuilds README.md's "Day Index" table from whatever .ipynb
    files actually exist in the folder (never hand-maintained, so it
    can't go stale)
  - git add -A -> commit -> push to origin/master (NOT main)

Run this once, in a terminal, from inside your repo folder:
    python auto_sync_month11.py

Leave it running in that terminal while you work in VS Code / Jupyter.
Stop it with Ctrl+C.

One-time setup before first run:
    pip install watchdog
    cd path/to/Month11-DataEngineering-Portfolio
    git init                     # only if repo doesn't exist locally yet
    git checkout -b master       # GitHub defaults new repos to 'main'
    git remote add origin https://github.com/deepanshu0110/Month11-DataEngineering-Portfolio.git
    git config credential.helper store   # so you're not typing a PAT every push
=====================================================================
"""

import subprocess
import sys
import re
import glob
import os
import time
from datetime import datetime
from threading import Timer

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Missing dependency. Run: pip install watchdog")
    sys.exit(1)

# ---------------------------------------------------------------
# CONFIG — adjust REPO_PATH to wherever this folder actually lives
# ---------------------------------------------------------------
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
DEBOUNCE_SECONDS = 3
BRANCH = "master"                      # this project uses master, not main
IGNORE_PATTERNS = (".git", "__pycache__", ".ipynb_checkpoints", ".DS_Store")


def should_ignore(path: str) -> bool:
    """Skip noise — git internals, notebook checkpoints, OS junk files."""
    return any(pattern in path for pattern in IGNORE_PATTERNS)


def rebuild_readme_day_index():
    """
    Auto-rebuild the 'Day Index' table inside README.md.

    Scans for DayNNN_*.ipynb files, sorts by day number, and writes a
    markdown table between two marker comments in README.md:

        <!-- DAY_INDEX_START -->
        ...table goes here, regenerated every sync...
        <!-- DAY_INDEX_END -->

    If README.md doesn't have these markers yet, they're added once.
    This means the day list can never silently go stale — it's always
    derived from what's actually on disk, not typed by hand.
    """
    readme_path = os.path.join(REPO_PATH, "README.md")

    notebooks = glob.glob(os.path.join(REPO_PATH, "notebooks", "Day*.ipynb"))
    notebooks += glob.glob(os.path.join(REPO_PATH, "Day*.ipynb"))  # also check root

    day_entries = []
    for path in notebooks:
        fname = os.path.basename(path)
        match = re.match(r"Day(\d+)_(.+)\.ipynb", fname)
        if match:
            day_num = int(match.group(1))
            topic = match.group(2).replace("_", " ")
            day_entries.append((day_num, topic, fname))

    day_entries.sort(key=lambda x: x[0])

    if not day_entries:
        print("  [readme] No DayNNN_*.ipynb files found — skipping index rebuild.")
        return

    table_lines = ["| Day | Topic | File |", "|---|---|---|"]
    for day_num, topic, fname in day_entries:
        table_lines.append(f"| {day_num} | {topic} | `{fname}` |")
    table_block = "\n".join(table_lines)

    start_marker = "<!-- DAY_INDEX_START -->"
    end_marker = "<!-- DAY_INDEX_END -->"

    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "# Month 11 — Data Engineering Portfolio\n\n"

    if start_marker in content and end_marker in content:
        pattern = re.compile(
            re.escape(start_marker) + r".*?" + re.escape(end_marker),
            re.DOTALL
        )
        new_block = f"{start_marker}\n{table_block}\n{end_marker}"
        content = pattern.sub(new_block, content)
    else:
        content += f"\n## Day Index (auto-generated — do not edit by hand)\n\n{start_marker}\n{table_block}\n{end_marker}\n"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  [readme] Rebuilt day index — {len(day_entries)} notebooks listed.")


def git_sync():
    """Stage everything, commit with a timestamp, push to master."""
    os.chdir(REPO_PATH)

    rebuild_readme_day_index()

    subprocess.run(["git", "add", "-A"], check=False)

    diff_check = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        capture_output=True
    )
    if diff_check.returncode == 0:
        print("  [sync] No changes to commit.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"chore: auto-sync {timestamp}"

    commit_result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        capture_output=True, text=True
    )
    print(f"  [git] {commit_result.stdout.strip() or commit_result.stderr.strip()}")

    push_result = subprocess.run(
        ["git", "push", "origin", BRANCH],
        capture_output=True, text=True
    )
    if push_result.returncode == 0:
        print(f"  [git] Pushed to origin/{BRANCH} ✓")
    else:
        print(f"  [git] Push failed — check auth/remote:\n{push_result.stderr.strip()}")


class DebouncedHandler(FileSystemEventHandler):
    """
    Collects filesystem events and only fires git_sync() once,
    after DEBOUNCE_SECONDS of silence — prevents a commit storm
    when saving multiple files or when a notebook autosave fires
    several times in a row.
    """
    def __init__(self):
        self._timer = None

    def _trigger(self):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Change detected — syncing...")
        git_sync()

    def _debounced_trigger(self):
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(DEBOUNCE_SECONDS, self._trigger)
        self._timer.daemon = True
        self._timer.start()

    def on_any_event(self, event):
        if should_ignore(event.src_path):
            return
        self._debounced_trigger()


def main():
    print(f"Watching: {REPO_PATH}")
    print(f"Debounce: {DEBOUNCE_SECONDS}s | Branch: {BRANCH}")
    print("Press Ctrl+C to stop.\n")

    event_handler = DebouncedHandler()
    observer = Observer()
    observer.schedule(event_handler, REPO_PATH, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopped.")
    observer.join()


if __name__ == "__main__":
    main()
