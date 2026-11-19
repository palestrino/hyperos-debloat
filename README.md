# HyperOS 1 Debloat

Remove bloatware de Xiaomi / Redmi / POCO com **HyperOS 1** (Android 14) pelo PC, **sem root** e sem desbloquear o bootloader. Interface gráfica em Python (Tkinter), tudo em português.

Funciona no **Windows, Linux e macOS** — o mesmo script, sem instalar nada além de Python e ADB.

## O que ele faz

- Detecta o aparelho por ADB e mostra modelo, Android e versão do HyperOS.
- Lista **84 pacotes curados** do HyperOS 1 com nome em português, categoria e nível de risco:
  - 🟢 **Seguro** — telemetria, anúncios (MSA, Analytics), Quick Apps, Mi Vídeo, Mi Música, Facebook pré-instalado etc.
  - 🟠 **Moderado** — app útil para alguns (GetApps, Mi Browser, Mi Remote, Mi Home, Gmail, Maps…). Só marque se não usa.
  - 🔴 **Cuidado** — perde uma função (Mi Cloud, Google Fotos, Always On Display, SIM virtual…). Leia a descrição antes.
- Presets: **Só Seguro** / **🚫 Só Anúncios** / **Seguro + Moderado** / todos visíveis.
- O preset **Só Anúncios** marca só os 34 pacotes que trazem anúncio: serviços de anúncio (MSA, System Ad Solution, Serviço de Anúncios Xiaomi) e os apps que exibem banners e recomendações — GetApps, Mi Vídeo, Mi Música, Mi Browser, Temas, Galeria, Gerenciador de Arquivos, Limpador, Carrossel da tela de bloqueio e outros.
- Busca (sem acento) e filtro por risco e categoria.
- **Desinstalar** com `pm uninstall -k --user 0` (só para o usuário 0 — não mexe na partição `/system`, não quebra banco nem OTA).
- **Restaurar** com `cmd package install-existing` — pacote por pacote ou os selecionados.
- **Pacote avulso**: remova ou restaure qualquer pacote digitando o nome.
- **Simular**: mostra os comandos sem executar nada.
- **Exportar script**: gera um `debloat_hyperos.bat` (Windows) ou `debloat_hyperos.sh` (Linux/macOS) com os pacotes marcados, para rodar depois sem a GUI.
- **Backup automático**: a cada remoção ele salva um `restore_hyperos_AAAA-MM-DD_HH-MM-SS.txt` ao lado do script, com todos os pacotes removidos e o comando para restaurar cada um.

## O que ele NUNCA remove

Bloqueado no programa, mesmo por pacote avulso:

`com.miui.securitycenter`, `com.lbe.security.miui`, `com.miui.guardprovider`, `com.xiaomi.finddevice`, `com.miui.home`, `com.android.systemui`, `com.android.updater`, `com.miui.powerkeeper`, `com.xiaomi.account`, `com.xiaomi.micloud.sdk` e outros pacotes críticos.

Remover o Security Center é a causa mais comum de **bootloop** em Xiaomi — por isso ele nem aparece na lista.

## Requisitos

### Windows

1. **Python 3.8+** — baixe em https://www.python.org/downloads/ e marque **“Add Python to PATH”** na instalação.
2. **ADB (platform-tools)** — o programa procura em: PATH, `platform-tools\` ao lado do script, `adb.exe` ao lado do script, `C:\platform-tools` e `%LOCALAPPDATA%\Android\Sdk\platform-tools`.
   - Não tem? Clique em **Baixar ADB** dentro do programa (site oficial do Google), extraia o ZIP e coloque a pasta `platform-tools` ao lado do `hyperos_debloat.py`.

### Linux

```bash
# Debian / Ubuntu
sudo apt install python3 python3-tk adb

# Arch Linux
sudo pacman -S python python-tk android-tools

