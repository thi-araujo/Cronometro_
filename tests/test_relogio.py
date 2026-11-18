import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from relogio import Cronometro, Temporizador, formatar, interpretar_duracao  # noqa: E402


class RelogioFalso:
    """Relógio controlado pelo teste: o tempo só anda quando mandamos."""

    def __init__(self) -> None:
        self.agora = 1000.0

    def __call__(self) -> float:
        return self.agora

    def avancar(self, segundos: float) -> None:
        self.agora += segundos


class TestFormatar(unittest.TestCase):
    def test_minutos_e_centesimos(self):
        self.assertEqual(formatar(0), "00:00.00")
        self.assertEqual(formatar(83.456), "01:23.45")

    def test_com_horas(self):
        self.assertEqual(formatar(3725.5), "01:02:05.50")

    def test_sem_centesimos_arredonda_para_cima(self):
        # Um timer com 0,2 s restante ainda mostra 00:01, não 00:00.
        self.assertEqual(formatar(0.2, centesimos=False), "00:01")
        self.assertEqual(formatar(60, centesimos=False), "01:00")
        self.assertEqual(formatar(0, centesimos=False), "00:00")

    def test_negativo_vira_zero(self):
        self.assertEqual(formatar(-5), "00:00.00")


class TestInterpretarDuracao(unittest.TestCase):
    def test_formatos_aceitos(self):
        casos = {"90": 90, "1:30": 90, "1:02:03": 3723, "25m": 1500, "25min": 1500,
                 "1h30m": 5400, "45s": 45, "1h 5m 10s": 3910, " 2:00 ": 120}
        for texto, esperado in casos.items():
            self.assertEqual(interpretar_duracao(texto), esperado, texto)

    def test_formatos_invalidos(self):
        for texto in ["", "abc", "1:75", "1h2x", "h", ":30"]:
            with self.assertRaises(ValueError, msg=texto):
                interpretar_duracao(texto)


class TestCronometro(unittest.TestCase):
    def setUp(self):
        self.relogio = RelogioFalso()
        self.c = Cronometro(self.relogio)

    def test_conta_apenas_enquanto_roda(self):
        self.relogio.avancar(5)
        self.assertEqual(self.c.decorrido(), 0)
        self.c.iniciar()
        self.relogio.avancar(10)
        self.c.pausar()
        self.relogio.avancar(100)
        self.assertEqual(self.c.decorrido(), 10)
        self.c.iniciar()
        self.relogio.avancar(2.5)
        self.assertEqual(self.c.decorrido(), 12.5)

    def test_iniciar_duas_vezes_nao_reinicia(self):
        self.c.iniciar()
        self.relogio.avancar(3)
        self.c.iniciar()
        self.assertEqual(self.c.decorrido(), 3)

    def test_voltas(self):
        self.assertIsNone(self.c.marcar_volta())  # parado não marca
        self.c.iniciar()
        for duracao in (10, 7, 12):
            self.relogio.avancar(duracao)
            self.c.marcar_volta()
        self.assertEqual([v.tempo for v in self.c.voltas], [10, 7, 12])
        self.assertEqual(self.c.voltas[-1].total, 29)
        self.assertEqual(self.c.volta_mais_rapida().numero, 2)
        self.assertEqual(self.c.volta_mais_lenta().numero, 3)

    def test_zerar(self):
        self.c.iniciar()
        self.relogio.avancar(4)
        self.c.marcar_volta()
        self.c.zerar()
        self.assertEqual(self.c.decorrido(), 0)
        self.assertFalse(self.c.rodando)
        self.assertEqual(self.c.voltas, [])


class TestTemporizador(unittest.TestCase):
    def setUp(self):
        self.relogio = RelogioFalso()
        self.t = Temporizador(self.relogio)
        self.t.definir(60)

    def test_contagem_e_pausa(self):
        self.t.iniciar()
        self.relogio.avancar(15)
        self.assertEqual(self.t.restante(), 45)
        self.assertAlmostEqual(self.t.progresso(), 0.25)
        self.t.pausar()
        self.relogio.avancar(30)
        self.assertEqual(self.t.restante(), 45)
        self.t.iniciar()
        self.relogio.avancar(5)
        self.assertEqual(self.t.restante(), 40)

    def test_termina_em_zero(self):
        self.t.iniciar()
        self.relogio.avancar(90)
        self.assertEqual(self.t.restante(), 0)
        self.assertTrue(self.t.terminou())
        self.assertFalse(self.t.rodando)
        self.assertTrue(self.t.ativo)

    def test_zerar_volta_ao_inicio(self):
        self.t.iniciar()
        self.relogio.avancar(20)
        self.t.zerar()
        self.assertEqual(self.t.restante(), 60)
        self.assertFalse(self.t.ativo)

    def test_duracao_zero_nao_inicia(self):
        self.t.definir(0)
        self.t.iniciar()
        self.assertFalse(self.t.ativo)
        self.assertFalse(self.t.terminou())


if __name__ == "__main__":
    unittest.main()
