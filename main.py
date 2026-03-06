import asyncio
import aiohttp
import os
from cogs.mangadex import MangaDexCog
from cogs.nyaa import NyaaCog
from cogs.compactador import CompactadorCog

def compilar_regras_capitulos(texto_selecao):
    regras = []
    if not texto_selecao or texto_selecao.strip().lower() == "todos":
        return regras 
    partes = texto_selecao.replace(';', ',').split(',')
    for parte in partes:
        parte = parte.strip()
        if not parte: continue
        if '-' in parte:
            inicio, fim = parte.split('-', 1)
            regras.append(('intervalo', float(inicio), float(fim)))
        else:
            regras.append(('exato', float(parte)))
    return regras

async def main():
    pasta_raiz = os.path.join(os.getcwd(), 'biblioteca_merlin')
    os.makedirs(pasta_raiz, exist_ok=True)

    print(r"""
      __  __           _ _       
     |  \/  |         | (_)      
     | \  / | ___ _ __| |_ _ __  
     | |\/| |/ _ \ '__| | | '_ \ 
     | |  | |  __/ |  | | | | | |
     |_|  |_|\___|_|  |_|_|_| |_|
    """)
    print(f"[*] Base de Conhecimento iniciada em: {pasta_raiz}")

    print("\n[i] Escolha a Categoria da Magia:")
    print("  1. Mangás (Via MangaDex - Capítulos soltos em Imagens)")
    print("  2. Mangás (Via Nyaa.si - Volumes completos em Torrent)")
    print("  3. Animes (Via Nyaa.si - Episódios/Temporadas em Torrent)")
    print("  4. Ferramentas Locais (Compactar para .cbz)")
    categoria = input("[?] Escolha (1/2/3/4): ").strip()

    # --- O BLOCO LOCAL (OPÇÃO 4) FICA ISOLADO AQUI ---
    if categoria == '4':
        print("\n[i] Ferramentas de Arquivamento Local")
        print("  1. Compactar Obra Inteira (Ex: Transformar todas as pastas em .cbz)")
        print("  2. Compactar Capítulo Único (Ex: Transformar apenas uma pasta em .cbz)")
        escolha_zip = input("[?] Escolha (1/2): ").strip()
        
        compactador = CompactadorCog()
        
        if escolha_zip == '1':
            caminho = input("[?] Cole o caminho absoluto da OBRA (Ex: Z:\\...\\Vagabond): ").strip()
            caminho = caminho.strip('"').strip("'") 
            compactador.transmutar_obra(caminho)
        elif escolha_zip == '2':
            caminho = input("[?] Cole o caminho absoluto do CAPÍTULO (Ex: Z:\\...\\Capitulo_1): ").strip()
            caminho = caminho.strip('"').strip("'")
            compactador.transmutar_capitulo(caminho)
        else:
            print("[!] Opção inválida.")
            
        print("\n[V] Operação finalizada.")
        return # Quebra a execução aqui! Ele não tenta buscar na internet.
    # --------------------------------------------------

    # Se não for a 4, o script segue o fluxo normal pedindo o alvo
    titulo_alvo = input("\n[?] O que o mago deseja conjurar hoje? ")
    
    regras = None
    if categoria == '1':
        print("[i] Formatos aceitos: 'todos', '1', '1, 3, 5', '1-10'")
        selecao_caps = input("[?] Quais capítulos deseja baixar? (Deixe em branco para TODOS): ")
        regras = compilar_regras_capitulos(selecao_caps)

    #connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
    headers_furtivos = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    timeout = aiohttp.ClientTimeout(total=30) # 30 segundos de paciência
    connector = aiohttp.TCPConnector(family=0) # 0 tenta IPv6 primeiro, depois IPv4

    # APENAS UM ÚNICO BLOCO 'async with' PARA GOVERNAR TODOS
    async with aiohttp.ClientSession(connector=connector, headers=headers_furtivos, timeout=timeout) as session:
        
        # Direciona para o Cog correto
        if categoria == '1':
            extrator = MangaDexCog(session, os.path.join(pasta_raiz, 'Mangas'))
        elif categoria == '2':
            extrator = NyaaCog(session, os.path.join(pasta_raiz, 'Mangas'), tipo_midia="manga")
        elif categoria == '3':
            extrator = NyaaCog(session, os.path.join(pasta_raiz, 'Animes'), tipo_midia="anime")
        else:
            print("[-] Categoria inválida.")
            return

        resultados = await extrator.buscar(titulo_alvo)
        
        if not resultados:
            print("[-] Nada encontrado nas runas...")
            if categoria in ['2', '3']:
                print("[!] Dica P2P: Tente remover o 'pt-br' ou buscar pelo título em inglês/romaji.")
            return

        print("\n[!] Múltiplos grimórios encontrados. Qual você deseja?")
        for idx, res in enumerate(resultados):
            print(f"  {idx + 1}. {res['titulo']}")
            
        try:
            escolha_idx = int(input(f"\n[?] Digite o número (1-{len(resultados)}): ")) - 1
            if escolha_idx < 0 or escolha_idx >= len(resultados):
                raise ValueError
            escolha = resultados[escolha_idx]
        except ValueError:
            print("[-] Escolha inválida. O feitiço falhou.")
            return

        titulo_para_baixar = escolha.get('titulo_limpo', escolha['titulo'])
        print(f"\n[+] Alvo travado: {titulo_para_baixar}")
        
        await extrator.baixar(escolha['id'], titulo_para_baixar, regras_capitulos=regras)

    print("\n[V] Operação finalizada.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())



#      ______ _   _____             _  __                                  
 #     |  ____| | |  __ \           | |/ /                                  
 #     | |__  | | | |__) |__ _   _  | ' / ___  _ __   __ _ _ __ ___   ___   
 #     |  __| | | |  ___/ __| | | | |  < / _ \| '_ \ / _` | '__/ _ \ / _ \  
 #     | |____| | | |   \__ \ |_| | | . \ (_) | | | | (_| | | | (_) | (_) | 
 #     |______|_| |_|   |___/\__, | |_|\_\___/|_| |_|\__, |_|  \___/ \___(_)
 #                            __/ |                   __/ |                 
 #                           |___/                   |___/     
 #by SuppaHackaD             
#