"""Minsky Native Capability Probe per Section 21.1.
Probes host environment for optional pyminsky library, checking ABI and version.
"""

from dataclasses import dataclass
import os
import subprocess
import sys
from typing import Optional


@dataclass(frozen=True)
class MinskyProbeResult:
    available: bool
    version: Optional[str] = None
    python_path: Optional[str] = None
    transport: str = "subprocess"
    message: str = "Minsky not installed"


def probe_minsky(python_path: Optional[str] = None) -> MinskyProbeResult:
    """Probes whether pyminsky is available in the target python interpreter."""
    target_py = python_path or os.getenv("MINSKY_PYTHON", sys.executable)
    probe_code = (
        "try:\n"
        "    from pyminsky import minsky\n"
        "    print('OK:' + str(getattr(minsky, 'minskyVersion', lambda: 'unknown')()))\n"
        "except Exception as e:\n"
        "    print('FAIL:' + str(e))\n"
    )
    
    try:
        proc = subprocess.run(
            [target_py, "-c", probe_code],
            capture_output=True,
            text=True,
            timeout=5,
        )
        out = proc.stdout.strip()
        if out.startswith("OK:"):
            version = out.split("OK:")[1].strip()
            return MinskyProbeResult(
                available=True,
                version=version,
                python_path=target_py,
                message=f"pyminsky {version} operational",
            )
        else:
            err = out.replace("FAIL:", "").strip() or proc.stderr.strip()
            return MinskyProbeResult(
                available=False,
                python_path=target_py,
                message=f"pyminsky not importable: {err}",
            )
    except Exception as exc:
        return MinskyProbeResult(
            available=False,
            python_path=target_py,
            message=f"Probe execution failed: {str(exc)}",
        )
