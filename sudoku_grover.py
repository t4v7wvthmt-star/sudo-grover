from qiskit import QuantumCircuit
import numpy as np

# --- 1. SUDOKU VISUALIZIERUNG LOGIK & ANALYSE ---

def print_sudoku_board(mat, title="Sudoku Board"):
    """Gibt das 4x4 Sudoku in einem formatierten Raster aus."""
    print(f"\n--- {title} ---")
    for i, row in enumerate(mat):
        # Horizontale Trennlinie nach jedem Block (alle 2 Zeilen)
        if i > 0 and i % 2 == 0:
            print("-" * 11)
        
        row_str = ""
        for j, val in enumerate(row):
            # Vertikale Trennlinie nach jedem Block (alle 2 Spalten)
            if j > 0 and j % 2 == 0:
                row_str += "| "
            
            # Zeige '.' für unbekannte Felder (0), sonst die Zahl
            display_val = str(val) if val != 0 else "."
            row_str += display_val + " "
        
        print(row_str.strip())
    print("-----------------\n")

def get_sudoku_block(x, y):
    """Bestimmt den 2x2 Block-Index eines 4x4 Sudokus."""
    if x < 2 and y < 2: return 0
    if x < 2: return 1
    if y < 2: return 2
    return 3

def find_cell_candidates(mat):
    """Analysiert das Board und findet erlaubte Zahlen (1-4) für jede leere Zelle."""
    cands = []
    for i in range(4):
        for j in range(4):
            if mat[i][j] != 0:
                continue
            tmp = []
            for k in range(4):
                val = k + 1
                f = True
                # Zeilen- & Spalten-Check
                for check in range(4):
                    if mat[check][j] == val or mat[i][check] == val:
                        f = False
                # Block-Check
                for x in range(4):
                    for y in range(4):
                        if get_sudoku_block(i, j) == get_sudoku_block(x, y):
                            if mat[x][y] == val:
                                f = False
                if f:
                    tmp.append(val)
            cands.append(tmp)
    
    return cands

def map_constraints_to_qubits(sudocu):
    """Erstellt eine Liste von Qubit-Paaren, die ungleich sein müssen (Constraints)."""
    s_map = np.zeros((4, 4), dtype=int)
    qubit_count = 0
    for i in range(4):
        for j in range(4):
            if sudocu[i][j] == 0:
                s_map[i][j] = qubit_count
                qubit_count += 1

    comp = []
    for i in range(4):
        for j in range(4):
            if sudocu[i][j] != 0: continue
            # Spalten-Constraint
            for row in range(i + 1, 4):
                if sudocu[row][j] == 0:
                    comp.append([s_map[i][j], s_map[row][j]])
            # Zeilen-Constraint
            for col in range(j + 1, 4):
                if sudocu[i][col] == 0:
                    comp.append([s_map[i][j], s_map[i][col]])
            # Block-Constraint
            if i % 2 == 0:
                row = i + 1
                col = j + 1 if j % 2 == 0 else j - 1
                if sudocu[row][col] == 0:
                    comp.append([s_map[i][j], s_map[row][col]])
    return comp

# --- 2. ZUSTANDS-PRÄPARATION (INITIALIZATION) ---

def set_fixed_value(qc, q0, q1, cands):
    """Setzt Qubits auf eine feste Zahl (1-4)."""
    if cands[0] == 2: qc.x(q1)
    elif cands[0] == 3: qc.x(q0)
    elif cands[0] == 4: 
        qc.x(q0)
        qc.x(q1)

def create_dual_superposition(qc, q0, q1, cands, inverse=False):
    """Erzeugt Superposition aus zwei Kandidaten."""
    prod = cands[0] * cands[1]
    if prod == 2: qc.h(q1) # 1 & 2
    elif prod == 3: qc.h(q0) # 1 & 3
    elif prod == 4: # 1 & 4
        if not inverse:
            qc.h(q0)
            qc.cx(q0, q1)
        else:
            qc.cx(q0, q1)
            qc.h(q0)
    elif prod == 6: # 2 & 3
        if not inverse:
            qc.x(q1)
            qc.h(q0)
            qc.cx(q0, q1)
        else:
            qc.cx(q0, q1)
            qc.h(q0)
            qc.x(q1)
    elif prod == 8: # 2 & 4
        qc.x(q1)
        qc.h(q0)
    else: # 3 & 4
        qc.h(q1)
        qc.x(q0)

