import os, subprocess, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def run(*args):
    p = subprocess.run([sys.executable, "-m", "noslop", *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def test_slop_is_blocked():
    code, out, _ = run("lint", "tests/fixtures/slop.md", "--json")
    assert code == 1
    ids = {h["id"] for h in json.loads(out)["tests/fixtures/slop.md"]["hits"]}
    for must in ("B01", "B02", "B03", "B04", "B06", "B07", "B08"):
        assert must in ids, must

def test_human_passes():
    code, out, _ = run("lint", "tests/fixtures/human.md", "--json")
    assert code == 0
    hits = json.loads(out)["tests/fixtures/human.md"]["hits"]
    assert not [h for h in hits if h["sev"] == "BLOCK"]

def test_score_threshold():
    assert run("score", "tests/fixtures/slop.md")[0] == 3
    assert run("score", "tests/fixtures/human.md")[0] == 0

def test_hook_blocks():
    p = subprocess.run([sys.executable, "-m", "noslop", "hook"], cwd=ROOT, input='{"tool_input":{"file_path":"tests/fixtures/slop.md"}}', capture_output=True, text=True)
    assert p.returncode == 2 and "BLOCK" in p.stderr

def test_docs_register_allows_labels():
    code, out, _ = run("lint", "tests/fixtures/slop.md", "--register", "docs", "--json")
    ids = {h["id"] for h in json.loads(out)["tests/fixtures/slop.md"]["hits"]}
    assert "B03" not in ids and "B04" not in ids
