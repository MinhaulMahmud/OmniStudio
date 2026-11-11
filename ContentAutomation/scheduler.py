"""
Content Scheduler
==================
Schedules automated content generation runs.
Supports:
  - Daily/weekly content schedules
  - Topic rotation
  - Multi-platform publishing queue

Can be run as a standalone daemon or integrated with Windows Task Scheduler.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SCHEDULE_FILE = Path(__file__).parent / "schedule.json"


class ContentSchedule:
    """
    Manages a content production schedule.

    Example schedule.json:
    {
        "enabled": true,
        "runs": [
            {
                "id": "daily_youtube",
                "cron": "0 9 * * *",   // 9 AM daily
                "topics": ["AI tools", "Python tips"],
                "platform": "youtube",
                "formats": ["youtube", "shorts"],
                "voice_name": "My Voice",
                "last_run": null,
                "next_run": "2026-11-10T09:00:00"
            }
        ]
    }
    """

    def __init__(self, schedule_path: Path = SCHEDULE_FILE):
        self.path = Path(schedule_path)
        self.schedule = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                with open(self.path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as exc:
                logger.error("Failed to load schedule: %s", exc)
        return {"enabled": True, "runs": []}

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.schedule, f, indent=2)

    def add_run(
        self,
        name: str,
        topics: list[str],
        platform: str = "youtube",
        formats: list[str] = None,
        voice_name: str = "",
        interval_hours: float = 24.0,
    ) -> dict:
        """Add a scheduled content run."""
        run = {
            "id": name.lower().replace(" ", "_"),
            "name": name,
            "topics": topics,
            "platform": platform,
            "formats": formats or ["youtube", "shorts"],
            "voice_name": voice_name,
            "interval_hours": interval_hours,
            "last_run": None,
            "next_run": datetime.now().isoformat(),
            "enabled": True,
        }
        self.schedule["runs"].append(run)
        self._save()
        logger.info("Scheduled run added: %s (every %.0fh)", name, interval_hours)
        return run

    def get_due_runs(self) -> list[dict]:
        """Return all runs that are due to execute now."""
        now = datetime.now()
        due = []
        for run in self.schedule.get("runs", []):
            if not run.get("enabled", True):
                continue
            next_run_str = run.get("next_run")
            if not next_run_str:
                due.append(run)
                continue
            try:
                next_run = datetime.fromisoformat(next_run_str)
                if now >= next_run:
                    due.append(run)
            except ValueError:
                due.append(run)
        return due

    def mark_completed(self, run_id: str):
        """Update last_run and schedule next_run for a completed run."""
        now = datetime.now()
        for run in self.schedule.get("runs", []):
            if run["id"] == run_id:
                run["last_run"] = now.isoformat()
                interval = run.get("interval_hours", 24.0)
                run["next_run"] = (now + timedelta(hours=interval)).isoformat()
                break
        self._save()

    def run_daemon(self, check_interval_seconds: int = 300):
        """
        Run as a daemon, checking and executing due runs every N seconds.
        
        Usage:
            python scheduler.py daemon
        """
        from pipeline import ContentAutomationPipeline
        pipeline = ContentAutomationPipeline()

        logger.info("🕐 Content scheduler daemon started (checking every %ds)", check_interval_seconds)
        while True:
            due_runs = self.get_due_runs()
            if due_runs:
                for run in due_runs:
                    logger.info("⏰ Executing scheduled run: %s", run["id"])
                    try:
                        pipeline.run(
                            topics=run.get("topics", []),
                            platform=run.get("platform", "youtube"),
                            formats=run.get("formats", ["youtube"]),
                            voice_name=run.get("voice_name") or None,
                        )
                        self.mark_completed(run["id"])
                    except Exception as exc:
                        logger.error("Scheduled run '%s' failed: %s", run["id"], exc)
            else:
                next_runs = [r.get("next_run", "?") for r in self.schedule.get("runs", [])]
                logger.debug("No runs due. Next: %s", min(next_runs) if next_runs else "none")

            time.sleep(check_interval_seconds)


def setup_windows_task_scheduler(
    name: str = "ContentAutomation",
    hour: int = 9,
    minute: int = 0,
    topic: str = "AI tools 2026",
) -> bool:
    """
    Create a Windows Task Scheduler task to run the pipeline daily.

    Args:
        name: Task name in Task Scheduler.
        hour: Hour to run (24h format).
        minute: Minute to run.
        topic: Topic to generate.

    Returns:
        True if task was created successfully.
    """
    import subprocess

    python_exe = sys.executable
    script = str(Path(__file__).parent / "main.py")
    cmd_args = f'run --topic "{topic}"'
    
    task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{datetime.now().strftime('%Y-%m-%d')}T{hour:02d}:{minute:02d}:00</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>{python_exe}</Command>
      <Arguments>{script} {cmd_args}</Arguments>
      <WorkingDirectory>{Path(script).parent}</WorkingDirectory>
    </Exec>
  </Actions>
  <Settings>
    <ExecutionTimeLimit>PT4H</ExecutionTimeLimit>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
  </Settings>
</Task>"""

    xml_path = Path(script).parent / "task.xml"
    with open(xml_path, "w", encoding="utf-16") as f:
        f.write(task_xml)

    result = subprocess.run(
        ["schtasks", "/Create", "/XML", str(xml_path), "/TN", name, "/F"],
        capture_output=True, text=True,
    )
    xml_path.unlink(missing_ok=True)
    
    if result.returncode == 0:
        logger.info("✅ Windows task '%s' created (runs daily at %02d:%02d)", name, hour, minute)
        return True
    else:
        logger.error("Failed to create task: %s", result.stderr)
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Content Automation Scheduler")
    subparsers = parser.add_subparsers(dest="cmd")

    # daemon
    daemon_p = subparsers.add_parser("daemon", help="Run scheduler daemon")
    daemon_p.add_argument("--interval", type=int, default=300, help="Check interval (seconds)")

    # add
    add_p = subparsers.add_parser("add", help="Add a scheduled run")
    add_p.add_argument("--name", required=True)
    add_p.add_argument("--topics", required=True, help="Comma-separated topics")
    add_p.add_argument("--platform", default="youtube")
    add_p.add_argument("--interval-hours", type=float, default=24.0)
    add_p.add_argument("--voice-name")

    # windows-task
    wt_p = subparsers.add_parser("windows-task", help="Create Windows Task Scheduler task")
    wt_p.add_argument("--name", default="ContentAutomation")
    wt_p.add_argument("--hour", type=int, default=9)
    wt_p.add_argument("--topic", default="AI tools 2026")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s │ %(levelname)-8s │ %(message)s",
        datefmt="%H:%M:%S",
    )

    schedule = ContentSchedule()

    if args.cmd == "daemon":
        schedule.run_daemon(check_interval_seconds=args.interval)
    elif args.cmd == "add":
        topics = [t.strip() for t in args.topics.split(",")]
        schedule.add_run(
            name=args.name,
            topics=topics,
            platform=args.platform,
            interval_hours=args.interval_hours,
            voice_name=args.voice_name or "",
        )
        print(f"✅ Scheduled run '{args.name}' added.")
    elif args.cmd == "windows-task":
        setup_windows_task_scheduler(name=args.name, hour=args.hour, topic=args.topic)
    else:
        parser.print_help()
