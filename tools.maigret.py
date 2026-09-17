from tools.base import BaseTool
from core.parser import ResultParser

class MaigretTool(BaseTool):
    def __init__(self):
        super().__init__("Maigret", "maigret", ["username"], timeout=180)

    def build_command(self, target: str) -> list[str]:
        return ["maigret", target, "--no-color", "--no-pdf"]

    def parse(self, raw_output: str) -> list[dict]:
        return ResultParser.parse_maigret(raw_output)