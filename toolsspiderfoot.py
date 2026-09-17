from tools.base import BaseTool
from core.parser import ResultParser

class SpiderFootTool(BaseTool):
    def __init__(self):
        super().__init__("SpiderFoot", "spiderfoot", ["domain", "ip"], timeout=240)

    def build_command(self, target: str) -> list[str]:
        return ["spiderfoot", "-s", target, "-m", "sfp_dns,sfp_whois", "-q"]

    def parse(self, raw_output: str) -> list[dict]:
        return ResultParser.parse_spiderfoot(raw_output)