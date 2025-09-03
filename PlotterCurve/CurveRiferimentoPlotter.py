import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# Caricamento dati simulazione (dopo skip seconda riga)
df = pd.read_csv("simulation.csv", skiprows=[1])
df["Time"] = df["Time"].astype(float)
df["Altitude"] = df["Altitude"].astype(float)
df["Velocity"] = df["Velocity"].astype(float)

# Estrazione dati
t = df["Time"].values
alt = df["Altitude"].values
vel = df["Velocity"].values

# Parametri grafici stile Ratio2Bar
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.size": 13,
    "axes.labelsize": 14,
    "axes.titlesize": 16,
    "legend.fontsize": 12,
    "lines.linewidth": 2
})

# Colori personalizzati
color_alt = '#0C4767'
color_vel = '#FE9920'
color_max_alt = '#77966D'
color_max_vel = '#CC444B'

# Figure con due sottografici
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# --- ALTITUDINE ---
ax1.plot(t, alt, color=color_alt, label="Altitudine [m]")
idx_max_alt = np.argmax(alt)
ax1.scatter(t[idx_max_alt], alt[idx_max_alt], color=color_max_alt, s=80,
            edgecolor='white', label=f"Apogeo: {alt[idx_max_alt]:.2f} m")
ax1.set_ylabel("Altitudine [m]")
ax1.grid(which='both', linestyle='--', alpha=0.4)
ax1.minorticks_on()
ax1.set_xlabel("Tempo [s]")
ax1.legend(loc='best')

# --- VELOCITÀ ---
ax2.plot(t, vel, color=color_vel, label="Velocità [m/s]")
idx_max_vel = np.argmax(vel)
ax2.scatter(t[idx_max_vel], vel[idx_max_vel], color=color_max_vel, s=80,
            edgecolor='white', label=f"Velocità Max: {vel[idx_max_vel]:.2f} m/s")
ax2.set_xlabel("Tempo [s]")
ax2.set_ylabel("Velocità [m/s]")
ax2.grid(which='both', linestyle='--', alpha=0.4)
ax2.minorticks_on()
ax2.legend(loc='best')

# Titolo generale
fig.suptitle("Curva di riferimento simulata")

# Layout e show
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()

# Salvataggio opzionale
def save_figure():
    path = os.path.join("C:\\Users\\fanin\\Desktop\\Dati WR\\Plots", "CurvaRiferimento.png")
    fig.savefig(path, dpi=300, edgecolor=fig.get_edgecolor())
    print(f"Grafico salvato in: {path}")

if input("Vuoi salvare il grafico della curva di riferimento? (s/n): ").strip().lower() == 's':
    save_figure()
