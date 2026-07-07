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

        # Exemplo 7: ID no final com hifens normais e termos descritivos
        f7 = "ISA ENERGIA - Capina Biológica - Gravação (ID 1720).mp4"
        p7 = self.app.parse_ctar_filename(f7)
        self.assertIsNotNone(p7)
        self.assertEqual(p7[0], "1720")
        self.assertEqual(p7[1], "ISA ENERGIA")

        # Exemplo 8: ID no final com hifens soltos/colados e termos descritivos
        f8 = "ISA ENERGIA Capina Biológica- -Gravação (ID 1720).mp4"
        p8 = self.app.parse_ctar_filename(f8)
        self.assertIsNotNone(p8)
        self.assertEqual(p8[0], "1720")
        self.assertEqual(p8[1], "ISA ENERGIA Capina Biológica")


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
        
        # Verificar se o arquivo foi copiado para o destino correto com o nome correto
        expected_folder = os.path.join(self.dir_destino, "Systemac (ID 1724)")
        expected_file = os.path.join(expected_folder, "Gravação CTAR (ID 1724) - Systemac.mp4")
        
        self.assertTrue(os.path.exists(expected_folder))
        self.assertTrue(os.path.exists(expected_file))
        self.assertTrue(os.path.exists(src_file)) # Deve ter sido COPIADO (permanece na origem)

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
        self.assertTrue(os.path.exists(src_trans)) # Permanece na origem
        self.assertTrue(os.path.exists(src_pres)) # Permanece na origem

    def test_ignore_existing_files_at_startup(self):
        # 1. Simular um arquivo pré-existente na pasta de gravações
        pre_file = os.path.join(self.dir_gravacoes, "[CTAR] ID 1585 - LEPRI - Gravacao.mp4")
        with open(pre_file, 'wb') as f:
            f.write(b"pre-existing recording content")
            
        # 2. Iniciar monitoramento (popula processed_files com o pre_file)
        self.app.start_monitoring()
        
        # 3. Rodar scan_folder na pasta de gravações
        self.app._scan_folder(self.dir_gravacoes, "gravacoes")
        
        # 4. Verificar que o arquivo pré-existente NÃO foi copiado para o destino
        expected_folder_pre = os.path.join(self.dir_destino, "LEPRI (ID 1585)")
        expected_file_pre = os.path.join(expected_folder_pre, "Gravação CTAR (ID 1585) - LEPRI.mp4")
        self.assertFalse(os.path.exists(expected_folder_pre))
        self.assertFalse(os.path.exists(expected_file_pre))
        
        # 5. Adicionar um NOVO arquivo na pasta de gravações (após o início)
        new_file = os.path.join(self.dir_gravacoes, "[CTAR] ID 1591 - ANJUNA TECH - Meeting.mp4")
        with open(new_file, 'wb') as f:
            f.write(b"new recording content")
            
        # 6. Rodar scan_folder novamente
        self.app._scan_folder(self.dir_gravacoes, "gravacoes")
        
        # 7. Verificar que o NOVO arquivo foi copiado com sucesso e o original continua lá
        expected_folder_new = os.path.join(self.dir_destino, "ANJUNA TECH (ID 1591)")
        expected_file_new = os.path.join(expected_folder_new, "Gravação CTAR (ID 1591) - ANJUNA TECH.mp4")
        
        self.assertTrue(os.path.exists(expected_folder_new))
        self.assertTrue(os.path.exists(expected_file_new))
        self.assertTrue(os.path.exists(new_file))
        
        # 8. Finalizar monitoramento de forma limpa
        self.app.stop_monitoring()

    def test_do_not_overwrite_existing_target_file(self):
        # 1. Simular uma pasta e um arquivo já existentes no destino
        dest_folder = os.path.join(self.dir_destino, "Systemac (ID 1724)")
        os.makedirs(dest_folder, exist_ok=True)
        dest_file = os.path.join(dest_folder, "Gravação CTAR (ID 1724) - Systemac.mp4")
        with open(dest_file, 'wb') as f:
            f.write(b"original sharepoint content")
            
        # 2. Criar um arquivo novo na origem com o mesmo nome
        src_file = os.path.join(self.dir_gravacoes, "[CTAR] ID 1724 - Systemac - IA Modelagem.mp4")
        with open(src_file, 'wb') as f:
            f.write(b"new local video content")
            
        # 3. Processar
        self.app.process_file(src_file, "gravacoes")
        
        # 4. Verificar que o conteúdo do arquivo no destino permanece inalterado (não foi sobrescrito)
        with open(dest_file, 'rb') as f:
            content = f.read()
        self.assertEqual(content, b"original sharepoint content")
        self.assertTrue(os.path.exists(src_file))

if __name__ == "__main__":
    unittest.main()
