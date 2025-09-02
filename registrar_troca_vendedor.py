from datetime import datetime

def registrar_troca_vendedor(vendedor):
    try:
        with open("log_vendedores.txt", "a", encoding="utf-8") as log_file:
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"{agora} - Vendedor atual definido para: {vendedor}\n")
    except Exception as e:
        print(f"[ERRO] Falha ao registrar troca de vendedor: {e}")
