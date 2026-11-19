#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HyperOS 1 Debloat — GUI para Windows, Linux e macOS
=====================================
Remove bloatware de Xiaomi / Redmi / POCO com HyperOS 1 (Android 14)
via ADB, sem root e sem desbloquear o bootloader.

Como funciona:
  adb shell pm uninstall -k --user 0 <pacote>
  -> remove só para o usuário 0, NÃO mexe na partição /system.
  -> reversível com: adb shell cmd package install-existing <pacote>
     ou com uma restauração de fábrica.

NUNCA remove (bloqueado no programa):
  com.miui.securitycenter, com.lbe.security.miui, com.miui.guardprovider,
  com.xiaomi.finddevice, com.miui.home, com.android.systemui,
  com.android.updater, com.miui.powerkeeper, com.xiaomi.account, etc.
  Remover o Security Center é a causa mais comum de bootloop em Xiaomi.

Requisitos:
  1. Python 3.8+ com Tkinter.
     Windows: instale em python.org e marque "Add Python to PATH",
       ou use o iniciar.bat que acompanha este script.
     Linux (Debian/Ubuntu): sudo apt install python3 python3-tk adb
     Linux (Arch): sudo pacman -S python python-tk android-tools
     Linux (Fedora): sudo dnf install python3 python3-tkinter android-tools
     macOS: brew install python android-platform-tools
       (o Tkinter já vem no Python do Homebrew; se faltar:
        brew install python-tk@3.12)
     Ou rode ./iniciar.sh (Linux/macOS), que confere tudo.
  2. Platform-tools (ADB) — o programa procura em:
     PATH, pasta platform-tools/ ao lado do script, adb ao lado
     do script, e nos locais padrão de cada sistema:
     Windows: C:\\platform-tools, %LOCALAPPDATA%\\Android\\Sdk\\platform-tools
     Linux: ~/Android/Sdk/platform-tools, /usr/lib/android-sdk/platform-tools
     macOS: ~/Library/Android/sdk/platform-tools, /opt/homebrew/bin/adb
     Se não achar, use o botão "Baixar ADB" (site oficial do Google).
  3. No celular: Configurações > Sobre o telefone > toque 7x em
     "Versão do HyperOS" (ou "Versão da MIUI") para ativar Opções do
     desenvolvedor, depois ative "Depuração USB" e autorize o PC.

Uso: python3 hyperos_debloat.py
     Windows: dois cliques em iniciar.bat
     Linux/macOS: ./iniciar.sh
