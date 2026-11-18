"""Cronômetro e Timer com interface gráfica.

    python cronometro.py

Atalhos: Espaço inicia/pausa, R zera, V marca volta (no cronômetro),
Ctrl+Tab troca de aba.
"""

from __future__ import annotations

import platform
import tkinter as tk
from tkinter import messagebox, ttk

from relogio import Cronometro, Temporizador, formatar, interpretar_duracao

ATUALIZACAO_MS = 31  # ~30 quadros por segundo
PRESETS = [("1 min", 60), ("5 min", 300), ("10 min", 600), ("Pomodoro 25", 1500)]

CORES = {
    "fundo": "#0f172a",
    "painel": "#1e293b",
    "borda": "#334155",
    "texto": "#e2e8f0",
    "texto_suave": "#94a3b8",
    "destaque": "#38bdf8",
    "verde": "#22c55e",
    "vermelho": "#ef4444",
    "ambar": "#f59e0b",
}

WINDOWS = platform.system() == "Windows"
FONTE = "Segoe UI" if WINDOWS else "Helvetica"
FONTE_MONO = "Consolas" if WINDOWS else "DejaVu Sans Mono"


def configurar_estilo(raiz: tk.Tk) -> None:
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    estilo.configure(".", background=CORES["fundo"], foreground=CORES["texto"], font=(FONTE, 10))
    sem_borda = dict(bordercolor=CORES["fundo"], lightcolor=CORES["fundo"], darkcolor=CORES["fundo"])
    estilo.configure("TNotebook", background=CORES["fundo"], borderwidth=0, tabmargins=(16, 12, 16, 0),
                     **sem_borda)
    estilo.configure("TNotebook.Tab", background=CORES["painel"], foreground=CORES["texto_suave"],
                     padding=(18, 8), borderwidth=0, font=(FONTE, 10, "bold"), **sem_borda)
    estilo.map("TNotebook.Tab", background=[("selected", CORES["borda"])],
               foreground=[("selected", CORES["destaque"])], expand=[("selected", (0, 0, 0, 0))])
    estilo.configure("TFrame", background=CORES["fundo"])
    estilo.configure("Painel.TFrame", background=CORES["painel"])
    estilo.configure("Suave.TLabel", foreground=CORES["texto_suave"])
    estilo.configure("TButton", background=CORES["borda"], foreground=CORES["texto"], borderwidth=0,
                     padding=(16, 8), font=(FONTE, 10, "bold"))
    estilo.map("TButton", background=[("disabled", CORES["painel"]), ("active", "#475569")],
               foreground=[("disabled", CORES["texto_suave"])])
    estilo.configure("Iniciar.TButton", background=CORES["verde"], foreground="#052e16")
    estilo.map("Iniciar.TButton", background=[("active", "#16a34a")])
    estilo.configure("Pausar.TButton", background=CORES["ambar"], foreground="#1c1917")
    estilo.map("Pausar.TButton", background=[("active", "#d97706")])
    estilo.configure("Preset.TButton", padding=(10, 4), font=(FONTE, 9))
    estilo.configure("TSpinbox", fieldbackground=CORES["painel"], foreground=CORES["texto"],
                     arrowcolor=CORES["texto"], background=CORES["borda"], bordercolor=CORES["borda"],
                     lightcolor=CORES["painel"], darkcolor=CORES["painel"])
    estilo.configure("Treeview", background=CORES["painel"], fieldbackground=CORES["painel"],
                     foreground=CORES["texto"], borderwidth=0, rowheight=26, font=(FONTE_MONO, 10),
                     bordercolor=CORES["painel"], lightcolor=CORES["painel"], darkcolor=CORES["painel"])
    estilo.configure("Treeview.Heading", background=CORES["borda"], foreground=CORES["texto_suave"],
                     borderwidth=0, font=(FONTE, 9, "bold"))
    estilo.map("Treeview", background=[("selected", CORES["borda"])])
    estilo.configure("Vertical.TScrollbar", background=CORES["borda"], troughcolor=CORES["painel"],
                     borderwidth=0, arrowcolor=CORES["texto_suave"], bordercolor=CORES["painel"],
                     lightcolor=CORES["borda"], darkcolor=CORES["borda"])
    estilo.map("Vertical.TScrollbar", background=[("disabled", CORES["painel"]), ("active", "#475569")],
               arrowcolor=[("disabled", CORES["painel"])])


