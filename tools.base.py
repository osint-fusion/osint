import shutil
import subprocess
import time
from abc import ABC, abstractmethod

class BaseTool(ABC):
    def __init__(self, name: str, command_name: str, supported_types: list[str], timeout: int = 120):
        self.name = name
        self.command_name = command_name
        self.supported_types = supported_types
        self.timeout = timeout

    def is_installed(self) -> bool:
        return shutil.which(self.command_name) is not None

    @abstractmethod
    def build_command(self, target: str) -> list[str]:
        pass

    @abstractmethod
    def parse(self, raw_output: str) -> list[dict]:
        pass

    def run(self, target: str) -> dict:
        if not self.is_installed():
            return {
                "tool_name": self.name,
                "status": "Not Installed",
                "execution_time": 0.0,
                "findings_count": 0,
                "raw_output": f"الأداة {self.name} غير مثبتة على هذا الجهاز.",
                "parsed_results": [],
                "error": "Command not found"
            }

        cmd = self.build_command(target)
        start_time = time.time()
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False
            )
            stdout, stderr = process.communicate(timeout=self.timeout)
            exec_time = round(time.time() - start_time, 2)

            if process.returncode != 0 and not stdout:
                return {
                    "tool_name": self.name,
                    "status": "Failed",
                    "execution_time": exec_time,
                    "findings_count": 0,
                    "raw_output": stderr or stdout,
                    "parsed_results": [],
                    "error": f"Exited with code {process.returncode}"
                }

            raw_combined = stdout + ("\n" + stderr if stderr else "")
            parsed = self.parse(stdout)
            return {
                "tool_name": self.name,
                "status": "Completed",
                "execution_time": exec_time,
                "findings_count": len(parsed),
                "raw_output": raw_combined,
                "parsed_results": parsed,
                "error": None
            }

        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "tool_name": self.name,
                "status": "Timeout",
                "execution_time": float(self.timeout),
                "findings_count": 0,
                "raw_output": f"تجاوزت الأداة الوقت المسموح ({self.timeout} ثانية).",
                "parsed_results": [],
                "error": "Execution timed out"
            }
        except Exception as e:
            return {
                "tool_name": self.name,
                "status": "Failed",
                "execution_time": round(time.time() - start_time, 2),
                "findings_count": 0,
                "raw_output": "",
                "parsed_results": [],
                "error": str(e)
            }