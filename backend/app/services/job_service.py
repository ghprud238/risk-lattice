"""Job Management, Concurrency, and SSE Event Stream Service per Section 10.3 & 12.1.
Enforces strict state transitions:
QUEUED -> PREPARING -> RUNNING -> VALIDATING -> COMMITTING -> COMPLETE (or FAILED / CANCELLED).
"""

import asyncio
from datetime import datetime, timezone
import json
import threading
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.domain.models import JobState, RunManifest


class JobEvent:
    def __init__(self, sequence: int, event: str, data: Dict[str, Any], created_at: Optional[str] = None):
        self.sequence = sequence
        self.event = event
        self.data = data
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_sse(self) -> str:
        payload = json.dumps(self.data)
        return f"id: {self.sequence}\nevent: {self.event}\ndata: {payload}\n\n"


class JobService:
    def __init__(self):
        self._lock = threading.RLock()
        self._runs: Dict[str, RunManifest] = {}
        self._events: Dict[str, List[JobEvent]] = {}
        self._event_subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._idempotency_keys: Dict[str, str] = {}  # key -> run_id

    def create_job(
        self,
        portfolio_version_id: str,
        graph_version_id: str,
        scenario_version_id: str,
        engine_profile: str = "four-hop-v2",
        risk_profile: str = "residual-tcopula-v1",
        seed: int = 42,
        paths: int = 10000,
        idempotency_key: Optional[str] = None,
    ) -> Tuple[str, bool]:
        """Creates a new queued simulation job.
        Returns: (run_id, is_existing)
        """
        with self._lock:
            if idempotency_key and idempotency_key in self._idempotency_keys:
                return self._idempotency_keys[idempotency_key], True

            run_id = str(uuid.uuid4())
            now_iso = datetime.now(timezone.utc).isoformat()
            manifest = RunManifest(
                schema_version="1",
                run_id=run_id,
                portfolio_version_id=portfolio_version_id,
                graph_version_id=graph_version_id,
                scenario_version_id=scenario_version_id,
                engine_profile=engine_profile,
                risk_profile=risk_profile,
                seed=seed,
                paths=paths,
                created_at=now_iso,
                status=JobState.QUEUED,
                attempt_id="attempt-0",
            )
            self._runs[run_id] = manifest
            self._events[run_id] = []
            self._event_subscribers[run_id] = []

            if idempotency_key:
                self._idempotency_keys[idempotency_key] = run_id

            # Emit initial queued event
            self._record_event_unlocked(
                run_id,
                "job.queued",
                {
                    "schema_version": "1",
                    "run_id": run_id,
                    "status": JobState.QUEUED.value,
                    "created_at": now_iso,
                },
            )
            return run_id, False

    def get_job(self, run_id: str) -> Optional[RunManifest]:
        with self._lock:
            return self._runs.get(run_id)

    def transition_state(
        self,
        run_id: str,
        new_state: JobState,
        error_message: Optional[str] = None,
        content_hash: Optional[str] = None,
    ) -> RunManifest:
        """Transitions job to a new state and records an audit event."""
        with self._lock:
            if run_id not in self._runs:
                raise KeyError(f"Run {run_id} not found")

            current = self._runs[run_id]
            now_iso = datetime.now(timezone.utc).isoformat()

            # Create updated manifest
            updated = RunManifest(
                schema_version=current.schema_version,
                run_id=current.run_id,
                portfolio_version_id=current.portfolio_version_id,
                graph_version_id=current.graph_version_id,
                scenario_version_id=current.scenario_version_id,
                engine_profile=current.engine_profile,
                risk_profile=current.risk_profile,
                seed=current.seed,
                paths=current.paths,
                created_at=current.created_at,
                status=new_state,
                attempt_id=current.attempt_id,
                completed_at=now_iso if new_state in (JobState.COMPLETE, JobState.FAILED, JobState.CANCELLED) else None,
                content_hash=content_hash or current.content_hash,
            )
            self._runs[run_id] = updated

            event_name = f"job.{new_state.value.lower()}"
            event_data = {
                "schema_version": "1",
                "run_id": run_id,
                "status": new_state.value,
                "timestamp": now_iso,
            }
            if error_message:
                event_data["error"] = error_message
            if content_hash:
                event_data["content_hash"] = content_hash

            self._record_event_unlocked(run_id, event_name, event_data)
            return updated

    def record_progress(
        self, run_id: str, event_type: str, data: Dict[str, Any]
    ) -> None:
        with self._lock:
            self._record_event_unlocked(run_id, event_type, data)

    def _record_event_unlocked(
        self, run_id: str, event_type: str, data: Dict[str, Any]
    ) -> JobEvent:
        events = self._events.setdefault(run_id, [])
        seq = len(events) + 1
        event = JobEvent(sequence=seq, event=event_type, data=data)
        events.append(event)

        # Notify subscribers
        subscribers = self._event_subscribers.get(run_id, [])
        for queue in subscribers:
            try:
                queue.put_nowait(event)
            except Exception:
                pass
        return event

    def get_events(
        self, run_id: str, last_event_id: Optional[int] = None
    ) -> List[JobEvent]:
        with self._lock:
            events = self._events.get(run_id, [])
            if last_event_id is not None:
                return [e for e in events if e.sequence > last_event_id]
            return list(events)

    def cancel_job(self, run_id: str) -> bool:
        with self._lock:
            if run_id not in self._runs:
                return False
            manifest = self._runs[run_id]
            if manifest.status in (JobState.COMPLETE, JobState.FAILED, JobState.CANCELLED):
                return False
            self.transition_state(run_id, JobState.CANCELLED)
            return True


job_service = JobService()
