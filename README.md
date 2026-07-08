# 🧙‍♂️ Projeto Merlin

O **Projeto Merlin** é uma ferramenta de automação assíncrona focada em web scraping de alta performance e rastreamento P2P para preservação de mídia digital local. 

O "motor" principal do projeto opera via Linha de Comando (CLI), interagindo com APIs públicas (como MangaDex) e indexadores BitTorrent (como Nyaa) para catalogar e arquivar mídias diretamente em servidores de armazenamento doméstico (NAS). Como funcionalidade secundária, o projeto inclui uma interface opcional via Bot do Discord para gestão remota.

## ⚙️ Arquitetura e Recursos Principais

* **Core de Raspagem (CLI):** O script principal (`main.py`) opera de forma independente, permitindo buscas e downloads diretos pelo terminal, ideal para servidores headless.
* **Design Assíncrono:** Utiliza `asyncio` e `aiohttp` para realizar requisições não-bloqueantes, garantindo velocidade máxima de I/O na rede.
* **Stateless Resume (Retomada Inteligente):** O sistema varre o disco antes de cada requisição. Em caso de queda de energia ou interrupção, o script ignora arquivos já arquivados localmente e retoma o download do exato ponto de parada.
* **Integração P2P (Torrent):** Captura de *Magnet Links* descentralizados, preparando o ambiente para integração nativa com clientes de torrent (qBittorrent/Transmission).
* **Interface Remota (Opcional):** Um módulo secundário (`bot.py`) permite que toda a infraestrutura de scraping seja controlada via comandos em um servidor privado do Discord.

## 🛠️ Tecnologias Utilizadas

* `Python 3.10+`
* `aiohttp` (Requisições HTTP assíncronas)
* `BeautifulSoup4` (Parseamento de HTML/DOM)
* `discord.py` (Interface secundária via WebSockets)
* `python-dotenv` (Gerenciamento seguro de credenciais)

## 🚀 Como Executar

Clone o repositório e instale as dependências:
```bash
git clone https://github.com/SuppaHackaD/Merlin_project.git
cd Merlin_project
pip install -r requirements.txt
```

### Opção A: Execução Principal (Terminal/CLI)
Inicie o motor principal para interagir diretamente pelo console:
```bash
python main.py
```

### Opção B: Interface Secundária (Bot do Discord)
1. Crie um arquivo `.env` na raiz do projeto.
2. Adicione o seu token: `DISCORD_TOKEN=seu_token_aqui`
3. Inicie a interface:
```bash
python bot.py
```

## 📜 Isenção de Responsabilidade (Disclaimer)


Este projeto tem fins estritamente educacionais e de pesquisa em automação, engenharia de software e preservação de dados descentralizados. Os desenvolvedores não hospedam, não distribuem e não se responsabilizam pelo conteúdo trafegado pelas APIs públicas de terceiros ou redes P2P integradas a este código.
