"""Minsky Simulation Subprocess Supervisor per Section 21.3.
Executes Minsky simulations in an isolated child process with strict resource and time bounds.
"""

from dataclasses import dataclass
import os
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional
import pandas as pd

from app.domain.errors import ContagionDomainException, FailureCode
from integrations.minsky.normalizer import normalize_minsky_output
from integrations.minsky.probe import probe_minsky


@dataclass(frozen=True)
class MinskyRunResult:
    success: bool
    scenario_id: str
    csv_path: Optional[str] = None
    step_count: int = 0
    message: str = ""


class MinskySupervisor:
    def __init__(
        self,
        python_path: Optional[str] = None,
        max_run_seconds: int = 60,
        max_steps: int = 10000,
    ):
        self.python_path = python_path or os.getenv("MINSKY_PYTHON", sys.executable)
        self.max_run_seconds = max_run_seconds
        self.max_steps = max_steps

    def run_simulation(
        self,
        model_path: str,
        output_csv_path: Optional[str] = None,
        steps: int = 500,
    ) -> MinskyRunResult:
        """Executes a Minsky model simulation in an isolated child process."""
        probe = probe_minsky(self.python_path)
        if not probe.available:
            raise ContagionDomainException(
                code=FailureCode.MINSKY_UNAVAILABLE,
                message=f"Minsky runtime is not available: {probe.message}",
                status_code=503,
            )

        if not os.path.exists(model_path):
            raise ContagionDomainException(
                code=FailureCode.ENTITY_AMBIGUOUS,
                message=f"Minsky model file not found: {model_path}",
                status_code=404,
            )

        csv_out = output_csv_path or tempfile.mktemp(suffix=".csv")
        bounded_steps = min(steps, self.max_steps)

        runner_script = (
            f"import sys\n"
            f"from pyminsky import minsky\n"
            f"import pandas as pd\n"
            f"minsky.load('{model_path}')\n"
            f"minsky.reset()\n"
            f"records = []\n"
            f"for step in range({bounded_steps}):\n"
            f"    minsky.step()\n"
            f"    row = {{'time': minsky.t()}}\n"
            f"    for k, v in minsky.variableValues.items():\n"
            f"        row[k] = v\n"
            f"    records.append(row)\n"
            f"df = pd.DataFrame(records)\n"
            f"df.to_csv('{csv_out}', index=False)\n"
            f"print(f'DONE:{{len(records)}}')\n"
        )

        try:
            proc = subprocess.run(
                [self.python_path, "-c", runner_script],
                capture_output=True,
                text=True,
                timeout=self.max_run_seconds,
            )
            if proc.returncode != 0:
                raise ContagionDomainException(
                    code=FailureCode.MINSKY_OUTPUT_INVALID,
                    message=f"Minsky process failed: {proc.stderr.strip()}",
                    status_code=500,
                )
            return MinskyRunResult(
                success=True,
                scenario_id=os.path.basename(model_path),
                csv_path=csv_out,
                step_count=bounded_steps,
                message="Simulation completed successfully",
            )
        except subprocess.TimeoutExpired:
            raise ContagionDomainException(
                code=FailureCode.RESOURCE_LIMIT,
                message=f"Minsky simulation timed out after {self.max_run_seconds}s",
                status_code=504,
            )
