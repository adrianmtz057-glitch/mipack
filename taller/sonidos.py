"""
Los sonidos de Khaset, sintetizados (nada grabado): se escriben como .ogg mono en
mod/src/main/resources/assets/mipack/sounds/khaset/ (ffmpeg con libvorbis).
  - silbato: el silbato de la muerte azteca. Un grito de viento: ruido que pasa por dos resonancias agudas que suben
    de golpe, aguantan temblando y caen; con un poco de distorsion (asi suena el de barro: aire que grita).
  - rugido: ruido grave con aspereza (modulado a ~30 Hz) sobre un diente de sierra que baja, como un jaguar enorme.
  - sacrificio: dos latidos graves y el soplido de fuego del cristal.
Uso: python3 -m taller.sonidos
"""

import os
import subprocess
import tempfile

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

TASA = 44100
CARPETA = os.path.join(os.path.dirname(__file__), "..", "mod", "src", "main", "resources", "assets", "mipack", "sounds",
                       "khaset")
AZAR = np.random.default_rng(7)


def _resonador(x, frec, ancho):
    """Filtro de dos polos con la frecuencia que cambia en cada muestra (frec: arreglo en Hz)."""
    y = np.zeros_like(x)
    r = np.exp(-np.pi * ancho / TASA)
    c = 2 * r * np.cos(2 * np.pi * frec / TASA)
    r2 = r * r
    y1 = y2 = 0.0
    for n in range(len(x)):
        v = x[n] + c[n] * y1 - r2 * y2
        y[n] = v
        y2, y1 = y1, v
    return y


def _env(t, puntos):
    ts, vs = zip(*puntos)
    return np.interp(t, ts, vs)


def _normal(x, pico=0.9):
    return x / (np.max(np.abs(x)) + 1e-9) * pico


def silbato():
    dur = 2.4
    t = np.arange(int(dur * TASA)) / TASA
    ruido = AZAR.standard_normal(len(t))
    sube = _env(t, [(0, 0.0), (0.12, 0.85), (0.35, 1.0), (1.8, 0.95), (2.4, 0.4)])
    tiembla = 1 + 0.03 * np.sin(2 * np.pi * 7.5 * t) + 0.015 * np.sin(2 * np.pi * 13 * t)
    f1 = (900 + 1300 * sube) * tiembla
    f2 = (1500 + 1900 * sube) * tiembla
    a = _resonador(ruido, f1, 90) + 0.6 * _resonador(ruido, f2, 140)
    a += 0.25 * lfilter(*butter(2, [3500, 7000], btype="band", fs=TASA), ruido)      # el aire
    a = np.tanh(_normal(a, 1.0) * 2.2)                                                 # aspereza
    vol = _env(t, [(0, 0), (0.06, 0.7), (0.18, 1.0), (1.9, 0.9), (2.4, 0.0)])
    return _normal(a * vol)


def rugido():
    dur = 1.8
    t = np.arange(int(dur * TASA)) / TASA
    f = _env(t, [(0, 95), (0.3, 120), (1.0, 85), (1.8, 60)])
    fase = 2 * np.pi * np.cumsum(f) / TASA
    sierra = 2 * ((fase / (2 * np.pi)) % 1.0) - 1
    ruido = lfilter(*butter(2, 900, btype="low", fs=TASA), AZAR.standard_normal(len(t)))
    aspero = 1 + 0.6 * np.sin(2 * np.pi * 31 * t + 2 * np.sin(2 * np.pi * 3 * t))
    a = (0.7 * sierra + 1.4 * _normal(ruido)) * aspero
    a = lfilter(*butter(2, [60, 1600], btype="band", fs=TASA), a)
    a = np.tanh(_normal(a, 1.0) * 1.8)
    vol = _env(t, [(0, 0), (0.12, 1.0), (1.1, 0.8), (1.8, 0.0)])
    return _normal(a * vol)


def sacrificio():
    dur = 2.6
    t = np.arange(int(dur * TASA)) / TASA
    a = np.zeros_like(t)
    for t0, fuerza in ((0.05, 1.0), (0.33, 0.8), (1.25, 1.0), (1.53, 0.8)):
        k = np.clip(t - t0, 0, None)
        golpe = np.where(t >= t0, np.exp(-k * 18) * np.sin(2 * np.pi * (48 + 30 * np.exp(-k * 25)) * k), 0)
        a += fuerza * golpe
    ruido = AZAR.standard_normal(len(t))
    fuego = lfilter(*butter(2, [300, 3000], btype="band", fs=TASA), ruido)
    a += 0.35 * _normal(fuego) * _env(t, [(0, 0), (1.9, 0), (2.1, 1.0), (2.6, 0)])
    return _normal(a)


def escribir(nombre, x):
    os.makedirs(CARPETA, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, nombre + ".wav")
        wavfile.write(wav, TASA, (x * 32767).astype(np.int16))
        salida = os.path.join(CARPETA, nombre + ".ogg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-c:a", "libvorbis", "-q:a", "5",
                        salida], check=True)
    return os.path.getsize(salida)


def main():
    for nombre, f in (("silbato", silbato), ("rugido", rugido), ("sacrificio", sacrificio)):
        print(nombre, escribir(nombre, f()), "bytes")


if __name__ == "__main__":
    main()
