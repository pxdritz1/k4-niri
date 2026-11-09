#!/usr/bin/env python3
"""Rastro del cursor durante una grabación, para el zoom automático.

    rastro.py --salida /tmp/k4-captura/rastro-X.jsonl [--hz 30] [--region "X,Y WxH"]

Escribe JSONL: una línea de cabecera y luego una por muestra. Los clics NO se
sondean —Niri no los publica por IPC—: llegan por la entrada estándar, una línea
«clic <boton>» por cada uno, que es quien los recibe con un atajo global.

Niri no expone coordenadas globales del cursor por IPC. En esta plataforma,
el rastro conserva los marcadores de clic recibidos por stdin, pero no genera
muestras de posición.
"""
import argparse, json, os, select, signal, sys, time

parar = False


def al_cortar(*_):
    global parar
    parar = True


def posicion():
    """Niri does not expose global pointer coordinates through its IPC."""
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--hz", type=float, default=30.0)
    ap.add_argument("--region", default="")     # "X,Y WxH"
    args = ap.parse_args()

    signal.signal(signal.SIGINT, al_cortar)
    signal.signal(signal.SIGTERM, al_cortar)

    os.makedirs(os.path.dirname(args.salida), exist_ok=True)
    intervalo = 1.0 / args.hz
    t0 = time.monotonic()

    with open(args.salida, "w") as f:
        f.write(json.dumps({"meta": {
            "hz": args.hz,
            "region": args.region,
            "epoch": time.time(),
        }}) + "\n")
        f.flush()

        # El latido por stdout le sirve a quien nos lanzó para saber que
        # seguimos vivos sin tener que leer el fichero.
        print(json.dumps({"ok": True, "estado": "rastreando-sin-coordenadas"}), flush=True)

        muestras = 0
        while not parar:
            ciclo = time.monotonic()

            p = posicion()
            if p is not None:
                f.write(json.dumps({"t": round(ciclo - t0, 4),
                                    "x": p[0], "y": p[1]}) + "\n")
                muestras += 1

            # Los clics que hayan llegado mientras tanto. Se leen sin bloquear
            # porque el reloj de las muestras manda: un clic se apunta cuando
            # llega, no cuando nos apetece mirar.
            while select.select([sys.stdin], [], [], 0)[0]:
                linea = sys.stdin.readline()
                if not linea:
                    break
                partes = linea.split()
                if partes and partes[0] == "clic":
                    boton = int(partes[1]) if len(partes) > 1 else 1
                    f.write(json.dumps({"t": round(time.monotonic() - t0, 4),
                                        "tipo": "clic", "boton": boton}) + "\n")

            # Cada segundo por si se corta la luz: perder el rastro entero por
            # no haber vaciado el buffer sería tonto.
            if muestras % int(args.hz) == 0:
                f.flush()

            resto = intervalo - (time.monotonic() - ciclo)
            if resto > 0:
                time.sleep(resto)

        f.flush()

    print(json.dumps({"ok": True, "estado": "fin", "muestras": muestras}),
          flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, BrokenPipeError):
        # Que se muera quien nos lee no es un fallo nuestro.
        sys.exit(0)
