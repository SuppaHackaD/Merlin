import os
from cogs.base_cog import BaseCog

class MangaDexCog(BaseCog):
    API_URL = "https://api.mangadex.org"


    async def buscar(self, query: str):
        url = f"{self.API_URL}/manga"
        params = {"title": query, "limit": 5}
        
        try:
            async with self.session.get(url, params=params) as response:
                # --- A VACINA CONTRA O CLOUDFLARE ---
                if response.status != 200:
                    print(f"\n[-] A API do MangaDex tropeçou (HTTP {response.status}).")
                    print("[!] O servidor deles deve estar em manutenção ou o Cloudflare barrou a requisição.")
                    print("[i] Respire fundo e tente conjurar novamente em alguns minutos.")
                    return []
                # ------------------------------------

                data = await response.json()
                resultados = []
                for item in data.get("data", []):
                    # Tenta pegar o título em inglês, depois em romaji, ou o primeiro que achar
                    titulo = item["attributes"]["title"].get("en") or \
                             item["attributes"]["title"].get("ja-ro") or \
                             list(item["attributes"]["title"].values())[0]
                    
                    # Limpa o título para não quebrar a criação de pastas no Windows
                    import re
                    titulo_limpo = re.sub(r'[\\/*?:"<>|]', "", titulo)
                    
                    resultados.append({
                        "id": item["id"],
                        "titulo": titulo,
                        "titulo_limpo": titulo_limpo.strip()
                    })
                return resultados
                
        except Exception as e:
            print(f"\n[-] Falha crítica na comunicação com as runas da API: {e}")
            return []

    async def baixar(self, item_id: str, titulo: str, idioma="pt-br", regras_capitulos=None):
        print(f"[*] [MangaDex] Mapeando TODOS os capítulos em {idioma.upper()} (Bypass de Paginação)...")
        url = f"{self.API_URL}/manga/{item_id}/feed"
        
        limit = 100
        offset = 0
        total = 1
        capitulos = []

        while offset < total:
            params = {
                "translatedLanguage[]": idioma, 
                "limit": limit,
                "offset": offset
            }
            async with self.session.get(url, params=params) as response:
                if response.status != 200: break
                data = await response.json()
                total = data.get("total", 0)
                lote = data.get("data", [])
                if not lote: break
                capitulos.extend(lote)
                offset += limit
                import asyncio
                await asyncio.sleep(2.0)

        if not capitulos:
            print("[!] Nenhum capítulo encontrado nesse idioma.")
            return

        capitulos_unicos = {}
        for cap in capitulos:
            num_str = cap["attributes"]["chapter"]
            if not num_str: continue
            
            try: num_val = float(num_str)
            except ValueError: num_val = num_str

            if num_val not in capitulos_unicos:
                capitulos_unicos[num_val] = cap
            else:
                data_atual = cap["attributes"].get("createdAt", "")
                data_salva = capitulos_unicos[num_val]["attributes"].get("createdAt", "")
                if data_atual > data_salva:
                    capitulos_unicos[num_val] = cap

        def extrair_numero(c):
            try: return float(c["attributes"]["chapter"])
            except: return 9999.0
            
        capitulos_filtrados = list(capitulos_unicos.values())
        capitulos_filtrados.sort(key=extrair_numero)
        print(f"[+] Total de {len(capitulos_filtrados)} capítulos únicos (Priorizando Scans mais recentes).")

        baixados_count = 0
        for cap in capitulos_filtrados:
            num_str = cap["attributes"]["chapter"]
            
            try:
                num_val = float(num_str)
                num_pasta = str(int(num_val)) if num_val.is_integer() else str(num_val)
            except ValueError:
                num_pasta = num_str
            
            if not self.deve_baixar(num_pasta, regras_capitulos):
                continue
            
            baixados_count += 1
            at_home_url = f"{self.API_URL}/at-home/server/{cap['id']}"
            
            # --- O BYPASS DO BURACO NEGRO (PRIMEIRO CONTATO) ---
            params_node = {"forcePort443": "true"}
            async with self.session.get(at_home_url, params=params_node) as res:
                node = await res.json()
            
            base_url = node["baseUrl"]
            
            if "cmdxd" in base_url or "network" in base_url:
                print(f"      [!] Detectado Node corrompido de Cache ({base_url}). Forçando Rota Global...")
                base_url = "https://uploads.mangadex.org"
            # ----------------------------------------------------

            cap_hash = node["chapter"]["hash"]
            paginas = node["chapter"]["data"]
            
            caminho_cap = os.path.join(self.base_dir, titulo, f"Capitulo_{num_pasta}")
            os.makedirs(caminho_cap, exist_ok=True)
            
            print(f"[-] [MangaDex] Baixando Cap {num_pasta} ({len(paginas)} pags)...")
            
            for idx, nome_arquivo in enumerate(paginas):
                caminho_img = os.path.join(caminho_cap, f"{idx:03d}.jpg")
                
                if os.path.exists(caminho_img) and os.path.getsize(caminho_img) > 0:
                    print(f"      [~] Página {idx:03d} já existe localmente. A ignorar...")
                    continue

                sucesso = False
                for tentativa in range(3):
                    url_img = f"{base_url}/data/{cap_hash}/{nome_arquivo}"
                    try:
                        async with self.session.get(url_img) as img_res:
                            if img_res.status == 200:
                                with open(caminho_img, "wb") as f:
                                    f.write(await img_res.read())
                                sucesso = True
                                await self.resfriar_conexao("pagina")
                                break
                            else:
                                print(f"      [!] Node {base_url.split('//')[-1]} falhou (HTTP {img_res.status}). Solicitando novo servidor... ({tentativa+1}/3)")
                                async with self.session.get(at_home_url, params=params_node) as res_novo:
                                    node_novo = await res_novo.json()
                                    base_url = node_novo.get("baseUrl", base_url)
                                    if "cmdxd" in base_url or "network" in base_url:
                                        base_url = "https://uploads.mangadex.org"
                                await asyncio.sleep(2)
                    except Exception as e:
                        print(f"      [!] Falha na conexão. Solicitando novo servidor... ({tentativa+1}/3)")
                        async with self.session.get(at_home_url, params=params_node) as res_novo:
                            node_novo = await res_novo.json()
                            base_url = node_novo.get("baseUrl", base_url)
                            if "cmdxd" in base_url or "network" in base_url:
                                base_url = "https://uploads.mangadex.org"
                        await asyncio.sleep(2)

                if not sucesso:
                    print(f"      [X] ERRO CRÍTICO: Página {idx:03d} não pôde ser baixada de nenhum Node da rede.")
            
            await self.resfriar_conexao("capitulo")
        
        if baixados_count == 0:
            print(f"[!] Nenhum capítulo correspondente ao filtro foi encontrado.")

input("Press Enter to close this window...")