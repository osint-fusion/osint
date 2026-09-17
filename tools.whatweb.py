from tools.base import BaseTool
from core.parser import ResultParser

class WhatWebTool(BaseTool):
    def __init__(self):
        super().__init__("WhatWeb", "whatweb", ["domain", "ip"], timeout=60)

    def build_command(self, target: str) -> list[str]:
        return ["whatweb", "--color=never", target]

    def parse(self, raw_output: str) -> list[dict]:
        return ResultParser.parse_whatweb(raw_output)