Autor: feito para Francisco — HyperOS 1, pt-BR.
Versão: 1.1.0 (2026-11-19) — versão multiplataforma (Windows/Linux/macOS)
"""

import os
import re
import shutil
import subprocess
import sys
import threading
import unicodedata
import webbrowser
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:
    print("Falta o Tkinter (interface gráfica do Python).")
    print("  Debian/Ubuntu: sudo apt install python3-tk")
    print("  Arch:          sudo pacman -S python-tk")
    print("  Fedora:        sudo dnf install python3-tkinter")
    print("  macOS:         brew install python-tk@3.12")
    print("  Windows:       reinstale o Python marcando 'tcl/tk and IDLE'.")
    sys.exit(1)

VERSION = "1.1.0"
# Fontes por sistema (o Tkinter usa a padrão se o nome não existir).
if sys.platform == "darwin":
    UI_FONT, MONO_FONT = "Helvetica", "Menlo"
elif os.name == "nt":
    UI_FONT, MONO_FONT = "Segoe UI", "Consolas"
else:
    UI_FONT, MONO_FONT = "DejaVu Sans", "DejaVu Sans Mono"
ADB_DOWNLOAD_URL = "https://developer.android.com/tools/releases/platform-tools"

# ---------------------------------------------------------------------------
# Listas curadas — HyperOS 1 (global). Fontes conferidas em 2026-11-19:
# mysystemapp.com (lista Xiaomi/HyperOS), dev.to — Debloating MIUI/HyperOS,
# zerosuniverse ADB Debloater e Debloater-Enhanced (GitHub).
# Risco:
#   Seguro   = telemetria, anúncios e apps que ninguém sente falta.
#   Moderado = app útil para alguns — só marque se não usa.
#   Cuidado  = perde uma função (nuvem, fotos, AOD...). Leia a descrição.
# ---------------------------------------------------------------------------
# (pacote, nome em pt-BR, categoria, risco, descrição)
PACKAGES = [
    # --- Anúncios e telemetria (comece por aqui) ---
    ("com.miui.msa.global", "MSA — Anúncios do Sistema", "Anúncios e Telemetria", "Seguro",
     "Serviço de anúncios da Xiaomi dentro dos apps do sistema."),
    ("com.miui.systemAdSolution", "System Ad Solution", "Anúncios e Telemetria", "Seguro",
     "Solução de anúncios do sistema."),
    ("com.xiaomi.ad.service", "Serviço de Anúncios Xiaomi", "Anúncios e Telemetria", "Seguro",
     "Segundo serviço de anúncios do sistema (além do MSA)."),
    ("com.miui.contentcatcher", "Content Catcher", "Anúncios e Telemetria", "Seguro",
     "Coleta conteúdo do aparelho para recomendações e anúncios."),
    ("com.miui.analytics", "Analytics Xiaomi", "Anúncios e Telemetria", "Seguro",
     "Telemetria de uso do aparelho."),
    ("com.miui.daemon", "Daemon (diagnóstico)", "Anúncios e Telemetria", "Seguro",
     "Coleta dados de diagnóstico em segundo plano."),
    ("com.miui.bugreport", "Feedback / Bug Report", "Anúncios e Telemetria", "Seguro",
     "Envio de relatórios de erro para a Xiaomi."),
    ("com.miui.miservice", "Mi Service", "Anúncios e Telemetria", "Seguro",
     "Serviço de telemetria da Xiaomi."),
    ("com.miui.hybrid", "Quick Apps", "Anúncios e Telemetria", "Seguro",
     "Mini-apps instantâneos (anúncios/recomendações)."),
    ("com.miui.hybrid.accessory", "Quick Apps Acessório", "Anúncios e Telemetria", "Seguro",
     "Complemento do Quick Apps."),
    ("com.xiaomi.joyose", "Joyose", "Anúncios e Telemetria", "Moderado",
     "Ajusta desempenho/temperatura em jogos. Sem ele, jogos podem se comportar diferente."),
    ("com.miui.miwallpaper", "Carrossel de Papéis de Parede", "Anúncios e Telemetria", "Seguro",
     "Troca o papel de parede da tela de bloqueio (com anúncios)."),
    ("com.miui.android.fashiongallery", "Carrossel de Papéis de Parede (variante)", "Anúncios e Telemetria", "Seguro",
     "Variante do carrossel da tela de bloqueio, também com anúncios."),
    ("com.miui.personalassistant", "Assistente Pessoal / App Vault", "Anúncios e Telemetria", "Seguro",
     "Painel de recomendações à esquerda da tela inicial (variante)."),
    ("com.miui.yellowpage", "Yellow Page", "Anúncios e Telemetria", "Seguro",
     "Identificador de empresas/ligações comerciais."),
    ("com.miui.translation.youdao", "Tradutor Youdao", "Anúncios e Telemetria", "Seguro",
     "Tradutor embutido (chinês)."),
    ("com.miui.translation.kingsoft", "Tradutor Kingsoft", "Anúncios e Telemetria", "Seguro",
     "Tradutor embutido (chinês)."),
    # --- Loja, pagamentos e apps Xiaomi ---
    ("com.xiaomi.mipicks", "GetApps", "Loja e Pagamentos", "Moderado",
     "Loja da Xiaomi. Alguns apps Xiaomi só atualizam por ela."),
    ("com.xiaomi.market", "Mi Market (GetApps CN)", "Loja e Pagamentos", "Moderado",
     "Variante chinesa da loja GetApps."),
    ("com.xiaomi.shop", "Mi Store", "Loja e Pagamentos", "Seguro",
     "Loja oficial Xiaomi."),
    ("com.xiaomi.discover", "Discover", "Loja e Pagamentos", "Seguro",
     "Descoberta de apps/conteúdo Xiaomi."),
    ("com.xiaomi.payment", "Mi Pay / Pagamento", "Loja e Pagamentos", "Moderado",
     "Pagamentos Xiaomi. Só remova se não usa Mi Pay."),
    ("com.mipay.wallet.in", "Carteira Mi (global)", "Loja e Pagamentos", "Moderado",
     "Carteira Mi Pay — versão global."),
    ("com.mipay.wallet", "Carteira Mi", "Loja e Pagamentos", "Moderado",
     "Carteira Mi Pay."),
    ("com.xiaomi.mirecycle", "Mi Recycle", "Loja e Pagamentos", "Seguro",
     "Programa de reciclagem/troca Xiaomi."),
    ("com.mi.globalminusscreen", "App Vault (tela -1)", "Xiaomi", "Seguro",
     "Painel à esquerda da tela inicial (atalhos/notícias)."),
    ("com.miui.videoplayer", "Mi Vídeo", "Xiaomi", "Seguro",
     "Player de vídeo da Xiaomi."),
    ("com.miui.player", "Mi Música", "Xiaomi", "Seguro",
     "Player de música da Xiaomi."),
    ("com.mi.globalbrowser", "Mi Browser", "Xiaomi", "Moderado",
     "Navegador Mi. Só remova se já tiver outro navegador padrão."),
    ("com.miui.browser", "Mi Browser (variante)", "Xiaomi", "Moderado",
     "Variante do navegador Mi."),
    ("com.xiaomi.glgm", "Games (Game Hub)", "Xiaomi", "Seguro",
     "Central de jogos Xiaomi."),
    ("com.xiaomi.gamecenter", "Game Center", "Xiaomi", "Seguro",
     "Central de jogos Xiaomi."),
    ("com.miui.gamecenter", "Game Center (variante)", "Xiaomi", "Seguro",
     "Variante da central de jogos."),
    ("com.duokan.phone.remotecontroller", "Mi Remote", "Xiaomi", "Moderado",
     "Controle remoto por infravermelho. Perde o controle se usa."),
    ("com.xiaomi.smarthome", "Mi Home", "Xiaomi", "Moderado",
     "Controle de casa inteligente Xiaomi. Perde se usa."),
    ("com.xiaomi.midrop", "Mi Drop", "Xiaomi", "Moderado",
     "Compartilhamento de arquivos Xiaomi."),
    ("com.miui.mishare.connectivity", "Mi Share", "Xiaomi", "Moderado",
     "Compartilhamento rápido entre aparelhos Xiaomi."),
    ("com.miui.cloudservice", "Mi Cloud", "Xiaomi", "Cuidado",
     "Sincronização Mi Cloud. Perde sincronização/backup na nuvem Xiaomi."),
    ("com.miui.cloudbackup", "Backup Mi Cloud", "Xiaomi", "Cuidado",
     "Backup na Mi Cloud. Perde o backup automático Xiaomi."),
    ("com.miui.notes", "Notas Mi", "Xiaomi", "Moderado",
     "Bloco de notas Xiaomi. Exporte suas notas antes."),
    ("com.miui.weather", "Clima", "Xiaomi", "Moderado",
     "App de clima Xiaomi."),
    ("com.miui.compass", "Bússola", "Xiaomi", "Seguro",
     "Bússola."),
    ("com.miui.fm", "Rádio FM", "Xiaomi", "Seguro",
     "Rádio FM."),
    ("com.miui.calculator", "Calculadora Mi", "Xiaomi", "Moderado",
     "Calculadora Xiaomi. Tenha outra instalada antes."),
    ("com.miui.screenrecorder", "Gravador de Tela", "Xiaomi", "Moderado",
     "Gravação de tela nativa. Perde o recurso."),
    ("com.miui.voiceassist", "Assistente Mi AI", "Xiaomi", "Seguro",
     "Assistente de voz Xiaomi (não usado no Brasil)."),
    ("com.xiaomi.aiasst.vision", "Visão IA", "Xiaomi", "Seguro",
     "Recurso de visão do assistente Xiaomi."),
    ("com.miui.touchassistant", "Bola Flutuante", "Xiaomi", "Moderado",
     "Atalho flutuante na tela."),
    ("com.miui.aod", "Always On Display", "Xiaomi", "Moderado",
     "Tela sempre ativa. Perde o AOD."),
    ("com.xiaomi.scanner", "Scanner", "Xiaomi", "Seguro",
     "Leitor de QR / documentos."),
    ("com.xiaomi.barcode", "Leitor de Código", "Xiaomi", "Seguro",
     "Leitor de código de barras."),
    ("com.miui.smarttravel", "Viagem Inteligente", "Xiaomi", "Seguro",
     "Assistente de viagens Xiaomi."),
    ("com.miui.vsim", "SIM Virtual", "Xiaomi", "Cuidado",
     "SIM virtual Xiaomi. Não remova se usa eSIM da Xiaomi."),
    ("com.miui.cleanmaster", "Limpador (Clean Master)", "Xiaomi", "Moderado",
     "Limpador de arquivos. A Limpeza segue no app Segurança."),
    ("com.miui.cleaner", "Limpador (variante)", "Xiaomi", "Moderado",
     "Variante do app Limpador, com recomendações e anúncios."),
    ("com.mi.android.globalFileexplorer", "Gerenciador de Arquivos Mi", "Xiaomi", "Moderado",
     "Mostra anúncios e recomendações. Instale outro gerenciador antes; sem ele não dá pra escolher toque personalizado nem aplicar temas de terceiros."),
    ("com.android.fileexplorer", "Gerenciador de Arquivos (variante)", "Xiaomi", "Moderado",
     "Variante do gerenciador de arquivos, também com anúncios."),
    ("com.miui.gallery", "Galeria Mi", "Xiaomi", "Moderado",
     "Mostra recomendações e anúncios. Perde a galeria e a prévia de captura de tela — use o Google Fotos antes."),
    ("com.android.thememanager", "Temas", "Xiaomi", "Moderado",
     "Loja de temas com anúncios. Perde a troca de temas (o tema atual continua)."),
    # --- Parceiros / pré-instalados ---
    ("com.facebook.system", "Facebook System", "Parceiros", "Seguro",
     "Serviço de sistema do Facebook (pré-instalado)."),
    ("com.facebook.appmanager", "Facebook App Manager", "Parceiros", "Seguro",
     "Gerenciador do Facebook (pré-instalado)."),
    ("com.facebook.services", "Facebook Services", "Parceiros", "Seguro",
     "Serviços do Facebook (pré-instalado)."),
    ("com.facebook.katana", "Facebook", "Parceiros", "Seguro",
     "App Facebook pré-instalado (reinstalável pela Play Store)."),
    ("com.facebook.orca", "Messenger", "Parceiros", "Moderado",
     "Messenger pré-instalado."),
    ("com.instagram.android", "Instagram", "Parceiros", "Moderado",
     "Instagram pré-instalado (reinstalável pela Play Store)."),
    ("com.linkedin.android", "LinkedIn", "Parceiros", "Seguro",
     "LinkedIn pré-instalado."),
    ("com.spotify.music", "Spotify", "Parceiros", "Moderado",
     "Spotify pré-instalado."),
    ("com.netflix.mediaclient", "Netflix", "Parceiros", "Moderado",
     "Netflix pré-instalado."),
    ("com.netflix.partner", "Netflix Partner", "Parceiros", "Seguro",
     "Serviço parceiro Netflix."),
    ("com.amazon.mShop.android.shopping", "Amazon Shopping", "Parceiros", "Moderado",
     "Amazon pré-instalada."),
    ("com.microsoft.skydrive", "OneDrive", "Parceiros", "Moderado",
     "OneDrive pré-instalado."),
    ("com.booking", "Booking.com", "Parceiros", "Seguro",
     "Booking pré-instalado."),
    ("com.ebay.mobile", "eBay", "Parceiros", "Seguro",
     "eBay pré-instalado."),
    ("com.wps.moffice_eng", "WPS Office", "Parceiros", "Moderado",
     "WPS Office pré-instalado."),
    # --- Google (só se não usa) ---
    ("com.google.android.apps.docs", "Google Docs", "Google", "Moderado",
     "Docs pré-instalado."),
    ("com.google.android.apps.photos", "Google Fotos", "Google", "Cuidado",
     "Perde o backup de fotos do Google se usa."),
    ("com.google.android.youtube", "YouTube", "Google", "Moderado",
     "YouTube pré-instalado."),
    ("com.google.android.apps.youtube.music", "YouTube Music", "Google", "Moderado",
     "YouTube Music pré-instalado."),
    ("com.google.android.apps.maps", "Maps", "Google", "Moderado",
     "Google Maps pré-instalado."),
    ("com.google.android.gm", "Gmail", "Google", "Moderado",
     "Gmail pré-instalado."),
    ("com.google.android.apps.tachyon", "Meet (Duo)", "Google", "Seguro",
     "Google Meet pré-instalado."),
    ("com.google.android.apps.wellbeing", "Bem-estar Digital", "Google", "Seguro",
     "Bem-estar digital do Google."),
    ("com.android.chrome", "Chrome", "Google", "Moderado",
     "Chrome pré-instalado. Tenha outro navegador antes."),
    ("com.google.android.apps.fitness", "Google Fit", "Google", "Seguro",
     "Google Fit pré-instalado."),
]

# NUNCA remover — bloqueado no programa, mesmo por pacote personalizado.
NEVER_REMOVE = {
    "com.miui.securitycenter", "com.lbe.security.miui", "com.miui.guardprovider",
    "com.miui.securitycore", "com.miui.securityadd",
    "com.xiaomi.finddevice", "com.miui.home", "com.android.systemui",
    "com.android.settings", "com.android.phone", "com.android.contacts",
    "com.android.updater", "com.miui.powerkeeper", "com.xiaomi.account",
    "com.android.packageinstaller", "com.google.android.packageinstaller",
    "com.miui.packageinstaller", "com.android.providers.settings",
    "com.android.providers.media", "com.android.providers.telephony",
    "com.android.providers.contacts", "com.android.providers.downloads",
    "com.xiaomi.micloud.sdk",
}

RISK_COLORS = {"Seguro": "#2e7d32", "Moderado": "#e65100", "Cuidado": "#b71c1c"}

# Pacotes que trazem anúncios — usados pelo preset "Só Anúncios".
# Inclui os serviços de anúncio e os apps que exibem banners/recomendações.
AD_PACKAGES = {
    "com.miui.msa.global", "com.miui.systemAdSolution", "com.xiaomi.ad.service",
    "com.miui.analytics", "com.miui.daemon", "com.miui.bugreport",
    "com.miui.miservice", "com.miui.hybrid", "com.miui.hybrid.accessory",
    "com.miui.contentcatcher", "com.miui.miwallpaper",
    "com.miui.android.fashiongallery", "com.miui.yellowpage",
    "com.mi.globalminusscreen", "com.miui.personalassistant",
    "com.xiaomi.mipicks", "com.xiaomi.market", "com.xiaomi.shop",
    "com.xiaomi.discover", "com.miui.videoplayer", "com.miui.player",
    "com.mi.globalbrowser", "com.miui.browser", "com.xiaomi.glgm",
    "com.xiaomi.gamecenter", "com.miui.gamecenter", "com.miui.notes",
    "com.miui.weather", "com.miui.cleanmaster", "com.miui.cleaner",
    "com.mi.android.globalFileexplorer", "com.android.fileexplorer",
    "com.miui.gallery", "com.android.thememanager",
}


def _norm(s):
    """Minúsculas sem acento — 'Mi Vídeo' vira 'mi video' na busca."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def find_adb():
    """Procura o adb em ordem: PATH, ao lado do script, locais comuns
    de Windows, Linux e macOS."""
    exe = "adb.exe" if os.name == "nt" else "adb"
    found = shutil.which(exe) or shutil.which("adb")
    if found:
        return found
    base = os.path.dirname(os.path.abspath(__file__))
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(base, "platform-tools", exe),
        os.path.join(base, exe),
        os.path.join(base, "platform-tools", "adb"),
        # Windows
        r"C:\platform-tools\adb.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
        # Linux
        os.path.join(home, "Android/Sdk/platform-tools/adb"),
        os.path.join(home, "android-sdk/platform-tools/adb"),
        "/usr/lib/android-sdk/platform-tools/adb",
        "/opt/android-sdk/platform-tools/adb",
        # macOS
        os.path.join(home, "Library/Android/sdk/platform-tools/adb"),
        "/opt/homebrew/bin/adb",
        "/usr/local/bin/adb",
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def run_adb(adb, args, timeout=30):
    """Roda um comando adb e devolve (ok, stdout+stderr)."""
    try:
        r = subprocess.run(
            [adb] + args, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
        )
        return r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return False, "Tempo esgotado (timeout)."
    except Exception as e:  # noqa: BLE001 - mostrar o erro no log
        return False, str(e)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"HyperOS 1 Debloat  •  v{VERSION}")
        self.geometry("1020x760")
        self.minsize(880, 620)
        self.adb = find_adb()
        self.installed = set()
        self.device_info = {}
        self.vars = {}          # pacote -> BooleanVar
        self.rows = {}          # pacote -> frame da linha
        self.busy = False
        self._build_ui()
        self._apply_filter()
        self.after(200, self.refresh_device)

    # ---------------- UI ----------------
    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="HyperOS 1 Debloat", font=(UI_FONT, 16, "bold")).pack(side="left")
        ttk.Label(top, text="  Xiaomi • Redmi • POCO  —  sem root, reversível  •  Windows / Linux / macOS",
                  font=(UI_FONT, 10)).pack(side="left", pady=(6, 0))
        ttk.Label(top, text=f"v{VERSION}", font=(UI_FONT, 9)).pack(side="right")

        # --- Dispositivo / ADB ---
        dev = ttk.LabelFrame(self, text=" Aparelho e ADB ", padding=10)
        dev.pack(fill="x", padx=10, pady=(0, 8))
        self.lbl_device = ttk.Label(dev, text="Procurando aparelho…", font=(UI_FONT, 10))
        self.lbl_device.pack(side="left", fill="x", expand=True)
        ttk.Button(dev, text="↻ Conectar / Atualizar", command=self.refresh_device).pack(side="left", padx=4)
        ttk.Button(dev, text="Baixar ADB", command=self._download_adb).pack(side="left", padx=4)
        ttk.Button(dev, text="Como ativar a depuração USB", command=self._show_help).pack(side="left", padx=4)
        ttk.Button(dev, text="💡 Anúncios que sobram", command=self._show_ads_tips).pack(side="left", padx=4)

        # --- Filtros e presets ---
        bar = ttk.Frame(self, padding=(10, 0))
        bar.pack(fill="x")
        ttk.Label(bar, text="Buscar:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(bar, textvariable=self.search_var, width=28).pack(side="left", padx=4)

        ttk.Label(bar, text="Risco:").pack(side="left", padx=(10, 0))
        self.risk_var = tk.StringVar(value="Todos")
        risk_cb = ttk.Combobox(bar, textvariable=self.risk_var, width=11,
                               values=["Todos", "Seguro", "Moderado", "Cuidado"], state="readonly")
        risk_cb.pack(side="left", padx=4)
        risk_cb.bind("<<ComboboxSelected>>", lambda *_: self._apply_filter())

        ttk.Label(bar, text="Categoria:").pack(side="left", padx=(10, 0))
        cats = ["Todas"] + sorted({p[2] for p in PACKAGES})
        self.cat_var = tk.StringVar(value="Todas")
        cat_cb = ttk.Combobox(bar, textvariable=self.cat_var, width=20, values=cats, state="readonly")
        cat_cb.pack(side="left", padx=4)
        cat_cb.bind("<<ComboboxSelected>>", lambda *_: self._apply_filter())

        presets = ttk.Frame(self, padding=(10, 6))
        presets.pack(fill="x")
        ttk.Label(presets, text="Presets:").pack(side="left")
        ttk.Button(presets, text="✅ Só Seguro", command=lambda: self._preset("Seguro")).pack(side="left", padx=3)
        ttk.Button(presets, text="🚫 Só Anúncios", command=self._preset_ads).pack(side="left", padx=3)
        ttk.Button(presets, text="👍 Seguro + Moderado", command=lambda: self._preset("Moderado")).pack(side="left", padx=3)
        ttk.Button(presets, text="☑ Todos visíveis", command=self._select_visible).pack(side="left", padx=3)
        ttk.Button(presets, text="☐ Limpar seleção", command=self._clear_selection).pack(side="left", padx=3)
        self.lbl_count = ttk.Label(presets, text="0 selecionados", font=(UI_FONT, 10, "bold"))
        self.lbl_count.pack(side="right")

        # --- Lista rolável de pacotes ---
        list_frame = ttk.LabelFrame(self, text=" Pacotes — marque o que quer remover ", padding=6)
        list_frame.pack(fill="both", expand=True, padx=10, pady=4)
        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.list_inner = ttk.Frame(canvas)
        self.list_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.list_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- Pacote personalizado ---
        custom = ttk.Frame(self, padding=(10, 4))
        custom.pack(fill="x")
        ttk.Label(custom, text="Pacote avulso:").pack(side="left")
        self.custom_var = tk.StringVar()
        ttk.Entry(custom, textvariable=self.custom_var, width=42).pack(side="left", padx=4)
        ttk.Button(custom, text="Remover este", command=self._remove_custom).pack(side="left", padx=3)
        ttk.Button(custom, text="Restaurar este", command=self._restore_custom).pack(side="left", padx=3)
        ttk.Label(custom, text="ex.: com.exemplo.app", foreground="gray").pack(side="left", padx=6)

        # --- Ações ---
        actions = ttk.Frame(self, padding=10)
        actions.pack(fill="x")
        self.btn_uninstall = ttk.Button(actions, text="🗑  Desinstalar selecionados",
                                        command=self._uninstall_selected)
        self.btn_uninstall.pack(side="left", padx=3)
        ttk.Button(actions, text="↩  Restaurar selecionados",
                   command=self._restore_selected).pack(side="left", padx=3)
        ttk.Button(actions, text="🧪 Simular (só mostrar comandos)",
                   command=self._simulate).pack(side="left", padx=3)
        ttk.Button(actions, text="💾 Exportar script",
                   command=self._export_script).pack(side="left", padx=3)
        ttk.Button(actions, text="📋 Copiar lista p/ restaurar",
                   command=self._copy_restore_list).pack(side="left", padx=3)

        # --- Log ---
        log_frame = ttk.LabelFrame(self, text=" Log ", padding=6)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_text = tk.Text(log_frame, height=9, wrap="word", font=(MONO_FONT, 9))
        self.log_text.pack(fill="both", expand=True)
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=(0, 8))

    # ---------------- helpers ----------------
    def log(self, msg):
        self.log_text.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")
        self.update_idletasks()

    def _set_busy(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.btn_uninstall.configure(state=state)
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def _download_adb(self):
        webbrowser.open(ADB_DOWNLOAD_URL)
        self.log("Abrindo o download oficial do platform-tools (Google).")
        if os.name == "nt":
            where = "pasta 'platform-tools' ao lado deste script (ou em C:\\platform-tools)."
        elif sys.platform == "darwin":
            where = ("pasta 'platform-tools' ao lado deste script, ou instale com:\n"
                     "    brew install android-platform-tools")
        else:
            where = ("pasta 'platform-tools' ao lado deste script, ou instale com:\n"
                     "    Debian/Ubuntu: sudo apt install adb\n"
                     "    Arch: sudo pacman -S android-tools")
        messagebox.showinfo(
            "Baixar ADB",
            "Baixe o platform-tools no site oficial, extraia o ZIP e coloque a\n"
            + where + "\nDepois clique em 'Conectar / Atualizar'.")

    def _show_help(self):
        messagebox.showinfo(
            "Ativar a depuração USB — HyperOS 1",
            "1. No celular: Configurações > Sobre o telefone\n"
            "2. Toque 7 vezes em 'Versão do HyperOS' até aparecer\n"
            "    'Você já é um desenvolvedor!'\n"
            "3. Volte: Configurações > Configurações adicionais >\n"
            "    Opções do desenvolvedor > ative 'Depuração USB'\n"
            "4. Conecte o celular no PC por cabo USB\n"
            "5. No celular, toque em 'Permitir' na janela\n"
            "    'Permitir depuração USB?'\n"
            "6. Aqui no programa, clique em 'Conectar / Atualizar'\n\n"
            "Dica: use o cabo original e a porta USB traseira do PC.\n"
            "Se aparecer 'unauthorized', desconecte, reconecte e autorize de novo.")

    def _show_ads_tips(self):
        messagebox.showinfo(
            "Anúncios que não saem só com debloat",
            "Nem todo anúncio é um pacote que dá pra remover:\n"
            "Segurança, Downloads e o instalador de apps não podem\n"
            "ser removidos. Para esses, desligue na mão:\n\n"
            "1. Revogar o MSA: Configurações > Senhas e segurança\n"
            "    (ou Impressões digitais e bloqueio de tela) >\n"
            "    Autorização e revogação > desative 'msa' (e o\n"
            "    MiuiDaemon, se aparecer). Pode precisar de dados\n"
            "    móveis ligados e de uma segunda tentativa.\n\n"
            "2. Privacidade > Serviços de anúncios > desative\n"
            "    'Recomendações de anúncios personalizados'.\n\n"
            "3. Em cada app Xiaomi, desligue 'Receber\n"
            "    recomendações': Segurança, Downloads, Gerenciador\n"
            "    de Arquivos, Galeria, Temas, Mi Vídeo e Mi Música\n"
            "    (engrenagem ou ⋮ > Configurações do app).\n\n"
            "4. DNS privado: Configurações > Mais opções de\n"
            "    conectividade > DNS privado > 'dns.adguard.com'\n"
            "    — bloqueia boa parte dos anúncios na rede.\n\n"
            "Depois de uma atualização grande do HyperOS, confira\n"
            "esses ajustes: a Xiaomi costuma religar alguns.")

    # ---------------- dispositivo ----------------
    def refresh_device(self):
        if self.busy:
            return
        self._set_busy(True)

        def work():
            if not self.adb:
                self.after(0, self._device_failed,
                           "ADB não encontrado.\n"
                           "Clique em 'Baixar ADB', extraia o ZIP e coloque a pasta\n"
                           "'platform-tools' ao lado deste script, depois atualize.")
                return
            ok, out = run_adb(self.adb, ["devices"])
            lines = [l for l in out.splitlines()
                     if l.strip() and not l.startswith("List of devices")]
            devices = [l.split()[0] for l in lines if len(l.split()) >= 2 and l.split()[1] == "device"]
            unauthorized = any("unauthorized" in l for l in lines)
            if unauthorized:
                self.after(0, self._device_failed,
                           "Aparelho conectado mas NÃO AUTORIZADO.\n"
                           "No celular, toque em 'Permitir' na janela de depuração USB.")
                return
            if not devices:
                self.after(0, self._device_failed,
                           "Nenhum aparelho encontrado.\n"
                           "Confira o cabo, a depuração USB e a autorização no celular.")
                return
            serial = devices[0]
            info = {"serial": serial}
            for key, label in [
                ("ro.product.manufacturer", "fabricante"),
                ("ro.product.model", "modelo"),
                ("ro.build.version.release", "android"),
                ("ro.miui.ui.version.name", "hyperos"),
                ("ro.product.brand", "marca"),
            ]:
                ok2, out2 = run_adb(self.adb, ["-s", serial, "shell", "getprop", key])
                if ok2 and out2.strip():
                    info[label] = out2.strip()
            ok3, out3 = run_adb(self.adb, ["-s", serial, "shell", "pm", "list", "packages"])
            installed = set()
            if ok3:
                for line in out3.splitlines():
                    m = re.match(r"package:(.+)", line.strip())
                    if m:
                        installed.add(m.group(1).strip())
            self.after(0, self._device_ok, info, installed)

        threading.Thread(target=work, daemon=True).start()

    def _device_failed(self, msg):
        self._set_busy(False)
        self.lbl_device.configure(text="❌ " + msg.splitlines()[0])
        self.log("ERRO: " + msg.replace("\n", " "))
        messagebox.showwarning("Aparelho não conectado", msg)

    def _device_ok(self, info, installed):
        self._set_busy(False)
        self.device_info = info
        self.installed = installed
        marca = info.get("marca") or info.get("fabricante") or "Xiaomi"
        modelo = info.get("modelo") or "?"
        android = info.get("android") or "?"
        hyperos = info.get("hyperos") or "?"
        self.lbl_device.configure(
            text=f"✅ {marca} {modelo}  •  Android {android}  •  HyperOS {hyperos}  •  {info['serial']}")
        n_curated = sum(1 for p in PACKAGES if p[0] in installed)
        self.log(f"Conectado: {marca} {modelo} (Android {android}, HyperOS {hyperos}). "
                 f"{len(installed)} pacotes no aparelho, {n_curated} da lista curada instalados.")
        self._apply_filter()

    # ---------------- lista ----------------
    def _visible_packages(self):
        q = _norm(self.search_var.get().strip())
        risk = self.risk_var.get()
        cat = self.cat_var.get()
        out = []
        for pkg in PACKAGES:
            if risk != "Todos" and pkg[3] != risk:
                continue
            if cat != "Todas" and pkg[2] != cat:
                continue
            if q and q not in _norm(pkg[0] + " " + pkg[1] + " " + pkg[4]):
                continue
            out.append(pkg)
        return out

    def _apply_filter(self):
        for child in self.list_inner.winfo_children():
            child.destroy()
        self.rows = {}
        visible = self._visible_packages()
        for pkg, name, cat, risk, desc in visible:
            if pkg not in self.vars:
                self.vars[pkg] = tk.BooleanVar(value=False)
            var = self.vars[pkg]
            row = ttk.Frame(self.list_inner)
            row.pack(fill="x", padx=4, pady=1)
            installed = pkg in self.installed if self.installed else None
            mark = "📦" if installed is None else ("✅" if installed else "—")
            cb = ttk.Checkbutton(row, text=f"{mark}  {name}", variable=var,
                                 command=self._update_count)
            cb.pack(side="left", anchor="w")
            ttk.Label(row, text=f"  {pkg}", font=(MONO_FONT, 9),
                      foreground="gray").pack(side="left")
            ttk.Label(row, text=f"  [{risk}]", foreground=RISK_COLORS[risk],
                      font=(UI_FONT, 9, "bold")).pack(side="left")
            ttk.Label(row, text=f"  {cat} — {desc}", wraplength=420,
                      font=(UI_FONT, 9), foreground="#555").pack(side="left", fill="x")
            self.rows[pkg] = row
        if not visible:
            ttk.Label(self.list_inner, text="Nada encontrado com esse filtro.",
                      foreground="gray").pack(padx=10, pady=10)
        self._update_count()

    def _update_count(self):
        n = sum(1 for v in self.vars.values() if v.get())
        self.lbl_count.configure(text=f"{n} selecionado(s)")

    def _preset(self, max_risk):
        order = {"Seguro": 0, "Moderado": 1, "Cuidado": 2}
        limit = order[max_risk]
        for pkg, name, cat, risk, desc in PACKAGES:
            if pkg in self.vars:
                self.vars[pkg].set(order[risk] <= limit)
        self._update_count()
        self.log(f"Preset aplicado: até '{max_risk}'.")

    def _preset_ads(self):
        """Marca só os pacotes que trazem anúncios (AD_PACKAGES)."""
        for pkg, name, cat, risk, desc in PACKAGES:
            if pkg in self.vars:
                self.vars[pkg].set(pkg in AD_PACKAGES)
        n = sum(1 for v in self.vars.values() if v.get())
        self._update_count()
        self.log(f"Preset 'Só Anúncios' aplicado: {n} pacote(s) marcado(s). "
                 "Revise os Moderados antes de desinstalar.")

    def _select_visible(self):
        for pkg in self._visible_packages():
            if pkg[0] in self.vars:
                self.vars[pkg[0]].set(True)
        self._update_count()

    def _clear_selection(self):
        for v in self.vars.values():
            v.set(False)
        self._update_count()

    def _selected(self):
        return [p[0] for p in PACKAGES if self.vars.get(p[0]) and self.vars[p[0]].get()]

    # ---------------- ações ADB ----------------
    def _need_device(self):
        if not self.adb:
            messagebox.showerror("ADB não encontrado",
                                 "Instale o platform-tools e clique em 'Conectar / Atualizar'.")
            return False
        if not self.device_info:
            messagebox.showwarning("Sem aparelho",
                                   "Clique em 'Conectar / Atualizar' antes de continuar.")
            return False
        return True

    def _save_restore_file(self, pkgs):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            f"restore_hyperos_{stamp}.txt")
        lines = [
            "# HyperOS Debloat — lista para restaurar",
            f"# Gerado em {datetime.now():%d/%m/%Y %H:%M} — aparelho: "
            f"{self.device_info.get('modelo', '?')}",
            "# Para restaurar um pacote:",
            "#   adb shell cmd package install-existing <pacote>",
            "# Para restaurar todos, na pasta do script:",
            "#   Windows: for /f %p in (restore_hyperos_*.txt) do adb shell cmd package install-existing %p",
            "#   Linux/macOS: grep -v '^#' restore_hyperos_*.txt | while read p; do adb shell cmd package install-existing $p; done",
            "#   (ignore as linhas que começam com #)",
            "",
        ]
        lines += pkgs
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return path

    def _uninstall_selected(self):
        if not self._need_device():
            return
        pkgs = [p for p in self._selected() if p not in NEVER_REMOVE]
        if not pkgs:
            messagebox.showinfo("Nada selecionado", "Marque ao menos um pacote na lista.")
            return
        if not messagebox.askyesno(
                "Confirmar debloat",
                f"Remover {len(pkgs)} pacote(s) do usuário 0?\n\n"
                "Isso NÃO apaga a partição do sistema e é reversível\n"
                "(botão Restaurar ou restauração de fábrica).\n\n"
                "Uma lista de restauração será salva ao lado do script."):
            return
        self._run_uninstall(pkgs)

    def _run_uninstall(self, pkgs):
        self._set_busy(True)
        path = self._save_restore_file(pkgs)
        self.log(f"Lista de restauração salva em: {os.path.basename(path)}")

        def work():
            serial = self.device_info["serial"]
            ok_count = fail = 0
            for pkg in pkgs:
                ok, out = run_adb(self.adb, ["-s", serial, "shell", "pm",
                                             "uninstall", "-k", "--user", "0", pkg])
                success = ok and "Success" in out
                if not success:
                    # Alguns pacotes só aceitam desativar
                    ok2, out2 = run_adb(self.adb, ["-s", serial, "shell", "pm",
                                                   "disable-user", "--user", "0", pkg])
                    success = ok2 and ("disabled" in out2.lower() or "new state: disabled" in out2.lower())
                    out = out2 if success else out
                if success:
                    ok_count += 1
                    self.after(0, self.log, f"✅ Removido: {pkg}")
                else:
                    fail += 1
                    self.after(0, self.log, f"❌ Falhou: {pkg} — {out.strip()[:120]}")
                self.after(0, self._update_count)
            self.after(0, self._finish_uninstall, ok_count, fail, path)

        threading.Thread(target=work, daemon=True).start()

    def _finish_uninstall(self, ok_count, fail, path):
        self._set_busy(False)
        self.log(f"Fim: {ok_count} removido(s), {fail} falha(s). Restauração em {os.path.basename(path)}")
        messagebox.showinfo("Debloat concluído",
                            f"{ok_count} pacote(s) removido(s).\n"
                            f"{fail} falha(s) — veja o log.\n\n"
                            f"Lista de restauração salva em:\n{os.path.basename(path)}\n\n"
                            "Reinicie o celular para aplicar tudo.")
        self.refresh_device()

    def _restore_selected(self):
        if not self._need_device():
            return
        pkgs = self._selected()
        if not pkgs:
            messagebox.showinfo("Nada selecionado", "Marque os pacotes que quer restaurar.")
            return
        self._run_restore(pkgs, "selecionados")

    def _restore_custom(self):
        if not self._need_device():
            return
        pkg = self.custom_var.get().strip()
        if not pkg:
            messagebox.showinfo("Pacote vazio", "Digite o nome do pacote, ex.: com.miui.videoplayer")
            return
        self._run_restore([pkg], "avulso")

    def _run_restore(self, pkgs, label):
        self._set_busy(True)

        def work():
            serial = self.device_info["serial"]
            ok_count = fail = 0
            for pkg in pkgs:
                ok, out = run_adb(self.adb, ["-s", serial, "shell", "cmd", "package",
                                             "install-existing", pkg])
                if ok and ("installed" in out.lower() or "success" in out.lower() or not out.strip()):
                    ok_count += 1
                    self.after(0, self.log, f"↩ Restaurado: {pkg}")
                else:
                    fail += 1
                    self.after(0, self.log, f"❌ Restaurar falhou: {pkg} — {out.strip()[:120]}")
            self.after(0, self._finish_restore, ok_count, fail, label)

        threading.Thread(target=work, daemon=True).start()

    def _finish_restore(self, ok_count, fail, label):
        self._set_busy(False)
        messagebox.showinfo("Restauração",
                            f"{ok_count} pacote(s) restaurado(s) ({label}).\n{fail} falha(s).")
        self.refresh_device()

    def _remove_custom(self):
        if not self._need_device():
            return
        pkg = self.custom_var.get().strip()
        if not pkg:
            messagebox.showinfo("Pacote vazio", "Digite o nome do pacote.")
            return
        if pkg in NEVER_REMOVE:
            messagebox.showerror("Pacote protegido",
                                 f"{pkg} é um pacote crítico do sistema e NÃO pode ser removido.\n"
                                 "Removê-lo pode causar bootloop.")
            return
        if not messagebox.askyesno("Confirmar", f"Remover o pacote avulso?\n\n{pkg}"):
            return
        self._run_uninstall([pkg])

    def _simulate(self):
        pkgs = self._selected()
        if not pkgs:
            messagebox.showinfo("Nada selecionado", "Marque ao menos um pacote.")
            return
        self.log("— Simulação (nada foi executado) —")
        for pkg in pkgs:
            self.log(f"  adb shell pm uninstall -k --user 0 {pkg}")
        messagebox.showinfo("Simulação",
                            f"{len(pkgs)} comando(s) listados no log.\nNada foi executado.")

    def _export_script(self):
        """Exporta os pacotes marcados: .bat no Windows, .sh no Linux/macOS."""
        pkgs = self._selected()
        if not pkgs:
            messagebox.showinfo("Nada selecionado", "Marque ao menos um pacote.")
            return
        if os.name == "nt":
            path = filedialog.asksaveasfilename(
                defaultextension=".bat", initialfile="debloat_hyperos.bat",
                filetypes=[("Script Windows", "*.bat")])
            if not path:
                return
            lines = [
                "@echo off",
                "REM HyperOS 1 Debloat — gerado por hyperos_debloat.py",
                "REM Rode com o celular conectado e a depuração USB autorizada.",
                "REM Reversível: adb shell cmd package install-existing <pacote>",
                "",
            ]
            for pkg in pkgs:
                lines.append(f"adb shell pm uninstall -k --user 0 {pkg}")
            lines += ["", "echo Concluido. Reinicie o celular.", "pause", ""]
        else:
            path = filedialog.asksaveasfilename(
                defaultextension=".sh", initialfile="debloat_hyperos.sh",
                filetypes=[("Script shell", "*.sh")])
            if not path:
                return
            lines = [
                "#!/bin/bash",
                "# HyperOS 1 Debloat — gerado por hyperos_debloat.py",
                "# Rode com o celular conectado e a depuração USB autorizada.",
                "# Reversível: adb shell cmd package install-existing <pacote>",
                "set -e",
                "",
            ]
            for pkg in pkgs:
                lines.append(f"adb shell pm uninstall -k --user 0 {pkg}")
            lines += ["", 'echo "Concluído. Reinicie o celular."', ""]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        if os.name != "nt":
            try:
                os.chmod(path, 0o755)
            except OSError:
                pass
        self.log(f"Script exportado: {path}")
        messagebox.showinfo("Exportado", f"Script salvo em:\n{path}")

    def _copy_restore_list(self):
        pkgs = self._selected()
        if not pkgs:
            messagebox.showinfo("Nada selecionado", "Marque ao menos um pacote.")
            return
        text = "\n".join(f"adb shell cmd package install-existing {p}" for p in pkgs)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.log("Comandos de restauração copiados para a área de transferência.")
        messagebox.showinfo("Copiado",
                            "Comandos 'install-existing' copiados.\nCole no prompt para restaurar.")


def main():
    if sys.version_info < (3, 8):
        messagebox.showerror("Python antigo", "Use Python 3.8 ou mais recente.")
        sys.exit(1)
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