def create_triple_superposition(qc, q0, q1, cands, inverse=False):
    """
    Erzeugt eine exakte Superposition aus drei Kandidaten (je 1/3 Wahrscheinlichkeit).
    cands: Liste von 3 Zahlen aus {1, 2, 3, 4}
    """
    # 1. Mapping: Sudoku-Werte {1,2,3,4} auf Qubit-Zustände {0,1,2,3}
    # Summe(0,1,2,3) = 6. Der fehlende Wert ist 6 minus die Summe der (cands-1).
    missing_val = 6 - sum([c - 1 for c in cands])
    
    # Winkel für exakt 1/3 Wahrscheinlichkeit: theta = 2 * arcsin(sqrt(1/3))
    theta = 2 * np.arcsin(np.sqrt(1/3))

    if not inverse:
        # BASIS: Erzeuge Superposition von |00>, |01>, |10> (Wert 1, 2, 3)
        # 11 (Wert 4) bleibt auf 0%
        qc.ry(theta, q1)
        qc.ch(q1, q0, ctrl_state='0')
        
        # SHIFT: Falls nicht '4' fehlen soll, schiebe die 0% auf den missing_val
        if missing_val == 0:   # 1 fehlt (binär 00)
            qc.x(q0); qc.x(q1)
        elif missing_val == 1: # 2 fehlt (binär 01)
            qc.x(q0)
        elif missing_val == 2: # 3 fehlt (binär 10)
            qc.x(q1)
    else:
        # INVERSE: Gleiche Operationen in umgekehrter Reihenfolge
        if missing_val == 0:
            qc.x(q1); qc.x(q0)
        elif missing_val == 1:
            qc.x(q0)
        elif missing_val == 2:
            qc.x(q1)
            
        qc.ch(q1, q0, ctrl_state='0')
        qc.ry(-theta, q1)


def prepare_initial_state(qc, qr, mat, inverse=False):
    """Bereitet den Suchraum vor (oder macht ihn rückgängig)."""
    cands = find_cell_candidates(mat)
    indices = range(len(cands))
    if inverse: indices = reversed(indices)
    
    for i in indices:
        q0, q1 = qr[2*i], qr[2*i+1]
        c = cands[i]
        if len(c) == 1: set_fixed_value(qc, q0, q1, c)
        elif len(c) == 2: create_dual_superposition(qc, q0, q1, c, inverse)
        elif len(c) == 3: create_triple_superposition(qc, q0, q1, c, inverse)
        else: # 4 Kandidaten
            qc.h(q0)
            qc.h(q1)

    return cands

# --- 3. DAS ORAKEL (ORACLE) ---

def check_not_equal(qc, qr, v1, v2, target, inv=False):
    """Markiert das target Qubit, wenn zwei Zellen unterschiedliche Werte haben."""
    if inv: qc.x(qr[target])
    qc.x(qr[2*v2])
    qc.x(qr[2*v2+1])
    if not inv:
        qc.ccx(qr[2*v1], qr[2*v1+1], target)
        qc.ccx(qr[2*v1+1], qr[2*v2], target)
        qc.ccx(qr[2*v2], qr[2*v2+1], target)
        qc.ccx(qr[2*v1], qr[2*v2+1], target)
    else:
        qc.ccx(qr[2*v1], qr[2*v2+1], target)
        qc.ccx(qr[2*v2], qr[2*v2+1], target)
        qc.ccx(qr[2*v1+1], qr[2*v2], target)
        qc.ccx(qr[2*v1], qr[2*v1+1], target)
    qc.x(qr[2*v2+1])
    qc.x(qr[2*v2])
    if not inv: qc.x(qr[target])

