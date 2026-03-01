# stego_scout.py
import argparse, json, os, struct
from PIL import Image, ImageChops
import numpy as np
import math

def read_bytes(path):
    with open(path, 'rb') as f:
        return f.read()

# ---------- A) Metadatos y estructura ----------
def extract_exif(path):
    try:
        from PIL import Image
        img = Image.open(path)
        exif = img.getexif()
        return {Image.ExifTags.TAGS.get(k, k): str(v) for k, v in exif.items()}
    except Exception:
        return {}

def has_appended_data_png(data: bytes) -> bool:
    # Busca IEND y comprueba si hay bytes posteriores (típico para “append data”)
    iend = b'IEND'
    idx = data.rfind(iend)
    return idx != -1 and idx + 8 < len(data)  # 4 bytes len + 4 type

def has_extra_app_segments_jpeg(data: bytes) -> dict:
    # Cuenta APPn inusuales y tamaño
    i = 2
    app_counts = {}
    if not (data[:2] == b'\xff\xd8'):
        return {"ok_jpeg": False}
    while i < len(data)-1 and data[i] == 0xFF:
        marker = data[i+1]
        if 0xE0 <= marker <= 0xEF:  # APP0..APP15
            size = struct.unpack(">H", data[i+2:i+4])[0]
            app_counts[f"APP{marker-0xE0}"] = app_counts.get(f"APP{marker-0xE0}", 0) + 1
            i += 2 + size
        elif marker == 0xDA:  # SOS -> datos de imagen hasta EOI
            break
        else:
            # Otros marcadores con tamaño
            if marker in (0xC0,0xC2,0xC4,0xDB,0xDD,0xFE):
                size = struct.unpack(">H", data[i+2:i+4])[0]
                i += 2 + size
            else:
                i += 2
    # ¿Quedan bytes tras EOI?
    has_trailing = not data.endswith(b'\xff\xd9')
    return {"ok_jpeg": True, "app_counts": app_counts, "has_trailing": has_trailing}

# ---------- B) LSB y bitplanes (PNG/BMP/RGB) ----------
def lsb_chi_square(img: Image.Image) -> dict:
    arr = np.asarray(img.convert('L'))  # luminancia
    lsb = arr & 1
    ones = int(lsb.sum())
    zeros = lsb.size - ones
    # χ² para 1/0 esperados ~50/50 (heurística)
    expected = lsb.size / 2.0
    chi2 = (zeros - expected)**2/expected + (ones - expected)**2/expected
    p_imbalance = abs(ones - expected) / expected
    return {"chi2": float(chi2), "p_imbalance": float(p_imbalance), "ones": ones, "zeros": zeros}

def rs_analysis(img: Image.Image) -> dict:
    # Simplificación: mide cambios al voltear LSB en bloques (firma RS)
    arr = np.asarray(img.convert('L'), dtype=np.int16)
    def f(block):  # función de discriminación simple (gradiente local)
        gx = np.diff(block, axis=1)
        return np.sum(np.abs(gx))
    h, w = arr.shape
    block_w = 8
    blocks = []
    for y in range(0, h - block_w + 1, block_w):
        for x in range(0, w - block_w + 1, block_w):
            b = arr[y:y+block_w, x:x+block_w]
            blocks.append(b)
    if not blocks:
        return {"rs_score": 0.0, "blocks": 0}
    orig = np.array([f(b) for b in blocks])
    flipped = np.array([f((b ^ 1)) for b in blocks])  # voltear LSB
    rs_score = float(np.mean(flipped - orig))
    return {"rs_score": rs_score, "blocks": int(len(blocks))}

def visualize_bitplanes(img: Image.Image, out_prefix: str):
    arr = np.asarray(img.convert('L'))
    for k in range(8):
        bp = ((arr >> k) & 1) * 255
        Image.fromarray(bp.astype(np.uint8)).save(f"{out_prefix}_bit{k}.png")

