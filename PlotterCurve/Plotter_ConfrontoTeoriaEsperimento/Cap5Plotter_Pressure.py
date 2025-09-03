import os

import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from matplotlib.lines import Line2D

# Dati simul
pressure_bar = np.array([1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 3.25, 3.5, 3.75, 4, 4.25, 4.5, 4.75, 5])
altitude_m = np.array([3.22, 5.36, 7.53, 9.75, 11.95, 14.21, 16.49, 18.77, 21.03, 23.36, 25.68, 27.89, 30.2, 32.47, 34.8, 37.13, 40.62])
velocity_ms = np.array([6.41, 9.10, 11.22, 13.07, 14.70, 16.21, 17.62, 18.96, 20.24, 21.45, 22.63, 23.75, 24.86, 25.92, 26.97, 28.01, 29.50])

# ----------------------
# Dati sperimentali (pressioni)
# ----------------------
press_exp = np.array([1.50, 2.00, 2.00, 2.50, 3.00, 3.00, 3.50])
hmax_expP = np.array([8.37, 14.28, 14.23, 13.88, 22.26, 22.38, 27])
vplus_expP = np.array([10.56, 14.89, 13.94, 13.86, 21.45, 22.01, 29.31])

# ----------------------
# Parametri grafici
# ----------------------
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
series_colors = ['#59A14F', '#4E79A7', '#9C755F']  # verde, blu, marrone tenue
series_labels = ['Serie 1', 'Serie 2', 'Serie 3']

yerr_alt_val = 1       # ±0.25 m
yerr_vel_val = 3       # ±3 m/s
xerr_abs_val = 0.1      # ±0.1 bar

# ----------------------
# Funzione utility
# ----------------------
def make_series(x_raw, y_raw, i_rep):
    grp = defaultdict(list)
    for x, y in zip(x_raw, y_raw):
        grp[float(x)].append(float(y))
    xs, ys = [], []
    for x in sorted(grp.keys()):
        if len(grp[x]) > i_rep:
            xs.append(x)
            ys.append(grp[x][i_rep])
    return np.array(xs), np.array(ys)

# ----------------------
# Limiti Y uniformi
# ----------------------
yminP = (min(np.min(hmax_expP), np.min(vplus_expP)) - 0.5) * 0.8
ymaxP = (max(np.max(hmax_expP), np.max(vplus_expP)) + 0.5) * 1.2

# ----------------------
# Plot
# ----------------------
fig, (ax_altP, ax_velP) = plt.subplots(2, 1, figsize=(11, 7.8), sharex=True, linewidth=4, edgecolor=color_alt)
fig.patch.set_facecolor('white')
ax_altP.set_facecolor('white')
ax_velP.set_facecolor('white')
fig.subplots_adjust(right=0.78)

errkw = dict(ecolor='black', elinewidth=1.4, capsize=5, capthick=1.4, zorder=6)

# --- Altitudine ---
ax_altP.plot(pressure_bar, altitude_m, color=color_alt, marker='o', zorder=3, label="Simulazione")
idx_max = np.argmax(altitude_m)
ax_altP.scatter(pressure_bar[idx_max], altitude_m[idx_max],
                color='#77966D', s=80, edgecolor='white', zorder=5)



for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(press_exp, hmax_expP, i_rep)
    if len(xs) == 0: continue
    ax_altP.errorbar(xs, ys, yerr=yerr_alt_val, xerr=xerr_abs_val,
                     fmt='o', mfc=c, mec='black', mew=1.0, markersize=6,
                     **errkw, alpha=0.95)
    ord_idx = np.argsort(xs)
    ax_altP.fill_between(xs[ord_idx], (ys - yerr_alt_val)[ord_idx], (ys + yerr_alt_val)[ord_idx],
                         alpha=0.18, edgecolor='none', color=c, zorder=2)

# Linee che congiungono i punti di ciascuna serie (Altitudine)
for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(press_exp, hmax_expP, i_rep)
    if len(xs) == 0:
        continue
    ord_idx = np.argsort(xs)
    ax_altP.plot(xs[ord_idx], ys[ord_idx],
                 color=c, linestyle='-', linewidth=1.8,
                 alpha=0.7, zorder=1, label='_nolegend_')



