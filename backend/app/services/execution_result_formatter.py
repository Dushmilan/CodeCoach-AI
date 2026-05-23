import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ExecutionResultFormatter:
    def format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info(f"Piston API response: {json.dumps(result, indent=2)}")
        except Exception as e:
            logger.warning(f"Could not log full response: {e}")

        run_info = result.get("run", {})
        processed = {
            "stdout": run_info.get("stdout", ""),
            "stderr": run_info.get("stderr", ""),
            "exit_code": run_info.get("code", 1),
            "signal": run_info.get("signal", None),
            "execution_time": run_info.get("wall_time", run_info.get("time", None)),
            "memory_usage": run_info.get("memory", None),
            "language": result.get("language", ""),
            "version": result.get("version", ""),
        }

        try:
            stdout_preview = processed["stdout"][:100] if processed["stdout"] else ""
            logger.info(
                f"Processed execution result: stdout='{stdout_preview}...', exit_code={processed['exit_code']}"
            )
        except Exception as e:
            logger.warning(f"Could not log processed result: {e}")

        stderr = processed["stderr"]
        if stderr:
            lines = stderr.split("\n")
            filtered_lines = [
                line
                for line in lines
                if not any(
                    warning in line.lower()
                    for warning in ["warning", "deprecated", "note:", "#warning"]
                )
            ]
            processed["stderr"] = "\n".join(filtered_lines).strip()

        return processed
