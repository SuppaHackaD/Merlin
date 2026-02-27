from abc import ABC, abstractmethod
import aiohttp
import asyncio

class BaseCog(ABC):
    def __init__(self, session: aiohttp.ClientSession, base_dir: str):
        self.session = session
        self.base_dir = base_dir
        
        self.delay_pagina = 0.1   
        self.delay_capitulo = 2.5 

    async def resfriar_conexao(self, tipo="capitulo"):
        if tipo == "pagina":
            await asyncio.sleep(self.delay_pagina)
        else:
            print(f"    [zZz] Resfriando a rede do Merlin ({self.delay_capitulo}s)...")
            await asyncio.sleep(self.delay_capitulo)

    def deve_baixar(self, num_cap_str, regras):
        """Filtro universal de capítulos. Todos os cogs herdam isso agora."""
        if not regras: return True
        try:
            num = float(num_cap_str)
        except (ValueError, TypeError):
            return False
        
        for tipo, *valores in regras:
            if tipo == 'exato' and num == valores[0]:
                return True
            elif tipo == 'intervalo' and valores[0] <= num <= valores[1]:
                return True
        return False

    @abstractmethod
    async def buscar(self, query: str) -> list:
        pass

    @abstractmethod
    async def baixar(self, item_id: str, titulo: str, regras_capitulos: list = None):
        pass