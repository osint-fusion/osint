import re

class ResultParser:
    @staticmethod
    def parse_sherlock(raw_output: str) -> list[dict]:
        findings = []
        for line in raw_output.splitlines():
            line = line.strip()
            if line.startswith("[+]"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    findings.append({
                        "source": parts[0].replace("[+]", "").strip(),
                        "type": "Social Profile",
                        "value": parts[1].strip(),
                        "confidence": "High"
                    })
        return findings

    @staticmethod
    def parse_maigret(raw_output: str) -> list[dict]:
        findings = []
        for line in raw_output.splitlines():
            if "[+]" in line and ":" in line:
                clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                parts = clean_line.split("[+]", 1)[1].split(":", 1)
                if len(parts) == 2:
                    findings.append({
                        "source": parts[0].strip(),
                        "type": "Social Profile",
                        "value": parts[1].strip(),
                        "confidence": "High"
                    })
        return findings

    @staticmethod
    def parse_theharvester(raw_output: str) -> list[dict]:
        findings = []
        current_section = None
        for line in raw_output.splitlines():
            line = line.strip()
            if "Emails found:" in line:
                current_section = "Email"
                continue
            elif "Hosts found:" in line:
                current_section = "Host"
                continue
            elif not line or line.startswith("[*]") or line.startswith("-"):
                continue

            if current_section == "Email" and "@" in line:
                findings.append({"source": "theHarvester", "type": "Email", "value": line, "confidence": "Medium"})
            elif current_section == "Host" and ":" in line:
                findings.append({"source": "theHarvester", "type": "Subdomain / IP", "value": line, "confidence": "High"})
        return findings

    @staticmethod
    def parse_amass(raw_output: str) -> list[dict]:
        findings = []
        for line in raw_output.splitlines():
            line = line.strip()
            if line and not line.startswith("["):
                findings.append({"source": "OWASP Amass", "type": "Subdomain", "value": line, "confidence": "High"})
        return findings

    @staticmethod
    def parse_whatweb(raw_output: str) -> list[dict]:
        findings = []
        if not raw_output.strip():
            return findings
        matches = re.findall(r'([A-Za-z0-9_\-\.]+)(?:\[(.*?)\])?', raw_output)
        for name, details in matches:
            if name in ["http", "https", "Summary"]:
                continue
            val = f"{name} ({details})" if details else name
            findings.append({"source": "WhatWeb", "type": "Technology", "value": val, "confidence": "High"})
        return findings

    @staticmethod
    def parse_spiderfoot(raw_output: str) -> list[dict]:
        findings = []
        for line in raw_output.splitlines():
            if "," in line:
                parts = line.split(",")
                if len(parts) >= 3:
                    findings.append({"source": "SpiderFoot", "type": parts[1].strip(), "value": parts[2].strip(), "confidence": "Medium"})
        return findings