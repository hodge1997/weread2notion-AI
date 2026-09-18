import json

from weread2notion.export import export_weread


class Client:
    def shelf(self):
        return {"books": [{"bookId": "b1", "title": "测试书"}]}

    def book_bundle(self, book_id):
        return {
            "info": {"intro": "简介"},
            "highlights": [{"markText": "划线内容"}],
            "reviews": [{"content": "我的想法"}],
        }


def test_export_json_and_markdown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = export_weread(Client(), "export", "markdown")
    assert result["books"] == 1
    payload = json.loads((tmp_path / "export" / "manifest.json").read_text())
    assert payload["books"][0]["entry"]["bookId"] == "b1"
    markdown = (tmp_path / "export" / "books" / "测试书.md").read_text()
    assert "划线内容" in markdown
    assert "我的想法" in markdown
