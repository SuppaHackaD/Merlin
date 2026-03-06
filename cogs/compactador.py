import os
import zipfile

class CompactadorCog:
    def __init__(self):
        pass

    def transmutar_capitulo(self, caminho_pasta, apagar_original=False):
        """Compacta uma única pasta de capítulo para .cbz"""
        if not os.path.exists(caminho_pasta) or not os.path.isdir(caminho_pasta):
            print(f"[X] Erro: Diretório inválido -> {caminho_pasta}")
            return False

        pasta_pai = os.path.dirname(caminho_pasta)
        nome_pasta = os.path.basename(caminho_pasta)
        caminho_cbz = os.path.join(pasta_pai, f"{nome_pasta}.cbz")

        # Stateless Resume: Se o CBZ já existir, pula para economizar CPU
        if os.path.exists(caminho_cbz) and os.path.getsize(caminho_cbz) > 0:
            print(f"      [~] Grimório {nome_pasta}.cbz já selado. Pulando...")
            return True

        print(f"[*] Selando grimório: {nome_pasta} -> .cbz")
        try:
            with zipfile.ZipFile(caminho_cbz, 'w', zipfile.ZIP_DEFLATED) as zipf:
                arquivos = sorted(os.listdir(caminho_pasta))
                for arquivo in arquivos:
                    caminho_arquivo = os.path.join(caminho_pasta, arquivo)
                    if os.path.isfile(caminho_arquivo):
                        zipf.write(caminho_arquivo, arcname=arquivo)
            return True
        except Exception as e:
            print(f"[X] Falha na transmutação de {nome_pasta}: {e}")
            if os.path.exists(caminho_cbz):
                os.remove(caminho_cbz) # Mata o arquivo corrompido
            return False

    def transmutar_obra(self, caminho_obra, apagar_original=False):
        """Varre a pasta de um mangá e compacta todos os capítulos lá dentro"""
        if not os.path.exists(caminho_obra) or not os.path.isdir(caminho_obra):
            print(f"[X] Erro: Diretório da obra inválido -> {caminho_obra}")
            return

        print(f"\n[*] Iniciando Transmutação em Lote na Obra: {os.path.basename(caminho_obra)}")
        
        pastas = sorted(os.listdir(caminho_obra))
        sucessos = 0

        for item in pastas:
            caminho_item = os.path.join(caminho_obra, item)
            
            # Garante que só vai tentar zipar o que for pasta (ignora os .cbz já prontos)
            if os.path.isdir(caminho_item):
                if self.transmutar_capitulo(caminho_item, apagar_original):
                    sucessos += 1

        print(f"\n[V] Operação concluída! {sucessos} capítulos forjados em .cbz na obra '{os.path.basename(caminho_obra)}'.")