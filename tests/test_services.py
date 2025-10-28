import unittest
from datetime import date
from services.snapshot import SnapshotService
from utils.pdf_viewer import PDFViewer
from pathlib import Path
import os
import tempfile

class TestSnapshotService(unittest.TestCase):
    def setUp(self):
        self.service = SnapshotService()
        # Criar snapshot de teste
        self.snapshot_id = self.service.create_manual_snapshot(
            user_id=1,
            snapshot_date=date.today(),
            binance_value=1000.0,
            ledger_value=2000.0,
            defi_value=3000.0,
            other_value=500.0
        )

    def test_create_snapshot(self):
        """Testa a criação de um novo snapshot"""
        self.assertIsNotNone(self.snapshot_id)
        
        # Verificar se snapshot foi criado corretamente
        snapshot = self.service.get_latest_snapshot(1)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot['total_value'], 6500.0)

    def test_get_user_snapshots(self):
        """Testa a recuperação de snapshots do usuário"""
        snapshots = self.service.get_user_snapshots(1)
        self.assertGreater(len(snapshots), 0)

    def test_get_latest_snapshot(self):
        """Testa a recuperação do snapshot mais recente"""
        snapshot = self.service.get_latest_snapshot(1)
        self.assertIsNotNone(snapshot)
        self.assertIsInstance(snapshot['total_value'], float)

    def tearDown(self):
        # Limpar dados de teste
        if hasattr(self, 'snapshot_id'):
            with self.service.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM t_user_manual_snapshots WHERE snapshot_id = %s",
                    (self.snapshot_id,)
                )
                self.service.conn.commit()


class TestPDFViewer(unittest.TestCase):
    def setUp(self):
        # Criar arquivo PDF temporário para testes
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        
        # Criar PDF simples para teste
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test PDF')

    def test_get_pdf_display_html(self):
        """Testa a geração do HTML para exibição do PDF"""
        viewer = PDFViewer()
        html = viewer.get_pdf_display_html(self.test_pdf_path)
        
        self.assertIsNotNone(html)
        self.assertIn('<iframe', html)
        self.assertIn('application/pdf', html)

    def test_get_pdf_download_link(self):
        """Testa a geração do link de download do PDF"""
        viewer = PDFViewer()
        link = viewer.get_pdf_download_link(self.test_pdf_path, "Download Test")
        
        self.assertIsNotNone(link)
        self.assertIn('download="test.pdf"', link)
        self.assertIn('Download Test', link)

    def test_nonexistent_file(self):
        """Testa comportamento com arquivo inexistente"""
        viewer = PDFViewer()
        html = viewer.get_pdf_display_html("nonexistent.pdf")
        self.assertIsNone(html)
        
        link = viewer.get_pdf_download_link("nonexistent.pdf", "Download")
        self.assertIsNone(link)

    def tearDown(self):
        # Limpar arquivos temporários
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
        os.rmdir(self.temp_dir)


if __name__ == '__main__':
    unittest.main()