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
    VERSION = "1.0.5"

    def __init__(self, root):
        self.root = root
        self.root.title("Automação de Gravações e Documentos CTAR")
        self.root.geometry("960x650")
        self.root.minsize(920, 580)
        
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
        
        # Cores específicas do Stepper
        self.color_green = "#2E7D32"         # Verde sucesso
        self.color_light_green = "#E8F5E9"   # Verde claro para fundo de sucesso
        self.color_light_red = "#FFEBEE"     # Vermelho claro para brilho/glow ativo
        
        # Caminho do arquivo de logs locais
        self.log_filepath = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local')), 'Automacao_CTAR', 'app_log.txt')
        
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
        self.failed_files = set()
        
        # Estados das etapas do processamento (0 a 4)
        self.step_states = {0: "pending", 1: "pending", 2: "pending", 3: "pending", 4: "pending"}
        self.step_widgets = {}
        
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
        
        # --- CORPO PRINCIPAL ROLÁVEL ---
        container = tk.Frame(self.root, bg=self.color_bg)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas e Scrollbar
        self.canvas = tk.Canvas(container, bg=self.color_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        # Frame de conteúdo dentro do Canvas
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.color_bg)
        
        # Configurar canvas e frame de conteúdo
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Ajustar largura do scrollable_frame para preencher a largura do canvas
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_frame_id, width=e.width)
        )
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas e scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Adicionar suporte a scroll com a roda do mouse (MouseWheel)
        def _on_mousewheel(event):
            try:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
            
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # O body_frame agora é filho do scrollable_frame para rolar automaticamente
        body_frame = tk.Frame(self.scrollable_frame, bg=self.color_bg, padx=25, pady=20)
        body_frame.pack(fill=tk.BOTH, expand=True)
        
        # Estrutura Lado a Lado (Duas Colunas)
        cols_frame = tk.Frame(body_frame, bg=self.color_bg)
        cols_frame.pack(fill=tk.BOTH, expand=True)
        
        left_col = tk.Frame(cols_frame, bg=self.color_bg)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        right_col = tk.Frame(cols_frame, bg=self.color_bg, width=420)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(15, 0))
        right_col.pack_propagate(False)
        
        # --- COLUNA ESQUERDA: Configuração de Diretórios ---
        dir_card = tk.Frame(left_col, bg=self.color_card_bg, bd=1, highlightthickness=1, highlightbackground=self.color_border)
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

        # --- COLUNA ESQUERDA: Última Nomenclatura Gerada ---
        self.nomenclature_card = tk.Frame(left_col, bg=self.color_card_bg, bd=1, highlightthickness=1, highlightbackground=self.color_border)
        self.nomenclature_card.pack(fill=tk.X, pady=(0, 20))
        
        nom_content = tk.Frame(self.nomenclature_card, bg=self.color_card_bg, padx=20, pady=20)
        nom_content.pack(fill=tk.BOTH, expand=True)
        
        lbl_nom_title = tk.Label(
            nom_content, 
            text="ÚLTIMA NOMENCLATURA PROCESSADA", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.color_slate, 
            bg=self.color_card_bg
        )
        lbl_nom_title.pack(anchor="w", pady=(0, 15))
        
        # Auxiliar para criar labels de valor formatados
        def create_val_label(parent, title_text):
            lbl_title = tk.Label(parent, text=title_text, font=("Segoe UI", 9, "bold"), fg=self.color_muted, bg=self.color_card_bg)
            lbl_title.pack(anchor="w")
            
            border_frame = tk.Frame(parent, bg=self.color_border, bd=1)
            border_frame.pack(fill=tk.X, pady=(4, 10))
            
            lbl_val = tk.Label(
                border_frame,
                text="-",
                font=("Consolas", 9),
                fg=self.color_slate,
                bg=self.color_input_bg,
                anchor="w",
                padx=10,
                pady=6
            )
            lbl_val.pack(fill=tk.X)
            return lbl_val

        self.lbl_folder_val = create_val_label(nom_content, "Pasta no SharePoint / OneDrive:")
        self.lbl_file_val = create_val_label(nom_content, "Arquivo Sincronizado:")

        # --- COLUNA ESQUERDA: Card de Aviso / Atenção (Oculto por padrão) ---
        self.alert_card = tk.Frame(
            left_col,
            bg="#FEF2F2",
            bd=1,
            highlightthickness=1,
            highlightbackground="#FECACA",
        )
        alert_content = tk.Frame(self.alert_card, bg="#FEF2F2", padx=16, pady=14)
        alert_content.pack(fill=tk.BOTH, expand=True)

        alert_header = tk.Frame(alert_content, bg="#FEF2F2")
        alert_header.pack(fill=tk.X, pady=(0, 6))

        self.lbl_alert_title = tk.Label(
            alert_header,
            text="⚠️ Atenção no envio",
            font=("Segoe UI", 10, "bold"),
            fg="#B91C1C",
            bg="#FEF2F2",
            anchor="w",
        )
        self.lbl_alert_title.pack(side=tk.LEFT)

        self.btn_retry_alert = tk.Label(
            alert_header,
            text="Tentar novamente",
            font=("Segoe UI", 8, "bold"),
            fg="#FFFFFF",
            bg="#DC2626",
            padx=10,
            pady=3,
            cursor="hand2",
        )
        self.btn_retry_alert.pack(side=tk.RIGHT)
        self.btn_retry_alert.bind("<Button-1>", lambda e: self.retry_failed_files())

        self.lbl_alert_msg = tk.Label(
            alert_content,
            text="",
            font=("Segoe UI", 9),
            fg="#7F1D1D",
            bg="#FEF2F2",
            anchor="w",
            justify=tk.LEFT,
            wraplength=420,
        )
        self.lbl_alert_msg.pack(fill=tk.X, pady=(0, 4))

        self.lbl_alert_hint = tk.Label(
            alert_content,
            text="",
            font=("Segoe UI", 8),
            fg="#991B1B",
            bg="#FEF2F2",
            anchor="w",
            justify=tk.LEFT,
            wraplength=420,
        )
        self.lbl_alert_hint.pack(fill=tk.X)

        # --- COLUNA ESQUERDA: Painel de Controle ---
        self.control_frame = tk.Frame(left_col, bg=self.color_bg)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))
        control_frame = self.control_frame
        
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
        
        # --- COLUNA DIREITA: Etapas do Processamento ---
        stepper_card = tk.Frame(right_col, bg=self.color_card_bg, bd=1, highlightthickness=1, highlightbackground=self.color_border)
        stepper_card.pack(fill=tk.BOTH, expand=True)
        
        stepper_content = tk.Frame(stepper_card, bg=self.color_card_bg, padx=20, pady=20)
        stepper_content.pack(fill=tk.BOTH, expand=True)
        
        lbl_step_title = tk.Label(
            stepper_content, 
            text="ETAPAS DO PROCESSAMENTO", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.color_primary, 
            bg=self.color_card_bg
        )
        lbl_step_title.pack(anchor="w", pady=(0, 2))
        
        lbl_step_desc = tk.Label(
            stepper_content, 
            text="Acompanhe o fluxo de processamento e arquivos", 
            font=("Segoe UI", 9), 
            fg=self.color_muted, 
            bg=self.color_card_bg
        )
        lbl_step_desc.pack(anchor="w", pady=(0, 20))
        
        # Definição das etapas
        steps_info = [
            ("Inicialização", "Carregar parâmetros e validar pastas", "📅"),
            ("Leitura das gravações", "Identificar novos arquivos MP4", "🎥"),
            ("Leitura dos documentos", "Identificar arquivos DOCX / CSV", "📄"),
            ("Processamento", "Renomear e organizar por rodada", "🔄"),
            ("Envio ao SharePoint", "Sincronizar com a pasta de destino", "☁️")
        ]
        
        for idx, (title, desc, emoji) in enumerate(steps_info):
            step_frame = tk.Frame(stepper_content, bg=self.color_card_bg)
            step_frame.pack(fill=tk.X, pady=2)
            
            # Canvas do ícone e conector
            canvas = tk.Canvas(step_frame, width=50, height=60, bg=self.color_card_bg, highlightthickness=0)
            canvas.pack(side=tk.LEFT)
            
            # Textos
            text_frame = tk.Frame(step_frame, bg=self.color_card_bg)
            text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
            
            lbl_t = tk.Label(text_frame, text=title, font=("Segoe UI", 10, "bold"), fg=self.color_muted, bg=self.color_card_bg)
            lbl_t.pack(anchor="w")
            
            lbl_d = tk.Label(text_frame, text=desc, font=("Segoe UI", 8), fg=self.color_muted, bg=self.color_card_bg, justify=tk.LEFT, wraplength=300)
            lbl_d.pack(anchor="w")
            
            lbl_time = tk.Label(text_frame, text="", font=("Segoe UI", 8), fg=self.color_muted, bg=self.color_card_bg)
            lbl_time.pack(anchor="w")
            
            self.step_widgets[idx] = {
                "canvas": canvas,
                "title_label": lbl_t,
                "desc_label": lbl_d,
                "time_label": lbl_time,
                "emoji": emoji
            }
            
            # Desenhar estado inicial pendente
            self.draw_step_icon(idx, "pending")

        self.log("Painel carregado. Pronto para monitorar arquivos CTAR.", "info")

    def draw_step_icon(self, step_idx, state):
        if step_idx not in self.step_widgets:
            return
        widgets = self.step_widgets[step_idx]
        canvas = widgets["canvas"]
        emoji = widgets["emoji"]
        
        canvas.delete("all")
        
        # Cores com base no estado
        line_color = self.color_border
        circle_bg = self.color_bg
        circle_border = self.color_border
        emoji_color = self.color_muted
        
        if state == "completed":
            line_color = self.color_green
            circle_bg = self.color_light_green
            circle_border = self.color_green
            emoji_color = self.color_green
        elif state == "active":
            line_color = self.color_border
            circle_bg = self.color_primary
            circle_border = self.color_primary
            emoji_color = "white"
            
        # 1. Desenhar linhas conectoras verticalmente
        # Linha para cima (se não for o primeiro)
        if step_idx > 0:
            prev_state = self.step_states.get(step_idx - 1)
            up_color = self.color_green if (prev_state == "completed" and state == "completed") else self.color_border
            canvas.create_line(25, 0, 25, 30, fill=up_color, width=2)
            
        # Linha para baixo (se não for o último)
        if step_idx < 4:
            next_state = self.step_states.get(step_idx + 1)
            down_color = self.color_green if (state == "completed" and next_state == "completed") else self.color_border
            canvas.create_line(25, 30, 25, 60, fill=down_color, width=2)
            
        # 2. Desenhar brilho (glow) se estiver ativo
        if state == "active":
            canvas.create_oval(10, 15, 40, 45, fill=self.color_light_red, outline="")
            
        # 3. Desenhar o círculo do ícone
        canvas.create_oval(13, 18, 37, 42, fill=circle_bg, outline=circle_border, width=2)
        
        # 4. Desenhar o emoji no centro
        canvas.create_text(25, 30, text=emoji, font=("Segoe UI Emoji", 10), fill=emoji_color)
        
        # Atualizar a cor das fontes dos labels
        if state == "active":
            widgets["title_label"].configure(fg=self.color_primary)
            widgets["desc_label"].configure(fg=self.color_slate)
        elif state == "completed":
            widgets["title_label"].configure(fg=self.color_green)
            widgets["desc_label"].configure(fg=self.color_muted)
        else:
            widgets["title_label"].configure(fg=self.color_muted)
            widgets["desc_label"].configure(fg=self.color_muted)

    def update_stepper(self, step_idx, state, timestamp_str=None):
        self.step_states[step_idx] = state
        
        def _update():
            self.draw_step_icon(step_idx, state)
            if timestamp_str:
                self.step_widgets[step_idx]["time_label"].configure(
                    text=timestamp_str,
                    fg=self.color_primary if state == "active" else (self.color_green if state == "completed" else self.color_muted)
                )
            # Redesenhar etapas vizinhas para atualizar cores das linhas conectoras
            if step_idx > 0:
                self.draw_step_icon(step_idx - 1, self.step_states[step_idx - 1])
            if step_idx < 4:
                self.draw_step_icon(step_idx + 1, self.step_states[step_idx + 1])
                
        self.root.after(0, _update)

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
        print(f"{timestamp} [{msg_type.upper()}] {message}")
        try:
            os.makedirs(os.path.dirname(self.log_filepath), exist_ok=True)
            with open(self.log_filepath, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} [{msg_type.upper()}] {message}\n")
        except Exception:
            pass

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
        
        # Stepper: Ativar Inicialização
        self.update_stepper(0, "active", time.strftime("%H:%M:%S"))
        for i in range(1, 5):
            self.update_stepper(i, "pending")
            
        # Limpar e registrar arquivos que já existem no início para ignorá-los
        self.processed_files.clear()
        self.ignored_files.clear()
        self.failed_files.clear()
        self.hide_error_alert()
        for folder in [g_dir, d_dir]:
            if folder and os.path.exists(folder):
                try:
                    with os.scandir(folder) as entries:
                        for entry in entries:
                            if entry.is_file():
                                stat = entry.stat()
                                self.processed_files.add((entry.path, stat.st_mtime, stat.st_size))
                except Exception:
                    pass
        
        # Stepper: Concluir Inicialização
        self.update_stepper(0, "completed", time.strftime("%H:%M:%S"))
        
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
        
        # Stepper: Resetar tudo para pendente
        for i in range(5):
            self.update_stepper(i, "pending", "")
        self.hide_error_alert()
            
        # Aguardar finalização da thread para evitar erros em testes unitários
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=0.1)
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

    CATEGORY_PROPOSTAS = "03 – Propostas e Orçamentos"
    CTAR_SUBFOLDER = "CTAR"
    LEADING_ID_RE = re.compile(r"^\s*(?:ID\s*)?(\d+)(?!\d)", re.IGNORECASE)

    def _normalize_name(self, name):
        return " ".join(name.strip().split()).casefold()

    def _normalize_category_name(self, name):
        normalized = re.sub(r"[–—-]", "-", name)
        normalized = re.sub(r"\s*-\s*", " - ", normalized)
        return self._normalize_name(normalized)

    def _extract_leading_project_id(self, folder_name):
        match = self.LEADING_ID_RE.match(folder_name)
        if not match:
            return None
        return int(match.group(1))

    def _list_subdirs(self, path):
        with os.scandir(path) as entries:
            return [entry for entry in entries if entry.is_dir()]

    def resolve_hub_destination(self, dest_root, company_name, project_id):
        """Resolve o caminho Empresa -> Projeto (ID no início) -> 03 – Propostas e Orçamentos -> CTAR."""
        if not dest_root or not os.path.exists(dest_root):
            return None, f"Diretório de destino '{dest_root}' não encontrado."

        try:
            company_subdirs = self._list_subdirs(dest_root)
            target_company_norm = self._normalize_name(company_name)
            company_matches = [
                entry for entry in company_subdirs
                if self._normalize_name(entry.name) == target_company_norm
            ]
            if not company_matches:
                return None, f"A pasta da empresa '{company_name}' não foi encontrada na pasta do SharePoint."
            if len(company_matches) > 1:
                names = ", ".join(e.name for e in company_matches)
                return None, f"Existe mais de uma pasta parecida para a empresa '{company_name}': {names}."
            company_entry = company_matches[0]

            target_id_int = int(project_id)
            project_subdirs = self._list_subdirs(company_entry.path)
            project_matches = [
                entry for entry in project_subdirs
                if self._extract_leading_project_id(entry.name) == target_id_int
            ]
            if not project_matches:
                return None, f"Nenhuma pasta iniciando com o ID {project_id} foi encontrada dentro da empresa '{company_entry.name}'."
            if len(project_matches) > 1:
                names = ", ".join(e.name for e in project_matches)
                return None, f"Existe mais de uma pasta com o ID {project_id} na empresa '{company_entry.name}': {names}."
            project_entry = project_matches[0]

            category_subdirs = self._list_subdirs(project_entry.path)
            expected_category = self._normalize_category_name(self.CATEGORY_PROPOSTAS)
            category_matches = [
                entry for entry in category_subdirs
                if self._normalize_category_name(entry.name) == expected_category
            ]
            if not category_matches:
                return None, f"A pasta '{self.CATEGORY_PROPOSTAS}' não foi encontrada dentro do projeto '{project_entry.name}'."
            if len(category_matches) > 1:
                names = ", ".join(e.name for e in category_matches)
                return None, f"Existe mais de uma pasta '{self.CATEGORY_PROPOSTAS}' no projeto '{project_entry.name}': {names}."
            category_entry = category_matches[0]

            ctar_subdirs = self._list_subdirs(category_entry.path)
            ctar_matches = [
                entry for entry in ctar_subdirs
                if self._normalize_name(entry.name) == "ctar"
            ]
            if len(ctar_matches) > 1:
                names = ", ".join(e.name for e in ctar_matches)
                return None, f"Existe mais de uma subpasta 'CTAR' dentro de '{category_entry.name}': {names}."

            ctar_path = (
                ctar_matches[0].path
                if ctar_matches
                else os.path.join(category_entry.path, self.CTAR_SUBFOLDER)
            )
            return {
                "company_folder": company_entry.name,
                "project_folder": project_entry.name,
                "category_folder": category_entry.name,
                "ctar_path": ctar_path,
                "ctar_exists": bool(ctar_matches),
            }, None

        except PermissionError as e:
            return None, f"Sem permissão para acessar pastas no Hub: {e}"
        except OSError as e:
            return None, f"Erro de acesso ao sistema de arquivos do Hub: {e}"

    def parse_ctar_filename(self, filename):
        name_without_ext, ext = os.path.splitext(filename)

        # Remover sufixos de cópias do Windows (ex: " (1)") no final do nome
        name_without_ext = re.sub(r"\s*\(\d+\)\s*$", "", name_without_ext)

        # Remover prefixo opcional de rodada e/ou tag CTAR antes de interpretar o padrão ID | EMPRESA | TITULO
        working_name = re.sub(
            r"^\s*(?:\d+\s*(?:º|°|o|a)?\s*)?(?:\[\s*CTAR\s*\]|CTAR\b)\s*[-_:|]*\s*",
            "",
            name_without_ext,
            flags=re.IGNORECASE,
        )
        working_name = re.sub(r"^\s*\d+\s*(?:º|°)\s*", "", working_name)

        # 1. Novo padrão prioritário: ID | EMPRESA | TITULO (com separadores já mapeados no Windows)
        parts = None
        if re.search(r"\s{2,}", working_name):
            parts = re.split(r"\s{2,}", working_name)
        elif "|" in working_name:
            parts = working_name.split("|")
        elif "-" in working_name:
            parts = working_name.split("-")
        elif "_" in working_name:
            parts = working_name.split("_")

        if parts and len(parts) >= 2:
            first_part = parts[0].strip()
            if re.fullmatch(r"\d+", first_part):
                company_raw = " ".join(parts[1].strip().split()).strip("-_ ")
                title_raw = " ".join(p.strip() for p in parts[2:] if p.strip())
                if company_raw:
                    return first_part, company_raw, title_raw, ext.lower()

        # 2. Fallback para o padrão legado: ID seguido de números (ex: [CTAR] ID 1282 | Mangotex | ...)
        id_match = re.search(r"ID\s*(\d+)", name_without_ext, re.IGNORECASE)
        if not id_match:
            return None
        project_id = id_match.group(1).strip()
        
        # Termos genéricos e de serviços a serem desconsiderados
        ignore_words = {
            "gravação", "gravacao", "reunião", "reuniao", "ctar", "meeting", 
            "discussão", "discussao", "técnica", "tecnica", "desenvolvimento", 
            "geral", "final", "empresa", "cliente", "projeto", "discussao",
            "transcrição", "transcricao", "presença", "presenca", "comentário", 
            "comentario", "parecer", "de", "da", "do", "das", "dos", "com", 
            "para", "em", "um", "uma", "a", "o", "e", "of", "the", "and",
            # Termos de serviços da consultoria CTAR/Senai
            "capina", "biológica", "biologica", "eficiência", "eficiencia",
            "energética", "energetica", "lean", "manufacturing", "manufatura",
            "enxuta", "produtividade", "consultoria", "mentoria", "treinamento",
            "auditoria", "visita", "diagnóstico", "diagnostico", "acompanhamento",
            "gerencial", "digital", "digitalização", "digitalizacao"
        }
        
        # Função auxiliar para limpar um segmento de texto
        def clean_text(text):
            # Remover tudo que estiver entre parênteses
            text = re.sub(r"\([^)]*\)", "", text)
            
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
        
        # 2. Regra 2: O nome costuma estar após o ID ou separado por blocos de espaços duplos (  ), barras (|), traços (-) ou underlines (_)
        has_double_spaces = len(re.findall(r"\s{2,}", name_without_ext)) > 0
        
        if has_double_spaces:
            parts = re.split(r"\s{2,}", name_without_ext)
            for i, part in enumerate(parts):
                if "ID" in part.upper() and project_id in part:
                    if i + 1 < len(parts):
                        project_name = clean_text(parts[i+1])
                        break
                    elif i > 0:
                        project_name = clean_text(parts[0])
                        break
        elif "|" in name_without_ext:
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
        elif "_" in name_without_ext:
            parts = name_without_ext.split("_")
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
        
        return project_id, project_name, "", ext.lower()

    def get_ctar_subfolder(self, filename):
        # Detectar número de rodada do CTAR no início do nome (ex: "2º [CTAR]..." ou "2º 2062...")
        # Exige marcador ordinal (º/°) ou [CTAR] para não confundir o ID do projeto com a rodada.
        match = re.match(
            r"^\s*(\d+)\s*(?:(?:º|°)\b|(?:º|°|o|a)?\s*(?:\[\s*CTAR\s*\]|CTAR\b))",
            filename,
            re.IGNORECASE,
        )
        if match:
            num = match.group(1)
            return f"{num}º CTAR"
        return "1º CTAR"

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

    def update_nomenclature(self, folder_text, file_text):
        def _update():
            self.lbl_folder_val.configure(text=folder_text)
            self.lbl_file_val.configure(text=file_text)
        self.root.after(0, _update)

    def show_error_alert(self, title, message, hint="Corrija a pasta no SharePoint/OneDrive e clique em 'Tentar novamente'."):
        def _show():
            self.lbl_alert_title.configure(text=f"⚠️ {title}")
            self.lbl_alert_msg.configure(text=message)
            self.lbl_alert_hint.configure(text=hint)
            if not self.alert_card.winfo_ismapped():
                self.alert_card.pack(fill=tk.X, pady=(0, 15), before=self.control_frame)
        self.root.after(0, _show)

    def hide_error_alert(self):
        def _hide():
            if self.alert_card.winfo_ismapped():
                self.alert_card.pack_forget()
        self.root.after(0, _hide)

    def retry_failed_files(self):
        self.failed_files.clear()
        self.ignored_files.clear()
        self.hide_error_alert()
        self.log("Reprocessamento manual solicitado pelo usuário.", "info")

    def process_file(self, filepath, source_type):
        filename = os.path.basename(filepath)
        
        # 1. Resetar todas as etapas para pending no início do novo arquivo
        for i in range(5):
            self.update_stepper(i, "pending", "")
            
        # Ativar etapa de Inicialização
        self.update_stepper(0, "active", time.strftime("%H:%M:%S"))
        
        parsed = self.parse_ctar_filename(filename)
        
        if not parsed:
            self.update_stepper(0, "pending", "")
            if filepath not in self.ignored_files:
                self.log(f"Aviso: Arquivo '{filename}' não atende ao padrão esperado (ID | Empresa | Título). Pulando.", "warning")
                self.ignored_files.add(filepath)
            return
            
        project_id, project_name, title, ext = parsed
        
        # Definir tipo de arquivo e categoria
        if ext in ['.mp4', '.mkv', '.avi', '.mov', '.webm']:
            prefix = "Gravação"
            is_recording = True
        elif ext in ['.docx', '.doc', '.pdf', '.txt']:
            prefix = "Transcrição"
            is_recording = False
        elif ext in ['.csv', '.xlsx', '.xls']:
            prefix = "Presença"
            is_recording = False
        else:
            prefix = "Documento"
            is_recording = False

        dest_root = self.dir_destino.get()
        hub_info, hub_error = self.resolve_hub_destination(dest_root, project_name, project_id)
        if hub_error:
            self.update_stepper(0, "pending", "")
            self.log(f"Erro ao resolver destino no Hub para '{filename}': {hub_error}", "error")
            self.show_error_alert(
                "Não foi possível enviar o arquivo",
                f"Arquivo: {filename}\n{hub_error}",
                "Ajuste ou sincronize a pasta no SharePoint/OneDrive e clique em 'Tentar novamente'.",
            )
            try:
                stat = os.stat(filepath)
                self.failed_files.add((filepath, stat.st_mtime, stat.st_size))
            except Exception:
                self.failed_files.add(filepath)
            return

        resolved_company = hub_info["company_folder"]
        subfolder_name = self.get_ctar_subfolder(filename)
        final_folder_path = os.path.join(hub_info["ctar_path"], subfolder_name)
        
        new_filename = f"{prefix} CTAR (ID {project_id}) - {resolved_company}{ext}"
        target_filepath = os.path.join(final_folder_path, new_filename)
        display_folder = (
            f"{hub_info['company_folder']} / {hub_info['project_folder']} / "
            f"{hub_info['category_folder']} / {self.CTAR_SUBFOLDER} / {subfolder_name}"
        )
        
        self.log(f"Detectado arquivo: '{filename}'", "info")
        self.log(f"  -> Identificado como: {prefix} | Empresa: {resolved_company} (ID: {project_id}) | Pasta: {subfolder_name}", "info")
        
        # Concluir Inicialização
        self.update_stepper(0, "completed", time.strftime("%H:%M:%S"))
        
        # Ativar etapa correspondente de Leitura
        active_read_step = 1 if is_recording else 2
        self.update_stepper(active_read_step, "active", time.strftime("%H:%M:%S"))
        
        if not self.wait_for_file_ready(filepath):
            self.log(f"  -> Erro: O arquivo '{filename}' está bloqueado ou em gravação. Será reprocessado no próximo ciclo.", "warning")
            self.update_stepper(active_read_step, "pending", "")
            return

        # Concluir Leitura e ativar Processamento
        self.update_stepper(active_read_step, "completed", time.strftime("%H:%M:%S"))
        self.update_stepper(3, "active", time.strftime("%H:%M:%S"))

        try:
            if not hub_info["ctar_exists"]:
                self.log(f"  -> Subpasta '{self.CTAR_SUBFOLDER}' criada automaticamente em '{hub_info['category_folder']}'.", "info")
            os.makedirs(final_folder_path, exist_ok=True)
            
            if os.path.exists(target_filepath):
                self.log(f"  -> Aviso: O arquivo '{new_filename}' já existe no destino. Pulando cópia para não sobrescrever.", "warning")
                # Concluir Processamento e Envio ao SharePoint (já que já está lá)
                self.update_stepper(3, "completed", time.strftime("%H:%M:%S"))
                self.update_stepper(4, "completed", time.strftime("%H:%M:%S"))
                # Atualizar Nomenclatura na UI
                self.update_nomenclature(display_folder, new_filename)
                
                try:
                    stat = os.stat(filepath)
                    self.processed_files.add((filepath, stat.st_mtime, stat.st_size))
                except Exception:
                    self.processed_files.add(filepath)
                return
            
            shutil.copy2(filepath, target_filepath)
            
            # Concluir Processamento e ativar Envio ao SharePoint
            self.update_stepper(3, "completed", time.strftime("%H:%M:%S"))
            self.update_stepper(4, "active", time.strftime("%H:%M:%S"))
            
            # Simular tempo leve de sincronização
            time.sleep(0.5)
            
            # Concluir Envio ao SharePoint
            self.update_stepper(4, "completed", time.strftime("%H:%M:%S"))
            
            # Atualizar Nomenclatura na UI
            self.update_nomenclature(display_folder, new_filename)
            self.hide_error_alert()
            
            # Registrar metadados estáveis do arquivo copiado para não processar novamente
            try:
                stat = os.stat(filepath)
                self.processed_files.add((filepath, stat.st_mtime, stat.st_size))
            except Exception:
                self.processed_files.add(filepath)
                
            self.log(f"  -> Sucesso: Arquivo copiado e renomeado para '{os.path.basename(target_filepath)}'", "start")
            
        except Exception as e:
            self.log(f"  -> Falha crítica ao copiar o arquivo: {e}", "error")
            self.show_error_alert(
                "Falha ao enviar o arquivo",
                f"Não foi possível copiar '{filename}' para o destino.\nMotivo: {e}",
                "Verifique se o arquivo não está aberto e se há permissão/espaço na pasta de destino.",
            )
            self.update_stepper(3, "pending", "")
            self.update_stepper(4, "pending", "")
            try:
                stat = os.stat(filepath)
                self.failed_files.add((filepath, stat.st_mtime, stat.st_size))
            except Exception:
                self.failed_files.add(filepath)

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
            current_paths = set()
            entries = list(os.scandir(folder_path))
            for entry in entries:
                if entry.is_file():
                    current_paths.add(entry.path)

            # Se um arquivo que falhou/foi ignorado foi removido da pasta, limpar o registro
            # para permitir reprocessamento caso seja adicionado novamente.
            self.failed_files = {
                item for item in self.failed_files
                if (item[0] if isinstance(item, tuple) else item) in current_paths
                or not (item[0] if isinstance(item, tuple) else item).startswith(folder_path)
            }
            self.ignored_files = {
                path for path in self.ignored_files
                if path in current_paths or not path.startswith(folder_path)
            }

            for entry in entries:
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
                    if filepath in self.ignored_files or file_key in self.failed_files or filepath in self.failed_files:
                        continue

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
