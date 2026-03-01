from PIL import Image
import numpy as np

DELIM = "1111111111111110"  # 16-bit delimitador fin

def inject_lsb(input_path, output_path, message):
    img = Image.open(input_path).convert("RGB")
    arr = np.array(img, dtype=np.uint8)

    # mensaje -> bits
    bits = ''.join(format(ord(c), '08b') for c in message) + DELIM

    flat = arr.reshape(-1)  # 1D, comparte memoria con arr

    if len(bits) > flat.size:
        raise ValueError(f"Mensaje demasiado grande. Bits: {len(bits)} / Capacidad: {flat.size}")

    for i, b in enumerate(bits):
        flat[i] = (flat[i] & 0xFE) | int(b)  # 0xFE = 254 = 11111110

    out = Image.fromarray(arr, mode="RGB")
    out.save(output_path)
    print(f"OK: inyectado en {output_path}. Bits usados: {len(bits)}")

if __name__ == "__main__":
    inject_lsb("img1.png", "img1_infected.png", "HOLA ESTO ES UNA PRUEBA SECRETA")