import os

import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from matplotlib.lines import Line2D


# ----------------------
# Dati simulazione 3 bar
# ----------------------
percentuale3 = np.array([20.0, 22.5, 25.0, 27.5, 30.0, 32.5, 35.0, 37.5, 40.0,
                         42.5, 45.0, 47.5, 50.0, 52.5, 55.0, 57.5, 60.0])
altitudine3 = np.array([16.44, 17.78, 18.95, 19.86, 20.51, 21.07, 21.32, 21.70, 21.80,
                        21.66, 21.29, 20.67, 19.81, 18.77, 17.49, 15.97, 14.21])
velocita3 = np.array([17.93, 18.69, 19.31, 19.79, 20.13, 20.36, 20.48, 20.62, 20.63,
                      20.50, 20.25, 19.85, 19.32, 18.64, 17.80, 16.75, 15.44])

# ----------------------
# Dati sperimentali 3 bar
# ----------------------
perc_exp3 = np.array([25.00, 30.00, 35.00, 35.00, 40.00, 40.00, 45.00, 45.00, 50.00, 60.00])
hmax_exp3 = np.array([20.05, 19.46, 21.09, 21.95, 22.26, 22.38, 22.45, 21.70, 21.50, 16.23])
vplus_exp3 = np.array([18.85, 17.21, 19.31, 21.45, 21.45, 22.01, 21.93, 19.60, 20.12, 17.91])

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
series_colors = ['#59A14F', '#E15759', '#9C755F']   # verde, rosso, marrone
series_labels = ['Serie 1', 'Serie 2', 'Serie 3']

yerr_alt_val = 0.25
yerr_vel_val = 3
xerr_rel = 0.02

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
# Errori medi
# ----------------------
err_alt3 = np.mean(np.abs((hmax_exp3 - np.interp(perc_exp3, percentuale3, altitudine3)) / hmax_exp3)) * 100
err_vel3 = np.mean(np.abs((vplus_exp3 - np.interp(perc_exp3, percentuale3, velocita3)) / vplus_exp3)) * 100
err_alt_max3 = np.max(np.abs((hmax_exp3 - np.interp(perc_exp3, percentuale3, altitudine3)) / hmax_exp3)) * 100
err_vel_max3 = np.max(np.abs((vplus_exp3 - np.interp(perc_exp3, percentuale3, velocita3)) / vplus_exp3)) * 100
# ----------------------
# Limiti Y uniformi
# ----------------------
ymin3 = min(np.min(altitudine3), np.min(velocita3)) - 0.5
ymax3 = (max(np.max(altitudine3), np.max(velocita3)) + 0.5) * 1.05

# ----------------------
# Plot
# ----------------------
fig, (ax_alt3, ax_vel3) = plt.subplots(2, 1, figsize=(11, 7.8), sharex=True, linewidth=4, edgecolor=color_alt)
fig.patch.set_facecolor('white')
ax_alt3.set_facecolor('white')
ax_vel3.set_facecolor('white')
fig.subplots_adjust(right=0.78)

errkw = dict(ecolor='black', elinewidth=1.4, capsize=5, capthick=1.4, zorder=6)

# --- Altitudine ---
ax_alt3.plot(percentuale3, altitudine3, color=color_alt, marker='o', zorder=3, label="Simulazione")
idx_max = np.argmax(altitudine3)
ax_alt3.scatter(percentuale3[idx_max], altitudine3[idx_max],
                color='#77966D', s=80, edgecolor='white', zorder=5)

for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(perc_exp3, hmax_exp3, i_rep)
    if len(xs) == 0: continue
    ax_alt3.errorbar(xs, ys, yerr=yerr_alt_val, xerr=xerr_rel*xs,
                     fmt='o', mfc=c, mec='black', mew=1.0, markersize=6,
                     **errkw, alpha=0.95)
    ord_idx = np.argsort(xs)
    ax_alt3.fill_between(xs[ord_idx], (ys - yerr_alt_val)[ord_idx], (ys + yerr_alt_val)[ord_idx],
                         alpha=0.18, edgecolor='none', color=c, zorder=2)

# Linee che congiungono i punti di ciascuna serie (Altitudine)
for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(perc_exp3, hmax_exp3, i_rep)
    if len(xs) == 0:
        continue
    ord_idx = np.argsort(xs)
    ax_alt3.plot(xs[ord_idx], ys[ord_idx],
                 color=c, linestyle='-', linewidth=1.8,
                 alpha=0.7, zorder=1, label='_nolegend_')

