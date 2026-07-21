from weread2notion.notion import NotionWorkspace


class TransientError(RuntimeError):
    status = 520


class Client:
    def __init__(self):
        self.calls = 0

    def request(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            raise TransientError("temporary Notion failure")
        return {"ok": True}


def test_request_retries_transient_notion_errors(monkeypatch):
    monkeypatch.setattr("weread2notion.notion.time.sleep", lambda _: None)
    client = Client()
    notion = NotionWorkspace("token", "page", "version", client=client)
    assert notion.request("pages/page", "PATCH", {}) == {"ok": True}
    assert client.calls == 2


def test_upsert_refreshes_existing_page_icon(monkeypatch):
    notion = NotionWorkspace("token", "page", "version", client=Client())
    notion.schemas["year"] = {}
    monkeypatch.setattr(
        notion, "properties", lambda database, raw: {"Name": raw["Name"]}
    )
    monkeypatch.setattr(
        notion, "find", lambda database, key, value: {"id": "year-page"}
    )
    calls = []
    monkeypatch.setattr(
        notion, "request", lambda path, method, body: calls.append((path, method, body))
    )

    page_id = notion.upsert(
        "year",
        "Name",
        "2026",
        {"Name": "2026"},
        "https://www.notion.so/icons/target_red.svg",
    )

    assert page_id == "year-page"
    assert calls[0][2]["icon"] == {
        "type": "external",
        "external": {"url": "https://www.notion.so/icons/target_red.svg"},
    }


def test_upsert_reuses_known_page_without_query(monkeypatch):
    notion = NotionWorkspace("token", "page", "version", client=Client())
    notion.schemas["book"] = {}
    monkeypatch.setattr(notion, "properties", lambda database, raw: {"Name": "Book"})
    monkeypatch.setattr(
        notion,
        "find",
        lambda *args: (_ for _ in ()).throw(AssertionError("find should not run")),
    )
    calls = []
    monkeypatch.setattr(
        notion,
        "request",
        lambda path, method, body: calls.append((path, method, body)),
    )
    page_id = notion.upsert(
        "book", "BookId", "book-1", {"Name": "Book"}, existing_id="page-1"
    )
    assert page_id == "page-1"
    assert calls[0][0] == "pages/page-1"


def test_row_index_normalizes_integer_float_keys(monkeypatch):
    notion = NotionWorkspace("token", "page", "version", client=Client())
    monkeypatch.setattr(
        notion,
        "query_all",
        lambda database: [
            {
                "id": "record-page",
                "properties": {"时间戳": {"type": "number", "number": 1.0}},
            }
        ],
    )
    assert notion.row_index("阅读记录", "时间戳")["1"]["page_id"] == "record-page"
