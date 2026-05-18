from io import BytesIO
from pathlib import Path
import tempfile
import unittest

from werkzeug.datastructures import FileStorage

from app import create_app, init_db, 导入产品Excel
from models import Enterprise, Product, db


class ProductImportDuplicateTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test.db"
        self.app = create_app(
            {
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
                "TESTING": True,
                "BACKUP_ROOT": Path(self.tmpdir.name) / "backups",
                "DATABASE_BACKUP_ROOT": Path(self.tmpdir.name) / "backups" / "database",
                "FILES_BACKUP_ROOT": Path(self.tmpdir.name) / "backups" / "files",
            }
        )
        init_db(self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.enterprise = Enterprise(
            enterprise_code=f"E001-{self._testMethodName}",
            company_name=f"测试企业-{self._testMethodName}",
        )
        db.session.add(self.enterprise)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()
        self.tmpdir.cleanup()

    def _csv_upload(self, content):
        return FileStorage(
            stream=BytesIO(content.encode("utf-8-sig")),
            filename="products.csv",
            content_type="text/csv",
        )

    def test_import_fails_when_product_code_already_exists(self):
        db.session.add(
            Product(
                enterprise_id=self.enterprise.id,
                product_code="P001",
                product_name_cn="已存在产品",
            )
        )
        db.session.commit()

        success, failed = 导入产品Excel(
            self._csv_upload(
                "产品编号,所属企业名称,产品名称\n"
                "P001,测试企业-test_import_fails_when_product_code_already_exists,重复导入产品\n"
            )
        )

        self.assertEqual(success, 0)
        self.assertEqual(len(failed), 1)
        self.assertIn("产品编号已存在", failed[0]["原因"])
        self.assertEqual(Product.query.filter_by(product_code="P001").count(), 1)
        self.assertEqual(
            Product.query.filter_by(product_code="P001").first().product_name_cn,
            "已存在产品",
        )

    def test_import_succeeds_for_new_product_code(self):
        success, failed = 导入产品Excel(
            self._csv_upload(
                "产品编号,所属企业名称,产品名称\n"
                "P002,测试企业-test_import_succeeds_for_new_product_code,新产品\n"
            )
        )

        self.assertEqual(success, 1)
        self.assertEqual(failed, [])
        self.assertEqual(Product.query.filter_by(product_code="P002").count(), 1)


if __name__ == "__main__":
    unittest.main()