ax_alt3.set_ylabel("Altitudine [m]", color=color_alt)
ax_alt3.tick_params(axis='y', labelcolor=color_alt)
ax_alt3.set_ylim(ymin3, ymax3)
ax_alt3.grid(which='both', linestyle='--', alpha=0.35)
ax_alt3.minorticks_on()
handles_alt = [Line2D([], [], color=color_alt, marker='o', label='Simulazione')] + \
              [Line2D([], [], marker='o', color='none', markerfacecolor=c,
                      markeredgecolor='black', label=lab) for c, lab in zip(series_colors, series_labels)]
ax_alt3.legend(handles=handles_alt, loc='center left', bbox_to_anchor=(1.02, 0.5),
               frameon=True, framealpha=0.92, title="Altitudine")

# --- Velocità ---
ax_vel3.plot(percentuale3, velocita3, color=color_vel, marker='s', zorder=3, label="Simulazione")
idx2_max = np.argmax(velocita3)
ax_vel3.scatter(percentuale3[idx2_max], velocita3[idx2_max],
                color='#CC444B', s=80, edgecolor='white', zorder=5)

for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(perc_exp3, vplus_exp3, i_rep)
    if len(xs) == 0: continue
    ax_vel3.errorbar(xs, ys, yerr=yerr_vel_val, xerr=xerr_rel*xs,
                     fmt='o', mfc=c, mec='black', mew=1.0, markersize=6,
                     **errkw, alpha=0.95)
    ord_idx = np.argsort(xs)
    ax_vel3.fill_between(xs[ord_idx], (ys - yerr_vel_val)[ord_idx], (ys + yerr_vel_val)[ord_idx],
                         alpha=0.18, edgecolor='none', color=c, zorder=2)

# Linee che congiungono i punti di ciascuna serie (Velocità)
for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(perc_exp3, vplus_exp3, i_rep)
    if len(xs) == 0:
        continue
    ord_idx = np.argsort(xs)
    ax_vel3.plot(xs[ord_idx], ys[ord_idx],
                 color=c, linestyle='-', linewidth=1.8,
                 alpha=0.7, zorder=1, label='_nolegend_')

ax_vel3.set_xlabel(r"Percentuale di acqua (\%)")
ax_vel3.set_ylabel("Velocità [m/s]", color=color_vel)
ax_vel3.tick_params(axis='y', labelcolor=color_vel)
ax_vel3.set_ylim(ymin3, ymax3)
ax_vel3.grid(which='both', linestyle='--', alpha=0.35)
ax_vel3.minorticks_on()
handles_vel = [Line2D([], [], color=color_vel, marker='s', label='Simulazione')] + \
              [Line2D([], [], marker='o', color='none', markerfacecolor=c,
                      markeredgecolor='black', label=lab) for c, lab in zip(series_colors, series_labels)]
ax_vel3.legend(handles=handles_vel, loc='center left', bbox_to_anchor=(1.02, 0.5),
               frameon=True, framealpha=0.92, title="Velocità")

# --- Linee guida ---
for ax in [ax_alt3, ax_vel3]:
    ax.set_xlim(20, 65)
    ax.set_xticks(np.arange(20, 70, 5))
    for xref in [30, 40, 50]:
        ax.axvline(xref, color='gray', linestyle='--', alpha=0.3, zorder=1)

# --- Titolo ---
plt.suptitle(
    f"3 bar — Simulazione vs Sperimentale\n"
    f"Alt: medio {err_alt3:.1f}\\%, max {err_alt_max3:.1f}\\% | "
    f"Vel: medio {err_vel3:.1f}\\%, max {err_vel_max3:.1f}\\%",
    fontsize=16
)
plt.tight_layout()
plt.show()

# Salvataggio
def save_figure():
    path = os.path.join("C:\\Users\\fanin\\Desktop\\Dati accelerometro\\Plots", "WaterRatio_3bar_Sperimentale")
    fig.savefig(path, dpi=300, edgecolor=fig.get_edgecolor())
    print(f"Grafico salvato in: {path}")

if input("Vuoi salvare il grafico (3 bar leggibile)? (s/n): ").strip().lower() == 's':
    save_figure()
