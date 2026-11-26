from rag.sources.gdrive.gdrive_path_resolver import GDrivePathResolver

FOLDER = GDrivePathResolver.FOLDER


def make(id, name, parents=None, mime="application/pdf"):
    return {"id": id, "name": name, "mimeType": mime, "parents": parents}


def resolve(files):
    GDrivePathResolver().resolve_paths(files)
    return {f["id"]: f["path"] for f in files}


def test_nested_path():
    paths = resolve([
        make("1", "Projects", None, FOLDER),
        make("2", "Thesis", ["1"], FOLDER),
        make("3", "draft.pdf", ["2"]),
    ])
    assert paths["3"] == "Projects/Thesis/draft.pdf"


def test_file_at_root_has_just_its_name():
    paths = resolve([make("1", "notes.txt", None)])
    assert paths["1"] == "notes.txt"


def test_missing_parents_key():
    paths = resolve([{"id": "1", "name": "a.txt", "mimeType": "text/plain"}])
    assert paths["1"] == "a.txt"


def test_folders_get_paths_too():
    paths = resolve([
        make("1", "Projects", None, FOLDER),
        make("2", "Thesis", ["1"], FOLDER),
    ])
    assert paths["2"] == "Projects/Thesis"


def test_parent_not_in_listing_stops_at_known_part():
    # parent "x" is a folder we can't see (e.g. shared with you)
    paths = resolve([make("1", "a.pdf", ["x"])])
    assert paths["1"] == "a.pdf"


def test_cycle_does_not_loop_forever():
    paths = resolve([
        make("1", "A", ["2"], FOLDER),
        make("2", "B", ["1"], FOLDER),
        make("3", "f.pdf", ["1"]),
    ])
    assert paths["3"].endswith("f.pdf")   # finishing is the point


def test_same_name_in_different_folders():
    paths = resolve([
        make("1", "2023", None, FOLDER),
        make("2", "2024", None, FOLDER),
        make("3", "report.pdf", ["1"]),
        make("4", "report.pdf", ["2"]),
    ])
    assert paths["3"] == "2023/report.pdf"
    assert paths["4"] == "2024/report.pdf"