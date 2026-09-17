import uuid
from concurrent.futures import ThreadPoolExecutor
from tools.sherlock import SherlockTool
from tools.maigret import MaigretTool
from tools.theharvester import TheHarvesterTool
from tools.amass import AmassTool
from tools.whatweb import WhatWebTool
from tools.spiderfoot import SpiderFootTool

class ScanEngine:
    def __init__(self, db):
        self.db = db
        self.registered_tools = [
            SherlockTool(),
            MaigretTool(),
            TheHarvesterTool(),
            AmassTool(),
            WhatWebTool(),
            SpiderFootTool()
        ]
        self.active_scans = {}

    def get_tool_statuses(self) -> list[dict]:
        return [
            {
                "name": tool.name,
                "supported_types": tool.supported_types,
                "installed": tool.is_installed()
            }
            for tool in self.registered_tools
        ]

    def start_scan(self, target_type: str, target: str) -> str:
        scan_id = str(uuid.uuid4())
        self.db.create_scan(scan_id, target_type, target)
        
        applicable_tools = [t for t in self.registered_tools if target_type in t.supported_types]
        
        executor = ThreadPoolExecutor(max_workers=4)
        self.active_scans[scan_id] = {"executor": executor, "cancelled": False}

        executor.submit(self._run_scan_job, scan_id, target, applicable_tools)
        return scan_id

    def cancel_scan(self, scan_id: str) -> bool:
        if scan_id in self.active_scans:
            self.active_scans[scan_id]["cancelled"] = True
            self.active_scans[scan_id]["executor"].shutdown(wait=False, cancel_futures=True)
            self.db.update_scan_status(scan_id, "cancelled")
            del self.active_scans[scan_id]
            return True
        return False

    def _run_scan_job(self, scan_id: str, target: str, tools: list):
        for tool in tools:
            if self.active_scans.get(scan_id, {}).get("cancelled"):
                break
            
            res = tool.run(target)
            self.db.save_tool_result(
                scan_id=scan_id,
                tool_name=res["tool_name"],
                status=res["status"],
                exec_time=res["execution_time"],
                findings_count=res["findings_count"],
                raw_output=res["raw_output"],
                parsed_results=res["parsed_results"],
                error_msg=res["error"]
            )

        if not self.active_scans.get(scan_id, {}).get("cancelled"):
            self.db.update_scan_status(scan_id, "completed")
            if scan_id in self.active_scans:
                del self.active_scans[scan_id]