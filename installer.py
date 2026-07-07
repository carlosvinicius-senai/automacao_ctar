import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox

class CTARInstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador - Automação CTAR")
        self.root.geometry("480x280")
        self.root.resizable(False, False)
        
        # Carregar Ícone do App
        ico_path = 'app_icon.ico'
        if hasattr(sys, '_MEIPASS'):
            ico_path = os.path.join(sys._MEIPASS, 'app_icon.ico')
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass
        
        # Paleta de Cores Coerente com o App
        self.color_bg = "#E5D5CC"          # Bege Claro
        self.color_card = "#FFFFFF"        # Branco
        self.color_primary = "#D72042"     # Vermelho Cereja
        self.color_slate = "#303A42"       # Slate Escuro
        self.color_border = "#BCAA9F"      # Bege Escuro
        
        self.root.configure(bg=self.color_bg)
        
        # Centralizar a janela na tela
        self.center_window()
        
        self.create_widgets()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        # Card Interno
        card = tk.Frame(self.root, bg=self.color_card, bd=1, highlightthickness=1, highlightbackground=self.color_border)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        lbl_title = tk.Label(
            card, 
            text="Instalação do Assistente CTAR", 
            font=("Segoe UI", 14, "bold"), 
            fg=self.color_primary, 
            bg=self.color_card
        )
        lbl_title.pack(pady=(15, 10))
        
        # Descrição
        lbl_desc = tk.Label(
            card, 
            text="Este instalador copiará o aplicativo Automação CTAR para\nseu computador de forma local (sem necessidade de privilégios de administrador)\ne criará atalhos na Área de Trabalho e no Menu Iniciar.", 
            font=("Segoe UI", 10), 
            fg=self.color_slate, 
            bg=self.color_card,
            justify=tk.CENTER
        )
        lbl_desc.pack(pady=10)
        
        # Botão de Instalação
        self.btn_install = tk.Button(
            card, 
            text="Instalar Aplicativo", 
            command=self.run_installation,
            font=("Segoe UI", 10, "bold"),
            bg=self.color_primary,
            fg="white",
            activebackground="#b01732",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=25,
            pady=8,
            cursor="hand2"
        )
        self.btn_install.pack(pady=15)
        
        # Efeito Hover no botão
        self.btn_install.bind("<Enter>", lambda e: self.btn_install.configure(bg="#b01732"))
        self.btn_install.bind("<Leave>", lambda e: self.btn_install.configure(bg=self.color_primary))

    def run_installation(self):
        self.btn_install.configure(state="disabled", text="Instalando...")
        self.root.update()
        
        # Localizar o arquivo executável embarcado
        if hasattr(sys, '_MEIPASS'):
            src_exe = os.path.join(sys._MEIPASS, 'Automacao_CTAR.exe')
        else:
            # Fallback para execução local em desenvolvimento
            src_exe = os.path.join(os.path.dirname(__file__), 'dist', 'Automacao_CTAR.exe')
            if not os.path.exists(src_exe):
                src_exe = os.path.join(os.path.dirname(__file__), 'Automacao_CTAR.exe')

        if not os.path.exists(src_exe):
            messagebox.showerror("Erro de Instalação", "O executável principal 'Automacao_CTAR.exe' não foi encontrado no instalador!")
            self.btn_install.configure(state="normal", text="Instalar Aplicativo")
            return
            
        # Pasta de destino: %localappdata%\Automacao_CTAR
        local_appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        dest_dir = os.path.join(local_appdata, 'Automacao_CTAR')
        
        try:
            os.makedirs(dest_dir, exist_ok=True)
            dest_exe = os.path.join(dest_dir, 'Automacao_CTAR.exe')
            
            # Copiar arquivo
            shutil.copy2(src_exe, dest_exe)
            
            # Criar Atalhos via PowerShell
            import winreg
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            start_menu_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu', 'Programs')
            
            try:
                reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
                reg_desktop, _ = winreg.QueryValueEx(reg_key, "Desktop")
                desktop_path = os.path.expandvars(reg_desktop)
                reg_programs, _ = winreg.QueryValueEx(reg_key, "Programs")
                start_menu_path = os.path.expandvars(reg_programs)
            except Exception:
                pass
            
            shortcut_paths = [
                os.path.join(desktop_path, 'Automação CTAR.lnk'),
                os.path.join(start_menu_path, 'Automação CTAR.lnk')
            ]
            
            for sc_path in shortcut_paths:
                ps_script = f"""
                $WshShell = New-Object -ComObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut("{sc_path}")
                $Shortcut.TargetPath = "{dest_exe}"
                $Shortcut.WorkingDirectory = "{dest_dir}"
                $Shortcut.Description = "Automação de Arquivos CTAR"
                $Shortcut.Save()
                """
                subprocess.run(
                    ["powershell", "-Command", ps_script], 
                    capture_output=True, 
                    text=True, 
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
            messagebox.showinfo("Instalação Concluída", "O aplicativo Automação CTAR foi instalado com sucesso!\n\nOs atalhos foram criados na sua Área de Trabalho e no Menu Iniciar.")
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao copiar arquivos para a pasta de destino:\n{e}")
            self.btn_install.configure(state="normal", text="Instalar Aplicativo")

if __name__ == "__main__":
    root = tk.Tk()
    app = CTARInstallerApp(root)
    root.mainloop()