class AbaCronometro(ttk.Frame):
    def __init__(self, pai: tk.Widget) -> None:
        super().__init__(pai, padding=20)
        self.cronometro = Cronometro()

        self.lbl_tempo = tk.Label(self, text=formatar(0), font=(FONTE_MONO, 54, "bold"),
                                  bg=CORES["fundo"], fg=CORES["texto"])
        self.lbl_tempo.pack(pady=(10, 4))
        self.lbl_volta = ttk.Label(self, text=" ", style="Suave.TLabel", font=(FONTE_MONO, 12))
        self.lbl_volta.pack()

        botoes = ttk.Frame(self)
        botoes.pack(pady=16)
        self.btn_iniciar = ttk.Button(botoes, text="Iniciar", style="Iniciar.TButton", width=10,
                                      command=self.alternar)
        self.btn_iniciar.pack(side="left", padx=4)
        self.btn_volta = ttk.Button(botoes, text="Volta", width=10, command=self.marcar_volta)
        self.btn_volta.pack(side="left", padx=4)
        self.btn_zerar = ttk.Button(botoes, text="Zerar", width=10, command=self.zerar)
        self.btn_zerar.pack(side="left", padx=4)

        tabela = ttk.Frame(self)
        tabela.pack(fill="both", expand=True)
        self.voltas = ttk.Treeview(tabela, columns=("volta", "tempo", "total"), show="headings",
                                   height=6)
        for coluna, titulo, largura in (("volta", "Volta", 80), ("tempo", "Tempo da volta", 160),
                                        ("total", "Tempo total", 160)):
            self.voltas.heading(coluna, text=titulo)
            self.voltas.column(coluna, width=largura, anchor="center")
        self.voltas.tag_configure("rapida", foreground=CORES["verde"])
        self.voltas.tag_configure("lenta", foreground=CORES["vermelho"])
        barra = ttk.Scrollbar(tabela, orient="vertical", command=self.voltas.yview)
        self.voltas.configure(yscrollcommand=barra.set)
        self.voltas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self._atualizar_botoes()

    def alternar(self) -> None:
        self.cronometro.alternar()
        self._atualizar_botoes()

    def zerar(self) -> None:
        self.cronometro.zerar()
        self.voltas.delete(*self.voltas.get_children())
        self.lbl_volta.configure(text=" ")
        self._atualizar_botoes()
        self.atualizar()

    def marcar_volta(self) -> None:
        if self.cronometro.marcar_volta() is None:
            return
        self.voltas.delete(*self.voltas.get_children())
        rapida = self.cronometro.volta_mais_rapida()
        lenta = self.cronometro.volta_mais_lenta()
        for volta in reversed(self.cronometro.voltas):
            tag = "rapida" if volta == rapida else "lenta" if volta == lenta else ""
            self.voltas.insert("", "end", values=(f"{volta.numero:02d}", formatar(volta.tempo),
                                                  formatar(volta.total)), tags=(tag,))

    def _atualizar_botoes(self) -> None:
        if self.cronometro.rodando:
            self.btn_iniciar.configure(text="Pausar", style="Pausar.TButton")
            self.btn_volta.state(["!disabled"])
        else:
            texto = "Continuar" if self.cronometro.decorrido() > 0 else "Iniciar"
            self.btn_iniciar.configure(text=texto, style="Iniciar.TButton")
            self.btn_volta.state(["disabled"])
        self.btn_zerar.state(["!disabled"] if self.cronometro.decorrido() > 0 else ["disabled"])

    def atualizar(self) -> None:
        decorrido = self.cronometro.decorrido()
        self.lbl_tempo.configure(text=formatar(decorrido))
        if self.cronometro.voltas and self.cronometro.rodando:
            atual = decorrido - self.cronometro.voltas[-1].total
            self.lbl_volta.configure(text=f"Volta {len(self.cronometro.voltas) + 1}: {formatar(atual)}")


