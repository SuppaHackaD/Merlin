import os
from bs4 import BeautifulSoup
from cogs.base_cog import BaseCog

class NyaaCog(BaseCog):
    BASE_URL = "https://nyaa.si"

    def __init__(self, session, base_dir, tipo_midia="anime"):
        super().__init__(session, base_dir)
        self.tipo_midia = tipo_midia # Pode ser "anime" ou "manga"

    async def buscar(self, query: str) -> list:
        # A Mágica da Adaptação: Só força 'pt-br' se for Anime. Mangá vai em Inglês/Global por padrão.
        if self.tipo_midia == "anime":
            query_otimizada = query if "pt-br" in query.lower() else f"{query} pt-br"
        else:
            query_otimizada = query
            
        print(f"[*] [Nyaa.si] Rastreando a rede P2P ({self.tipo_midia.upper()}) por: {query_otimizada}")
        
        # 1_0 = Todos os Animes | 3_1 = Literatura Traduzida (Inglês na grande maioria)
        categoria_nyaa = "1_0" if self.tipo_midia == "anime" else "3_1"
        
        url = f"{self.BASE_URL}/"
        params = {"f": "0", "c": categoria_nyaa, "q": query_otimizada}
        
        async with self.session.get(url, params=params) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            resultados = []
            tabela = soup.find('table', class_='torrent-list')
            if not tabela:
                return resultados
                
            linhas = tabela.find('tbody').find_all('tr', limit=10)
            
            for linha in linhas:
                colunas = linha.find_all('td')
                if len(colunas) < 5: continue
                
                links_titulo = colunas[1].find_all('a')
                tag_titulo = links_titulo[-1] if links_titulo else None
                
                links_down = colunas[2].find_all('a')
                magnet_link = None
                for a in links_down:
                    if a['href'].startswith('magnet:'):
                        magnet_link = a['href']
                        break
                
                tamanho = colunas[3].text.strip()
                seeders = colunas[5].text.strip()
                
                if tag_titulo and magnet_link:
                    titulo_completo = tag_titulo.get('title') or tag_titulo.text.strip()
                    titulo_exibicao = f"[{seeders} SEED] {titulo_completo[:60]}... ({tamanho})"
                    
                    resultados.append({
                        "id": magnet_link,
                        "titulo": titulo_exibicao,
                        "titulo_limpo": titulo_completo
                    })
            return resultados

    async def baixar(self, item_id: str, titulo: str, regras_capitulos=None):
        print(f"[*] [Nyaa.si] Extraindo Magnet Link da rede P2P...")
        
        pasta_destino = os.path.join(self.base_dir, 'Torrents_Capturados')
        os.makedirs(pasta_destino, exist_ok=True)
        
        nome_arquivo_seguro = "".join([c for c in titulo if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        caminho_arquivo = os.path.join(pasta_destino, f"{nome_arquivo_seguro}.magnet")
        
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write(item_id)
            
        print(f"[+] Magnet Link capturado com sucesso!")
        print(f"[-] Salvo em: {caminho_arquivo}")