#!/usr/bin/env python3
"""
analyze_multimodal_top3.py

Versión para analizar calificaciones y top-3 de estrategias multimodales.
"""
import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

def get_sequence_ratings_columns(df):
    """Identifica las columnas que contienen calificaciones de videos (1-7)."""
    rating_cols = []
    base_name = "¿Qué tan claro fue el video para entender qué debe hacer el usuario?"
    for col in df.columns:
        if base_name in col:
            rating_cols.append(col)
    return sorted(rating_cols, key=lambda x: int(x.split('.')[-1]) if '.' in x else 0)

def calculate_total_ratings(df):
    """Calcula la suma total de calificaciones por combinación."""
    combinations = {
        "Combinación 1-4": 0, "Combinación 1-5": 0, "Combinación 1-6": 0,
        "Combinación 2-4": 0, "Combinación 2-5": 0, "Combinación 2-6": 0,
        "Combinación 3-4": 0, "Combinación 3-5": 0, "Combinación 3-6": 0
    }
    
    # Obtener la columna de secuencia y todas las columnas de calificación
    sequence_col = next(col for col in df.columns if 'Secuencia' in col)
    rating_cols = get_sequence_ratings_columns(df)
    
    # Crear el mapeo de secuencias a combinaciones
    base_combinations = list(combinations.keys())
    sequence_combinations = {}
    for i in range(1, 10):
        rotated = base_combinations[i-1:] + base_combinations[:i-1]
        sequence_combinations[f"Secuencia {i}"] = dict(enumerate(rotated))
    
    # Procesar cada fila
    for idx, row in df.iterrows():
        sequence = row[sequence_col]
        if pd.isna(sequence):
            continue
        
        # Obtener el mapeo para esta secuencia
        mapping = sequence_combinations[sequence]
        
        # Procesar los primeros 9 ratings de cada grupo de calificaciones
        # Cada grupo de 9 ratings corresponde a una repetición del experimento
        for start_idx in range(0, len(rating_cols), 9):
            group_cols = rating_cols[start_idx:start_idx + 9]
            for i, col in enumerate(group_cols):
                rating = row[col]
                if pd.notna(rating):
                    combination = mapping[i]
                    combinations[combination] += rating
    
    return pd.Series(combinations)

def get_sequence_mapping():
    """Define el mapeo de secuencias a combinaciones."""
    # Definir las combinaciones en orden base
    combinations = [
        "Combinación 1-4", "Combinación 1-5", "Combinación 1-6",
        "Combinación 2-4", "Combinación 2-5", "Combinación 2-6",
        "Combinación 3-4", "Combinación 3-5", "Combinación 3-6"
    ]
    
    # Crear el mapeo de secuencias (1-9) rotando la lista base
    sequence_mapping = {}
    for i in range(9):
        rotated = combinations[i:] + combinations[:i]
        sequence_mapping[f"Secuencia {i+1}"] = dict(enumerate(rotated))
    
    return sequence_mapping

def process_ratings(df):
    """Procesa las calificaciones según la secuencia asignada a cada usuario."""
    # Obtener columnas de calificación y mapeo de secuencias
    rating_cols = get_sequence_ratings_columns(df)
    sequence_mapping = get_sequence_mapping()
    
    # Crear DataFrame para almacenar las calificaciones procesadas
    processed_ratings = pd.DataFrame()
    
    # Encontrar la columna de secuencia y las columnas de calificación base
    sequence_col = next(col for col in df.columns if 'Secuencia' in col)
    base_cols = [col for col in df.columns if '¿Qué tan claro fue el video' in col][:9]  # Solo las primeras 9 columnas
    
    # Procesar cada fila (usuario)
    for idx, row in df.iterrows():
        sequence = row[sequence_col]
        if pd.isna(sequence) or sequence not in sequence_mapping:
            continue
            
        # Obtener el mapeo específico para esta secuencia
        mapping = sequence_mapping[sequence]
        
        # Crear una nueva fila con las calificaciones mapeadas correctamente
        new_row = {}
        for i, col in enumerate(base_cols):
            if pd.notna(row[col]):
                combination = sequence_mapping[sequence][i]
                new_row[combination] = row[col]
        
        processed_ratings = pd.concat([processed_ratings, 
                                    pd.DataFrame([new_row])], 
                                    ignore_index=True)
    
    return processed_ratings

