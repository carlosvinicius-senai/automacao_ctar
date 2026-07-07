import os
import shutil
import tempfile
import unittest
from main import CTARAutomationApp
import tkinter as tk

class TestCTARLogic(unittest.TestCase):
    def setUp(self):
        # Criar diretórios temporários para simular o ambiente
        self.test_dir = tempfile.mkdtemp()
        self.dir_gravacoes = os.path.join(self.test_dir, "gravacoes")
        self.dir_documentos = os.path.join(self.test_dir, "documentos")
        self.dir_destino = os.path.join(self.test_dir, "destino_sharepoint")
        
        os.makedirs(self.dir_gravacoes)
        os.makedirs(self.dir_documentos)
        os.makedirs(self.dir_destino)
        
        # Inicializar o Tkinter e a classe do App (sem rodar o mainloop)
        self.root = tk.Tk()
        self.app = CTARAutomationApp(self.root)
        
        # Definir as pastas nas variáveis do app
        self.app.dir_gravacoes.set(self.dir_gravacoes)
        self.app.dir_documentos.set(self.dir_documentos)
        self.app.dir_destino.set(self.dir_destino)

    def tearDown(self):
        # Destruir a janela e limpar arquivos temporários
        self.root.destroy()
        shutil.rmtree(self.test_dir)

    def test_parse_ctar_filename_examples(self):
        # Exemplo 1: [CTAR] ID 1282 | Mangotex | Desenvolvimento
        f1 = "[CTAR] ID 1282 | Mangotex | Desenvolvimento"
        p1 = self.app.parse_ctar_filename(f1)
        self.assertIsNotNone(p1)
        self.assertEqual(p1[0], "1282")
        self.assertEqual(p1[1], "Mangotex")
        
        # Exemplo 2: Gravação da Reunião_CTAR (ID 1318) - Shell.mp4
        f2 = "Gravação da Reunião_CTAR (ID 1318) - Shell.mp4"
        p2 = self.app.parse_ctar_filename(f2)
        self.assertIsNotNone(p2)
        self.assertEqual(p2[0], "1318")
        self.assertEqual(p2[1], "Shell")
        
        # Exemplo 3: Reunião Geral CTAR - ID 5544 - Petrobras - Final.vtt
        f3 = "Reunião Geral CTAR - ID 5544 - Petrobras - Final.vtt"
        p3 = self.app.parse_ctar_filename(f3)
        self.assertIsNotNone(p3)
        self.assertEqual(p3[0], "5544")
        self.assertEqual(p3[1], "Petrobras")
        
        # Exemplo 4: ID 9090 Klabin Discussão Técnica
        f4 = "ID 9090 Klabin Discussão Técnica"
        p4 = self.app.parse_ctar_filename(f4)
        self.assertIsNotNone(p4)
        self.assertEqual(p4[0], "9090")
        self.assertEqual(p4[1], "Klabin")

        # Exemplo de Gravação com bug fixado de pipe: [CTAR] ID 1482 - Hovercraft | AERONAVAL | IA Modelagem.mp4
        f5 = "[CTAR] ID 1482 - Hovercraft | AERONAVAL | IA Modelagem.mp4"
        p5 = self.app.parse_ctar_filename(f5)
        self.assertIsNotNone(p5)
        self.assertEqual(p5[0], "1482")
        self.assertEqual(p5[1], "AERONAVAL")

        # Exemplo de Gravação simples sem pipe: [CTAR] ID 1724 - Systemac - IA Modelagem Estruturas Metálicas.mp4
        f6 = "[CTAR] ID 1724 - Systemac - IA Modelagem Estruturas Metálicas.mp4"
        p6 = self.app.parse_ctar_filename(f6)
        self.assertIsNotNone(p6)
        self.assertEqual(p6[0], "1724")
        self.assertEqual(p6[1], "Systemac")


    def test_parse_ctar_filename_invalid(self):
        # Nome sem ID
        filename = "[CTAR] Systemac - IA Modelagem.mp4"
        parsed = self.app.parse_ctar_filename(filename)
        self.assertIsNone(parsed)

    def test_process_file_recording(self):
        # Simular arquivo de gravação de entrada
        src_file = os.path.join(self.dir_gravacoes, "[CTAR] ID 1724 - Systemac - IA Modelagem Estruturas Metálicas.mp4")
        with open(src_file, 'wb') as f:
            f.write(b"video content data dummy")
            
        # Processar o arquivo
        self.app.process_file(src_file, "gravacoes")
        
        # Verificar se o arquivo foi movido para o destino correto com o nome correto
        expected_folder = os.path.join(self.dir_destino, "Systemac (ID 1724)")
        expected_file = os.path.join(expected_folder, "Gravação CTAR (ID 1724) - Systemac.mp4")
        
        self.assertTrue(os.path.exists(expected_folder))
        self.assertTrue(os.path.exists(expected_file))
        self.assertFalse(os.path.exists(src_file)) # Deve ter sido movido (removido da origem)

    def test_process_file_transcription_and_presence(self):
        # Simular arquivo de transcrição
        src_trans = os.path.join(self.dir_documentos, "[CTAR] ID 1482 - AERONAVAL - Transcrição.docx")
        with open(src_trans, 'wb') as f:
            f.write(b"transcription content data dummy")
            
        # Simular arquivo de presença
        src_pres = os.path.join(self.dir_documentos, "[CTAR] ID 1482 - AERONAVAL - Presença.csv")
        with open(src_pres, 'wb') as f:
            f.write(b"presence list content data dummy")
            
        # Processar ambos
        self.app.process_file(src_trans, "documentos")
        self.app.process_file(src_pres, "documentos")
        
        # Verificar resultados no destino
        expected_folder = os.path.join(self.dir_destino, "AERONAVAL (ID 1482)")
        expected_trans_file = os.path.join(expected_folder, "Transcrição CTAR (ID 1482) - AERONAVAL.docx")
        expected_pres_file = os.path.join(expected_folder, "Presença CTAR (ID 1482) - AERONAVAL.csv")
        
        self.assertTrue(os.path.exists(expected_folder))
        self.assertTrue(os.path.exists(expected_trans_file))
        self.assertTrue(os.path.exists(expected_pres_file))
        self.assertFalse(os.path.exists(src_trans))
        self.assertFalse(os.path.exists(src_pres))

if __name__ == "__main__":
    unittest.main()