# Fedora
sudo dnf install python3 python3-tkinter android-tools
```

### macOS

```bash
brew install python android-platform-tools
# Se faltar o Tkinter:
brew install python-tk@3.12
```

## Passo a passo

### 1. Ativar a depuração USB no celular

1. Configurações > Sobre o telefone.
2. Toque **7 vezes** em “Versão do HyperOS” até aparecer “Você já é um desenvolvedor!”.
3. Volte em Configurações > Configurações adicionais > Opções do desenvolvedor.
4. Ative **Depuração USB**.
5. Conecte o celular no PC (use o cabo original, de preferência numa porta traseira).
6. No celular, toque em **Permitir** na janela “Permitir depuração USB?”.

### 2. Abrir o programa

- **Windows:** extraia o ZIP e dê dois cliques em **`iniciar.bat`** (ou rode `python hyperos_debloat.py` no prompt).
- **Linux / macOS:** extraia e rode `./iniciar.sh` no terminal (ou `python3 hyperos_debloat.py`).
- Clique em **Conectar / Atualizar**. Tem que aparecer o modelo do aparelho no topo, com ✅.
- Se aparecer “unauthorized”, desconecte, reconecte e autorize de novo no celular.
- Se aparecer “Nenhum aparelho encontrado”, troque o cabo/porta e confira a depuração USB.

### 3. Fazer o debloat

1. Comece pelo preset **✅ Só Seguro** — é o que mais limpa anúncios e telemetria sem risco.
2. Para focar só nos anúncios, use o preset **🚫 Só Anúncios**. Revise os Moderados dessa lista um por um (Galeria, Gerenciador de Arquivos e Temas fazem falta se você usa — instale um substituto antes de remover).
3. Se quiser mais, revise os **Moderados** um por um (desmarque o que você usa).
4. **Não marque os de Cuidado sem ler a descrição.**
5. Clique em **🗑 Desinstalar selecionados** e confirme.
6. Reinicie o celular.

### 4. Anúncios que não saem só com debloat

Nem todo anúncio é um pacote removível. Segurança, Downloads e o instalador de apps não podem ser removidos — para esses, o programa tem o botão **💡 Anúncios que sobram**, com o passo a passo:

1. **Revogar o MSA:** Configurações > Senhas e segurança (ou Impressões digitais e bloqueio de tela) > Autorização e revogação > desative `msa` (e o MiuiDaemon, se aparecer). Pode precisar de dados móveis ligados e de uma segunda tentativa.
2. **Privacidade > Serviços de anúncios** > desative “Recomendações de anúncios personalizados”.
3. Em cada app Xiaomi, desligue **“Receber recomendações”**: Segurança, Downloads, Gerenciador de Arquivos, Galeria, Temas, Mi Vídeo e Mi Música.
4. **DNS privado** `dns.adguard.com` (Configurações > Mais opções de conectividade > DNS privado) bloqueia boa parte dos anúncios na rede.

Depois de uma atualização grande do HyperOS, confira esses ajustes — a Xiaomi costuma religar alguns.

### 5. Se algo der errado

- Marque o pacote na lista e clique em **↩ Restaurar selecionados**.
- Ou use o arquivo `restore_hyperos_*.txt` salvo ao lado do script.
- Último recurso: restauração de fábrica devolve tudo (faça backup dos seus dados antes de qualquer debloat).

## Arquivos

| Arquivo | O que é |
|---|---|
| `hyperos_debloat.py` | O programa (GUI Tkinter, Python, só biblioteca padrão) |
| `iniciar.bat` | Launcher para Windows — dois cliques e abre |
| `iniciar.sh` | Launcher para Linux e macOS — `./iniciar.sh` |
| `README.md` | Este guia |
| `LICENSE` | Licença MIT |

## Observações

- Atualizações grandes do HyperOS podem reinstalar apps removidos. É só rodar o programa de novo.
- A lista foi conferida em 2026-11-19 a partir de listas públicas de HyperOS/MIUI (MySystemApp, DEV Community, Debloater-Enhanced). Pacotes variam por modelo e região — o programa só remove o que estiver instalado, e mostra ✅ ao lado dos que estão no aparelho.
- Faça backup dos seus dados antes. O debloat é reversível, mas backup nunca é demais.
- Versão 1.1.0 — multiplataforma (Windows, Linux, macOS). Para HyperOS 2 a lista é parecida, mas alguns pacotes mudaram de nome; confira a lista antes de usar.

## Licença

MIT — veja `LICENSE`.