# ---------- C) JPEG: ELA y heurística DCT ----------
def error_level_analysis(path: str, quality=90) -> dict:
    img = Image.open(path).convert('RGB')
    # recomprime y resta
    tmp = "_tmp_ela.jpg"
    img.save(tmp, "JPEG", quality=quality)
    recompressed = Image.open(tmp).convert('RGB')
    diff = ImageChops.difference(img, recompressed)
    # Amplifica para ver artefactos
    extrema = diff.getextrema()
    scale = max(e[1] for e in extrema) or 1
    ela = diff.point(lambda p: 255 * p / scale)
    out = os.path.splitext(path)[0] + "_ELA.png"
    ela.save(out)
    arr = np.asarray(diff.convert('L'))
    stats = {"ela_mean": float(np.mean(arr)), "ela_std": float(np.std(arr)), "ela_image": out}
    return stats

# ---------- D) Scoring ----------
def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x

def _ramp(x: float, lo: float, hi: float) -> float:
    """0 por debajo de lo, 1 por encima de hi, lineal entre medias."""
    if hi <= lo:
        return 0.0
    return _clamp01((x - lo) / (hi - lo))

def score_heuristic(results: dict) -> dict:
    """
    Scoring heurístico para PNG/BMP (LSB) y JPEG (ELA).
    - Para LSB: chi2 es la señal principal (tu caso real).
    - p_imbalance se usa como señal secundaria.
    - RS (versión simple) se usa con poco peso (da falsos positivos).
    - trailing/appended data suma bastante.
    """

    score = 0.0
    notes = []

    # --- Señales de "bytes extra" (muy relevantes) ---
    if results.get("appended_png"):
        score += 0.35
        notes.append("Bytes extra tras IEND (PNG)")
    if "structure" in results and isinstance(results["structure"], dict):
        if results["structure"].get("has_trailing"):
            score += 0.35
            notes.append("Bytes extra tras fin de archivo (JPEG)")

    # --- LSB (PNG/BMP/TIFF) ---
    if "lsb" in results:
        chi2 = float(results["lsb"].get("chi2", 0.0))
        imb = float(results["lsb"].get("p_imbalance", 0.0))

        # chi2: en tus pruebas:
        # - limpio ~0.3
        # - 30%  ~3.3
        # - 100% ~93
        #
        # Usamos una rampa “suave”:
        #   <1   -> casi nada
        #   1..10 -> empieza a oler
        #   >10  -> muy sospechoso
        chi2_s = _ramp(math.log10(chi2 + 1.0), lo=math.log10(2.0), hi=math.log10(11.0))
        # (equivale aprox a chi2 entre 1 y 10)

        score += chi2_s * 0.50
        if chi2 >= 10:
            notes.append("Chi2 LSB alto (posible embedding)")
        elif chi2 >= 3:
            notes.append("Chi2 LSB moderado")

        # p_imbalance: normalmente es pequeño, pero si crece suma un poco
        imb_s = _ramp(imb, lo=0.002, hi=0.02)
        score += imb_s * 0.10
        if imb >= 0.01:
            notes.append("LSB desequilibrado")

    # --- RS (tu versión simple) con poco peso ---
    if "rs" in results:
        rs = float(results["rs"].get("rs_score", 0.0))
        # Tus valores rondan 11-13 incluso en limpio: lo tratamos como señal débil.
        rs_s = _ramp(abs(rs), lo=15.0, hi=40.0)
        score += rs_s * 0.10
        if rs_s > 0.3:
            notes.append("Firma RS anómala")

    # --- JPEG ELA ---
    if "jpeg" in results:
        m = float(results["jpeg"].get("ela_mean", 0.0))
        s = float(results["jpeg"].get("ela_std", 0.0))
        ela = m + s
        ela_s = _ramp(ela, lo=15.0, hi=60.0)
        score += ela_s * 0.25
        if ela_s > 0.4:
            notes.append("ELA elevado (posible manipulación)")

    score = float(_clamp01(score))

    if score >= 0.70:
        verdict = "SOSPECHOSO"
    elif score >= 0.40:
        verdict = "INTERMEDIO"
    else:
        verdict = "BAJO"

    return {"score": score, "verdict": verdict, "notes": list(dict.fromkeys(notes))}