class AbaTimer(ttk.Frame):
    TAMANHO = 260
    ESPESSURA = 12

    def __init__(self, pai: tk.Widget, raiz: tk.Tk) -> None:
        super().__init__(pai, padding=20)
        self.raiz = raiz
        self.timer = Temporizador()
        self.timer.definir(300)
        self._alarme_tocando = False
        self._piscar = False

        topo = ttk.Frame(self)
        topo.pack()
        self.var_h = tk.StringVar(value="00")
        self.var_m = tk.StringVar(value="05")
        self.var_s = tk.StringVar(value="00")
        self.caixas = []
        for var, maximo, rotulo in ((self.var_h, 99, "h"), (self.var_m, 59, "min"), (self.var_s, 59, "s")):
            caixa = ttk.Spinbox(topo, from_=0, to=maximo, textvariable=var, width=3, wrap=True,
                                format="%02.0f", font=(FONTE_MONO, 12), command=self._ler_campos)
            caixa.bind("<FocusOut>", lambda _e: self._ler_campos())
            caixa.bind("<Return>", lambda _e: self._ler_campos())
            caixa.pack(side="left")
            self.caixas.append(caixa)
            ttk.Label(topo, text=rotulo, style="Suave.TLabel").pack(side="left", padx=(3, 12))
        presets = ttk.Frame(self)
        presets.pack(pady=(10, 0))
        self.botoes_preset = []
        for texto, segundos in PRESETS:
            botao = ttk.Button(presets, text=texto, style="Preset.TButton",
                               command=lambda s=segundos: self.definir(s))
            botao.pack(side="left", padx=2)
            self.botoes_preset.append(botao)

        t = self.TAMANHO
        self.canvas = tk.Canvas(self, width=t, height=t, bg=CORES["fundo"], highlightthickness=0)
        self.canvas.pack(pady=(14, 16))
        m = self.ESPESSURA
        self.canvas.create_oval(m, m, t - m, t - m, outline=CORES["painel"], width=m)
        self.arco = self.canvas.create_arc(m, m, t - m, t - m, start=90, extent=-359.9,
                                           style="arc", outline=CORES["destaque"], width=m)
        self.texto = self.canvas.create_text(t / 2, t / 2 - 6, text="", fill=CORES["texto"],
                                             font=(FONTE_MONO, 34, "bold"))
        self.subtexto = self.canvas.create_text(t / 2, t / 2 + 34, text="", fill=CORES["texto_suave"],
                                                font=(FONTE, 10))

        botoes = ttk.Frame(self)
        botoes.pack()
        self.btn_iniciar = ttk.Button(botoes, text="Iniciar", style="Iniciar.TButton", width=10,
                                      command=self.alternar)
        self.btn_iniciar.pack(side="left", padx=4)
        self.btn_zerar = ttk.Button(botoes, text="Zerar", width=10, command=self.zerar)
        self.btn_zerar.pack(side="left", padx=4)

        self._atualizar_botoes()
        self.atualizar()

    # ------------------------------------------------------------------ ações

    def _ler_campos(self) -> None:
        if self.timer.rodando:
            return
        try:
            total = interpretar_duracao(f"{int(self.var_h.get())}h{int(self.var_m.get())}m"
                                        f"{int(self.var_s.get())}s")
        except ValueError:
            total = int(self.timer.duracao)
        if total != int(self.timer.duracao):
            self.definir(total)

    def definir(self, segundos: int) -> None:
        self._parar_alarme()
        horas, resto = divmod(int(segundos), 3600)
        minutos, segs = divmod(resto, 60)
        horas = min(horas, 99)
        self.var_h.set(f"{horas:02d}")
        self.var_m.set(f"{minutos:02d}")
        self.var_s.set(f"{segs:02d}")
        self.timer.definir(horas * 3600 + minutos * 60 + segs)
        self._atualizar_botoes()
        self.atualizar()

    def alternar(self) -> None:
        if self._alarme_tocando:
            self.zerar()
            return
        if not self.timer.rodando:
            self._ler_campos()
        if self.timer.duracao <= 0:
            return
        self.timer.alternar()
        self._atualizar_botoes()

    def zerar(self) -> None:
        self._parar_alarme()
        self.timer.zerar()
        self._atualizar_botoes()
        self.atualizar()

    def _atualizar_botoes(self) -> None:
        rodando = self.timer.rodando
        if self._alarme_tocando:
            self.btn_iniciar.configure(text="OK", style="Pausar.TButton")
        elif rodando:
            self.btn_iniciar.configure(text="Pausar", style="Pausar.TButton")
        else:
            pausado = 0 < self.timer.restante() < self.timer.duracao
            self.btn_iniciar.configure(text="Continuar" if pausado else "Iniciar", style="Iniciar.TButton")
        bloquear = ["disabled"] if rodando or self._alarme_tocando else ["!disabled"]
        for widget in [*self.caixas, *self.botoes_preset]:
            widget.state(bloquear)

    # ------------------------------------------------------------------ alarme

    def _tocar_alarme(self) -> None:
        self._alarme_tocando = True
        self._atualizar_botoes()
        self.raiz.deiconify()
        self.raiz.lift()
        self.raiz.attributes("-topmost", True)
        self.raiz.after(500, lambda: self.raiz.attributes("-topmost", False))
        self._bipar()

    def _bipar(self) -> None:
        if not self._alarme_tocando:
            return
        self._piscar = not self._piscar
        cor = CORES["vermelho"] if self._piscar else CORES["texto"]
        self.canvas.itemconfigure(self.texto, fill=cor)
        if self._piscar:
            if WINDOWS:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            else:
                self.raiz.bell()
        self.after(500, self._bipar)

    def _parar_alarme(self) -> None:
        self._alarme_tocando = False
        self._piscar = False
        self.canvas.itemconfigure(self.texto, fill=CORES["texto"])

    # ------------------------------------------------------------------ tela

    def atualizar(self) -> None:
        restante = self.timer.restante()
        self.canvas.itemconfigure(self.texto, text=formatar(restante, centesimos=False))
        fracao = 1 - self.timer.progresso()
        self.canvas.itemconfigure(self.arco, extent=-359.9 * fracao if fracao > 0 else 0,
                                  outline=CORES["vermelho"] if restante <= 10 and self.timer.rodando
                                  else CORES["destaque"])
        if self._alarme_tocando:
            sub = "Tempo esgotado!"
        elif self.timer.rodando:
            sub = f"de {formatar(self.timer.duracao, centesimos=False)}"
        elif 0 < restante < self.timer.duracao:
            sub = "Pausado"
        else:
            sub = "Pronto"
        self.canvas.itemconfigure(self.subtexto, text=sub)
        if self.timer.terminou() and not self._alarme_tocando and self.timer.ativo:
            self.timer.pausar()
            self._tocar_alarme()


