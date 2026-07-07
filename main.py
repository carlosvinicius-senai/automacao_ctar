import os
import sys
import re
import time
import json
import shutil
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext

CONFIG_FILE = "config.json"

class CTARAutomationApp:
    VERSION = "1.0.2"

    def __init__(self, root):
        self.root = root
        self.root.title("Automação de Gravações e Documentos CTAR")
        self.root.geometry("800x780")
        self.root.minsize(780, 720)
        
        # Carregar Ícone do App
        ico_path = 'app_icon.ico'
        if hasattr(sys, '_MEIPASS'):
            ico_path = os.path.join(sys._MEIPASS, 'app_icon.ico')
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass
        
        # Paleta de Cores (Premium Dashboard)
        self.color_bg = "#F8FAFC"            # Cinza azulado muito claro (Fundo principal)
        self.color_card_bg = "#FFFFFF"       # Branco para os cartões
        self.color_border = "#E2E8F0"        # Cinza claro para bordas
        
        self.color_primary = "#D72042"       # Vermelho Cereja (Botão Iniciar, Títulos)
        self.color_orange_neon = "#FF3300"   # Laranja Neon (Erros, Parar)
        self.color_slate = "#0F172A"         # Slate Escuro para texto principal
        self.color_muted = "#64748B"         # Slate Muted para subtítulos e rótulos
        self.color_white = "#FFFFFF"
        self.color_input_bg = "#F8FAFC"      # Fundo do campo de texto
        self.color_button_secondary = "#F1F5F9" # Fundo do botão Buscar
        
        # Terminal Log Colors
        self.color_term_bg = "#1E222B"       # Preto/Cinza Terminal
        self.color_term_fg = "#ABB2BF"       # Texto cinza claro
        
        # Configurar background da janela principal
        self.root.configure(bg=self.color_bg)
        
        # Variáveis de Configuração
        self.dir_gravacoes = tk.StringVar()
        self.dir_documentos = tk.StringVar()
        self.dir_destino = tk.StringVar()
        
        # Estado do Monitoramento
        self.is_monitoring = False
        self.monitor_thread = None
        self.ignored_files = set()
        self.processed_files = set()
        
        # Inicializar UI
        self.create_widgets()
        
        # Carregar Configuração Existente
        self.load_config()
        
        # Configurar fechamento seguro
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Iniciar verificação de atualizações em segundo plano
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def create_widgets(self):
        # --- 1. CABEÇALHO (Header) ---
        header_frame = tk.Frame(self.root, bg=self.color_white, pady=15, padx=25, bd=0)
        header_frame.pack(fill=tk.X)
        
        # Divisor inferior do cabeçalho
        header_divider = tk.Frame(self.root, bg=self.color_border, height=1)
        header_divider.pack(fill=tk.X)
        
        # Ícone Redondo em Canvas no Cabeçalho (Emoji 🔄 sobre círculo vermelho)
        self.icon_canvas = tk.Canvas(header_frame, width=40, height=40, bg=self.color_white, highlightthickness=0)
        self.icon_canvas.pack(side=tk.LEFT, padx=(0, 15))
        self.icon_canvas.create_oval(2, 2, 38, 38, fill=self.color_primary, outline="")
        self.icon_canvas.create_text(20, 20, text="🔄", font=("Segoe UI Emoji", 14))
        
        # Títulos do Cabeçalho
        title_info_frame = tk.Frame(header_frame, bg=self.color_white)
        title_info_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        lbl_title = tk.Label(
            title_info_frame, 
            text="Automação de Gravações e Documentos CTAR", 
            font=("Segoe UI", 14, "bold"), 
            fg=self.color_slate, 
            bg=self.color_white,
            anchor="w"
        )
        lbl_title.pack(anchor="w")
        
        lbl_subtitle = tk.Label(
            title_info_frame, 
            text="Sincronização automática de gravações e documentos com o SharePoint", 
            font=("Segoe UI", 9), 
            fg=self.color_muted, 
            bg=self.color_white,
            anchor="w"
        )
        lbl_subtitle.pack(anchor="w")
        
        # Badge de Status Rápido no Cabeçalho (Pill)
        self.pill_status_frame = tk.Frame(header_frame, bg="#F1F5F9", padx=12, pady=4)
        self.pill_status_frame.pack(side=tk.RIGHT, pady=5)
        self.lbl_pill_status = tk.Label(
            self.pill_status_frame, 
            text="● Parado", 
            font=("Segoe UI", 8, "bold"), 
            fg=self.color_muted, 
            bg="#F1F5F9"
        )
        self.lbl_pill_status.pack()
        
        # --- CORPO PRINCIPAL ---
        body_frame = tk.Frame(self.root, bg=self.color_bg, padx=25, pady=20)
        body_frame.pack(fill=tk.BOTH, expand=True)
        
        # Card de Configuração de Diretórios (Borda fina cinza)
        dir_card = tk.Frame(body_frame, bg=self.color_card_bg, bd=1, highlightthickness=1, highlightbackground=self.color_border)
        dir_card.pack(fill=tk.X, pady=(0, 20))
        
        # Padding interno do cartão
        dir_card_content = tk.Frame(dir_card, bg=self.color_card_bg, padx=20, pady=20)
        dir_card_content.pack(fill=tk.BOTH, expand=True)
        
        lbl_section_title = tk.Label(
            dir_card_content, 
            text="CONFIGURAÇÃO DE DIRETÓRIOS", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.color_slate, 
            bg=self.color_card_bg
        )
        lbl_section_title.pack(anchor="w", pady=(0, 15))
        
        # Métodos de desenho para os ícones usando Emojis Coloridos em Canvas
        def draw_camera_emoji(canvas):
            canvas.create_oval(1, 1, 31, 31, fill="#FDF2F4", outline="")
            canvas.create_text(16, 16, text="🎥", font=("Segoe UI Emoji", 12))
            
        def draw_document_emoji(canvas):
            canvas.create_oval(1, 1, 31, 31, fill="#FDF2F4", outline="")
            canvas.create_text(16, 16, text="📄", font=("Segoe UI Emoji", 12))
            
        def draw_cloud_emoji(canvas):
            canvas.create_oval(1, 1, 31, 31, fill="#F0F5FF", outline="")
            canvas.create_text(16, 16, text="☁", font=("Segoe UI Emoji", 12))

        # Helper para criar os sub-cards de entrada
        def create_directory_row(parent, title_text, subtitle_text, var_path, draw_func):
            row_card = tk.Frame(parent, bg=self.color_card_bg, bd=1, highlightthickness=1, highlightbackground=self.color_border)
            row_card.pack(fill=tk.X, pady=6)
            
            row_padding = tk.Frame(row_card, bg=self.color_white, padx=15, pady=12)
            row_padding.pack(fill=tk.BOTH, expand=True)
            
            # Linha superior: Ícone, Título e Subtítulo
            top_line = tk.Frame(row_padding, bg=self.color_white)
            top_line.pack(fill=tk.X, pady=(0, 10))
            
            # Canvas para o ícone com emoji colorido
            ic_canvas = tk.Canvas(top_line, width=32, height=32, bg=self.color_white, highlightthickness=0)
            ic_canvas.pack(side=tk.LEFT, padx=(0, 12))
            draw_func(ic_canvas)
            
            text_frame = tk.Frame(top_line, bg=self.color_white)
            text_frame.pack(side=tk.LEFT, fill=tk.Y)
            
            t_lbl = tk.Label(text_frame, text=title_text, font=("Segoe UI", 10, "bold"), fg=self.color_slate, bg=self.color_white)
            t_lbl.pack(anchor="w")
            
            st_lbl = tk.Label(text_frame, text=subtitle_text, font=("Segoe UI", 9), fg=self.color_muted, bg=self.color_white)
            st_lbl.pack(anchor="w")
            
            # Linha inferior: Input com ícone interno e botão buscar
            input_line = tk.Frame(row_padding, bg=self.color_white)
            input_line.pack(fill=tk.X)
            
            # Caixa do input (flat outline com bg cinza claro)
            input_border = tk.Frame(input_line, bg=self.color_border, bd=1)
            input_border.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            input_container = tk.Frame(input_border, bg=self.color_input_bg)
            input_container.pack(fill=tk.BOTH, expand=True)
            
            # Ícone de pasta emoji colorido dentro do input
            folder_icon_lbl = tk.Label(
                input_container, 
                text="  📁", 
                font=("Segoe UI Emoji", 10), 
                bg=self.color_input_bg
            )
            folder_icon_lbl.pack(side=tk.LEFT)
            
            entry = tk.Entry(
                input_container, 
                textvariable=var_path, 
                font=("Segoe UI", 10), 
                bg=self.color_input_bg, 
                fg=self.color_slate,
                relief=tk.FLAT,
                bd=6
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Criar botão customizado de busca (estilo flat com ícone emoji)
            btn_frame = tk.Frame(input_line, bg=self.color_button_secondary, cursor="hand2")
            btn_frame.pack(side=tk.RIGHT)
            
            btn_canvas = tk.Canvas(btn_frame, width=20, height=20, bg=self.color_button_secondary, highlightthickness=0)
            btn_canvas.pack(side=tk.LEFT, padx=(10, 2), pady=6)
            # Desenhar emoji de pasta aberta no botão
            btn_canvas.create_text(10, 10, text="📂", font=("Segoe UI Emoji", 10))
            
            btn_lbl = tk.Label(
                btn_frame, 
                text="Buscar", 
                font=("Segoe UI", 9, "bold"), 
                fg=self.color_slate, 
                bg=self.color_button_secondary
            )
            btn_lbl.pack(side=tk.LEFT, padx=(0, 12), pady=6)
            
            # Eventos e Binds de clique e hover
            for widget in (btn_frame, btn_canvas, btn_lbl):
                widget.bind("<Button-1>", lambda e: self.browse_directory(var_path))
                widget.bind("<Enter>", lambda e: self.on_custom_btn_hover(btn_frame, btn_canvas, btn_lbl, True))
                widget.bind("<Leave>", lambda e: self.on_custom_btn_hover(btn_frame, btn_canvas, btn_lbl, False))
            
            return entry, btn_frame
            
        self.entry_gravacoes, self.btn_gravacoes = create_directory_row(
            dir_card_content, 
            "Pasta de Gravações", 
            "Origem dos arquivos MP4", 
            self.dir_gravacoes, 
            draw_camera_emoji
        )
        self.entry_documentos, self.btn_documentos = create_directory_row(
            dir_card_content, 
            "Pasta de Documentos", 
            "Origem dos arquivos DOCX / CSV", 
            self.dir_documentos, 
            draw_document_emoji
        )
        self.entry_destino, self.btn_destino = create_directory_row(
            dir_card_content, 
            "Pasta SharePoint Sincronizada", 
            "Destino dos arquivos processados", 
            self.dir_destino, 
            draw_cloud_emoji
        )

        # Painel de Controle (Botões)
        control_frame = tk.Frame(body_frame, bg=self.color_bg)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Botão Toggle Principal (Iniciar/Parar) - Customizado e Flat com ícones Play/Pause em vetor
        self.btn_toggle_frame = tk.Frame(control_frame, bg=self.color_primary, cursor="hand2")
        self.btn_toggle_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.btn_toggle_canvas = tk.Canvas(self.btn_toggle_frame, width=20, height=20, bg=self.color_primary, highlightthickness=0)
        self.btn_toggle_canvas.pack(side=tk.LEFT, padx=(15, 5), pady=8)
        
        self.btn_toggle_lbl = tk.Label(
            self.btn_toggle_frame, 
            text="Iniciar monitoramento", 
            font=("Segoe UI", 10, "bold"), 
            fg=self.color_white, 
            bg=self.color_primary
        )
        self.btn_toggle_lbl.pack(side=tk.LEFT, padx=(0, 20), pady=8)
        
        # Desenhar ícone Play inicial (Vetor)
        self.draw_play_icon()
        
        # Binds do botão principal
        for w in (self.btn_toggle_frame, self.btn_toggle_canvas, self.btn_toggle_lbl):
            w.bind("<Button-1>", lambda e: self.toggle_monitoring())
            w.bind("<Enter>", lambda e: self.on_btn_hover(True))
            w.bind("<Leave>", lambda e: self.on_btn_hover(False))
        
        # Badge de Status Estilizada na Direita
        self.status_badge_border = tk.Frame(control_frame, bg=self.color_border, bd=1)
        self.status_badge_border.pack(side=tk.RIGHT)
        
        self.status_badge = tk.Frame(self.status_badge_border, bg=self.color_white, padx=20, pady=10)
        self.status_badge.pack()
        
        self.lbl_status = tk.Label(
            self.status_badge, 
            text="⚡ Status: Inativo", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.color_white, 
            fg=self.color_muted
        )
        self.lbl_status.pack()
        
        # --- 3. CONSOLE DE LOGS ---
        log_card = tk.Frame(body_frame, bg=self.color_term_bg, bd=1, highlightthickness=1, highlightbackground=self.color_border)
        log_card.pack(fill=tk.BOTH, expand=True)
        
        # Header do Log
        log_header = tk.Frame(log_card, bg=self.color_term_bg, padx=15, pady=8)
        log_header.pack(fill=tk.X)
        
        lbl_log_title = tk.Label(
            log_header, 
            text=">_ LOG DE ATIVIDADES E HISTÓRICO", 
            font=("Consolas", 9, "bold"), 
            fg=self.color_term_fg, 
            bg=self.color_term_bg
        )
        lbl_log_title.pack(side=tk.LEFT)
        
        # Círculos de Controle macOS na Direita
        controls_canvas = tk.Canvas(log_header, width=50, height=12, bg=self.color_term_bg, highlightthickness=0)
        controls_canvas.pack(side=tk.RIGHT, padx=5)
        controls_canvas.create_oval(5, 1, 15, 11, fill="#FF5F56", outline="")   # Vermelho
        controls_canvas.create_oval(20, 1, 30, 11, fill="#FFBD2E", outline="")  # Amarelo
        controls_canvas.create_oval(35, 1, 45, 11, fill="#27C93F", outline="")  # Verde
        
        # Caixa de Texto Console
        self.log_area = scrolledtext.ScrolledText(
            log_card, 
            wrap=tk.WORD, 
            height=10, 
            font=('Consolas', 10),
            bg=self.color_term_bg,
            fg=self.color_term_fg,
            insertbackground=self.color_white,
            relief=tk.FLAT,
            bd=10
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state='disabled')
        
        # Tags de Cor para o Log Console
        self.log_area.tag_config('timestamp', foreground='#5C6370')
        self.log_area.tag_config('info', foreground='#ABB2BF')
        self.log_area.tag_config('start', foreground='#98C379') # Verde (OK)
        self.log_area.tag_config('stop', foreground='#E06C75')  # Laranja/Vermelho
        self.log_area.tag_config('warning', foreground='#E5C07B') # Amarelo (Warning)

        self.log("Painel carregado. Pronto para monitorar arquivos CTAR.", "info")

    def draw_play_icon(self):
        self.btn_toggle_canvas.delete("all")
        self.btn_toggle_canvas.create_polygon(5, 3, 17, 10, 5, 17, fill="white", outline="")
        
    def draw_pause_icon(self):
        self.btn_toggle_canvas.delete("all")
        self.btn_toggle_canvas.create_rectangle(5, 3, 8, 17, fill="white", outline="")
        self.btn_toggle_canvas.create_rectangle(12, 3, 15, 17, fill="white", outline="")

    def on_custom_btn_hover(self, frame, canvas, label, entering):
        bg_color = self.color_border if entering else self.color_button_secondary
        frame.configure(bg=bg_color)
        canvas.configure(bg=bg_color)
        label.configure(bg=bg_color)

    def on_btn_hover(self, entering):
        if self.is_monitoring:
            # Botão Parar (Laranja/Vermelho)
            color = "#D32F2F" if entering else self.color_orange_neon
        else:
            # Botão Iniciar (Vermelho Escuro)
            color = "#B71C1C" if entering else self.color_primary
            
        self.btn_toggle_frame.configure(bg=color)
        self.btn_toggle_canvas.configure(bg=color)
        self.btn_toggle_lbl.configure(bg=color)

    def log(self, message, msg_type="info"):
        timestamp = time.strftime("[%H:%M:%S]")
        self.root.after(0, self._append_log, timestamp, message, msg_type)

    def _append_log(self, timestamp, message, msg_type):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"{timestamp} ", 'timestamp')
        self.log_area.insert(tk.END, f"{message}\n", msg_type)
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def browse_directory(self, var):
        directory = filedialog.askdirectory()
        if directory:
            var.set(os.path.normpath(directory))
            self.save_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.dir_gravacoes.set(config.get("dir_gravacoes", ""))
                    self.dir_documentos.set(config.get("dir_documentos", ""))
                    self.dir_destino.set(config.get("dir_destino", ""))
                self.log("Parâmetros do arquivo config.json carregados.", "info")
            except Exception as e:
                self.log(f"Erro ao ler arquivo config.json: {e}", "warning")

    def save_config(self):
        config = {
            "dir_gravacoes": self.dir_gravacoes.get(),
            "dir_documentos": self.dir_documentos.get(),
            "dir_destino": self.dir_destino.get()
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"Falha ao salvar config.json: {e}", "warning")

    def toggle_monitoring(self):
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        # Validar Pastas
        g_dir = self.dir_gravacoes.get()
        d_dir = self.dir_documentos.get()
        dest_dir = self.dir_destino.get()
        
        if not g_dir or not d_dir or not dest_dir:
            messagebox.showerror("Erro de Configuração", "Preencha todos os diretórios de origem e destino antes de iniciar!")
            return
            
        if not os.path.exists(g_dir) or not os.path.exists(d_dir) or not os.path.exists(dest_dir):
            messagebox.showerror("Erro de Diretório", "Um ou mais diretórios configurados não existem na sua máquina!")
            return
            
        self.save_config()
        
        self.is_monitoring = True
        
        # Atualizar botão toggle principal para estilo Parar
        self.btn_toggle_lbl.configure(text="Parar monitoramento")
        self.update_button_colors()
        
        # Atualizar pills de status
        self.lbl_pill_status.configure(text="● Ativo", fg="#2E7D32")
        self.pill_status_frame.configure(bg="#E8F5E9")
        self.lbl_pill_status.configure(bg="#E8F5E9")
        
        self.lbl_status.configure(text="⚡ Status: Ativo", fg="#2E7D32")
        
        # Desabilitar inputs de configuração
        self.set_inputs_state('disabled')
        
        self.log("Monitoramento iniciado. Observando alterações nas pastas de origem.", "start")
        
        # Limpar e registrar arquivos que já existem no início para ignorá-los
        self.processed_files.clear()
        self.ignored_files.clear()
        for folder in [g_dir, d_dir]:
            if folder and os.path.exists(folder):
                try:
                    for entry in os.scandir(folder):
                        if entry.is_file():
                            stat = entry.stat()
                            self.processed_files.add((entry.path, stat.st_mtime, stat.st_size))
                except Exception:
                    pass
        
        # Iniciar thread do monitor
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.is_monitoring = False
        
        # Atualizar botão toggle principal para estilo Iniciar
        self.btn_toggle_lbl.configure(text="Iniciar monitoramento")
        self.update_button_colors()
        
        # Atualizar pills de status
        self.lbl_pill_status.configure(text="● Parado", fg=self.color_muted)
        self.pill_status_frame.configure(bg="#F1F5F9")
        self.lbl_pill_status.configure(bg="#F1F5F9")
        
        self.lbl_status.configure(text="⚡ Status: Inativo", fg=self.color_muted)
        
        # Habilitar inputs de configuração
        self.set_inputs_state('normal')
        self.log("Monitoramento interrompido pelo usuário.", "stop")
        
        # Aguardar finalização da thread para evitar erros em testes unitários
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=0.1)

    def update_button_colors(self):
        if self.is_monitoring:
            color = self.color_orange_neon
            self.draw_pause_icon()
        else:
            color = self.color_primary
            self.draw_play_icon()
            
        self.btn_toggle_frame.configure(bg=color)
        self.btn_toggle_canvas.configure(bg=color)
        self.btn_toggle_lbl.configure(bg=color)

    def set_inputs_state(self, state):
        self.entry_gravacoes.configure(state=state)
        self.entry_documentos.configure(state=state)
        self.entry_destino.configure(state=state)
        
        # Para botões customizados (frames), alteramos cursor e binds conforme estado
        cursor_style = "arrow" if state == "disabled" else "hand2"
        self.btn_gravacoes.configure(cursor=cursor_style)
        self.btn_documentos.configure(cursor=cursor_style)
        self.btn_destino.configure(cursor=cursor_style)
        
        if state == "disabled":
            self.btn_gravacoes.unbind("<Button-1>")
            self.btn_documentos.unbind("<Button-1>")
            self.btn_destino.unbind("<Button-1>")
        else:
            self.btn_gravacoes.bind("<Button-1>", lambda e: self.browse_directory(self.dir_gravacoes))
            self.btn_documentos.bind("<Button-1>", lambda e: self.browse_directory(self.dir_documentos))
            self.btn_destino.bind("<Button-1>", lambda e: self.browse_directory(self.dir_destino))

    def parse_ctar_filename(self, filename):
        name_without_ext, ext = os.path.splitext(filename)
        
        # 1. Regra 1: Extrair o ID do projeto (ID seguido de números)
        id_match = re.search(r"ID\s*(\d+)", name_without_ext, re.IGNORECASE)
        if not id_match:
            return None
        project_id = id_match.group(1).strip()
        
        # Termos genéricos a serem desconsiderados
        ignore_words = {
            "gravação", "gravacao", "reunião", "reuniao", "ctar", "meeting", 
            "discussão", "discussao", "técnica", "tecnica", "desenvolvimento", 
            "geral", "final", "empresa", "cliente", "projeto", "discussao",
            "transcrição", "transcricao", "presença", "presenca", "comentário", 
            "comentario", "parecer", "de", "da", "do", "das", "dos", "com", 
            "para", "em", "um", "uma", "a", "o", "e", "of", "the", "and"
        }
        
        # Função auxiliar para limpar um segmento de texto
        def clean_text(text):
            cleaned = re.sub(r"[\[\]()_.\/]", " ", text)
            cleaned = re.sub(r"\bID\b", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\b" + project_id + r"\b", "", cleaned)
            cleaned = re.sub(r"\b\d{6,}\b", "", cleaned)
            cleaned = re.sub(r"\b\d{8}_\d{6}\b", "", cleaned)
            
            words = []
            for word in cleaned.split():
                word_clean = word.strip().strip("-").lower()
                word_clean = re.sub(r"[^\wÀ-ÿ]", "", word_clean)
                if word_clean and word_clean not in ignore_words and not word_clean.isdigit():
                    word_preserved = word.strip().strip("-")
                    if word_preserved:
                        words.append(word_preserved)
            
            return " ".join(words).strip()

        project_name = None
        
        # 2. Regra 2: O nome costuma estar após o ID ou separado por traços (-) ou barras (|)
        if "|" in name_without_ext:
            parts = name_without_ext.split("|")
            for i, part in enumerate(parts):
                if "ID" in part.upper() and project_id in part:
                    if i + 1 < len(parts):
                        project_name = clean_text(parts[i+1])
                        break
                    elif i > 0:
                        project_name = clean_text(parts[0])
                        break
        elif "-" in name_without_ext:
            parts = name_without_ext.split("-")
            for i, part in enumerate(parts):
                if "ID" in part.upper() and project_id in part:
                    if i + 1 < len(parts):
                        project_name = clean_text(parts[i+1])
                        break
                    elif i > 0:
                        project_name = clean_text(parts[0])
                        break
                        
        # 3. Caso não haja delimitadores (| ou -), limpa a string inteira
        if not project_name:
            project_name = clean_text(name_without_ext)
            
        if not project_name:
            project_name = "Projeto"
            
        project_name = re.sub(r'\s+', ' ', project_name).strip()
        name_clean, _ = os.path.splitext(project_name)
        project_name = name_clean.strip()
        
        return project_id, project_name, ext.lower()

    def is_file_ready(self, filepath):
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, 'rb+') as f:
                pass
            return True
        except (OSError, PermissionError):
            return False

    def wait_for_file_ready(self, filepath, max_attempts=5, check_interval=1):
        attempts = 0
        last_size = -1
        
        while attempts < max_attempts and self.is_monitoring:
            if not os.path.exists(filepath):
                return False
            try:
                current_size = os.path.getsize(filepath)
                if current_size == last_size and current_size > 0:
                    if self.is_file_ready(filepath):
                        return True
                last_size = current_size
            except OSError:
                pass
            attempts += 1
            time.sleep(check_interval)
            
        return self.is_file_ready(filepath)

    def process_file(self, filepath, source_type):
        filename = os.path.basename(filepath)
        parsed = self.parse_ctar_filename(filename)
        
        if not parsed:
            if filepath not in self.ignored_files:
                self.log(f"Aviso: Arquivo '{filename}' possui 'CTAR' no nome mas não atende ao padrão esperado de ID e Nome de Empresa. Pulando.", "warning")
                self.ignored_files.add(filepath)
            return
            
        project_id, project_name, ext = parsed
        
        # Definir tipo de arquivo
        if ext in ['.mp4', '.mkv', '.avi', '.mov', '.webm']:
            prefix = "Gravação"
        elif ext in ['.docx', '.doc', '.pdf', '.txt']:
            prefix = "Transcrição"
        elif ext in ['.csv', '.xlsx', '.xls']:
            prefix = "Presença"
        else:
            prefix = "Documento"

        dest_root = self.dir_destino.get()
        target_folder_name = f"{project_name} (ID {project_id})"
        target_folder_path = os.path.join(dest_root, target_folder_name)
        
        new_filename = f"{prefix} CTAR (ID {project_id}) - {project_name}{ext}"
        target_filepath = os.path.join(target_folder_path, new_filename)
        
        self.log(f"Detectado arquivo: '{filename}'", "info")
        self.log(f"  -> Identificado como: {prefix} | Projeto: {project_name} (ID: {project_id})", "info")
        
        if not self.wait_for_file_ready(filepath):
            self.log(f"  -> Erro: O arquivo '{filename}' está bloqueado ou em gravação. Será reprocessado no próximo ciclo.", "warning")
            return

        try:
            os.makedirs(target_folder_path, exist_ok=True)
            
            if os.path.exists(target_filepath):
                self.log(f"  -> Aviso: O arquivo '{new_filename}' já existe no destino. Pulando cópia para não sobrescrever.", "warning")
                # Registrar metadados estáveis do arquivo de origem para não processar novamente
                try:
                    stat = os.stat(filepath)
                    self.processed_files.add((filepath, stat.st_mtime, stat.st_size))
                except Exception:
                    self.processed_files.add(filepath)
                return
            
            shutil.copy2(filepath, target_filepath)
            
            # Registrar metadados estáveis do arquivo copiado para não processar novamente
            try:
                stat = os.stat(filepath)
                self.processed_files.add((filepath, stat.st_mtime, stat.st_size))
            except Exception:
                self.processed_files.add(filepath)
                
            self.log(f"  -> Sucesso: Arquivo copiado e renomeado para '{os.path.basename(target_filepath)}'", "start")
            
        except Exception as e:
            self.log(f"  -> Falha crítica ao copiar o arquivo: {e}", "warning")

    def _monitor_loop(self):
        while self.is_monitoring:
            try:
                g_dir = self.dir_gravacoes.get()
                d_dir = self.dir_documentos.get()
                
                self._scan_folder(g_dir, "gravacoes")
                self._scan_folder(d_dir, "documentos")
            except (tk.TclError, RuntimeError):
                # Ocorre quando a janela do Tkinter foi destruída
                break
            
            time.sleep(2)

    def _scan_folder(self, folder_path, source_type):
        if not os.path.exists(folder_path):
            return
            
        try:
            for entry in os.scandir(folder_path):
                if not self.is_monitoring:
                    break
                if entry.is_file():
                    filepath = entry.path
                    filename = entry.name
                    
                    if filename.startswith("~$") or filename.startswith("."):
                        continue
                        
                    # Obter metadados para verificar se já foi processado
                    try:
                        stat = entry.stat()
                        file_key = (filepath, stat.st_mtime, stat.st_size)
                    except Exception:
                        file_key = filepath
                        
                    if file_key in self.processed_files or filepath in self.processed_files:
                        continue
                        
                    if "CTAR" in filename.upper():
                        self.process_file(filepath, source_type)
        except Exception as e:
            pass

    def on_closing(self):
        if self.is_monitoring:
            if messagebox.askokcancel("Sair", "O monitoramento está ativo. Tem certeza que deseja fechar a aplicação?"):
                self.stop_monitoring()
                self.root.destroy()
        else:
            self.root.destroy()

    def check_for_updates(self):
        try:
            import urllib.request
            import json
            
            url = "https://api.github.com/repos/carlosvinicius-senai/automacao_ctar/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "CTAR-Automation-Updater"})
            
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    tag_name = data.get("tag_name", "")
                    
                    if not tag_name:
                        return
                        
                    clean_latest = tag_name.lstrip("vV").strip()
                    clean_curr = self.VERSION.lstrip("vV").strip()
                    
                    def parse_version(v_str):
                        return [int(x) for x in re.findall(r'\d+', v_str)]
                        
                    if parse_version(clean_latest) > parse_version(clean_curr):
                        # Procurar a url de download do Setup_Automacao_CTAR.exe
                        download_url = None
                        for asset in data.get("assets", []):
                            if "Setup_Automacao_CTAR" in asset.get("name", ""):
                                download_url = asset.get("browser_download_url")
                                break
                        
                        if download_url:
                            self.root.after(0, self.prompt_update, tag_name, download_url)
        except Exception:
            # Falha silenciosa para não quebrar a inicialização se estiver sem rede
            pass
            
    def prompt_update(self, new_version, download_url):
        if messagebox.askyesno(
            "Atualização Disponível", 
            f"Uma nova versão ({new_version}) da Automação CTAR está disponível!\n\nDeseja baixar e instalar agora?"
        ):
            # Iniciar download em segundo plano
            threading.Thread(target=self.download_and_run_updater, args=(download_url,), daemon=True).start()
            
    def download_and_run_updater(self, download_url):
        self.log("Baixando nova atualização de Setup_Automacao_CTAR.exe...", "warning")
        try:
            import urllib.request
            temp_dir = os.environ.get('TEMP', os.path.expanduser('~\\AppData\\Local\\Temp'))
            installer_path = os.path.join(temp_dir, 'Setup_Automacao_CTAR_Update.exe')
            
            # Baixar o instalador
            urllib.request.urlretrieve(download_url, installer_path)
            
            self.log("Download concluído. Iniciando instalador...", "start")
            
            # Executar instalador e fechar o app
            os.startfile(installer_path)
            self.root.after(100, self.root.destroy)
            
        except Exception as e:
            self.log(f"Erro ao baixar atualização: {e}", "warning")
            self.root.after(0, lambda: messagebox.showerror("Erro de Atualização", f"Não foi possível baixar a atualização:\n{e}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = CTARAutomationApp(root)
    root.mainloop()
