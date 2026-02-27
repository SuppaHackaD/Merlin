import os
from cogs.base_cog import BaseCog

class MangaDexCog(BaseCog):
    API_URL = "https://api.mangadex.org"


    async def buscar(self, query: str) -> list:
        print(f"[*] [MangaDex] Sondando a API por: {query}")
        url = f"{self.API_URL}/manga"
        params = {"title": query, "limit": 5} # Traz 5 opções pra você escolher
        
        async with self.session.get(url, params=params) as response:
            data = await response.json()
            resultados = []
            if data.get("data"):
                for item in data["data"]:
                    titulo = item["attributes"]["title"].get("en", query)
                    resultados.append({"id": item["id"], "titulo": titulo})
            return resultados

    async def baixar(self, item_id: str, titulo: str, idioma="pt-br", regras_capitulos=None):
        print(f"[*] [MangaDex] Mapeando capítulos em {idioma.upper()}...")
        url = f"{self.API_URL}/manga/{item_id}/feed"
        params = {"translatedLanguage[]": idioma, "order[chapter]": "asc", "limit": 100}
        
        async with self.session.get(url, params=params) as response:
            data = await response.json()
            capitulos = data.get("data", [])

        if not capitulos:
            print("[!] Nenhum capítulo encontrado nesse idioma.")
            return

        baixados_count = 0
        for cap in capitulos:
            num_cap = cap["attributes"]["chapter"]
            
            if not num_cap or not self.deve_baixar(num_cap, regras_capitulos):
                continue
            
            baixados_count += 1
            at_home_url = f"{self.API_URL}/at-home/server/{cap['id']}"
            async with self.session.get(at_home_url) as res:
                node = await res.json()
            
            base_url = node["baseUrl"]
            cap_hash = node["chapter"]["hash"]
            paginas = node["chapter"]["data"]
            
            caminho_cap = os.path.join(self.base_dir, titulo, f"Capitulo_{num_cap}")
            os.makedirs(caminho_cap, exist_ok=True)
            
            print(f"[-] [MangaDex] Baixando Cap {num_cap} ({len(paginas)} pags)...")
            
            for idx, nome_arquivo in enumerate(paginas):
                url_img = f"{base_url}/data/{cap_hash}/{nome_arquivo}"
                caminho_img = os.path.join(caminho_cap, f"{idx:03d}.jpg")
                
                # --- A MÁGICA DA RETOMADA (RESUME) ---
                # Se o ficheiro já existe e não está vazio (tamanho > 0 bytes), salta a transferência
                if os.path.exists(caminho_img) and os.path.getsize(caminho_img) > 0:
                    print(f"      [~] Página {idx:03d} já existe localmente. A ignorar...")
                    continue
                # -------------------------------------

                async with self.session.get(url_img) as img_res:
                    if img_res.status == 200:
                        with open(caminho_img, "wb") as f:
                            f.write(await img_res.read())
                        # Puxa o respiro leve da base
                        await self.resfriar_conexao("pagina")
            
            # Puxa o resfriamento pesado da base ao fim do capítulo
            await self.resfriar_conexao("capitulo")
        
        if baixados_count == 0:
            print(f"[!] Nenhum capítulo correspondente ao filtro foi encontrado.")