import matplotlib.pyplot as plt
import numpy as np
import os

# Dati da immagine (densità, altitude, velocity)
densità = np.array([0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95,
                    1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5, 1.7, 1.9, 2.1, 2.3, 2.5]) * 1000
altitudine =   np.array([18.01, 18.57, 19.04, 19.44, 19.79, 20.07, 20.33, 20.56, 20.74, 20.90,
                         21.04, 21.13, 21.20, 21.29, 21.35, 21.39, 21.42, 21.43, 21.45, 21.46,
                         21.44, 21.35, 21.20, 20.99, 20.73, 20.45])
velocita =     np.array([18.71, 19.01, 19.26, 19.46, 19.64, 19.78, 19.91, 20.02, 20.10, 20.18,
                         20.24, 20.28, 20.32, 20.35, 20.37, 20.38, 20.39, 20.39, 20.39, 20.38,
                         20.37, 20.29, 20.18, 20.05, 19.89, 19.72])

# Etichette speciali con densità corrispondenti
speciali = {
    "Benzina": 650,
    "Acqua": 1000,
    "Glicerina": 1250,
    "Soluzioni di Sali pesanti" : 1900
}

# Stile LaTeX e grafica coerente
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

# Setup figura
fig, ax1 = plt.subplots(figsize=(10,6), linewidth=4, edgecolor=color_alt)
fig.patch.set_facecolor('white')
ax1.set_facecolor('white')

# Primo asse: altitudine
ax1.plot(densità, altitudine, color=color_alt, marker='o', label="Altitudine [m]")
idx_max = np.argmax(altitudine)
ax1.scatter([densità[idx_max]], [altitudine[idx_max]], color='#77966D', s=80,
            edgecolor='white', zorder=5, label=f"Apogeo: {altitudine[idx_max]:.2f} m")

# Secondo asse: velocità
ax2 = ax1.twinx()
ax2.plot(densità, velocita, color=color_vel, marker='s', label="Velocità [m/s]")
idx2_max = np.argmax(velocita)
ax2.scatter([densità[idx2_max]], [velocita[idx2_max]], color='#CC444B', s=80,
            edgecolor='white', zorder=5, label=f"Velocità Max: {velocita[idx_max]:.2f} m/s")


# Scale Y uniformi, ma centrate sul range effettivo
ymin = min(np.min(altitudine), np.min(velocita)) -0.5
ymax = max(np.max(altitudine), np.max(velocita)) +0.5
ax1.set_ylim(ymin, ymax)
ax2.set_ylim(ymin, ymax)

# Etichette
ax1.set_xlabel("Densità [kg/m$^3$]")
ax1.set_ylabel("Altitudine [m]", color=color_alt)
ax1.tick_params(axis='y', labelcolor=color_alt)
ax1.grid(which='both', linestyle='--', alpha=0.4)
ax1.minorticks_on()

ax2.set_ylabel("Velocità [m/s]", color=color_vel)
ax2.tick_params(axis='y', labelcolor=color_vel)

# Annota i punti speciali
for label, dens in speciali.items():
    # trova indice più vicino a densità specificata
    idx = np.abs(densità - dens).argmin()
    ax1.scatter(dens, altitudine[idx], color='red', marker='^', s=100, zorder=6)
    ax1.text(dens, altitudine[idx] + 0.2, label, color='red', ha='center', va='bottom')

# Titolo e legenda
plt.title("Altitudine e Velocità in funzione della Densità")


l1, lab1 = ax1.get_legend_handles_labels()
l2, lab2 = ax2.get_legend_handles_labels()
ax1.legend(l1 + l2, lab1 + lab2, loc='best')


# Mostra
plt.tight_layout()
plt.show()

# Salvataggio condizionale via input
def save_figure():
    path = os.path.join("C:\\Users\\fanin\\Desktop\\Dati accelerometro\\Plots", "Density_vs_Altitude_Velocity.png")
    fig.savefig(path, dpi=300, edgecolor=fig.get_edgecolor())
    print(f"Grafico salvato in: {path}")

# Chiede all'utente se salvare
if input("Vuoi salvare il grafico? (s/n): ").strip().lower() == 's':
    save_figure()