def sudoku_oracle(qc: QuantumCircuit, qr, constraints):
    """Überprüft alle Sudoku-Regeln."""
    n = len(constraints)
    parts = [constraints[:n//2], constraints[n//2:]]
    # Hilfsqubits für Teilergebnisse [16, 17, 18, 19, 20, 21, 22, 23, 24, 25] maximal 20/2 = 10 nötig
    ancillas = [26, 27] # tmp1, tmp2
    final_dst = 28

    def process_part(part, ancilla_idx):
        t_ptr = 16
        for pair in part:
            check_not_equal(qc, qr, pair[0], pair[1], t_ptr)
            t_ptr += 1
        qc.mcx(qr[16:t_ptr], qr[ancillas[ancilla_idx]])
        for pair in reversed(part):
            t_ptr -= 1
            check_not_equal(qc, qr, pair[0], pair[1], t_ptr, inv=True)

    # Vorwärts
    for i in range(2): process_part(parts[i], i)
    qc.mcx(qr[ancillas], qr[final_dst])
    # Rückwärts (Uncomputation)
    for i in reversed(range(2)): process_part(parts[i], i)

# --- 4. AMPLIFICATION (DIFFUSION) ---

def diffusion(qc, qr, mat):
    """Inversion about the mean."""
    prepare_initial_state(qc, qr, mat, inverse=True)
    qc.x(qr[:16])
    qc.h(qr[15])
    qc.mcx(qr[:15], qr[15])
    qc.h(qr[15])
    qc.x(qr[:16])
    prepare_initial_state(qc, qr, mat, inverse=False)

# --- 5. HILFSPROGRAMME & AUSFÜHRUNG ---

def generate_random_puzzle():
    """Erzeugt ein 4x4 Sudoku mit leeren Feldern."""
    # Beispielhaftes statisches Layout für Stabilität
    base = [1,2,3,4, 3,4,1,2, 2,1,4,3, 4,3,2,1]
    base = np.array([1, 2, 3, 4, 3, 4, 1, 2, 2, 1, 4, 3, 4, 3, 2, 1])

    # Einzigartige Zahlen zufällig durchmischen
    shuffled = np.random.permutation([1, 2, 3, 4])

    # Mapping erstellen und auf base anwenden
    mapping = dict(zip([1, 2, 3, 4], shuffled))
    marked = np.array([mapping[val] for val in base])
    eindeutige_zahlen = np.random.choice(np.arange(16), size=8, replace=False)
    for i in eindeutige_zahlen: marked[i] = 0
    marked.resize(4, 4)
    return marked

# 2. Bestimme M (Anzahl der gültigen Lösungen) klassisch für die Adaption
# (In einer echten Black-Box-Suche müsste man Grover-Search mehrfach mit 
# variierenden Iterationen probieren, hier optimieren wir für die Erfolgsrate)

def count_solutions(sudoku, candidates):
    # Einfacher rekursiver Check der Kandidaten-Kombinationen
    import itertools
    valid_count = 0
    empty_indices = np.where(sudoku == 0)
    for combo in itertools.product(*candidates):
        test_sudoku = sudoku.copy()
        test_sudoku[empty_indices] = combo
        if valid_sudoku(test_sudoku):
            valid_count += 1
    return max(1, valid_count) # Mindestens 1 annehmen

def quantum_state_to_sudoku_format(bin_str):
    """Konvertiert Bitstring in Zahlen 1-4."""
    bin_str = bin_str[::-1]
    return ''.join([str(int(bin_str[2*i:2*i+2], 2) + 1) for i in range(len(bin_str)//2)])

def valid_sudoku(board):
    for i in range(4):
        if sorted(board[i]) != [1,2,3,4]:
            return False
        if sorted(board[:,i]) != [1,2,3,4]:
            return False

    for bx in range(2):
        for by in range(2):
            block=[]
            for i in range(2):
                for j in range(2):
                    block.append(board[bx*2+i][by*2+j])
            if sorted(block) != [1,2,3,4]:
                return False
    return True
