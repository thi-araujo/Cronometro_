"""Lógica do cronômetro e do timer, sem interface gráfica.

As classes recebem a função de relógio por parâmetro (por padrão
time.monotonic), o que permite testá-las sem esperar o tempo passar.
time.monotonic não muda quando o relógio do sistema é ajustado, então a
contagem continua certa mesmo se a hora do computador mudar.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable

Relogio = Callable[[], float]


def formatar(segundos: float, centesimos: bool = True) -> str:
    """Formata segundos como MM:SS.cc, ou HH:MM:SS.cc a partir de 1 hora."""
    segundos = max(0.0, segundos)
    if centesimos:
        total_cent = int(segundos * 100)
        inteiros, cent = divmod(total_cent, 100)
    else:
        inteiros, cent = int(-(-segundos // 1)), 0  # arredonda para cima
    horas, resto = divmod(inteiros, 3600)
    minutos, segs = divmod(resto, 60)
    texto = f"{horas:02d}:{minutos:02d}:{segs:02d}" if horas else f"{minutos:02d}:{segs:02d}"
    return f"{texto}.{cent:02d}" if centesimos else texto


def interpretar_duracao(texto: str) -> int:
    """Converte o que o usuário digitou em segundos.

    Aceita "90", "1:30", "1:02:03", "25m", "1h30m", "45s" e "1h 5m 10s".
    Levanta ValueError se o texto não for uma duração válida.
    """
    texto = texto.strip().lower().replace(" ", "")
    if not texto:
        raise ValueError("duração vazia")
    if re.fullmatch(r"\d+", texto):
        return int(texto)
    if re.fullmatch(r"\d+(:\d{1,2}){1,2}", texto):
        partes = [int(p) for p in texto.split(":")]
        if any(p >= 60 for p in partes[1:]):
            raise ValueError(f"minutos e segundos vão até 59: {texto}")
        while len(partes) < 3:
            partes.insert(0, 0)
        horas, minutos, segundos = partes
        return horas * 3600 + minutos * 60 + segundos
    combinacao = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m(?:in)?)?(?:(\d+)s)?", texto)
    if combinacao and any(combinacao.groups()):
        horas, minutos, segundos = (int(g or 0) for g in combinacao.groups())
        return horas * 3600 + minutos * 60 + segundos
    raise ValueError(f"duração inválida: {texto}")


@dataclass(frozen=True)
class Volta:
    numero: int
    tempo: float  # duração desta volta
    total: float  # tempo acumulado até o fim da volta


class Cronometro:
    def __init__(self, relogio: Relogio = time.monotonic) -> None:
        self._relogio = relogio
        self._acumulado = 0.0
        self._inicio: float | None = None
        self.voltas: list[Volta] = []

    @property
    def rodando(self) -> bool:
        return self._inicio is not None

    def decorrido(self) -> float:
        if self._inicio is None:
            return self._acumulado
        return self._acumulado + self._relogio() - self._inicio

    def iniciar(self) -> None:
        if self._inicio is None:
            self._inicio = self._relogio()

    def pausar(self) -> None:
        if self._inicio is not None:
            self._acumulado = self.decorrido()
            self._inicio = None

    def alternar(self) -> None:
        self.pausar() if self.rodando else self.iniciar()

    def zerar(self) -> None:
        self._acumulado = 0.0
        self._inicio = None
        self.voltas.clear()

    def marcar_volta(self) -> Volta | None:
        if not self.rodando:
            return None
        total = self.decorrido()
        anterior = self.voltas[-1].total if self.voltas else 0.0
        volta = Volta(len(self.voltas) + 1, total - anterior, total)
        self.voltas.append(volta)
        return volta

    def volta_mais_rapida(self) -> Volta | None:
        return min(self.voltas, key=lambda v: v.tempo) if len(self.voltas) > 1 else None

    def volta_mais_lenta(self) -> Volta | None:
        return max(self.voltas, key=lambda v: v.tempo) if len(self.voltas) > 1 else None


class Temporizador:
    """Timer de contagem regressiva."""

    def __init__(self, relogio: Relogio = time.monotonic) -> None:
        self._relogio = relogio
        self.duracao = 0.0
        self._restante = 0.0
        self._inicio: float | None = None

    @property
    def ativo(self) -> bool:
        """Contagem em andamento (pode já ter chegado a zero)."""
        return self._inicio is not None

    @property
    def rodando(self) -> bool:
        return self.ativo and self.restante() > 0

    def definir(self, segundos: float) -> None:
        self.duracao = max(0.0, float(segundos))
        self._restante = self.duracao
        self._inicio = None

    def restante(self) -> float:
        if self._inicio is None:
            return self._restante
        return max(0.0, self._restante - (self._relogio() - self._inicio))

    def progresso(self) -> float:
        """Fração já concluída, de 0.0 a 1.0."""
        if self.duracao <= 0:
            return 0.0
        return 1.0 - self.restante() / self.duracao

    def terminou(self) -> bool:
        return self.duracao > 0 and self.restante() <= 0

    def iniciar(self) -> None:
        if self._inicio is None and self._restante > 0:
            self._inicio = self._relogio()

    def pausar(self) -> None:
        if self._inicio is not None:
            self._restante = self.restante()
            self._inicio = None

    def alternar(self) -> None:
        self.pausar() if self._inicio is not None else self.iniciar()

    def zerar(self) -> None:
        self.definir(self.duracao)
