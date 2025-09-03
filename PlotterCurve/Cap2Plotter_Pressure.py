import matplotlib.pyplot as plt
import numpy as np
import os

# Dati simul
pressure_bar = np.array([1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 3.25, 3.5, 3.75, 4, 4.25, 4.5, 4.75, 5])
altitude_m = np.array([3.22, 5.36, 7.53, 9.75, 11.95, 14.21, 16.49, 18.77, 21.03, 23.36, 25.68, 27.89, 30.2, 32.47, 34.8, 37.13, 40.62])
velocity_ms = np.array([6.41, 9.10, 11.22, 13.07, 14.70, 16.21, 17.62, 18.96, 20.24, 21.45, 22.63, 23.75, 24.86, 25.92, 26.97, 28.01, 29.50])

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

# Crea figura
fig, ax1 = plt.subplots(figsize=(10, 6), linewidth=4, edgecolor=color_alt)
fig.patch.set_facecolor('white')
ax1.set_facecolor('white')

# Primo asse: altitudine
ax1.plot(pressure_bar, altitude_m, color=color_alt, marker='o', label="Altitudine [m]", linewidth=2.5)
idx_max = np.argmax(altitude_m)
#ax1.scatter([pressure_bar[idx_max]], [altitude_m[idx_max]], color=color_max, s=80,
#            edgecolor='white', zorder=5, label=f"Massimo: {altitude_m[idx_max]:.2f} m")

# Secondo asse: velocità
ax2 = ax1.twinx()
ax2.plot(pressure_bar, velocity_ms, color=color_vel, marker='o', label="Velocità [m/s]", linewidth=2.5)

# Uniforma i limiti degli assi Y
ymin = 0
ymax = max(np.max(altitude_m), np.max(velocity_ms)) * 1.1  # margine del 10%
ax1.set_ylim(ymin, ymax)
ax2.set_ylim(ymin, ymax)

# Etichette e assi
ax1.set_xlabel("Pressione [bar]")
ax1.set_ylabel("Altitudine [m]", color=color_alt)
ax1.tick_params(axis='y', labelcolor=color_alt)
ax1.grid(which='both', linestyle='--', alpha=0.4)
ax1.minorticks_on()

ax2.set_ylabel("Velocità [m/s]", color=color_vel)
ax2.tick_params(axis='y', labelcolor=color_vel)

# Titolo e legenda
plt.title("Altitudine Massima e Velocità massima in funzione della Pressione")
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

# Mostra grafico
plt.tight_layout()
plt.show()

# Funzione per salvataggio
def save_figure():
    output_path = os.path.join("C:\\Users\\fanin\\Desktop\\Dati WR\\Plots", "Pressure_vs_Altitude_Velocity.png")
    fig.savefig(output_path, dpi=300, edgecolor=fig.get_edgecolor())
    print(f"✅ Grafico salvato in: {output_path}")

# Chiede all'utente se salvare
salva = input("Vuoi salvare il grafico? (s/n): ").strip().lower()
if salva == 's':
    save_figure()
else:
    print("❌ Salvataggio annullato.")
