# Sudoku-Solver mit Grover-Algorithmus
 
Dieses Projekt löst 4×4-Sudokus mit dem **Grover-Algorithmus**. Die Quantenschaltkreise werden mit [Qiskit](https://qiskit.org/) gebaut und mit dem `AerSimulator` (Matrix-Product-State-Methode) simuliert.
 
Das Projekt ist ein Lern- und Demonstrationsbeispiel. Es zeigt, wie sich ein Constraint-Problem als Suchproblem für Grover formulieren lässt, und kein Verfahren, das klassische Sudoku-Löser übertrifft.
 
## Idee
 
Jede leere Zelle eines 4×4-Sudokus wird mit **2 Qubits** codiert (die Werte 1–4 entsprechen den Zuständen `00` bis `11`). Die Grover-Suche findet dann die Belegung, die alle Sudoku-Regeln erfüllt.
 
Ablauf:
 
1. **Preprocessing (klassisch):** Für jede leere Zelle werden die erlaubten Kandidaten (1–4) bestimmt. Außerdem wird eine Liste aller Paare leerer Zellen erstellt, die sich in Zeile, Spalte oder 2×2-Block unterscheiden müssen.
2. **Zustandspräparation:** Statt einer gleichverteilten Superposition über alle 4 Werte wird nur über die erlaubten Kandidaten jeder Zelle superponiert (1 Kandidat: fester Wert, 2 oder 3 Kandidaten: gezielte Superposition, 4 Kandidaten: Hadamard). Das verkleinert den Suchraum `N` deutlich.
3. **Orakel:** Für jedes Zellpaar prüft eine Ungleichheits-Schaltung, ob beide Zellen verschiedene Werte haben. Sind alle Bedingungen erfüllt, wird die Phase des Lösungszustands per Phase-Kickback umgedreht. Die Hilfsqubits werden anschließend wieder zurückgerechnet (Uncomputation).
4. **Diffusion:** Inversion am Mittelwert, angepasst an die präparierte Startverteilung (Zustandspräparation rückwärts, Reflexion, Zustandspräparation vorwärts).
5. **Iterationen:** Die Anzahl der Grover-Iterationen wird aus `N` und der Anzahl der Lösungen `M` berechnet:
   `k = round( π / (4 · arcsin(√(M/N))) − 1/2 )`
6. **Messung und Auswertung:** Der häufigste Bitstring wird in Sudoku-Werte umgewandelt und klassisch mit `valid_sudoku` geprüft.
## Voraussetzungen
 
- Python 3.10 oder neuer (getestet mit Python 3.14.3)
- Pakete: siehe `requirements.txt`
## Installation
 
```bash
git clone https://github.com/DEIN-NAME/sudoku-grover.git
cd sudoku-grover
 
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
 
pip install -r requirements.txt
```
 
## Verwendung
 
Das Notebook `sudoku_grover_Simulation.ipynb` enthält den kompletten Ablauf:
 
```bash
jupyter notebook sudoku_grover_Simulation.ipynb
```
 
Es erzeugt ein zufälliges Rätsel, berechnet Kandidaten, Constraints, `N`, `M` und `k`, baut den Schaltkreis, simuliert ihn mit 1000 Shots und gibt die gefundene Lösung samt Histogramm aus.
 
Beispielausgabe:
 
```
--- Rätsel (Eingabe) ---
. . | . 2
4 . | . 3
-----------
3 . | . .
2 4 | 3 1
 
Suchraum N: 16, Lösungen M: 1
Grover-Iterationen: 3
 
--- Lösung GEFUNDEN ✅ ---
1 3 | 4 2
4 2 | 1 3
-----------
3 1 | 2 4
2 4 | 3 1
```
 
## Projektstruktur
 
| Datei | Inhalt |
|---|---|
| `sudoku_grover.py` | Preprocessing, Zustandspräparation, Orakel, Diffusion und Hilfsfunktionen |
| `sudoku_grover_Simulation.ipynb` | Beispielablauf mit Simulation und Auswertung |
| `requirements.txt` | Python-Abhängigkeiten |
 
## Schaltkreis-Layout (29 Qubits)
 
| Qubits | Verwendung |
|---|---|
| 0–15 | Datenqubits (bis zu 8 leere Zellen à 2 Qubits) |
| 16–25 | Hilfsqubits für die Ungleichheitsprüfungen |
| 26–27 | Zwischenergebnisse der beiden Orakel-Hälften |
| 28 | Zielqubit für den Phase-Kickback |
 
## Einschränkungen
 
- Das Layout ist auf **16 Datenqubits** (8 leere Zellen) und höchstens **20 Constraints** ausgelegt. Die Hilfsqubits reichen für je 10 Constraints pro Orakel-Hälfte.
- Die Anzahl der Lösungen `M` wird **klassisch** bestimmt, um die optimale Iterationszahl zu berechnen. Das ist keine echte Black-Box-Suche. Dort müsste man `M` schätzen oder mit verschiedenen Iterationszahlen probieren.
- Hat ein Puzzle mehrere Lösungen, liefert die Messung eine davon (die häufigste).
- Das Projekt läuft nur im Simulator. Für echte Quantenhardware wäre der Schaltkreis zu tief und zu groß.
- Die Simulation nutzt die Matrix-Product-State-Methode. Die Laufzeit kann bei vielen Iterationen deutlich steigen.
