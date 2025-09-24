import matplotlib.pyplot as plt
import numpy as np
import os

# Dati da immagine 2 bar
percentuale = np.array([15.0, 17.5, 20.0, 22.5, 25.0, 27.5, 30.0, 32.5, 35.0,
                        37.5, 40.0, 42.5, 45.0, 47.5, 50.0, 52.5, 55.0, 57.5, 60.0])

altitudine = np.array([7.21, 8.84, 9.83, 10.64, 11.34, 11.87, 12.24, 12.46, 12.56,
                       12.7, 12.6, 12.46, 12.04, 11.43, 10.66, 9.67, 8.46, 6.96, 5.2])

velocita = np.array([12.02, 12.89, 13.6, 14.15, 14.61, 14.91, 15.13, 15.22, 15.23,
                     15.28, 15.2, 14.98, 14.61, 14.08, 13.39, 12.47, 11.23, 9.33, 7.67])

# Parametri grafici
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.size": 13,
    "axes.labelsize": 14,
    "axes.titlesize": 16,
    "legend.fontsize": 12,
    "lines.linewidth": 2
})
color_alt = '#0C4767'
color_vel = '#FE9920'

fig, ax1 = plt.subplots(figsize=(10,6), linewidth=4, edgecolor=color_alt)
fig.patch.set_facecolor('white')
ax1.set_facecolor('white')

# Altitudine
ax1.plot(percentuale, altitudine, color=color_alt, marker='o', label="Altitudine [m]")
idx_max = np.argmax(altitudine)
ax1.scatter([percentuale[idx_max]], [altitudine[idx_max]], color='#77966D', s=80,
            edgecolor='white', zorder=5, label=f"Altitudine max: {altitudine[idx_max]:.2f} m")

# Velocità
ax2 = ax1.twinx()
ax2.plot(percentuale, velocita, color=color_vel, marker='s', label="Velocità [m/s]")
idx2_max = np.argmax(velocita)
ax2.scatter([percentuale[idx2_max]], [velocita[idx2_max]], color='#CC444B', s=80,
            edgecolor='white', zorder=5, label=f"Velocità Max: {velocita[idx2_max]:.2f} m/s")

# Scale Y uniformi centrate
ymin = min(np.min(altitudine), np.min(velocita)) - 0.5
ymax = (max(np.max(altitudine), np.max(velocita)) + 0.5)*1.05
ax1.set_ylim(ymin, ymax)
ax2.set_ylim(ymin, ymax)

# Asse X leggibile
ax1.set_xlim(10, 65)
ax1.set_xticks(np.arange(10, 70, 5))
ax1.set_xlabel(r"Percentuale di acqua (\%)")

# Linee guida verticali
for xref in [30, 40, 50]:
    ax1.axvline(xref, color='gray', linestyle='--', alpha=0.3)

# Etichette Y
ax1.set_ylabel("Altitudine [m]", color=color_alt)
ax1.tick_params(axis='y', labelcolor=color_alt)
ax1.grid(which='both', linestyle='--', alpha=0.4)
ax1.minorticks_on()
ax2.set_ylabel("Velocità [m/s]", color=color_vel)
ax2.tick_params(axis='y', labelcolor=color_vel)

# Titolo e legenda
plt.title("Altitudine e Velocità in funzione della Percentuale (2 bar)")
l1, lab1 = ax1.get_legend_handles_labels()
l2, lab2 = ax2.get_legend_handles_labels()
ax1.legend(l1 + l2, lab1 + lab2, loc='upper right')

plt.tight_layout()
plt.show()

# Salvataggio
def save_figure():
    path = os.path.join("C:\\Users\\fanin\\Desktop\\Dati WR\\Plots", "WaterRatio_2bar_LEGIBILE.png")
    fig.savefig(path, dpi=300, edgecolor=fig.get_edgecolor())
    print(f"Grafico salvato in: {path}")

if input("Vuoi salvare il grafico (2 bar leggibile)? (s/n): ").strip().lower() == 's':
    save_figure()
