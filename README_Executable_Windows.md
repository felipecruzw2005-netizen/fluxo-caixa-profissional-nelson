
# Fluxo Pro — Executável Windows (1 clique)

## Como gerar o .exe (Windows)
1) Instale Python 3.10+ e **Git**.
2) Extraia esta pasta em um diretório sem espaços (ex.: `C:\FluxoPro`).
3) **Clique duas vezes** em `build_windows.bat`.
4) Ao final, abra `dist\FluxoPro\FluxoPro.exe` (crie atalho para a área de trabalho).

> Atualizações futuras: substitua os arquivos do projeto e rode `build_windows.bat` novamente.

## Rodar sem empacotar (modo portátil)
Clique em `run_portable.bat` — ele cria a venv, instala dependências e abre o app.

## Onde ficam os dados?
- Banco de dados: `.\data\fluxo.db`
- Uploads: `.\data\uploads\`

Você pode **backupar** apenas essa pasta `data\`.

## Dicas
- Se o firewall perguntar, permita acesso local.
- Se o antivírus acusar falso positivo (comum com .exe novos), marque como confiável.
