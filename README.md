# 🕵️ KANTEI

A Python-based heuristic tool for detecting potential steganography in
images (PNG / JPEG).

---

# 🐍 Python Compatibility

This project requires:

**Python 3.9 or newer**\
(Recommended: Python 3.9 -- 3.13)

Python 3.14+ may work but is very recent and some third-party libraries
may take time to fully support it.

## Check your Python version

Windows:

```bash
py --version
```

or

```bash
python --version
```

Linux / macOS:

```bash
python3 --version
```

---

# 📦 Installation

## 1️⃣ Clone the repository

```bash
git clone https://github.com/zer0trace1/KANTEI.git
cd KANTEI
```

---

## 2️⃣ Create a virtual environment

### Windows (PowerShell)

```bash
py -m venv [name]
.\[name]\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv [name]
source [name]/bin/activate
```

---

## 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

If you do not have `requirements.txt`, install manually:

```bash
pip install pillow numpy matplotlib
```

Optional (for future ML module):

```bash
pip install scikit-learn pandas
```

---

# 🚀 Running the Program

Depending on your OS and Python installation:

### Windows

```bash
py stego-scanner.py image.png --plot
```

or

```bash
python stego-scanner.py image.png --plot
```

### Linux / macOS

```bash
python3 stego-scanner.py image.png --plot
```

If multiple Python versions are installed, you can specify one
explicitly:

```bash
py -3.12 stego-scanner.py image.png
```

---

# 🔍 Analyze an Image

```bash
python stego-scanner.py image.png --plot --report report.json
```

---

## Available Options

Option Description

---

`--visualize` Generates bitplane images (PNG/BMP)
`--plot` Generates metric graph (`*_metrics.png`)
`--report file.json` Saves full report as JSON
`--csv metrics.csv` Appends metrics to a cumulative CSV

---

# 🧪 Generate Test Images (LSB Injection)

```bash
python inject_lsb_fill.py
```

By default, it generates:

- `img1_infected_30.png`
- `img1_infected_100.png`

---

# 📊 Generated Outputs

- `*_metrics.png` → Metric visualization graph
- `*_ELA.png` → JPEG ELA image
- `*_bit0.png ... *_bit7.png` → Bitplanes
- `metrics.csv` → Accumulated dataset of runs
- `report.json` → Full analysis report

---

# 🧠 Technical Overview

The system combines classical steganalysis techniques:

- **LSB Chi-Square** (statistical deviation detection)
- **Simplified RS Analysis**
- **ELA (JPEG recompression difference)**
- **Structural file analysis (trailing data detection)**

The tool produces a **heuristic score (0--1)** and a verdict:

- `LOW`
- `MEDIUM`
- `SUSPICIOUS`

---

# ⚠️ Limitations

- Heuristic-based detection (not mathematically definitive).
- Does not automatically extract hidden payloads.
- Advanced DCT-based detection not yet implemented.

---

# 🔮 Roadmap

- 🤖 Machine Learning classifier based on extracted features
- 📊 Large-scale dataset evaluation
- 🧠 Full RS and SPA implementation
- 🔍 Advanced DCT-based JPEG analysis
- 📦 Packaging as an installable CLI tool

---

# ⚖️ Legal Notice

This project is intended for educational and cybersecurity research
purposes only.\
Do not use it for illegal activities.
