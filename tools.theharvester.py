from tools.base import BaseTool
from core.parser import ResultParser

class TheHarvesterTool(BaseTool):
    def __init__(self):
        super().__init__("theHarvester", "theHarvester", ["domain"], timeout=150)

    def build_command(self, target: str) -> list[str]:
        return ["theHarvester", "-d", target, "-b", "crtsh,certspotter"]

    def parse(self, raw_output: str) -> list[dict]:
        return ResultParser.parse_theharvester(raw_output)