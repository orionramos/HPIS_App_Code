#!/usr/bin/env python3
"""
analyze_multimodal_full.py

Script unificado:
- Analiza top-3 de estrategias y genera Borda, posiciones y pairwise.
- Calcula puntajes de combinaciones de videos y genera tabla y gráfica.
"""
import pandas as pd
import numpy as np
import re
import os
import matplotlib.pyplot as plt
import seaborn as sns

# --------------------------
# FUNCIONES TOP-3
# --------------------------
def detect_rank_columns(df):
    rank_indicators = ['primer', '1er', 'primero', 'segundo', '2do', 'tercero', '3er']
    detected = []
    for c in df.columns:
        col = df[c].astype(str).str.lower()
        if any(col.str.contains(ind, na=False).any() for ind in rank_indicators):
            detected.append(c)
    return detected

def parse_position_string(s):
    if pd.isna(s): return None
    s = str(s).lower()
    if re.search(r'primer|primero|1er', s): return 1
    if re.search(r'segundo|2do', s): return 2
    if re.search(r'tercer|3er', s): return 3
    return None

def extract_strategy_label(colname):
    m = re.search(r'\[(.*?)\]\s*$', colname)
    if m: return m.group(1).strip()
    parts = re.split(r'[-—\)\:]', colname)
    return parts[-1].strip() if parts else colname

def parse_top3_lists(df, rank_cols):
    col_to_label = {c: extract_strategy_label(c) for c in rank_cols}
    parsed_lists = []
    for idx, row in df.iterrows():
        pos_map = {}
        for c in rank_cols:
            pos = parse_position_string(row.get(c, None))
            if pos: pos_map[pos] = col_to_label[c]
        ordered = [pos_map.get(1), pos_map.get(2), pos_map.get(3)]
        parsed_lists.append([x for x in ordered if x])
    return parsed_lists, col_to_label

def compute_counts_and_borda(parsed_lists, strategies):
    counts = {s: {'top1':0,'top2':0,'top3':0,'borda':0} for s in strategies}
    points = {1:3, 2:2, 3:1}
    for lst in parsed_lists:
        for pos, s in enumerate(lst, start=1):
            if s is None: continue
            if pos <=3:
                counts[s][f'top{pos}'] += 1
                counts[s]['borda'] += points[pos]
    df = pd.DataFrame(counts).T
    df['borda_norm'] = df['borda']/df['borda'].sum()
    return df.sort_values('borda', ascending=False)

def pairwise_matrix(parsed_lists, strategies):
    wins = pd.DataFrame(0, index=strategies, columns=strategies, dtype=int)
    for lst in parsed_lists:
        for i in strategies:
            for j in strategies:
                if i==j: continue
                if i in lst and (j not in lst or lst.index(i)<lst.index(j)):
                    wins.loc[i,j] += 1
    return wins

def plot_borda(df_counts, outdir):
    plt.figure(figsize=(8,4))
    sns.barplot(x=df_counts.index, y='borda', data=df_counts.reset_index())
    plt.xticks(rotation=45, ha='right')
    plt.title('Borda score por estrategia')
    plt.tight_layout()
    path = os.path.join(outdir, 'borda_bar.png')
    plt.savefig(path, dpi=200)
    plt.close()
    return path

def plot_stacked_top_positions(df_counts, outdir):
    ind = np.arange(len(df_counts))
    plt.figure(figsize=(8,4))
    plt.bar(ind, df_counts['top1'], label='1°')
    plt.bar(ind, df_counts['top2'], bottom=df_counts['top1'], label='2°')
    plt.bar(ind, df_counts['top3'], bottom=df_counts['top1']+df_counts['top2'], label='3°')
    plt.xticks(ind, df_counts.index, rotation=45, ha='right')
    plt.title('Distribución posiciones top-3')
    plt.legend()
    plt.tight_layout()
    path = os.path.join(outdir, 'stacked_top123.png')
    plt.savefig(path, dpi=200)
    plt.close()
    return path

def plot_pairwise(wins, outdir):
    plt.figure(figsize=(6,6))
    sns.heatmap(wins, annot=True, fmt='d', cmap='viridis')
    plt.title('Pairwise wins')
    plt.tight_layout()
    path = os.path.join(outdir, 'pairwise_heatmap.png')
    plt.savefig(path, dpi=200)
    plt.close()
    return path

# --------------------------
# FUNCIONES COMBINACIONES
# --------------------------
def compute_combinations(df, clarity_cols, combinations):
    total_points = {k:0 for k in combinations}
    for idx, row in df.iterrows():
        ratings = row[clarity_cols].tolist()
        shift = idx % 9
        aligned_ratings = ratings[shift:] + ratings[:shift]
        for comb_name, video_nums in combinations.items():
            comb_score = sum(aligned_ratings[v-1] for v in video_nums)
            total_points[comb_name] += comb_score
    df_totals = pd.DataFrame.from_dict(total_points, orient='index', columns=['Total'])
    df_totals = df_totals.sort_values('Total', ascending=False)
    return df_totals

def plot_combinations(df_totals, outdir):
    plt.figure(figsize=(10,5))
    df_totals['Total'].plot(kind='bar', color='skyblue')
    plt.title('Total de puntos por combinación')
    plt.ylabel('Puntos totales')
    plt.xlabel('Combinación')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    path = os.path.join(outdir, 'combinations_totals.png')
    plt.savefig(path, dpi=200)
    plt.close()
    return path

# --------------------------
# MAIN
# --------------------------
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'Multi-Modal Selection.csv')
    outdir = os.path.join(script_dir, 'results')
    os.makedirs(outdir, exist_ok=True)

    df = pd.read_csv(csv_path)

    # --- TOP-3 ---
    rank_cols = detect_rank_columns(df)
    if rank_cols:
        parsed_lists, col_to_label = parse_top3_lists(df, rank_cols)
        strategies = sorted(set(col_to_label.values()))
        df_counts = compute_counts_and_borda(parsed_lists, strategies)
        df_counts.to_csv(os.path.join(outdir, 'counts_borda.csv'))
        wins = pairwise_matrix(parsed_lists, strategies)
        wins.to_csv(os.path.join(outdir, 'pairwise_wins.csv'))
        plot_borda(df_counts, outdir)
        plot_stacked_top_positions(df_counts, outdir)
        plot_pairwise(wins, outdir)
        print("Análisis top-3 completado.")
    else:
        print("No se detectaron columnas top-3.")

    # --- COMBINACIONES DE VIDEOS ---
    clarity_cols = [c for c in df.columns if "claridad" in c.lower()]
    videos = list(range(1,10))
    combinations = {
        "1-4":[1,4],"1-5":[1,5],"1-6":[1,6],
        "2-4":[2,4],"2-5":[2,5],"2-6":[2,6],
        "3-4":[3,4],"3-5":[3,5],"3-6":[3,6]
    }
    df_totals = compute_combinations(df, clarity_cols, combinations)
    df_totals.to_csv(os.path.join(outdir, 'combinations_totals.csv'))
    plot_combinations(df_totals, outdir)
    print("Análisis de combinaciones completado.")

    print("Resultados guardados en carpeta:", outdir)

if __name__ == '__main__':
    main()