def detect_rank_columns(df):
    """Detecta columnas que contienen rankings (1er, 2do, 3er lugar)."""
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
    plt.figure(figsize=(10,5))
    
    # Translate combination names to English
    df_counts.index = [name.replace('Combinación', 'Combination') for name in df_counts.index]
    
    sns.barplot(x=df_counts.index, y='borda', data=df_counts.reset_index())
    plt.xticks(rotation=45, ha='right')
    plt.title('Borda Score by Strategy', pad=20, fontsize=12)
    plt.xlabel('Strategy Type', fontsize=10)
    plt.ylabel('Borda Score', fontsize=10)
    plt.tight_layout()
    path = os.path.join(outdir, 'borda_bar.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    return path

def plot_stacked_top_positions(df_counts, outdir):
    ind = np.arange(len(df_counts))
    plt.figure(figsize=(10,5))
    
    # Translate combination names to English
    df_counts.index = [name.replace('Combinación', 'Combination') for name in df_counts.index]
    
    plt.bar(ind, df_counts['top1'], label='1st Place')
    plt.bar(ind, df_counts['top2'], bottom=df_counts['top1'], label='2nd Place')
    plt.bar(ind, df_counts['top3'], bottom=df_counts['top1']+df_counts['top2'], label='3rd Place')
    plt.xticks(ind, df_counts.index, rotation=45, ha='right')
    plt.title('Distribution of Top-3 Positions', pad=20, fontsize=12)
    plt.xlabel('Strategy Type', fontsize=10)
    plt.ylabel('Number of Rankings', fontsize=10)
    plt.legend()
    plt.tight_layout()
    path = os.path.join(outdir, 'stacked_top123.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    return path

def plot_pairwise(wins, outdir):
    plt.figure(figsize=(8,8))
    
    # Translate combination names to English
    wins.index = [name.replace('Combinación', 'Combination') for name in wins.index]
    wins.columns = [name.replace('Combinación', 'Combination') for name in wins.columns]
    
    sns.heatmap(wins, annot=True, fmt='d', cmap='viridis')
    plt.title('Pairwise Strategy Comparison', pad=20, fontsize=12)
    plt.xlabel('Strategy Type', fontsize=10)
    plt.ylabel('Strategy Type', fontsize=10)
    plt.tight_layout()
    path = os.path.join(outdir, 'pairwise_heatmap.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    return path

def analyze_combinations(ratings_stats, rankings_df, total_ratings, pairwise_wins):
    """
    Realiza un análisis exhaustivo y estandarizado de las combinaciones.
    """
    analysis = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Encabezado del análisis
    analysis.append("=== COMPREHENSIVE MULTIMODAL ANALYSIS REPORT ===")
    analysis.append(f"Generated on: {current_time}\n")
    
    # Preparar diccionarios para análisis de modalidades
    modality_scores = {
        'audio_expert': {'borda': [], 'first': [], 'combinations': []},
        'audio_minimal': {'borda': [], 'first': [], 'combinations': []},
        'audio_llm': {'borda': [], 'first': [], 'combinations': []},
        'text_expert': {'borda': [], 'first': [], 'combinations': []},
        'video': {'borda': [], 'first': [], 'combinations': []},
        'animation_3d': {'borda': [], 'first': [], 'combinations': []}
    }

    # 2. Resumen General de Participación
    analysis.append("1. GENERAL PARTICIPATION METRICS")
    analysis.append("-" * 50)
    # El número de participantes es la suma de cualquier columna top1/top2/top3
    # porque cada participante contribuye exactamente una vez a cada columna
    total_participants = int(rankings_df['top1'].sum())
    total_combinations = len(rankings_df)
    total_top3_selections = int(rankings_df[['top1', 'top2', 'top3']].sum().sum())
    
    analysis.append(f"Total participants: {total_participants}")
    analysis.append(f"Total combinations evaluated: {total_combinations}")
    analysis.append(f"Total top-3 selections: {total_top3_selections}\n")

    # 3. Análisis de las Mejores Combinaciones
    analysis.append("2. TOP PERFORMING COMBINATIONS")
    analysis.append("-" * 50)
    top_combinations = rankings_df.sort_values('borda', ascending=False).head(3)
    
    for i, (comb, row) in enumerate(top_combinations.iterrows(), 1):
        analysis.append(f"\n{i}. {comb}")
        analysis.append(f"   Borda Score: {row['borda']:.1f} (normalized: {row['borda_norm']:.3f})")
        analysis.append(f"   First Place Rankings: {int(row['top1'])} times")
        analysis.append(f"   Second Place Rankings: {int(row['top2'])} times")
        analysis.append(f"   Third Place Rankings: {int(row['top3'])} times")
        analysis.append(f"   Total Top-3 Appearances: {int(row[['top1','top2','top3']].sum())}")
        
        # Calcular net wins en comparaciones pareadas
        if comb in pairwise_wins.index:
            net_wins = pairwise_wins.loc[comb].sum() - pairwise_wins[comb].sum()
            analysis.append(f"   Net Wins in Pairwise Comparisons: {int(net_wins)}")

    # 4. Análisis de las Peores Combinaciones
    analysis.append("\n\n3. LOWEST PERFORMING COMBINATIONS")
    analysis.append("-" * 50)
    bottom_combinations = rankings_df.sort_values('borda', ascending=True).head(3)
    
    for i, (comb, row) in enumerate(bottom_combinations.iterrows(), 1):
        analysis.append(f"\n{i}. {comb}")
        analysis.append(f"   Borda Score: {row['borda']:.1f} (normalized: {row['borda_norm']:.3f})")
        analysis.append(f"   First Place Rankings: {int(row['top1'])} times")
        analysis.append(f"   Second Place Rankings: {int(row['top2'])} times")
        analysis.append(f"   Third Place Rankings: {int(row['top3'])} times")
        analysis.append(f"   Total Top-3 Appearances: {int(row[['top1','top2','top3']].sum())}")
        
        # Calcular net wins en comparaciones pareadas
        if comb in pairwise_wins.index:
            net_wins = pairwise_wins.loc[comb].sum() - pairwise_wins[comb].sum()
            analysis.append(f"   Net Wins in Pairwise Comparisons: {int(net_wins)}")

    # 5. Análisis de Patrones
    analysis.append("\n\n4. PATTERN ANALYSIS")
    analysis.append("-" * 50)
    
    # Analizar patrones en los tipos de modalidad
    for idx, row in rankings_df.iterrows():
        # Clasificar por tipo de audio
        if '1 -' in idx or '1-' in idx:
            modality_scores['audio_expert']['borda'].append(row['borda'])
            modality_scores['audio_expert']['first'].append(row['top1'])
            modality_scores['audio_expert']['combinations'].append(idx)
        elif '2 -' in idx or '2-' in idx:
            modality_scores['audio_minimal']['borda'].append(row['borda'])
            modality_scores['audio_minimal']['first'].append(row['top1'])
            modality_scores['audio_minimal']['combinations'].append(idx)
        elif '3 -' in idx or '3-' in idx:
            modality_scores['audio_llm']['borda'].append(row['borda'])
            modality_scores['audio_llm']['first'].append(row['top1'])
            modality_scores['audio_llm']['combinations'].append(idx)
            
        # Clasificar por tipo de presentación
        if '- 4' in idx or '-4' in idx:
            modality_scores['text_expert']['borda'].append(row['borda'])
            modality_scores['text_expert']['first'].append(row['top1'])
            modality_scores['text_expert']['combinations'].append(idx)
        elif '- 5' in idx or '-5' in idx:
            modality_scores['video']['borda'].append(row['borda'])
            modality_scores['video']['first'].append(row['top1'])
            modality_scores['video']['combinations'].append(idx)
        elif '- 6' in idx or '-6' in idx:
            modality_scores['animation_3d']['borda'].append(row['borda'])
            modality_scores['animation_3d']['first'].append(row['top1'])
            modality_scores['animation_3d']['combinations'].append(idx)

    analysis.append("\nModality Performance Analysis:\n")
    modality_avg_scores = {}
    
    for modality_name, data in modality_scores.items():
        if data['borda']:  # Solo si hay datos para esta modalidad
            avg_borda = sum(data['borda']) / len(data['borda'])
            avg_first = sum(data['first']) / len(data['first'])
            modality_avg_scores[modality_name] = avg_borda
            
            display_name = modality_name.replace('_', ' ').title()
            analysis.append(f"{display_name}:")
            analysis.append(f"   Average Borda Score: {avg_borda:.2f}")
            analysis.append(f"   Average First Place Rankings: {avg_first:.2f}")
            analysis.append(f"   Number of combinations: {len(data['combinations'])}")
            analysis.append(f"   Combinations: {', '.join(data['combinations'])}\n")

    # 6. Estadísticas Descriptivas
    analysis.append("\n5. DESCRIPTIVE STATISTICS")
    analysis.append("-" * 50)
    stats_summary = ratings_stats.round(2)
    analysis.append("\nRatings Statistics:")
    analysis.append(str(stats_summary))

    # 7. Conclusiones y Recomendaciones
    analysis.append("\n\n6. CONCLUSIONS AND RECOMMENDATIONS")
    analysis.append("-" * 50)
    
    # Identificar tendencias principales basadas en los promedios calculados
    if modality_avg_scores:
        best_modality = max(modality_avg_scores.items(), key=lambda x: x[1])
        worst_modality = min(modality_avg_scores.items(), key=lambda x: x[1])
        
        analysis.append("\nKey Findings:")
        analysis.append(f"1. Most Effective Modality: {best_modality[0].replace('_', ' ').title()} (Average Borda: {best_modality[1]:.2f})")
        analysis.append(f"2. Least Effective Modality: {worst_modality[0].replace('_', ' ').title()} (Average Borda: {worst_modality[1]:.2f})")
    
    # Calcular la brecha de preferencia (solo considerando las estrategias que aparecen en el top-3)
    top_3_strategies = top_combinations.index.tolist()
    bottom_3_strategies = bottom_combinations.index.tolist()
    
    # Solo usar estrategias que realmente fueron seleccionadas (top1 + top2 + top3 > 0)
    valid_strategies = rankings_df[rankings_df[['top1', 'top2', 'top3']].sum(axis=1) > 0]
    
    if len(valid_strategies) > 0:
        preference_gap = valid_strategies['borda_norm'].max() - valid_strategies['borda_norm'].min()
        analysis.append(f"\n3. Preference Gap: {preference_gap:.3f}")
        
        consensus_level = "strong" if preference_gap > 0.20 else "moderate" if preference_gap > 0.10 else "weak"
        analysis.append(f"4. User Consensus Level: {consensus_level.title()}")
    
    # Análisis de submodalidades - SOLO de las combinaciones que realmente salieron en el top-3
    analysis.append("\n\nDetailed Modal Analysis (for Top-3 Performing Combinations):\n")
    
    # Análisis de tipos de audio - solo con estrategias válidas
    audio_scores = {}
    for audio_type_name, audio_key in [('Expert Audio', 'audio_expert'), 
                                        ('Minimal Audio', 'audio_minimal'), 
                                        ('LLM Audio', 'audio_llm')]:
        scores = [row['borda'] for comb, row in rankings_df.iterrows() 
                 if comb in valid_strategies.index and modality_scores[audio_key]['combinations'] 
                 and comb in modality_scores[audio_key]['combinations']]
        if scores:
            audio_scores[audio_type_name] = sum(scores) / len(scores)
            analysis.append(f"- {audio_type_name}: Avg Borda = {audio_scores[audio_type_name]:.2f}")
    
    if audio_scores:
        best_audio = max(audio_scores.items(), key=lambda x: x[1])
        analysis.append(f"\n  → BEST AUDIO TYPE: {best_audio[0]} ({best_audio[1]:.2f})")
    
    # Análisis de tipos de presentación visual - solo con estrategias válidas
    visual_scores = {}
    for visual_type_name, visual_key in [('Text Expert', 'text_expert'), 
                                         ('Video', 'video'), 
                                         ('Animation 3D', 'animation_3d')]:
        scores = [row['borda'] for comb, row in rankings_df.iterrows() 
                 if comb in valid_strategies.index and modality_scores[visual_key]['combinations']
                 and comb in modality_scores[visual_key]['combinations']]
        if scores:
            visual_scores[visual_type_name] = sum(scores) / len(scores)
            analysis.append(f"- {visual_type_name}: Avg Borda = {visual_scores[visual_type_name]:.2f}")
    
    if visual_scores:
        best_visual = max(visual_scores.items(), key=lambda x: x[1])
        analysis.append(f"\n  → BEST VISUAL TYPE: {best_visual[0]} ({best_visual[1]:.2f})")
    
    # Recomendación final basada en top-3
    analysis.append("\n\n7. FINAL RECOMMENDATION")
    analysis.append("-" * 50)
    analysis.append("\nBased on Borda scores and user preferences, the top 3 recommended combinations are:")
    for i, comb in enumerate(top_3_strategies, 1):
        analysis.append(f"\n{i}. {comb}")
        analysis.append(f"   - Borda Score: {rankings_df.loc[comb, 'borda']:.1f}")
        analysis.append(f"   - Times selected as 1st choice: {int(rankings_df.loc[comb, 'top1'])}")

    # 8. COMBINED RANKING - Mejores estrategias basadas en calificaciones Y selecciones
    analysis.append("\n\n8. COMBINED RANKING: BEST STRATEGIES FOR IMPLEMENTATION")
    analysis.append("=" * 50)
    analysis.append("\nThis ranking combines both quantitative metrics:")
    analysis.append("- Average Ratings (how clear/effective was the strategy)")
    analysis.append("- Borda Score (user preferences and selections)\n")
    
    # Crear un ranking combinado iterando sobre rankings_df (que tiene los nombres correctos)
    combined_ranking = []
    for combo_name in rankings_df.index:
        # Buscar la columna correspondiente en ratings_stats
        # El nombre en ratings_stats es "Combinación X-Y" 
        # El nombre en rankings_df es "Combination X - Y (audio ... + ...)"
        rating_col = None
        for col in ratings_stats.columns:
            # Extraer el patrón "X-Y" de ambos
            pattern1 = col.replace('Combinación ', '').strip()  # "1-5"
            # Buscar en el índice de rankings_df
            if pattern1 in combo_name:
                rating_col = col
                break
        
        avg_rating = ratings_stats[rating_col]['mean'] if rating_col else 0
        borda_score = rankings_df.loc[combo_name, 'borda']
        top1_count = rankings_df.loc[combo_name, 'top1']
        
        # Calcular puntuación combinada (normalizada)
        rating_score = avg_rating / 7.0 if avg_rating > 0 else 0
        borda_norm = borda_score / rankings_df['borda'].sum() if rankings_df['borda'].sum() > 0 else 0
        
        # Promedio ponderado: 50% calificación, 50% preferencia (Borda)
        combined_score = (rating_score * 0.5) + (borda_norm * 0.5)
        
        combined_ranking.append({
            'combo_name': combo_name,
            'avg_rating': avg_rating,
            'borda_score': borda_score,
            'top1_count': top1_count,
            'combined_score': combined_score
        })
    
    # Ordenar por puntuación combinada
    combined_ranking = sorted(combined_ranking, key=lambda x: x['combined_score'], reverse=True)
    
    analysis.append("TOP 3 STRATEGIES FOR IMPLEMENTATION:\n")
    for i, item in enumerate(combined_ranking[:3], 1):
        analysis.append(f"{i}. {item['combo_name']}")
        analysis.append(f"   Combined Score: {item['combined_score']:.3f}")
        analysis.append(f"   - Average Rating (1-7): {item['avg_rating']:.2f}")
        analysis.append(f"   - Borda Score: {item['borda_score']:.0f}")
        analysis.append(f"   - Times as 1st Choice: {int(item['top1_count'])}")
        analysis.append("")
    
    analysis.append("\nRATIONALE FOR THESE RECOMMENDATIONS:")
    analysis.append("-" * 50)
    if combined_ranking:
        best = combined_ranking[0]
        analysis.append(f"\n✓ Primary Strategy: {best['combo_name']}")
        analysis.append(f"  This strategy excels in both metrics:")
        analysis.append(f"  - Users rated it {best['avg_rating']:.2f}/7.0 (clarity and effectiveness)")
        analysis.append(f"  - Users selected it {int(best['top1_count'])} times as their preferred choice")
        analysis.append(f"  - Overall preference score: {best['combined_score']:.3f}/1.0")
    
    if len(combined_ranking) > 1:
        second = combined_ranking[1]
        analysis.append(f"\n✓ Secondary Strategy: {second['combo_name']}")
        analysis.append(f"  - Users rated it {second['avg_rating']:.2f}/7.0")
        analysis.append(f"  - Users selected it {int(second['top1_count'])} times as their preferred choice")
        analysis.append(f"  - This serves as a strong backup option")
    
    if len(combined_ranking) > 2:
        third = combined_ranking[2]
        analysis.append(f"\n✓ Tertiary Strategy: {third['combo_name']}")
        analysis.append(f"  - Users rated it {third['avg_rating']:.2f}/7.0")
        analysis.append(f"  - Users selected it {int(third['top1_count'])} times as their preferred choice")
        analysis.append(f"  - This provides additional flexibility and variety")
    
    analysis.append("\nIMPLEMENTATION PRIORITY:")
    analysis.append("-" * 50)
    for i, item in enumerate(combined_ranking[:3], 1):
        if i == 1:
            priority = "HIGHEST - Implement immediately as primary strategy"
        elif i == 2:
            priority = "HIGH - Implement as secondary/backup strategy"
        else:
            priority = "MEDIUM - Consider for variety and flexibility"
        analysis.append(f"\n{i}. {item['combo_name']}")
        analysis.append(f"   Priority: {priority}")

    return "\n".join(analysis)

def plot_ratings_analysis(df, processed_ratings, outdir):
    # Distribution boxplot
    plt.figure(figsize=(12, 6))
    melted_data = processed_ratings.melt()
    # Convert Spanish column names to English
    melted_data['variable'] = melted_data['variable'].replace({f'Combinación {i}': f'Combination {i}' for i in ['1-4', '1-5', '1-6', '2-4', '2-5', '2-6', '3-4', '3-5', '3-6']})
    sns.boxplot(data=melted_data, x='variable', y='value')
    plt.xticks(rotation=45, ha='right')
    plt.title('Distribution of Ratings by Combination', pad=20, fontsize=12)
    plt.xlabel('Combination Type', fontsize=10)
    plt.ylabel('Rating Value (1-7)', fontsize=10)
    plt.tight_layout()
    path = os.path.join(outdir, 'ratings_distribution.png')
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()

    # Total ratings bar plot
    plt.figure(figsize=(12, 6))
    totals = calculate_total_ratings(df)
    
    # Create a mapping of Spanish to English names
    name_mapping = {
        f"Combinación {i}": f"Combination {i}" for i in ['1-4', '1-5', '1-6', '2-4', '2-5', '2-6', '3-4', '3-5', '3-6']
    }
    
    # Convert index to English
    totals.index = [name_mapping.get(name, name) for name in totals.index]
    
    sns.barplot(x=totals.index, y=totals.values)
    plt.xticks(rotation=45, ha='right')
    plt.title('Total Ratings by Combination Type', pad=20, fontsize=12)
    plt.xlabel('Combination Type', fontsize=10)
    plt.ylabel('Total Rating Score', fontsize=10)
    plt.tight_layout()
    path_sums = os.path.join(outdir, 'ratings_total_sums.png')
    plt.savefig(path_sums, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Print totals
    print("\nTotal ratings by combination:")
    print(totals.to_string())
    
    return path

# --------------------------
# MAIN
# --------------------------
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'Multi-Modal Selection.csv')
    outdir = os.path.join(script_dir, 'results')
    os.makedirs(outdir, exist_ok=True)

    # Cargar y procesar datos
    print("Cargando datos...")
    df = pd.read_csv(csv_path)
    
    # Procesar calificaciones según secuencias
    print("Procesando calificaciones...")
    processed_ratings = process_ratings(df)
    
    # Calcular estadísticas por combinación
    print("Calculando estadísticas...")
    ratings_stats = processed_ratings.agg(['mean', 'std', 'count']).round(2)
    
    # Visualizar distribución de calificaciones
    print("Generando gráficas de calificaciones...")
    plot_ratings_analysis(df, processed_ratings, outdir)
    
    # Procesar rankings top-3
    print("Procesando rankings top-3...")
    rank_cols = detect_rank_columns(df)
    if not rank_cols:
        print("No se detectaron columnas top-3.")
        return
        
    parsed_lists, col_to_label = parse_top3_lists(df, rank_cols)
    strategies = sorted(set(col_to_label.values()))
    print("\nEstrategias detectadas:", strategies)

    # Calcular métricas y generar visualizaciones
    print("\nGenerando análisis y visualizaciones...")
    df_counts = compute_counts_and_borda(parsed_lists, strategies)
    df_counts.to_csv(os.path.join(outdir, 'counts_borda.csv'))
    
    wins = pairwise_matrix(parsed_lists, strategies)
    wins.to_csv(os.path.join(outdir, 'pairwise_wins.csv'))

    plot_borda(df_counts, outdir)
    plot_stacked_top_positions(df_counts, outdir)
    plot_pairwise(wins, outdir)

    print("\nResultados guardados en:", outdir)
    print("\nResumen de calificaciones:")
    print(ratings_stats)
    print("\nResumen de rankings:")
    print(df_counts)
    
    # Generar análisis completo
    totals = calculate_total_ratings(df)
    analysis = analyze_combinations(ratings_stats, df_counts, totals, wins)
    
    # Guardar el análisis en un archivo
    analysis_file = os.path.join(outdir, 'comprehensive_analysis.txt')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        f.write(analysis)
    print(f"Análisis completo guardado en: {analysis_file}")

if __name__ == '__main__':
    main()

