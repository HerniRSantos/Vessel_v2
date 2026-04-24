import subprocess
import time
import sys
import os
import signal
import argparse
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Definir os caminhos para os serviços do backend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
CLOUDFLARED_BIN = os.path.join(BASE_DIR, '../cloudflared')

# Verificar se AIS_API_KEY está disponível
AIS_API_KEY = os.getenv("AIS_API_KEY")
if AIS_API_KEY:
    SERVICES = [
        {"name": "API Server (FastAPI)", "cmd": ["python3", "-m", "uvicorn", "backend.api_server:app", "--host", "0.0.0.0", "--port", "8000"]},
        {"name": "AIS Ingestor", "cmd": ["python3", "backend/ais_ingestor.py"]},
        {"name": "OSINT Enricher", "cmd": ["python3", "backend/osint_enricher.py"]},
    ]
else:
    print("[WARNING] AIS_API_KEY não encontrada no .env - recolha AIS desativada")
    SERVICES = [
        {"name": "API Server (FastAPI)", "cmd": ["python3", "-m", "uvicorn", "backend.api_server:app", "--host", "0.0.0.0", "--port", "8000"]},
    ]

processes = []

def signal_handler(sig, frame):
    print("\n[Orchestrator] Recebido sinal de paragem. Encerrando todos os subserviços...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
            p.wait()
    print("[Orchestrator] Encerramento limpo concluído. Stand down.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_services(use_tunnel: bool):
    print("="*60)
    print("🚀 VESSEL_V2 MASTER LAUNCHER STARTING".center(60))
    print("="*60)
    
    try:
        from backend.database import init_db
        init_db()
        print("[DB] Configuração inicializada (WAL ativado)")
    except Exception as e:
        print(f"[DB] Erro a injetar BD: {e}")

    # Ligar os serviços vitais
    for idx, svc in enumerate(SERVICES):
        print(f"[{idx}] Arrancando {svc['name']}...")
        p = subprocess.Popen(svc["cmd"], cwd=BASE_DIR)
        processes.append(p)
        time.sleep(1)
        
    # Inicializar Cloudflare Túnel se solicitado
    if use_tunnel:
        if not os.path.exists(CLOUDFLARED_BIN):
            print("[TUNNEL] ATENÇÃO: Binário 'cloudflared' não encontrado na pasta raiz!")
            print("[TUNNEL] Túnel abortado. Terá que correr o guião start_tunnel.sh na v1.")
        else:
            print("\n[TUNNEL] A inicializar ligação WAN / TryCloudflare...")
            tunnel_cmd = [CLOUDFLARED_BIN, "tunnel", "--url", "http://localhost:8000"]
            tunnel_p = subprocess.Popen(tunnel_cmd, cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            processes.append(tunnel_p)
            SERVICES.append({"name": "Cloudflare Tunnel", "cmd": tunnel_cmd})
            
            print("="*60)
            print("[!] O SEU SITE ESTARÁ DISPONÍVEL NA INTERNET.")
            print("[!] Leia o link gerado nos logs originais ou execute um script à parte para capturar a URL gerada pelo túnel.")
            print("="*60)

    print("\nStatus: Orquestrador está Ativo. Pressione Ctrl+C para encerrar.")
    
    # Watcher Loop
    while True:
        time.sleep(5)
        for idx, (p, svc) in enumerate(zip(processes, SERVICES)):
            if p.poll() is not None:
                print(f"[CRITICAL] {svc['name']} crashou com código {p.returncode}! Reiniciando em 5 segundos...")
                time.sleep(5)
                processes[idx] = subprocess.Popen(svc["cmd"], cwd=BASE_DIR)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VesselControl V2 Master Launcher")
    parser.add_argument("--tunnel", action="store_true", help="Gera um URL seguro na Internet usando o Cloudflared")
    args = parser.parse_args()
    
    start_services(args.tunnel)
