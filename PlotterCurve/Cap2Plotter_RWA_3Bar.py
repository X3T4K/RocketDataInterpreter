import matplotlib.pyplot as plt
import numpy as np
import os

# Dati da immagine 3 bar
percentuale = np.array([20.0, 22.5, 25.0, 27.5, 30.0, 32.5, 35.0, 37.5, 40.0,
                        42.5, 45.0, 47.5, 50.0, 52.5, 55.0, 57.5, 60.0])
altitudine = np.array([
    16.44, 17.78, 18.95, 19.86, 20.51, 21.07, 21.32, 21.70, 21.80,
    21.66, 21.29, 20.67, 19.81, 18.77, 17.49, 15.97, 14.21
])
velocita = np.array([
    17.93, 18.69, 19.31, 19.79, 20.13, 20.36, 20.48, 20.62, 20.63,
    20.50, 20.25, 19.85, 19.32, 18.64, 17.80, 16.75, 15.44
])


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
            edgecolor='white', zorder=5, label=f"Apogeo: {altitudine[idx_max]:.2f} m")

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
plt.title("Altitudine e Velocità in funzione della Percentuale (3 bar)")
l1, lab1 = ax1.get_legend_handles_labels()
l2, lab2 = ax2.get_legend_handles_labels()
ax1.legend(l1 + l2, lab1 + lab2, loc='best')

plt.tight_layout()
plt.show()

# Salvataggio
def save_figure():
    path = os.path.join("C:\\Users\\fanin\\Desktop\\Dati accelerometro\\Plots", "WaterRatio_3bar_LEGIBILE.png")
    fig.savefig(path, dpi=300, edgecolor=fig.get_edgecolor())
    print(f"Grafico salvato in: {path}")

if input("Vuoi salvare il grafico (3 bar leggibile)? (s/n): ").strip().lower() == 's':
    save_figure()
