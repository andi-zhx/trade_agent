"""Regression tests for shared editing, authentication and recoverable storage."""
from contextlib import closing
from io import BytesIO
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import uuid
from zipfile import ZipFile

from sqlalchemy import create_engine, inspect, MetaData, Table
from werkzeug.security import check_password_hash

from app import create_app, init_db
from backup_service import create_bundle, restore_bundle
from models import BackupRecord, Document, Enterprise, Product, User, db


class SharedLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.options = {'TESTING': True, 'DATA_ROOT': self.root, 'RATELIMIT_ENABLED': False}
        self.app = create_app(self.options)
        init_db(self.app)
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.temp.cleanup()

    def token(self, response):
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))
        self.assertIsNotNone(match, response.get_data(as_text=True)[:300])
        return match.group(1)

    def login(self, client=None, name='admin', password='admin123'):
        client = client or self.client
        token = self.token(client.get('/登录'))
        response = client.post('/登录', data={'csrf_token': token, '用户名': name, '密码': password})
        self.assertEqual(response.status_code, 302)
        return self.token(client.get('/library/enterprises/new'))

    def post(self, path, data, client=None):
        client = client or self.client
        token = self.token(client.get('/library/enterprises/new'))
        return client.post(path, data={**data, 'csrf_token': token})

    def enterprise(self, **extra):
        data = {'submission_key': uuid.uuid4().hex, 'company_name': '稳定保存测试企业', 'primary_contact_name': '张女士', **extra}
        response = self.post('/library/enterprises/new', data)
        self.assertEqual(response.status_code, 302, response.get_data(as_text=True))
        with self.app.app_context():
            item = Enterprise.query.filter_by(submission_key=data['submission_key']).one()
            return item.id, data

    def product(self, enterprise_id, **extra):
        data = {'submission_key': uuid.uuid4().hex, 'enterprise_id': enterprise_id, 'product_name_cn': '测试产品', **extra}
        response = self.post('/library/products/new', data)
        self.assertEqual(response.status_code, 302, response.get_data(as_text=True))
        with self.app.app_context():
            item = Product.query.filter_by(submission_key=data['submission_key']).one()
            return item.id, data

    def test_create_attachment_and_persist_after_restart(self):
        self.login()
        enterprise_id, _ = self.enterprise(attachments=(BytesIO(b'company document'), '企业介绍.txt'), next_step='product')
        product_id, _ = self.product(enterprise_id, model='规格 A', attachments=(BytesIO(b'product document'), '产品资料.pdf'))
        with self.app.app_context():
            self.assertEqual(Document.query.count(), 2)
            for doc in Document.query.all():
                data = self.client.get(f'/documents/{doc.id}/download')
                self.assertEqual(data.status_code, 200)
                self.assertIn(b'document', data.data)
                data.close()
        restarted = create_app(self.options)
        init_db(restarted)
        with restarted.app_context():
            self.assertEqual(Enterprise.query.filter_by(id=enterprise_id).one().company_name, '稳定保存测试企业')
            self.assertEqual(Product.query.filter_by(id=product_id).one().model, '规格 A')
            self.assertEqual(Document.query.count(), 2)
            db.session.remove()
            db.engine.dispose()

    def test_duplicate_submit_does_not_create_second_record(self):
        self.login()
        enterprise_id, data = self.enterprise()
        response = self.post('/library/enterprises/new', data)
        self.assertEqual(response.status_code, 302)
        self.product(enterprise_id)
        with self.app.app_context():
            self.assertEqual(Enterprise.query.count(), 1)
        _, product_data = self.product(enterprise_id)
        self.assertEqual(self.post('/library/products/new', product_data).status_code, 302)
        with self.app.app_context():
            self.assertEqual(Product.query.count(), 2)

    def test_update_preserves_old_extra_fields(self):
        self.login()
        enterprise_id, _ = self.enterprise()
        with self.app.app_context():
            item = db.session.get(Enterprise, enterprise_id)
            item.enterprise_extra_fields = {**item.enterprise_extra_fields, 'legacy_certificates': ['ISO9001']}
            db.session.commit()
            version = item.version_id
        response = self.post(f'/library/enterprises/{enterprise_id}/edit', {'version_id': version, 'company_name': '修改后企业', 'primary_contact_name': '李女士'})
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            item = db.session.get(Enterprise, enterprise_id)
            self.assertEqual(item.enterprise_extra_fields['legacy_certificates'], ['ISO9001'])
            self.assertEqual(item.enterprise_extra_fields['primary_contact_name'], '李女士')

    def test_stale_edit_is_rejected_and_input_retained(self):
        self.login()
        enterprise_id, _ = self.enterprise()
        with self.app.app_context():
            version = db.session.get(Enterprise, enterprise_id).version_id
        path = f'/library/enterprises/{enterprise_id}/edit'
        self.assertEqual(self.post(path, {'version_id': version, 'company_name': '成员甲的新资料'}).status_code, 302)
        stale = self.post(path, {'version_id': version, 'company_name': '成员乙未保存的输入'})
        self.assertEqual(stale.status_code, 409)
        self.assertIn('成员乙未保存的输入', stale.get_data(as_text=True))
        with self.app.app_context():
            self.assertEqual(db.session.get(Enterprise, enterprise_id).company_name, '成员甲的新资料')

    def test_product_stale_edit_and_extra_data_preservation(self):
        self.login()
        enterprise_id, _ = self.enterprise()
        product_id, _ = self.product(enterprise_id)
        with self.app.app_context():
            item = db.session.get(Product, product_id)
            item.product_extra_fields = {'certifications': 'historical'}
            db.session.commit()
            version = item.version_id
        data = {'version_id': version, 'enterprise_id': enterprise_id, 'product_name_cn': '更新产品'}
        self.assertEqual(self.post(f'/library/products/{product_id}/edit', data).status_code, 302)
        self.assertEqual(self.post(f'/library/products/{product_id}/edit', {**data, 'product_name_cn': '旧页面的输入'}).status_code, 409)
        with self.app.app_context():
            self.assertEqual(db.session.get(Product, product_id).product_extra_fields, {'certifications': 'historical'})

    def test_invalid_form_keeps_input_and_writes_nothing(self):
        self.login()
        result = self.post('/library/enterprises/new', {'submission_key': uuid.uuid4().hex, 'company_name': '', 'primary_contact_name': '保留我的输入'})
        self.assertEqual(result.status_code, 400)
        self.assertIn('保留我的输入', result.get_data(as_text=True))
        with self.app.app_context():
            self.assertEqual(Enterprise.query.count(), 0)

    def test_product_requires_valid_enterprise(self):
        self.login()
        result = self.post('/library/products/new', {'submission_key': uuid.uuid4().hex, 'product_name_cn': '产品', 'enterprise_id': 999})
        self.assertEqual(result.status_code, 400)
        with self.app.app_context():
            self.assertEqual(Product.query.count(), 0)

    def test_failed_attachment_write_rolls_back_record_and_retains_input(self):
        self.login()
        with patch('app.保存文件并登记记录', side_effect=OSError('simulated disk full')):
            with self.assertLogs(self.app.logger, level='ERROR'):
                response = self.post('/library/enterprises/new', {
                    'submission_key': uuid.uuid4().hex,
                    'company_name': '写入失败仍保留的输入',
                    'attachments': (BytesIO(b'not saved'), 'example.txt'),
                })
        self.assertEqual(response.status_code, 400)
        self.assertIn('写入失败仍保留的输入', response.get_data(as_text=True))
        self.assertNotIn('保存成功，资料已存入资料库。', response.get_data(as_text=True))
        with self.app.app_context():
            self.assertEqual(Enterprise.query.count(), 0)
            self.assertEqual(Document.query.count(), 0)

    def test_archive_and_restore_preserves_product_and_files(self):
        self.login()
        enterprise_id, _ = self.enterprise(attachments=(BytesIO(b'keep me'), 'keep.txt'))
        product_id, _ = self.product(enterprise_id)
        with self.app.app_context():
            version = db.session.get(Enterprise, enterprise_id).version_id
        response = self.post(f'/library/enterprises/{enterprise_id}/archive', {'version_id': version})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(f'/library/enterprises/{enterprise_id}').status_code, 404)
        self.assertNotIn('测试产品', self.client.get('/library/products').get_data(as_text=True))
        self.assertEqual(self.post('/library/trash', {'kind': 'enterprise', 'id': enterprise_id}).status_code, 302)
        self.assertIn('测试产品', self.client.get(f'/library/enterprises/{enterprise_id}').get_data(as_text=True))
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(Product, product_id))
            self.assertEqual((self.root / Document.query.one().file_path).read_bytes(), b'keep me')

    def test_csrf_required_for_login_and_record_mutation(self):
        self.assertEqual(self.client.post('/登录', data={'用户名': 'admin', '密码': 'admin123'}).status_code, 400)
        self.login()
        self.assertEqual(self.client.post('/library/enterprises/new', data={'company_name': 'unauthorized mutation'}).status_code, 400)
        self.assertEqual(self.client.get('/退出').status_code, 405)

    def test_member_cannot_manage_accounts_backup_or_archive(self):
        self.login(name='user', password='user123')
        enterprise_id, _ = self.enterprise()
        self.assertEqual(self.client.get('/members').status_code, 403)
        self.assertEqual(self.client.get('/library/trash').status_code, 403)
        self.assertEqual(self.post(f'/library/enterprises/{enterprise_id}/archive', {'version_id': 1}).status_code, 403)
        backup = self.client.get('/backup', follow_redirects=True)
        self.assertIn('无备份管理权限', backup.get_data(as_text=True))
        self.assertNotIn('一键备份数据库', backup.get_data(as_text=True))

    def test_password_change_invalidates_other_sessions(self):
        self.login()
        other = self.app.test_client()
        self.login(other)
        response = self.post('/account/password', {'current_password': 'admin123', 'new_password': 'a-long-new-test-password', 'confirm_password': 'a-long-new-test-password'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(other.get('/library').status_code, 302)
        self.assertEqual(self.client.get('/library').status_code, 200)

    def test_member_disable_and_reenable_does_not_revive_old_session(self):
        self.login()
        self.assertEqual(self.post('/members', {'username': 'member01', 'password': 'long-member-test-password'}).status_code, 302)
        member_client = self.app.test_client()
        self.login(member_client, 'member01', 'long-member-test-password')
        with self.app.app_context():
            member_id = User.query.filter_by(username='member01').one().id
        self.post('/members', {'action': 'toggle', 'user_id': member_id})
        self.post('/members', {'action': 'toggle', 'user_id': member_id})
        self.assertEqual(member_client.get('/library').status_code, 302)

    def test_daily_backup_runs_without_request_and_is_idempotent(self):
        self.login()
        self.enterprise(attachments=(BytesIO(b'backup data'), 'backup.txt'))
        with self.app.app_context():
            self.app.extensions['run_daily_backup']()
            self.app.extensions['run_daily_backup']()
            self.assertEqual(BackupRecord.query.filter_by(status='成功').count(), 1)
            self.assertEqual(BackupRecord.query.filter_by(status='失败').count(), 0)
            complete = BackupRecord.query.filter_by(backup_type='complete').one()
            target = self.root / 'restored'
            restore_bundle(self.root / complete.file_path, target)
        with closing(sqlite3.connect(target / 'trade_agent.db')) as connection:
            self.assertEqual(connection.execute('SELECT company_name FROM enterprises').fetchone()[0], '稳定保存测试企业')
            path = connection.execute('SELECT file_path FROM documents').fetchone()[0]
        self.assertEqual((target / path).read_bytes(), b'backup data')

    def test_backup_reads_committed_wal_and_restore_refuses_overwrite(self):
        self.login()
        self.enterprise()
        with self.app.app_context():
            self.assertEqual(db.session.execute(db.text('PRAGMA journal_mode')).scalar(), 'wal')
            output = create_bundle(self.app, self.root / 'complete.zip')
        target = self.root / 'restored'
        restore_bundle(output, target)
        with closing(sqlite3.connect(target / 'trade_agent.db')) as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM enterprises').fetchone()[0], 1)
        with self.assertRaises(ValueError):
            restore_bundle(output, target)

    def test_corrupt_and_path_traversal_backups_are_rejected(self):
        self.login()
        self.enterprise()
        with self.app.app_context():
            create_bundle(self.app, self.root / 'valid.zip')
        with ZipFile(self.root / 'valid.zip') as source, ZipFile(self.root / 'corrupt.zip', 'w') as output:
            for name in source.namelist():
                output.writestr(name, b'corrupt db' if name == 'trade_agent.db' else source.read(name))
        with self.assertRaises(ValueError):
            restore_bundle(self.root / 'corrupt.zip', self.root / 'invalid')
        self.assertFalse((self.root / 'invalid').exists())
        with ZipFile(self.root / 'traversal.zip', 'w') as output:
            output.writestr('manifest.json', json.dumps({'format': 1, 'sha256': {'trade_agent.db': 'x', 'uploads/../../escaped': 'x'}}))
            output.writestr('trade_agent.db', b'x')
            output.writestr('uploads/../../escaped', b'x')
        with self.assertRaises(ValueError):
            restore_bundle(self.root / 'traversal.zip', self.root / 'invalid')
        self.assertFalse((self.root / 'escaped').exists())

    def test_production_requires_secret_and_migrates_default_accounts(self):
        self.login()
        self.enterprise()
        with self.assertRaises(RuntimeError):
            create_app({**self.options, 'PRODUCTION': True, 'SECRET_KEY': None})
        production = create_app({**self.options, 'PRODUCTION': True, 'SECRET_KEY': 'a' * 64})
        with patch.dict('os.environ', {'TRADE_ADMIN_PASSWORD': 'long-production-test-password'}):
            init_db(production)
        with production.app_context():
            self.assertTrue(check_password_hash(User.query.filter_by(username='admin').one().password, 'long-production-test-password'))
            self.assertIsNone(User.query.filter_by(username='user').first())
            self.assertEqual(Enterprise.query.count(), 1)
            db.session.remove()
            db.engine.dispose()

    def test_auxiliary_anonymous_request_does_not_invalidate_login_csrf(self):
        token = self.token(self.client.get('/登录'))
        self.client.get('/favicon.ico', follow_redirects=True)
        response = self.client.post('/登录', data={'csrf_token': token, '用户名': 'admin', '密码': 'admin123'})
        self.assertEqual(response.status_code, 302)

    def test_login_rate_limit(self):
        limited = create_app({**self.options, 'RATELIMIT_ENABLED': True})
        client = limited.test_client()
        token = self.token(client.get('/登录'))
        for _ in range(10):
            result = client.post('/登录', data={'csrf_token': token, '用户名': 'admin', '密码': 'invalid'})
            self.assertEqual(result.status_code, 200)
        self.assertEqual(client.post('/登录', data={'csrf_token': token, '用户名': 'admin', '密码': 'invalid'}).status_code, 429)
        with limited.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_legacy_schema_migration_preserves_data_and_makes_snapshot(self):
        legacy_root = self.root / 'legacy'
        legacy_root.mkdir()
        engine = create_engine(f'sqlite:///{legacy_root}/trade_agent.db')
        metadata = MetaData()
        for table in db.metadata.sorted_tables:
            Table(table.name, metadata, *[column._copy() for column in table.columns if column.name not in {'version_id', 'submission_key'}])
        metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(metadata.tables['enterprises'].insert().values(enterprise_code='OLD001', company_name='原有企业', enterprise_extra_fields={'historical': '保留'}, is_deleted=False))
        engine.dispose()
        legacy_app = create_app({**self.options, 'DATA_ROOT': legacy_root})
        init_db(legacy_app)
        init_db(legacy_app)
        with legacy_app.app_context():
            item = Enterprise.query.one()
            self.assertEqual(item.enterprise_extra_fields['historical'], '保留')
            self.assertEqual(item.company_name, '原有企业')
            self.assertEqual(item.version_id, 1)
            self.assertIn('submission_key', {c['name'] for c in inspect(db.engine).get_columns('enterprises')})
            db.session.remove()
            db.engine.dispose()
        self.assertEqual(len(list((legacy_root / 'backups/database').glob('pre_upgrade_*.sqlite'))), 1)


if __name__ == '__main__':
    unittest.main()
