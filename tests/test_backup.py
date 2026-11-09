import hashlib
import sqlite3
from scripts.backup_sqlite import backup_and_verify, readonly


def test_live_wal_snapshot_restore_preserves_rows_and_does_not_overwrite(tmp_path):
    origin=tmp_path/'origen.db'
    live=sqlite3.connect(origin)
    live.execute('PRAGMA journal_mode=WAL')
    live.execute('CREATE TABLE casos (id INTEGER PRIMARY KEY, importe INTEGER)')
    live.execute('INSERT INTO casos (importe) VALUES (35123)'); live.commit()
    result=backup_and_verify(origin,tmp_path/'respaldos')
    assert result['restauracion_aislada']=='ok'
    assert result['tablas_y_filas']=={'casos':1}
    snapshot=tmp_path/'respaldos'/result['archivo']
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest()==result['sha256']
    with readonly(tmp_path/'respaldos'/result['archivo_restauracion']) as restored:
        assert restored.execute('SELECT importe FROM casos').fetchall()==[(35123,)]
    live.execute('INSERT INTO casos (importe) VALUES (7)'); live.commit()
    second=backup_and_verify(origin,tmp_path/'respaldos')
    assert second['archivo']!=result['archivo'] and second['tablas_y_filas']=={'casos':2}
    with readonly(snapshot) as old:
        assert old.execute('SELECT COUNT(*) FROM casos').fetchone()==(1,)
    live.close()
