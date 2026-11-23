"""
Resilient Gateway Circuit Breaker Service.
Provides a 3-state Circuit Breaker (CLOSED -> OPEN -> HALF_OPEN)
for external LLM semantic routers, external market APIs, and AIS feeds.

Features:
- Configurable failure threshold (default: 3 consecutive failures)
- Recovery timeout (default: 15.0 seconds before attempting trial call in HALF_OPEN)
- Trial success threshold (default: 2 consecutive successes to re-close circuit)
- Fast-fail when OPEN with instant execution of deterministic fallback
- Zero unhandled exceptions thrown to caller
- Manual trip/reset controls for chaos engineering drills
- Telemetry reporting for health checks and Prometheus metrics
"""

from enum import Enum
import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger("risklattice.circuit_breaker")

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # Normal operation: requests pass through
    OPEN = "OPEN"            # Tripped: requests fail fast to fallback
    HALF_OPEN = "HALF_OPEN"  # Testing: trial requests probe upstream recovery


class CircuitBreakerService:
    def __init__(
        self,
        name: str = "llm_gateway",
        failure_threshold: int = 3,
        recovery_timeout: float = 15.0,
        success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change: float = time.time()
        self._last_failure_reason: Optional[str] = None

        # Lifetime counters
        self._total_calls = 0
        self._total_failures = 0
        self._total_fallbacks = 0
        self._total_trips = 0

    @property
    def state(self) -> CircuitState:
        """Returns current circuit state, checking if recovery timeout has elapsed."""
        if self._state == CircuitState.OPEN and self._last_failure_time is not None:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN, reason="Recovery timeout elapsed; probing upstream")
        return self._state

    def _transition_to(self, new_state: CircuitState, reason: str = ""):
        old_state = self._state
        self._state = new_state
        self._last_state_change = time.time()
        if new_state == CircuitState.OPEN:
            self._total_trips += 1
            self._consecutive_successes = 0
        elif new_state == CircuitState.CLOSED:
            self._consecutive_failures = 0
            self._consecutive_successes = 0
            self._last_failure_reason = None
        elif new_state == CircuitState.HALF_OPEN:
            self._consecutive_successes = 0

        logger.warning(
            f"CircuitBreaker[{self.name}] transition: {old_state.value} -> {new_state.value}. {reason}"
        )

    def record_success(self):
        """Records a successful upstream invocation."""
        self._consecutive_failures = 0
        if self.state == CircuitState.HALF_OPEN:
            self._consecutive_successes += 1
            if self._consecutive_successes >= self.success_threshold:
                self._transition_to(
                    CircuitState.CLOSED,
                    reason=f"{self._consecutive_successes} consecutive trial successes",
                )

    def record_failure(self, error: Exception):
        """Records an upstream failure and trips circuit if threshold is reached."""
        self._total_failures += 1
        self._consecutive_failures += 1
        self._last_failure_time = time.time()
        self._last_failure_reason = f"{type(error).__name__}: {str(error)}"

        if self.state == CircuitState.HALF_OPEN:
            # Immediate return to OPEN on trial failure
            self._transition_to(
                CircuitState.OPEN,
                reason=f"Trial request in HALF_OPEN failed: {self._last_failure_reason}",
            )
        elif self.state == CircuitState.CLOSED:
            if self._consecutive_failures >= self.failure_threshold:
                self._transition_to(
                    CircuitState.OPEN,
                    reason=f"Reached failure threshold ({self.failure_threshold} consecutive errors): {self._last_failure_reason}",
                )

    def call(
        self,
        func: Callable[..., T],
        *args: Any,
        fallback: Optional[Callable[..., T]] = None,
        **kwargs: Any,
    ) -> T:
        """
        Executes func guarded by circuit breaker.
        If OPEN: immediately calls fallback (or returns None).
        If CLOSED or HALF_OPEN: attempts func; on exception records failure and calls fallback.
        """
        self._total_calls += 1

        current_state = self.state
        if current_state == CircuitState.OPEN:
            self._total_fallbacks += 1
            logger.info(
                f"CircuitBreaker[{self.name}] is OPEN. Fast-failing directly to fallback."
            )
            if fallback is not None:
                return fallback(*args, **kwargs)
            raise RuntimeError(f"CircuitBreaker[{self.name}] is OPEN and no fallback provided")

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            self._total_fallbacks += 1
            logger.warning(
                f"CircuitBreaker[{self.name}] caught error during call: {e}. Executing fallback."
            )
            if fallback is not None:
                return fallback(*args, **kwargs)
            raise

    def trip(self, reason: str = "Manual chaos injection"):
        """Manually trips the circuit breaker to OPEN state (for testing/chaos drills)."""
        self._last_failure_time = time.time()
        self._last_failure_reason = reason
        self._consecutive_failures = self.failure_threshold
        self._transition_to(CircuitState.OPEN, reason=reason)

    def reset(self, reason: str = "Manual reset"):
        """Manually resets the circuit breaker to CLOSED state."""
        self._transition_to(CircuitState.CLOSED, reason=reason)

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns diagnostic telemetry dictionary."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_sec": self.recovery_timeout,
            "success_threshold": self.success_threshold,
            "consecutive_failures": self._consecutive_failures,
            "consecutive_successes": self._consecutive_successes,
            "last_failure_reason": self._last_failure_reason,
            "time_in_current_state_sec": round(time.time() - self._last_state_change, 2),
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_fallbacks": self._total_fallbacks,
            "total_trips": self._total_trips,
            "fallback_active": self.state != CircuitState.CLOSED,
        }


# Global circuit breaker instances
llm_circuit_breaker = CircuitBreakerService(
    name="llm_router",
    failure_threshold=3,
    recovery_timeout=15.0,
    success_threshold=2,
)

ais_circuit_breaker = CircuitBreakerService(
    name="ais_feed",
    failure_threshold=3,
    recovery_timeout=15.0,
    success_threshold=2,
)
