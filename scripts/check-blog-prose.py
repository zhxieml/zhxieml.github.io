"""Verify a figure-only migration against saved, pre-migration Markdown files."""
import argparse
import difflib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALL = r"\{\{< research-(?:figure|interactive)\b[\s\S]*?>\}\}"
IMAGE = r"!\[([\s\S]*?)\]\((Untitled(?:_\d+)?\.png)\)"


def arguments(call):
    return {k: json.loads(v) for k,v in re.findall(r'(\w+)=("(?:\\.|[^"\\])*"|true|false)', call)}


def normalized(source):
    body = source.split("---", 2)[2]
    body = re.sub(IMAGE, lambda m: "[FIGURE:"+m[2]+"]", body)
    return re.sub(CALL, lambda m: "[FIGURE:"+arguments(m[0])["src"]+"]", body)


def check(baseline):
    snapshots = sorted(baseline.glob("*.md"))
    if not snapshots:
        raise ValueError("No Markdown snapshots found in " + str(baseline))
    for snapshot in snapshots:
        path = ROOT / "content/blog" / snapshot.stem / "index.md"
        before = snapshot.read_text()
        after = path.read_text()
        if normalized(before) != normalized(after):
            raise AssertionError("\n".join(difflib.unified_diff(normalized(before).splitlines(), normalized(after).splitlines(), fromfile="before", tofile=str(path))))
        def metadata(text):
            return [line for line in text.split("---",2)[1].splitlines() if line.strip() and not line.startswith(("layout:", "plain_images:"))]
        assert metadata(before) == metadata(after), (path,"metadata changed")
        old = {arguments(m[0])["src"]: arguments(m[0]) for m in re.finditer(CALL,before)}
        new = {arguments(m[0])["src"]: arguments(m[0]) for m in re.finditer(CALL,after)}
        for src,params in old.items():
            assert all(new[src].get(k)==v for k,v in params.items()), (path,src,"figure wording changed")
        for m in re.finditer(IMAGE,before):
            if m[2] in new:
                assert new[m[2]]["alt"] == m[1], (path,m[2],"image description changed")
        print(path.parent.name+": PASS — prose, headings, formulas, metadata and original image descriptions are unchanged")


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--baseline",type=Path,required=True)
    check(parser.parse_args().baseline)
