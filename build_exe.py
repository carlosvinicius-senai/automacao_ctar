import os
import sys
import subprocess

def install_and_build():
    print("=== Iniciando Processo de Compilação ===")
    
    # 1. Garantir que as dependências do requirements.txt estão instaladas
    print("\n[1/3] Verificando e instalando dependências...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar dependências: {e}")
        sys.exit(1)
        
    # 2. Executar o PyInstaller para compilar em um único arquivo .exe sem console
    print("\n[2/3] Executando PyInstaller...")
    try:
        import PyInstaller.__main__
        
        args = [
            'main.py',
            '--onefile',         # Compila tudo em um único arquivo .exe
            '--windowed',        # Não exibe janela de console preta (apenas a interface Tkinter)
            '--name=Automacao_CTAR',
            '--icon=app_icon.ico',
            '--add-data=app_icon.ico;.',
            '--clean'            # Limpa o cache antes de compilar
        ]
        
        PyInstaller.__main__.run(args)
        print("\n[3/3] Compilação concluída com sucesso!")
        
        exe_path = os.path.join("dist", "Automacao_CTAR.exe")
        if os.path.exists(exe_path):
            print(f"\nO executável foi gerado com sucesso em: {os.path.abspath(exe_path)}")
        else:
            print("\nAviso: Compilação terminou, mas o arquivo final não foi encontrado na pasta 'dist'.")
            
    except Exception as e:
        print(f"Erro durante a compilação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_and_build()
