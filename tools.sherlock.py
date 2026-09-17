from tools.base import BaseTool
from core.parser import ResultParser

class SherlockTool(BaseTool):
    def __init__(self):
        super().__init__("Sherlock", "sherlock", ["username"], timeout=120)

    def build_command(self, target: str) -> list[str]:
        return ["sherlock", target, "--print-found", "--no-color"]

    def parse(self, raw_output: str) -> list[dict]:
        return ResultParser.parse_sherlock(raw_output)