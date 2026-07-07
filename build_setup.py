import os
import sys

def main():
    print("=== Iniciando Processo de Compilação do Instalador ===")
    
    # 1. Garantir que o executável principal existe
    main_exe = os.path.join("dist", "Automacao_CTAR.exe")
    if not os.path.exists(main_exe):
        print(f"Erro: '{main_exe}' não encontrado. Compile o aplicativo principal primeiro.")
        sys.exit(1)
        
    print("[1/2] Verificando dependências...")
    try:
        import PyInstaller.__main__
    except ImportError:
        print("Instalando PyInstaller...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        import PyInstaller.__main__

    print("[2/2] Compilando Setup_Automacao_CTAR.exe usando PyInstaller...")
    
    # Argumentos para o PyInstaller para criar o executável de instalação de arquivo único
    pyinstaller_args = [
        "installer.py",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=Setup_Automacao_CTAR",
        "--add-data=dist/Automacao_CTAR.exe;.",
        "--add-data=app_icon.ico;.",
        "--icon=app_icon.ico",
        "--clean"
    ]
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("\n=== Compilação Concluída com Sucesso! ===")
        print("O instalador de clique único foi gerado em:")
        print(os.path.abspath(os.path.join("dist", "Setup_Automacao_CTAR.exe")))
    except Exception as e:
        print(f"\nErro durante a compilação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
