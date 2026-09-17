from tools.base import BaseTool
from core.parser import ResultParser

class AmassTool(BaseTool):
    def __init__(self):
        super().__init__("OWASP Amass", "amass", ["domain"], timeout=180)

    def build_command(self, target: str) -> list[str]:
        return ["amass", "enum", "-passive", "-d", target]

    def parse(self, raw_output: str) -> list[dict]:
        return ResultParser.parse_amass(raw_output)