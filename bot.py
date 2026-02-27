import discord
from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv
import asyncio

# Importando nossos extratores
from cogs.mangadex import MangaDexCog
from cogs.nyaa import NyaaCog

load_dotenv()

# Diretório base
PASTA_RAIZ = os.path.join(os.getcwd(), 'biblioteca_merlin')
os.makedirs(PASTA_RAIZ, exist_ok=True)

# --- CLASSE DO BOT (Para manter a sessão HTTP viva) ---
class MerlinBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.web_session = None

    async def setup_hook(self):
        # Quando o bot liga, criamos UMA sessão global e indestrutível
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0"}
        self.web_session = aiohttp.ClientSession(connector=connector, headers=headers)

    async def close(self):
        # Fecha a sessão com segurança se o bot for desligado
        if self.web_session:
            await self.web_session.close()
        await super().close()

bot = MerlinBot()

# --- INTERFACE DE MENU (DROPDOWN + EMBED) ---
class MenuResultados(discord.ui.Select):
    def __init__(self, resultados, extrator, regras):
        opcoes = []
        for i, res in enumerate(resultados[:10]): # Limitamos a 10 pra não poluir o chat
            # O Select Menu agora tem um nome curto, os detalhes ficam no Embed
            opcoes.append(discord.SelectOption(
                label=f"Opção {i + 1}", 
                description="Clique para baixar este grimório",
                value=str(i)
            ))

        super().__init__(placeholder="Selecione a opção desejada...", min_values=1, max_values=1, options=opcoes)
        self.resultados = resultados
        self.extrator = extrator
        self.regras = regras

    async def callback(self, interaction: discord.Interaction):
        escolha = self.resultados[int(self.values[0])]
        titulo_alvo = escolha.get('titulo_limpo', escolha['titulo'])
        
        await interaction.response.send_message(f"🧙‍♂️ **Feitiço conjurado!**\nIniciando o download de:\n`{titulo_alvo}`\n\n*Verifique os logs do terminal para acompanhar o progresso.*", ephemeral=False)
        
        # Inicia a tarefa em background usando a sessão viva do bot
        asyncio.create_task(self.extrator.baixar(escolha['id'], titulo_alvo, regras_capitulos=self.regras))

class ViewResultados(discord.ui.View):
    def __init__(self, resultados, extrator, regras):
        super().__init__(timeout=120)
        self.add_item(MenuResultados(resultados, extrator, regras))


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


# --- COMANDOS DO BOT ---

@bot.event
async def on_ready():
    print(f"[*] O Mago {bot.user} despertou e a sessão web está blindada.")

@bot.command()
async def manga(ctx, capitulos: str, *, busca: str):
    """Busca mangás no MangaDex. Ex: !manga todos Dandadan OU !manga 1-5 Berserk"""
    
    # Se o mago esquecer a regra e digitar só o nome, a string 'capitulos' pega a primeira palavra.
    # Ex: se ele digitar "!manga Gachiakuta", capitulos="Gachiakuta" e busca="". 
    # O Discord.py vai xingar antes mesmo de rodar o comando, exigindo os dois argumentos.
    
    msg = await ctx.send(f"🔍 Vasculhando o MangaDex por `{busca}` (Filtro: Capítulos {capitulos})...")
    
    # Transforma o texto "1-5" nas regras de tuplas que o nosso extrator entende
    regras_compiladas = compilar_regras_capitulos(capitulos)
    
    extrator = MangaDexCog(bot.web_session, os.path.join(PASTA_RAIZ, 'Mangas'))
    resultados = await extrator.buscar(busca)
    
    if not resultados:
        await msg.edit(content="❌ Nenhum grimório encontrado nas runas.")
        return

    embed = discord.Embed(title="📚 Mangás Encontrados", color=discord.Color.blue())
    descricao = ""
    for i, res in enumerate(resultados[:10]):
        descricao += f"**Opção {i + 1}:** {res['titulo']}\n\n"
    embed.description = descricao

    # Aqui a mágica acontece: passamos as regras_compiladas para o menu
    view = ViewResultados(resultados, extrator, regras=regras_compiladas)
    await msg.edit(content=None, embed=embed, view=view)

@bot.command()
async def torrent(ctx, tipo: str, *, busca: str):
    """Busca no Nyaa. Ex: !torrent anime Jujutsu Kaisen OU !torrent manga Berserk"""
    tipo = tipo.lower()
    if tipo not in ["anime", "manga"]:
        await ctx.send("⚠️ Use `!torrent anime <nome>` ou `!torrent manga <nome>`")
        return

    msg = await ctx.send(f"🏴‍☠️ Rastreando a rede P2P ({tipo.upper()}) por `{busca}`...")
    
    pasta_destino = os.path.join(PASTA_RAIZ, 'Animes' if tipo == 'anime' else 'Mangas')
    extrator = NyaaCog(bot.web_session, pasta_destino, tipo_midia=tipo)
    resultados = await extrator.buscar(busca)
    
    if not resultados:
        await msg.edit(content="❌ Nada encontrado. Tente buscar pelo nome original ou remova termos específicos.")
        return

    # Monta o Embed com os títulos longos do Torrent
    embed = discord.Embed(title=f"🏴‍☠️ Torrents P2P ({tipo.capitalize()})", color=discord.Color.green())
    descricao = ""
    for i, res in enumerate(resultados[:10]):
        descricao += f"**Opção {i + 1}:** {res['titulo']}\n\n"
    embed.description = descricao

    view = ViewResultados(resultados, extrator, regras=None)
    await msg.edit(content=None, embed=embed, view=view)


# Substitua pela token do ZBOT ou a nova que você gerar
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("[!] ERRO CRÍTICO: Token do Discord não encontrado no ficheiro .env!")
    exit()

bot.run(TOKEN)