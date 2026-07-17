import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox

class CTARInstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador/Desinstalador - Automação CTAR")
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
            text="Assistente de Instalação CTAR", 
            font=("Segoe UI", 14, "bold"), 
            fg=self.color_primary, 
            bg=self.color_card
        )
        lbl_title.pack(pady=(15, 10))
        
        # Descrição
        lbl_desc = tk.Label(
            card, 
            text="Gerencie a instalação local do aplicativo Automação CTAR.\nVocê pode instalar o assistente de monitoramento ou removê-lo completamente.", 
            font=("Segoe UI", 10), 
            fg=self.color_slate, 
            bg=self.color_card,
            justify=tk.CENTER
        )
        lbl_desc.pack(pady=10)
        
        # Frame de botões
        btn_frame = tk.Frame(card, bg=self.color_card)
        btn_frame.pack(pady=15)
        
        # Botão de Instalação
        self.btn_install = tk.Button(
            btn_frame, 
            text="Instalar", 
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
        self.btn_install.pack(side=tk.LEFT, padx=10)
        
        # Botão de Desinstalação
        self.btn_uninstall = tk.Button(
            btn_frame, 
            text="Desinstalar", 
            command=self.run_ui_uninstallation,
            font=("Segoe UI", 10, "bold"),
            bg=self.color_slate,
            fg="white",
            activebackground="#202A30",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=25,
            pady=8,
            cursor="hand2"
        )
        self.btn_uninstall.pack(side=tk.LEFT, padx=10)
        
        # Efeitos Hover
        self.btn_install.bind("<Enter>", lambda e: self.btn_install.configure(bg="#b01732"))
        self.btn_install.bind("<Leave>", lambda e: self.btn_install.configure(bg=self.color_primary))
        
        self.btn_uninstall.bind("<Enter>", lambda e: self.btn_uninstall.configure(bg="#202A30"))
        self.btn_uninstall.bind("<Leave>", lambda e: self.btn_uninstall.configure(bg=self.color_slate))

    def run_installation(self):
        self.btn_install.configure(state="disabled", text="Instalando...")
        self.btn_uninstall.configure(state="disabled")
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
            self.btn_install.configure(state="normal", text="Instalar")
            self.btn_uninstall.configure(state="normal")
            return
            
        # Pasta de destino: %localappdata%\Automacao_CTAR
        local_appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        dest_dir = os.path.join(local_appdata, 'Automacao_CTAR')
        
        try:
            # Fechar qualquer instância do app que esteja rodando
            subprocess.run(["taskkill", "/f", "/im", "Automacao_CTAR.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            os.makedirs(dest_dir, exist_ok=True)
            dest_exe = os.path.join(dest_dir, 'Automacao_CTAR.exe')
            
            # Copiar arquivo principal
            shutil.copy2(src_exe, dest_exe)
            
            # Copiar o instalador atual como desinstalador (para remoção via painel de controle)
            try:
                if sys.executable.lower().endswith(".exe") and "python" not in os.path.basename(sys.executable).lower():
                    shutil.copy2(sys.executable, os.path.join(dest_dir, 'uninstall.exe'))
            except Exception:
                pass
            
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
                
            # Registrar no Add/Remove Programs do Windows (HKEY_CURRENT_USER)
            try:
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Automacao_CTAR"
                key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Automação CTAR")
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{os.path.join(dest_dir, "uninstall.exe")}" --uninstall')
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, dest_exe)
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.4")
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "CTAR")
                winreg.CloseKey(key)
            except Exception:
                pass
                
            messagebox.showinfo("Instalação Concluída", "O aplicativo Automação CTAR foi instalado com sucesso!\n\nOs atalhos foram criados na sua Área de Trabalho e no Menu Iniciar.")
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao copiar arquivos para a pasta de destino:\n{e}")
            self.btn_install.configure(state="normal", text="Instalar")
            self.btn_uninstall.configure(state="normal")

    def run_ui_uninstallation(self):
        confirm = messagebox.askyesno("Desinstalar Automação CTAR", "Tem certeza que deseja desinstalar o Automação CTAR e todos os seus atalhos?")
        if not confirm:
            return
            
        self.btn_install.configure(state="disabled")
        self.btn_uninstall.configure(state="disabled", text="Desinstalando...")
        self.root.update()
        
        try:
            self.perform_uninstallation()
            messagebox.showinfo("Desinstalação Concluída", "O aplicativo Automação CTAR foi desinstalado com sucesso!")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro durante a desinstalação:\n{e}")
            self.btn_install.configure(state="normal")
            self.btn_uninstall.configure(state="normal", text="Desinter")

    def perform_uninstallation(self):
        # 1. Fechar o aplicativo caso esteja rodando
        subprocess.run(["taskkill", "/f", "/im", "Automacao_CTAR.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # 2. Remover atalhos do Desktop e Start Menu
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
            if os.path.exists(sc_path):
                try:
                    os.remove(sc_path)
                except Exception:
                    pass
                    
        # 3. Remover registro de desinstalação
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Automacao_CTAR")
        except Exception:
            pass
            
        # 4. Agendar a remoção da pasta do appdata após fechar
        local_appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        dest_dir = os.path.join(local_appdata, 'Automacao_CTAR')
        
        # Script powershell para esperar e deletar recursivamente a pasta (já que o uninstall.exe atual sairá)
        ps_del = f'Start-Sleep -s 1; Remove-Item -Recurse -Force "{dest_dir}"'
        subprocess.Popen(["powershell", "-Command", ps_del], creationflags=subprocess.CREATE_NO_WINDOW)


def run_silent_uninstallation():
    # Pergunta com diálogo nativo simples
    root = tk.Tk()
    root.withdraw()
    confirm = messagebox.askyesno("Desinstalar Automação CTAR", "Tem certeza que deseja desinstalar o Automação CTAR e remover todos os seus atalhos?")
    if confirm:
        try:
            app_installer = CTARInstallerApp(root)
            app_installer.perform_uninstallation()
            messagebox.showinfo("Desinstalação Concluída", "O aplicativo Automação CTAR foi desinstalado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro de Desinstalação", f"Não foi possível concluir a desinstalação:\n{e}")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        run_silent_uninstallation()
    else:
        root = tk.Tk()
        app = CTARInstallerApp(root)
        root.mainloop()
