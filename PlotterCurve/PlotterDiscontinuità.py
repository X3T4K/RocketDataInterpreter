import os

import pandas as pd
import matplotlib.pyplot as plt

# Leggi i dati
df = pd.read_csv('simulation.csv')

# Converti in numerici (alcuni valori potrebbero essere stringhe)
df = df.apply(pd.to_numeric, errors='coerce')

# Trova il punto con la variazione più significativa nell'accelerazione
df['Acceleration_diff'] = df['Acceleration'].diff().abs()
max_diff_idx = df['Acceleration_diff'].idxmax()
max_diff_time = df.loc[max_diff_idx, 'Time']
max_diff_value = df.loc[max_diff_idx, 'Acceleration_diff']

print(f"Salto più significativo nell'accelerazione:")
print(f"Tempo: {max_diff_time:.6f} s")
print(f"Variazione: {max_diff_value:.6f} m/s²")
print(f"Accelerazione prima: {df.loc[max_diff_idx-1, 'Acceleration']:.6f} m/s²")
print(f"Accelerazione dopo: {df.loc[max_diff_idx, 'Acceleration']:.6f} m/s²")

# Stile LaTeX e grafica
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.size": 13,
    "axes.labelsize": 14,
    "axes.titlesize": 16,
    "legend.fontsize": 12,
    "lines.linewidth": 2
})

# Colori
color_alt = '#0C4767'  # blu
color_vel = '#FE9920'  # arancione
color_max = 'black'

# Crea la figura con subplot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), linewidth=4, edgecolor=color_alt)

# Primo subplot: Accelerazione
ax1.plot(df['Time'], df['Acceleration'], color='#2E8B57', label='Accelerazione')
ax1.plot(max_diff_time, df.loc[max_diff_idx, 'Acceleration'], 'ro', markersize=8)

ax1.set_ylabel('Accelerazione (m/s²)')
ax1.set_title('Analisi del salto nell\'accelerazione')
ax1.grid(True, alpha=0.3)
ax1.legend()
ax1.set_xlim(0, 0.3)  # Zoom sull'area di interesse

# Secondo subplot: Confronto con velocità e quota
ax2.plot(df['Time'], df['Velocity'], color=color_vel, label='Velocità')
ax2.plot(df['Time'], df['Altitude'], color=color_alt, label='Quota')

ax2.set_xlabel('Tempo (s)')
ax2.set_ylabel('Velocità (m/s) / Quota (m)')
ax2.grid(True, alpha=0.3)
ax2.legend()
ax2.set_xlim(0, 0.3)  # Zoom sull'area di interesse

plt.tight_layout()
salva = input("Vuoi salvare il grafico? (s/n): ").strip().lower()
if salva == 's':
    output_path = os.path.join("C:\\Users\\fanin\\Desktop\\Dati WR\\Plots", "salto_accelerazione.png")
    plt.savefig(output_path, dpi=300, edgecolor=fig.get_edgecolor())
    print(f"✅ Grafico salvato in: {output_path}")
else:
    print("❌ Salvataggio annullato.")


plt.show()

# Dettagli aggiuntivi sul punto critico
print(f"\nDettagli del punto critico (t = {max_diff_time:.6f} s):")
print(f"Accelerazione: {df.loc[max_diff_idx, 'Acceleration']:.6f} m/s²")
print(f"Velocità: {df.loc[max_diff_idx, 'Velocity']:.6f} m/s")
print(f"Quota: {df.loc[max_diff_idx, 'Altitude']:.6f} m")
print(f"Spinta: {df.loc[max_diff_idx, 'Thrust']:.6f} N")