ax_altP.set_ylabel("Altitudine [m]", color=color_alt)
ax_altP.tick_params(axis='y', labelcolor=color_alt)
ax_altP.set_ylim(yminP, ymaxP)
ax_altP.grid(which='both', linestyle='--', alpha=0.35)
ax_altP.minorticks_on()
handles_alt = [Line2D([], [], marker='o', color='none', markerfacecolor=c,
                      markeredgecolor='black', label=lab) for c, lab in zip(series_colors, series_labels)]
ax_altP.legend(handles=handles_alt, loc='center left', bbox_to_anchor=(1.02, 0.5),
               frameon=True, framealpha=0.92, title="Altitudine")

# --- Velocità ---
ax_velP.plot(pressure_bar, velocity_ms, color=color_vel, marker='s', zorder=3, label="Simulazione")
idx2_max = np.argmax(velocity_ms)
ax_velP.scatter(pressure_bar[idx2_max], velocity_ms[idx2_max],
                color='#CC444B', s=80, edgecolor='white', zorder=5)


for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(press_exp, vplus_expP, i_rep)
    if len(xs) == 0: continue
    ax_velP.errorbar(xs, ys, yerr=yerr_vel_val, xerr=xerr_abs_val,
                     fmt='o', mfc=c, mec='black', mew=1.0, markersize=6,
                     **errkw, alpha=0.95)
    ord_idx = np.argsort(xs)
    ax_velP.fill_between(xs[ord_idx], (ys - yerr_vel_val)[ord_idx], (ys + yerr_vel_val)[ord_idx],
                         alpha=0.18, edgecolor='none', color=c, zorder=2)

# Linee che congiungono i punti di ciascuna serie (Velocità)
for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(press_exp, vplus_expP, i_rep)
    if len(xs) == 0:
        continue
    ord_idx = np.argsort(xs)
    ax_velP.plot(xs[ord_idx], ys[ord_idx],
                 color=c, linestyle='-', linewidth=1.8,
                 alpha=0.7, zorder=1, label='_nolegend_')


ax_velP.set_xlabel(r"Pressione [bar]")
ax_velP.set_ylabel("Velocità [m/s]", color=color_vel)
ax_velP.tick_params(axis='y', labelcolor=color_vel)
ax_velP.set_ylim(yminP, ymaxP)
ax_velP.grid(which='both', linestyle='--', alpha=0.35)
ax_velP.minorticks_on()
handles_vel = [Line2D([], [], marker='o', color='none', markerfacecolor=c,
                      markeredgecolor='black', label=lab) for c, lab in zip(series_colors, series_labels)]
ax_velP.legend(handles=handles_vel, loc='center left', bbox_to_anchor=(1.02, 0.5),
               frameon=True, framealpha=0.92, title="Velocità")

# --- Linee guida ---
for ax in [ax_altP, ax_velP]:
    ax.set_xlim(1.4, 3.6)
    ax.set_xticks(np.arange(1.5, 3.6, 0.25))
    for xref in [2.0, 3.0]:
        ax.axvline(xref, color='gray', linestyle='--', alpha=0.3, zorder=1)

# Imposta limiti e tick su X
for ax in [ax_altP, ax_velP]:
    ax.set_xlim(1.3, 3.7)  # limiti X
    ax.set_xticks(np.arange(1.5, 3.6, 0.25))  # intervallo tick


# --- Titolo ---
plt.suptitle("Altitudine e Velocità in funzione della Pressione  — Errori: \n"
    f"Alt: medio 11.09\\%, max 18.08\\% | "
    f"Vel: medio 10.94\\%, max 27.13\\%", fontsize=16)
plt.tight_layout()
plt.show()

# Salvataggio
def save_figure():
    path = os.path.join("C:\\Users\\fanin\\Desktop\\Dati WR\\Plots", "Pressure_vs_Altitude.png")
    fig.savefig(path, dpi=300, edgecolor=fig.get_edgecolor())
    print(f"Grafico salvato in: {path}")

if input("Vuoi salvare il grafico Pressure? (s/n): ").strip().lower() == 's':
    save_figure()