class Aplicativo(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Cronômetro")
        self.geometry("560x600")
        self.minsize(520, 580)
        self.configure(bg=CORES["fundo"])
        configurar_estilo(self)

        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True)
        self.aba_cronometro = AbaCronometro(self.abas)
        self.aba_timer = AbaTimer(self.abas, self)
        self.abas.add(self.aba_cronometro, text="Cronômetro")
        self.abas.add(self.aba_timer, text="Timer")
        self.abas.enable_traversal()  # Ctrl+Tab troca de aba

        rodape = ttk.Label(self, text="Espaço: iniciar/pausar   R: zerar   V: volta",
                           style="Suave.TLabel", font=(FONTE, 9))
        rodape.pack(pady=(0, 10))

        self.bind("<space>", self._atalho(lambda aba: aba.alternar()))
        self.bind("<KeyPress-r>", self._atalho(lambda aba: aba.zerar()))
        self.bind("<KeyPress-v>", self._atalho(
            lambda aba: aba.marcar_volta() if isinstance(aba, AbaCronometro) else None))
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self._laco()

    def _aba_atual(self):
        return self.nametowidget(self.abas.select())

    def _atalho(self, acao):
        def tratar(evento):
            if isinstance(evento.widget, (ttk.Spinbox, tk.Entry, ttk.Entry)):
                return None
            acao(self._aba_atual())
            return "break"
        return tratar

    def _laco(self) -> None:
        self.aba_cronometro.atualizar()
        self.aba_timer.atualizar()
        self.after(ATUALIZACAO_MS, self._laco)

    def _ao_fechar(self) -> None:
        if self.aba_timer.timer.rodando or self.aba_cronometro.cronometro.rodando:
            if not messagebox.askyesno("Cronômetro", "Ainda há contagem em andamento. Fechar mesmo assim?",
                                       parent=self):
                return
        self.destroy()


def main() -> None:
    Aplicativo().mainloop()


if __name__ == "__main__":
    main()
