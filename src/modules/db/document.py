from src import get_db


class Document:
    def __init__(self):
        self.db = get_db()

    def add_document(self, content: str, metadata: str):
        query = """INSERT INTO documents(content, metadata)
                   VALUES (?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                   content = excluded.content,
                   metadata = excluded.metadata;"""
        return self.db.execute_query(query, (content, metadata))

    def get_document(self, id: int):
        query = "SELECT * FROM documents WHERE id = ?;"
        return self.db.execute_read_query(query, (id,))

    def delete_document(self, id: int):
        query = "DELETE FROM documents WHERE id = ?;"
        return self.db.execute_query(query, (id,))
