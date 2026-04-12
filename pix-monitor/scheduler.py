"""
PIX Monitor — Automated Monitoring Scheduler
Per-field configurable intervals (7/14/30 days).
Uses threading.Timer — no external dependencies.
Persists schedule in SQLite via db.py.
"""

import threading
import time
from datetime import datetime, timezone, timedelta

_scheduler_thread = None
_scheduler_running = False
_CHECK_INTERVAL = 60  # Check for due jobs every 60 seconds


def start_scheduler(compute_fn, save_fn, alert_fn):
    """Start the background scheduler loop.
    Args:
        compute_fn: callable(field) -> monitoring result dict
        save_fn: callable(field_id, result) -> saves result + updates field
        alert_fn: callable(alert) -> saves alert to DB
    """
    global _scheduler_thread, _scheduler_running
    if _scheduler_running:
        print('[Scheduler] Already running')
        return

    _scheduler_running = True

    def _loop():
        print('[Scheduler] Started — checking every 60s for due jobs')
        while _scheduler_running:
            try:
                _check_due_jobs(compute_fn, save_fn, alert_fn)
            except Exception as e:
                print(f'[Scheduler] Error: {e}')
            time.sleep(_CHECK_INTERVAL)
        print('[Scheduler] Stopped')

    _scheduler_thread = threading.Thread(target=_loop, daemon=True, name='pix-scheduler')
    _scheduler_thread.start()


def stop_scheduler():
    global _scheduler_running
    _scheduler_running = False
    print('[Scheduler] Stop requested')


def _check_due_jobs(compute_fn, save_fn, alert_fn):
    """Check SQLite for jobs whose next_run <= now and execute them."""
    from db import get_scheduler_jobs, save_scheduler_job, get_field

    now = datetime.now(timezone.utc)
    now_str = now.isoformat()

    jobs = get_scheduler_jobs(enabled_only=True)
    for job in jobs:
        next_run = job.get('next_run')
        if not next_run:
            # First run — schedule it
            job['next_run'] = now_str
            save_scheduler_job(job)
            continue

        try:
            next_dt = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            next_dt = now  # Force run if date is invalid

        if next_dt > now:
            continue

        # Job is due — run it
        field_id = job['field_id']
        field = get_field(field_id)
        if not field:
            print(f'[Scheduler] Field {field_id} not found, skipping job {job["id"]}')
            continue

        print(f'[Scheduler] Running job {job["id"]} for field "{field.get("name", field_id)}"')
        try:
            # Reconstruct field dict expected by compute_monitoring
            field_data = {
                'id': field['id'],
                'name': field.get('name', ''),
                'crop': field.get('crop', 'soja'),
                'plantingDate': field.get('planting_date') or field.get('plantingDate'),
                'boundary': field.get('boundary', {}),
                'monitoring': {
                    'active': True,
                    'checkCount': field.get('check_count', 0)
                }
            }

            result = compute_fn(field_data)

            if result and not result.get('error'):
                save_fn(field_id, result)

                # Generate alerts from anomalies
                for anomaly in result.get('anomalies', []):
                    alert_fn(anomaly)

                # Check agronomic interpretation for urgent alerts
                agronomic = result.get('agronomicInterpretation')
                if agronomic:
                    for interp in agronomic:
                        if interp.get('urgency') == 'alta' and interp.get('confidence', 0) >= 60:
                            from monitoring_api_core import gen_id, now_iso
                            alert_fn({
                                'id': gen_id('agro-'),
                                'fieldId': field_id,
                                'type': f'agronomic_{interp["type"]}',
                                'severity': interp.get('severity', 'warning'),
                                'description': interp.get('recommendation', ''),
                                'status': 'active'
                            })

                print(f'[Scheduler] Completed: {field.get("name")} — z={result.get("zScore")}')
            else:
                error = result.get('error', 'Unknown error') if result else 'No result'
                print(f'[Scheduler] Failed: {field.get("name")} — {error}')

        except Exception as e:
            print(f'[Scheduler] Job error: {e}')

        # Update next_run regardless of success/failure
        interval = job.get('interval_days', 14)
        next_run_dt = now + timedelta(days=interval)
        job['last_run'] = now_str
        job['next_run'] = next_run_dt.isoformat()
        save_scheduler_job(job)


def create_job(field_id, interval_days=14, enabled=True):
    """Create or update a scheduler job for a field."""
    from db import save_scheduler_job, get_scheduler_jobs
    from monitoring_api_core import gen_id

    # Check if job already exists for this field
    existing = [j for j in get_scheduler_jobs() if j['field_id'] == field_id]
    if existing:
        job = existing[0]
        job['interval_days'] = interval_days
        job['enabled'] = 1 if enabled else 0
    else:
        next_run = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        job = {
            'id': gen_id('sched-'),
            'field_id': field_id,
            'interval_days': interval_days,
            'enabled': 1 if enabled else 0,
            'last_run': None,
            'next_run': next_run
        }

    save_scheduler_job(job)
    return job


def remove_job(job_id):
    """Remove a scheduler job."""
    from db import delete_scheduler_job
    delete_scheduler_job(job_id)


def list_jobs():
    """List all scheduler jobs."""
    from db import get_scheduler_jobs
    return get_scheduler_jobs()
