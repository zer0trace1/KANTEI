from PIL import Image
import numpy as np
import os

def inject_lsb_fill(input_path, output_path, fill_ratio=1.0, seed=1337):
    """
    fill_ratio: 0.0 a 1.0 -> porcentaje de valores (canales) a modificar en su LSB
    """
    rng = np.random.default_rng(seed)

    img = Image.open(input_path).convert("RGB")
    arr = np.array(img, dtype=np.uint8)
    flat = arr.reshape(-1)

    n = flat.size
    k = int(n * float(fill_ratio))
    if k <= 0:
        raise ValueError("fill_ratio demasiado bajo")

    # Elegimos k posiciones aleatorias
    idx = rng.choice(n, size=k, replace=False)

    # Generamos bits aleatorios 0/1
    bits = rng.integers(0, 2, size=k, dtype=np.uint8)

    # Escribimos en LSB
    flat[idx] = (flat[idx] & 0xFE) | bits

    Image.fromarray(arr, "RGB").save(output_path)
    print(f"OK: escrito LSB en {k}/{n} valores ({fill_ratio*100:.1f}%). Guardado: {output_path}")

if __name__ == "__main__":
    inject_lsb_fill("img1.png", "img1_infected_30.png", fill_ratio=0.30, seed=1337)
    inject_lsb_fill("img1.png", "img1_infected_100.png", fill_ratio=1.00, seed=1337)