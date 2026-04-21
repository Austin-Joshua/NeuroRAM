from neuroram.backend.dbms.database import DatabaseManager


def test_db_initializes():
    db = DatabaseManager()
    status = db.get_index_status()
    assert isinstance(status, dict)
