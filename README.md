# 🕵️ Stego Scanner

A Python-based heuristic tool for detecting potential steganography in images (PNG / JPEG).

This project includes:

- 📊 LSB statistical analysis (Chi-square, imbalance)
- 🔎 Simplified RS analysis
- 🖼 ELA (Error Level Analysis) for JPEG
- 📈 Automatic metric visualization
- 🧪 LSB injection script for generating test images
- 📁 Export of results to JSON and CSV

---

# 📦 Installation

## 1️⃣ Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/stego-scanner.git
cd stego-scanner
```

---

## 2️⃣ Create a virtual environment

### Windows (PowerShell)

```bash
python -m venv stego
.\stego\Scriptsctivate
```

### Linux / macOS

```bash
python3 -m venv stego
source stego/bin/activate
```

---

## 3️⃣ Install dependencies

If `requirements.txt` is included:

```bash
pip install -r requirements.txt
```

If not, install manually:

```bash
pip install pillow numpy matplotlib
```

Optional (for upcoming ML features):

```bash
pip install scikit-learn pandas
```

---

# 🚀 Usage

## 🔍 Analyze an image

```bash
python stego-scanner.py image.png --plot --report report.json
```

---

## Available Options

| Option | Description |
|--------|------------|
| `--visualize` | Generates bitplane images (PNG/BMP) |
| `--plot` | Generates metric graph (`*_metrics.png`) |
| `--report file.json` | Saves full report as JSON |
| `--csv metrics.csv` | Appends metrics to a cumulative CSV |

---

### 🔎 Full Example

```bash
python stego-scanner.py img1.png --visualize --plot --report report.json --csv metrics.csv
```

---

# 🧪 Generate Test Images (LSB Injection)

To generate modified test images:

```bash
python inject_lsb_fill.py
```

By default, it generates:

- `img1_infected_30.png`
- `img1_infected_100.png`

You can then analyze them with:

```bash
python stego-scanner.py img1_infected_100.png --plot
```

---

# 📊 Generated Outputs

- `*_metrics.png` → Metric visualization graph
- `*_ELA.png` → JPEG ELA image
- `*_bit0.png ... *_bit7.png` → Bitplanes
- `metrics.csv` → Accumulated dataset of runs
- `report.json` → Full analysis report

---

# 🧠 Technical Background

The system combines classical steganalysis techniques:

### 📌 LSB Chi-Square
Detects statistical deviations in the least significant bit distribution.

### 📌 Simplified RS Analysis
Evaluates block behavior under simulated LSB modification.

### 📌 ELA (JPEG)
Highlights recompression inconsistencies that may indicate manipulation.

### 📌 Structural Analysis
Checks for trailing data and unusual file segments.

The tool produces a **heuristic score (0–1)** and a verdict:

- `LOW`
- `MEDIUM`
- `SUSPICIOUS`

---

# ⚠️ Limitations

- This is a heuristic detector, not a guaranteed proof of steganography.
- It does not automatically extract hidden payloads.
- Advanced DCT-based steganography detection is not yet implemented.

---

# 🔮 Roadmap

- 🤖 Machine Learning classifier based on extracted features
- 📊 Large-scale dataset evaluation
- 🧠 Full RS and SPA implementation
- 🔍 Advanced DCT-based JPEG analysis
- 📦 Packaging as an installable CLI tool

---

# ⚖️ Legal Notice

This project is intended for educational and cybersecurity research purposes only.  
Do not use it for illegal activities.

---

# 👨‍💻 Author

Personal project focused on learning steganalysis and cyber intelligence techniques.
