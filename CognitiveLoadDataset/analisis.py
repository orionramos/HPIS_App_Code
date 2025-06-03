import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, f_oneway

# Cargar el dataset
df = pd.read_csv("C:\HPIS_App_Code\CognitiveLoadDataset\dataset_unificado.csv")

# Paso 1: Calcular HR en reposo
hr_reposo = df[df['carga_cognitiva'] == 0]['HR'].mean()
print(f"✅ HR en reposo estimada: {hr_reposo:.2f} bpm")

# Paso 2: Crear nueva columna delta_HR
df['delta_HR'] = df['HR'] - hr_reposo

# Paso 3: Estadísticas por carga cognitiva
resumen = df.groupby('carga_cognitiva').agg(
    HR_media=('HR', 'mean'),
    HR_min=('HR', 'min'),
    HR_max=('HR', 'max'),
    HR_std=('HR', 'std'),
    HR_median=('HR', 'median'),
    delta_HR_promedio=('delta_HR', 'mean')
).reset_index()

# Mostrar tabla resumen
print("\n📊 Estadísticas por carga cognitiva:")
print(resumen)

# Paso 4: Correlación HR vs carga cognitiva
corr_hr, p_corr = pearsonr(df['HR'], df['carga_cognitiva'])
print(f"\n📈 Correlación HR vs Carga Cognitiva: r = {corr_hr:.3f}, p = {p_corr:.4f}")

# Paso 5: ANOVA de una vía para HR según carga cognitiva
# Agrupar por carga cognitiva
grupos_hr = [grupo['HR'].values for _, grupo in df.groupby('carga_cognitiva')]
anova_stat, p_anova = f_oneway(*grupos_hr)
print(f"\n🔬 ANOVA HR ~ carga_cognitiva: F = {anova_stat:.2f}, p = {p_anova:.4f}")

# Paso 6: Guardar resumen en CSV
resumen.to_csv("resumen_cognitivo.csv", index=False)
print("\n💾 Archivo 'resumen_cognitivo.csv' guardado.")

# Paso 7: Graficar tendencias
plt.figure(figsize=(10, 6))
plt.plot(resumen['carga_cognitiva'], resumen['HR_media'], marker='o', label='HR Media')
plt.plot(resumen['carga_cognitiva'], resumen['delta_HR_promedio'], marker='x', label='ΔHR Promedio')
plt.title("Tendencia de HR según la carga cognitiva")
plt.xlabel("Carga Cognitiva")
plt.ylabel("Frecuencia Cardíaca (bpm)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
