import gc
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
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
        
        # Evitar thread de verificação de atualizações em rede durante testes
        self._update_patcher = patch.object(CTARAutomationApp, "check_for_updates", return_value=None)
        self._update_patcher.start()

        # Inicializar o Tkinter e a classe do App (sem rodar o mainloop)
        self.root = tk.Tk()
        self.app = CTARAutomationApp(self.root)
        
        # Definir as pastas nas variáveis do app
        self.app.dir_gravacoes.set(self.dir_gravacoes)
        self.app.dir_documentos.set(self.dir_documentos)
        self.app.dir_destino.set(self.dir_destino)

    def tearDown(self):
        # Destruir referências e coletar StringVars na thread principal antes de destruir o Tk
        self.app = None
        gc.collect()
        self.root.destroy()
        self._update_patcher.stop()
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
        self.assertEqual(p8[1], "ISA ENERGIA")

        # Exemplo 9: ID no início com underline como delimitador
        f9 = "[CTAR] ID 1726 _ Systemac _ Tintas sem primer base água  (1).mp4"
        p9 = self.app.parse_ctar_filename(f9)
        self.assertIsNotNone(p9)
        self.assertEqual(p9[0], "1726")
        self.assertEqual(p9[1], "Systemac")

        # Exemplo 10: Espaços duplos e parênteses (Votorantim)
        f10 = "[CTAR] ID 1495  SIQLO TECH (Votorantim)  VOD para Mineração-20260716_080826-Gravação de Reunião.mp4"
        p10 = self.app.parse_ctar_filename(f10)
        self.assertIsNotNone(p10)
        self.assertEqual(p10[0], "1495")
        self.assertEqual(p10[1], "SIQLO TECH")

        # Exemplo 11: Espaços duplos e assunto complexo
        f11 = "[CTAR] ID 1296  Moinho  Biopolímero - Resistência ao Calor-20260714_162547-Gravação de Reunião.mp4"
        p11 = self.app.parse_ctar_filename(f11)
        self.assertIsNotNone(p11)
        self.assertEqual(p11[0], "1296")
        self.assertEqual(p11[1], "Moinho")

        # Exemplo 12: Espaços duplos e CSN Cimentos
        f12 = "[CTAR] ID 1599  CSN Cimentos  Concretos Nanoaditivos-20260714_151305-Gravação de Reunião.mp4"
        p12 = self.app.parse_ctar_filename(f12)
        self.assertIsNotNone(p12)
        self.assertEqual(p12[0], "1599")
        self.assertEqual(p12[1], "CSN Cimentos")

        # Exemplo 13: Espaços duplos e ANJUNA TECH
        f13 = "[CTAR] ID 1591  ANJUNA TECH  AGENTIC-I Plataforma Nacional de IA-20260707_150957-Gravação de Reunião.mp4"
        p13 = self.app.parse_ctar_filename(f13)
        self.assertIsNotNone(p13)
        self.assertEqual(p13[0], "1591")
        self.assertEqual(p13[1], "ANJUNA TECH")

        # Exemplo 14: Espaços duplos e LEPRI
        f14 = "[CTAR] ID 1585  LEPRI  Formulação Cerâmica com Vidro Reciclado.mp4"
        p14 = self.app.parse_ctar_filename(f14)
        self.assertIsNotNone(p14)
        self.assertEqual(p14[0], "1585")
        self.assertEqual(p14[1], "LEPRI")


    def _create_hub_project(self, company, project_folder, create_category=True, create_ctar=True):
        project_path = os.path.join(self.dir_destino, company, project_folder)
        os.makedirs(project_path, exist_ok=True)
        if create_category:
            cat_path = os.path.join(project_path, "03 – Propostas e Orçamentos")
            os.makedirs(cat_path, exist_ok=True)
            if create_ctar:
                os.makedirs(os.path.join(cat_path, "CTAR"), exist_ok=True)
            return cat_path
        return project_path

    def test_parse_new_hub_filename_patterns(self):
        # Padrão com espaços duplos (sanitização de | pelo Windows/Teams)
        p1 = self.app.parse_ctar_filename(
            "2062  ADVANTAG  Plataforma RFID para rastrear fluxo produtivo-20260716_080826-Gravação de Reunião.mp4"
        )
        self.assertIsNotNone(p1)
        self.assertEqual(p1[0], "2062")
        self.assertEqual(p1[1], "ADVANTAG")
        self.assertEqual(p1[3], ".mp4")
        self.assertEqual(self.app.get_ctar_subfolder("2062  ADVANTAG  Plataforma.mp4"), "1º CTAR")

        # Padrão com pipe literal
        p2 = self.app.parse_ctar_filename("2062 | ADVANTAG | Plataforma RFID.docx")
        self.assertIsNotNone(p2)
        self.assertEqual(p2[0], "2062")
        self.assertEqual(p2[1], "ADVANTAG")
        self.assertIn("Plataforma RFID", p2[2])

        # Padrão com hífen e rodada explícita (2º)
        p3 = self.app.parse_ctar_filename("2º 2062 - ADVANTAG - Plataforma RFID.mp4")
        self.assertIsNotNone(p3)
        self.assertEqual(p3[0], "2062")
        self.assertEqual(p3[1], "ADVANTAG")
        self.assertEqual(self.app.get_ctar_subfolder("2º 2062 - ADVANTAG - Plataforma RFID.mp4"), "2º CTAR")

        # Padrão com prefixo CTAR sem palavra "ID" (ex: CTAR 1925 _ SINDICERCON _ Bloco Acústico de Vedação.docx)
        p4 = self.app.parse_ctar_filename("CTAR 1925 _ SINDICERCON _ Bloco Acústico de Vedação.docx")
        self.assertIsNotNone(p4)
        self.assertEqual(p4[0], "1925")
        self.assertEqual(p4[1], "SINDICERCON")
        self.assertEqual(p4[2], "Bloco Acústico de Vedação")
        self.assertEqual(p4[3], ".docx")
        self.assertEqual(
            self.app.get_ctar_subfolder("CTAR 1925 _ SINDICERCON _ Bloco Acústico de Vedação.docx"),
            "1º CTAR",
        )
        self.assertEqual(
            self.app.get_ctar_subfolder("2º CTAR 1925 _ SINDICERCON _ Bloco Acústico de Vedação.docx"),
            "2º CTAR",
        )

    def test_parse_ctar_filename_invalid(self):
        # Nome sem ID
        filename = "[CTAR] Systemac - IA Modelagem.mp4"
        parsed = self.app.parse_ctar_filename(filename)
        self.assertIsNone(parsed)

    def test_process_file_recording_2062_single_project(self):
        cat_path = self._create_hub_project("ADVANTAG", "2062 - ADVANTAG - Plataforma RFID")
        src_file = os.path.join(self.dir_gravacoes, "2062  ADVANTAG  Plataforma RFID.mp4")
        with open(src_file, 'wb') as f:
            f.write(b"video content data dummy")

        self.app.process_file(src_file, "gravacoes")

        expected_file = os.path.join(cat_path, "CTAR", "1º CTAR", "Gravação CTAR (ID 2062) - ADVANTAG.mp4")
        self.assertTrue(os.path.exists(expected_file))
        self.assertTrue(os.path.exists(src_file))

    def test_process_file_transcription_and_presence(self):
        cat_path = self._create_hub_project("AERONAVAL", "1482 - AERONAVAL - Hovercraft")
        src_trans = os.path.join(self.dir_documentos, "1482  AERONAVAL  Transcrição.docx")
        with open(src_trans, 'wb') as f:
            f.write(b"transcription content data dummy")

        src_pres = os.path.join(self.dir_documentos, "1482  AERONAVAL  Presença.csv")
        with open(src_pres, 'wb') as f:
            f.write(b"presence list content data dummy")

        self.app.process_file(src_trans, "documentos")
        self.app.process_file(src_pres, "documentos")

        expected_trans = os.path.join(cat_path, "CTAR", "1º CTAR", "Transcrição CTAR (ID 1482) - AERONAVAL.docx")
        expected_pres = os.path.join(cat_path, "CTAR", "1º CTAR", "Presença CTAR (ID 1482) - AERONAVAL.csv")
        self.assertTrue(os.path.exists(expected_trans))
        self.assertTrue(os.path.exists(expected_pres))
        self.assertTrue(os.path.exists(src_trans))
        self.assertTrue(os.path.exists(src_pres))

    def test_ignore_existing_files_at_startup(self):
        cat_lepri = self._create_hub_project("LEPRI", "1585 - LEPRI - Cerâmica")
        cat_anjuna = self._create_hub_project("ANJUNA TECH", "1591 - ANJUNA TECH - AGENTIC-I")

        pre_file = os.path.join(self.dir_gravacoes, "1585  LEPRI  Gravacao.mp4")
        with open(pre_file, 'wb') as f:
            f.write(b"pre-existing recording content")

        self.app.start_monitoring()
        self.app._scan_folder(self.dir_gravacoes, "gravacoes")

        expected_pre = os.path.join(cat_lepri, "CTAR", "1º CTAR", "Gravação CTAR (ID 1585) - LEPRI.mp4")
        self.assertFalse(os.path.exists(expected_pre))

        new_file = os.path.join(self.dir_gravacoes, "1591  ANJUNA TECH  Meeting.mp4")
        with open(new_file, 'wb') as f:
            f.write(b"new recording content")

        self.app._scan_folder(self.dir_gravacoes, "gravacoes")

        expected_new = os.path.join(cat_anjuna, "CTAR", "1º CTAR", "Gravação CTAR (ID 1591) - ANJUNA TECH.mp4")
        self.assertTrue(os.path.exists(expected_new))
        self.app.stop_monitoring()

    def test_do_not_overwrite_existing_target_file(self):
        cat_path = self._create_hub_project("Systemac", "1724 - Systemac - IA Modelagem")
        dest_folder = os.path.join(cat_path, "CTAR", "1º CTAR")
        os.makedirs(dest_folder, exist_ok=True)
        dest_file = os.path.join(dest_folder, "Gravação CTAR (ID 1724) - Systemac.mp4")
        with open(dest_file, 'wb') as f:
            f.write(b"original sharepoint content")

        src_file = os.path.join(self.dir_gravacoes, "1724  Systemac  IA Modelagem.mp4")
        with open(src_file, 'wb') as f:
            f.write(b"new local video content")

        self.app.process_file(src_file, "gravacoes")

        with open(dest_file, 'rb') as f:
            self.assertEqual(f.read(), b"original sharepoint content")

    def test_ctar_subfolders_rounds(self):
        cat_path = self._create_hub_project("Systemac", "1724 - Systemac - IA Modelagem")
        src_file2 = os.path.join(self.dir_gravacoes, "2º 1724  Systemac  IA Modelagem.mp4")
        with open(src_file2, 'wb') as f:
            f.write(b"2nd video dummy")

        self.app.process_file(src_file2, "gravacoes")

        expected_file2 = os.path.join(cat_path, "CTAR", "2º CTAR", "Gravação CTAR (ID 1724) - Systemac.mp4")
        self.assertTrue(os.path.exists(expected_file2))

    def test_company_with_multiple_projects(self):
        cat_1890 = self._create_hub_project("ADVANTAG", "1890 - ADVANTAG - Projeto Antigo")
        cat_2062 = self._create_hub_project("ADVANTAG", "2062 - ADVANTAG - Plataforma RFID")
        cat_2501 = self._create_hub_project("ADVANTAG", "2501 - ADVANTAG - Outro Projeto")

        src_file = os.path.join(self.dir_gravacoes, "2062  ADVANTAG  Plataforma RFID.mp4")
        with open(src_file, 'wb') as f:
            f.write(b"rfid video")

        self.app.process_file(src_file, "gravacoes")

        self.assertTrue(os.path.exists(os.path.join(cat_2062, "CTAR", "1º CTAR", "Gravação CTAR (ID 2062) - ADVANTAG.mp4")))
        self.assertFalse(os.path.exists(os.path.join(cat_1890, "CTAR", "1º CTAR", "Gravação CTAR (ID 2062) - ADVANTAG.mp4")))
        self.assertFalse(os.path.exists(os.path.join(cat_2501, "CTAR", "1º CTAR", "Gravação CTAR (ID 2062) - ADVANTAG.mp4")))

    def test_varied_id_lengths_and_formats(self):
        cases = [
            ("5", "5 - EMPRESA - Um digito"),
            ("15", "15 - EMPRESA - Dois digitos"),
            ("247", "247 - EMPRESA - Tres digitos"),
            ("2062", "ID2062 - EMPRESA - Quatro digitos"),
            ("12543", "012543 - EMPRESA - Cinco digitos com zero"),
            ("123456", "123456 - EMPRESA - Seis digitos"),
        ]
        for project_id, folder_name in cases:
            self._create_hub_project("EMPRESA", folder_name)

        for project_id, folder_name in cases:
            src_file = os.path.join(self.dir_gravacoes, f"{project_id}  EMPRESA  Projeto Teste.mp4")
            with open(src_file, 'wb') as f:
                f.write(b"data")
            self.app.process_file(src_file, "gravacoes")
            expected = os.path.join(
                self.dir_destino, "EMPRESA", folder_name, "03 – Propostas e Orçamentos", "CTAR", "1º CTAR",
                f"Gravação CTAR (ID {project_id}) - EMPRESA.mp4"
            )
            self.assertTrue(os.path.exists(expected), f"Falha para ID {project_id}")

    def test_id_substring_false_positive_12062_and_20620(self):
        cat_12062 = self._create_hub_project("ADVANTAG", "12062 - ADVANTAG - Projeto Maior")
        cat_20620 = self._create_hub_project("ADVANTAG", "20620 - ADVANTAG - Projeto Sufixo")

        src_file = os.path.join(self.dir_gravacoes, "2062  ADVANTAG  Plataforma RFID.mp4")
        with open(src_file, 'wb') as f:
            f.write(b"rfid video")

        self.app.process_file(src_file, "gravacoes")

        self.assertFalse(os.path.exists(os.path.join(cat_12062, "CTAR", "1º CTAR", "Gravação CTAR (ID 2062) - ADVANTAG.mp4")))
        self.assertFalse(os.path.exists(os.path.join(cat_20620, "CTAR", "1º CTAR", "Gravação CTAR (ID 2062) - ADVANTAG.mp4")))
        self.assertEqual(len(self.app.processed_files), 0)

    def test_id_not_found_and_duplicate_id_abort(self):
        # ID inexistente
        self._create_hub_project("ADVANTAG", "9999 - ADVANTAG - Outro")
        src_missing = os.path.join(self.dir_gravacoes, "2062  ADVANTAG  Plataforma RFID.mp4")
        with open(src_missing, 'wb') as f:
            f.write(b"rfid video")
        self.app.process_file(src_missing, "gravacoes")
        self.assertEqual(len(self.app.processed_files), 0)

        # ID duplicado
        cat_a = self._create_hub_project("DUPLICADA", "2062 - DUPLICADA - Projeto A")
        cat_b = self._create_hub_project("DUPLICADA", "ID 2062 - DUPLICADA - Projeto B")
        src_dup = os.path.join(self.dir_gravacoes, "2062  DUPLICADA  Reunião.mp4")
        with open(src_dup, 'wb') as f:
            f.write(b"dup video")
        self.app.process_file(src_dup, "gravacoes")
        self.assertFalse(os.path.exists(os.path.join(cat_a, "CTAR", "1º CTAR", "Gravação CTAR (ID 2062) - DUPLICADA.mp4")))
        self.assertFalse(os.path.exists(os.path.join(cat_b, "CTAR", "1º CTAR", "Gravação CTAR (ID 2062) - DUPLICADA.mp4")))

    def test_company_not_found_and_category_03_missing(self):
        # Empresa inexistente não cria pasta na raiz
        src_no_comp = os.path.join(self.dir_gravacoes, "2062  INEXISTENTE  Projeto.mp4")
        with open(src_no_comp, 'wb') as f:
            f.write(b"data")
        self.app.process_file(src_no_comp, "gravacoes")
        self.assertFalse(os.path.exists(os.path.join(self.dir_destino, "INEXISTENTE")))

        # 03 – Propostas e Orçamentos inexistente não cria categoria
        proj_path = self._create_hub_project("ADVANTAG", "2062 - ADVANTAG - Sem Categoria", create_category=False)
        src_no_cat = os.path.join(self.dir_gravacoes, "2062  ADVANTAG  Projeto.mp4")
        with open(src_no_cat, 'wb') as f:
            f.write(b"data")
        self.app.process_file(src_no_cat, "gravacoes")
        self.assertFalse(os.path.exists(os.path.join(proj_path, "03 – Propostas e Orçamentos")))

    def test_auto_create_ctar_subfolder_when_missing(self):
        cat_path = self._create_hub_project("ADVANTAG", "2062 - ADVANTAG - Plataforma RFID", create_category=True, create_ctar=False)
        self.assertFalse(os.path.exists(os.path.join(cat_path, "CTAR")))

        src_file = os.path.join(self.dir_gravacoes, "2062  ADVANTAG  Plataforma RFID.mp4")
        with open(src_file, 'wb') as f:
            f.write(b"rfid video")
        self.app.process_file(src_file, "gravacoes")

        expected_file = os.path.join(cat_path, "CTAR", "1º CTAR", "Gravação CTAR (ID 2062) - ADVANTAG.mp4")
        self.assertTrue(os.path.exists(expected_file))

    def test_permission_error_and_copy_failure(self):
        self._create_hub_project("ADVANTAG", "2062 - ADVANTAG - Plataforma RFID")
        src_file = os.path.join(self.dir_gravacoes, "2062  ADVANTAG  Plataforma RFID.mp4")
        with open(src_file, 'wb') as f:
            f.write(b"rfid video")

        # Erro de permissão ao listar diretórios do Hub
        with patch.object(self.app, "_list_subdirs", side_effect=PermissionError("Acesso negado")):
            self.app.process_file(src_file, "gravacoes")
        self.assertEqual(len(self.app.processed_files), 0)
        self.assertTrue(len(self.app.failed_files) > 0)

        self.app.failed_files.clear()

        # Falha de cópia / upload
        with patch("main.shutil.copy2", side_effect=OSError("Falha de rede")):
            self.app.process_file(src_file, "gravacoes")
        self.assertEqual(len(self.app.processed_files), 0)
        self.assertTrue(len(self.app.failed_files) > 0)

    def test_retry_after_creating_missing_category_folder(self):
        proj_path = self._create_hub_project("SINDICERCON", "ID 1925 - SINDICERCON - Bloco Acústico de Vedação", create_category=False)
        src_file = os.path.join(self.dir_documentos, "CTAR 1925 _ SINDICERCON _ Bloco Acústico de Vedação.docx")
        with open(src_file, 'wb') as f:
            f.write(b"docx content")

        self.app.is_monitoring = True
        self.app._scan_folder(self.dir_documentos, "documentos")
        self.assertEqual(len(self.app.failed_files), 1)
        self.assertEqual(len(self.app.processed_files), 0)

        # Criar a pasta 03 – Propostas e Orçamentos e acionar Tentar novamente
        cat_path = os.path.join(proj_path, "03 – Propostas e Orçamentos")
        os.makedirs(cat_path, exist_ok=True)
        self.app.retry_failed_files()
        self.app._scan_folder(self.dir_documentos, "documentos")
        self.app.is_monitoring = False

        expected_file = os.path.join(cat_path, "CTAR", "1º CTAR", "Transcrição CTAR (ID 1925) - SINDICERCON.docx")
        self.assertTrue(os.path.exists(expected_file))
        self.assertEqual(len(self.app.failed_files), 0)

if __name__ == "__main__":
    unittest.main()
