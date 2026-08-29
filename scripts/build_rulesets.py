#!/usr/bin/env python3
"""Convert comma-separated Clash/Surge-style rules to sing-box 1.12 SRS files."""
from __future__ import annotations
import argparse
import json
import subprocess
import tempfile
import urllib.request
from collections.abc import Iterable
from pathlib import Path

GISTS = "https://api.github.com/users/{}/gists?per_page=100&page={}"
TYPES = {"DOMAIN": "domain", "DOMAIN-SUFFIX": "domain_suffix", "DOMAIN-KEYWORD": "domain_keyword", "DOMAIN-REGEX": "domain_regex", "IP-CIDR": "ip_cidr", "IP-CIDR6": "ip_cidr"}
IGNORED = {"URL-REGEX", "PROCESS-NAME", "PROCESS-PATH", "USER-AGENT"}

def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "sing-box-rule-set-builder"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8-sig")

def gist_files(user: str) -> Iterable[tuple[str, str]]:
    for page in range(1, 101):
        response = json.loads(fetch(GISTS.format(user, page)))
        if not isinstance(response, list):
            raise RuntimeError(f"Unexpected Gist API response for {user}")
        if not response:
            return
        for gist in response:
            for file in gist.get("files", {}).values():
                filename, raw_url = file.get("filename"), file.get("raw_url")
                if isinstance(filename, str) and isinstance(raw_url, str):
                    yield filename, raw_url

def source_from(lines: Iterable[str], source_name: str) -> tuple[dict[str, object], list[str]]:
    values: dict[str, list[str]] = {}
    warnings: list[str] = []
    for number, raw in enumerate(lines, 1):
        text = raw.strip()
        if not text or text.startswith(("#", "!", ";")):
            continue
        fields = [field.strip() for field in text.split(",")]
        kind = fields[0].upper()
        if kind in IGNORED:
            warnings.append(f"{source_name}:{number}: {kind} has no sing-box rule-set equivalent; skipped")
            continue
        target = TYPES.get(kind)
        if target is None or len(fields) < 2 or not fields[1]:
            warnings.append(f"{source_name}:{number}: unsupported or empty {kind!r}; skipped")
            continue
        value = fields[1] if target == "domain_regex" else fields[1].rstrip(".").lower()
        values.setdefault(target, []).append(value)
    rule = {key: list(dict.fromkeys(value)) for key, value in values.items()}
    if not rule:
        raise ValueError(f"{source_name}: no convertible rules")
    # Version 3 is compatible with sing-box 1.12.
    return {"version": 3, "rules": [rule]}, warnings

def compile_one(binary: Path, source: dict[str, object], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        input_path = Path(temporary) / "rules.json"
        input_path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
        subprocess.run([str(binary), "rule-set", "compile", "--output", str(destination), str(input_path)], check=True)

def build(binary: Path, output: Path, name: str, url: str, claimed: set[str]) -> bool:
    if name in claimed:
        raise ValueError(f"Duplicate output filename: {name}")
    try:
        source, warnings = source_from(fetch(url).splitlines(), name)
    except ValueError as error:
        print(f"warning: {error}; skipped")
        return False
    for warning in warnings:
        print(f"warning: {warning}")
    compile_one(binary, source, output / name)
    claimed.add(name)
    print(f"Wrote {output / name}")
    return True

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("rulesets.json"))
    parser.add_argument("--output-directory", type=Path, default=Path("rule-set"))
    parser.add_argument("--sing-box", type=Path, required=True)
    arguments = parser.parse_args()
    config = json.loads(arguments.config.read_text(encoding="utf-8"))
    claimed: set[str] = set()
    generated = 0
    for item in config["rulesets"]:
        generated += build(arguments.sing_box, arguments.output_directory, f"{item['name']}.srs", item["url"], claimed)
    for user in config.get("gist_users", []):
        for filename, raw_url in gist_files(user):
            stem = Path(filename).stem
            if not stem:
                print(f"warning: invalid Gist filename {filename!r}; skipped")
                continue
            generated += build(arguments.sing_box, arguments.output_directory, f"{stem}.srs", raw_url, claimed)
    if not generated:
        raise RuntimeError("No rule-sets were generated")

if __name__ == "__main__":
    main()