def plot_metrics(results: dict, out_path: str):
    import matplotlib.pyplot as plt

    labels = []
    values = []

    if "lsb" in results:
        labels += ["chi2", "p_imbalance"]
        values += [float(results["lsb"].get("chi2", 0.0)),
                   float(results["lsb"].get("p_imbalance", 0.0))]

    if "rs" in results:
        labels += ["rs_score"]
        values += [float(results["rs"].get("rs_score", 0.0))]

    if "jpeg" in results:
        labels += ["ela_mean", "ela_std"]
        values += [float(results["jpeg"].get("ela_mean", 0.0)),
                   float(results["jpeg"].get("ela_std", 0.0))]

    # Siempre mostramos score final si está
    if "summary" in results:
        labels += ["final_score"]
        values += [float(results["summary"].get("score", 0.0))]

    plt.figure()
    plt.title(f"Métricas - {results.get('path', '')}\nVeredicto: {results.get('summary', {}).get('verdict', '')}")
    plt.bar(labels, values)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def save_metrics_csv(results: dict, out_csv: str):
    # CSV sencillo (1 fila) para comparar muchos runs rápido
    import csv

    row = {
        "path": results.get("path", ""),
        "format": results.get("format", ""),
        "chi2": results.get("lsb", {}).get("chi2", ""),
        "p_imbalance": results.get("lsb", {}).get("p_imbalance", ""),
        "rs_score": results.get("rs", {}).get("rs_score", ""),
        "ela_mean": results.get("jpeg", {}).get("ela_mean", ""),
        "ela_std": results.get("jpeg", {}).get("ela_std", ""),
        "final_score": results.get("summary", {}).get("score", ""),
        "verdict": results.get("summary", {}).get("verdict", ""),
    }

    file_exists = os.path.exists(out_csv)
    with open(out_csv, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            w.writeheader()
        w.writerow(row)

# ---------- Main CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Stego Scout - detector heurístico de esteganografía")
    ap.add_argument("image", help="Ruta de la imagen")
    ap.add_argument("--visualize", action="store_true", help="Guardar bitplanes/ELA")
    ap.add_argument("--report", default=None, help="Guardar JSON con resultados")
    ap.add_argument("--plot", action="store_true", help="Guardar gráfico de métricas (PNG)")
    ap.add_argument("--csv", default=None, help="Guardar/append métricas en CSV")
    args = ap.parse_args()

    path = args.image
    data = read_bytes(path)
    ext = os.path.splitext(path)[1].lower().strip(".")
    res = {"path": path, "format": ext, "exif": extract_exif(path)}
    # estructura
    if ext in ("jpg", "jpeg"):
        res["structure"] = has_extra_app_segments_jpeg(data)
    elif ext == "png":
        res["appended_png"] = has_appended_data_png(data)

    # análisis por formato
    if ext in ("png", "bmp", "tiff"):
        img = Image.open(path)
        res["lsb"] = lsb_chi_square(img)
        res["rs"] = rs_analysis(img)
        if args.visualize:
            visualize_bitplanes(img, os.path.splitext(path)[0])
    elif ext in ("jpg", "jpeg"):
        res["jpeg"] = error_level_analysis(path)
    else:
        res["note"] = "Formato no soportado aún."

    res["summary"] = score_heuristic(res)
    
    base = os.path.splitext(path)[0]

    if args.plot:
        plot_path = base + "_metrics.png"
        plot_metrics(res, plot_path)

    if args.csv:
        save_metrics_csv(res, args.csv)

    print(json.dumps(res, ensure_ascii=False, indent=2))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()