import importlib.util
from pathlib import Path
from types import SimpleNamespace

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_sync.py"
SPEC = importlib.util.spec_from_file_location("run_sync", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Could not load script module from {SCRIPT_PATH}")
run_sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run_sync)


class FakeDataSource:
    def __init__(self):
        self.connected = False

    def connect(self):
        self.connected = True

    def list_source_files(self):
        return ["file-1", "file-2"]


class FakeFileRepo:
    def __init__(self):
        self.files = None
        self.count_calls = 0

    def upsert_files(self, files):
        self.files = files

    def count_files(self):
        self.count_calls += 1
        return 2


def test_main_uses_container_components(monkeypatch, capsys):
    source = FakeDataSource()
    repo = FakeFileRepo()
    container = SimpleNamespace(
        data_source=source,
        file_repo=repo,
    )
    monkeypatch.setattr(run_sync, "build_container", lambda: container)

    run_sync.main()

    assert source.connected
    assert repo.files == ["file-1", "file-2"]
    assert repo.count_calls == 1
    assert capsys.readouterr().out.splitlines() == [
        "listed 2 files from Drive",
        "files in repository: 2",
    ]
