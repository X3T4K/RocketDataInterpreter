import os

import matplotlib.pyplot as plt
import numpy as np

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


# --- Dati sperimentali ---
perc_exp = np.array([
    20.00, 20.00,
    25.00, 25.00,
    30.00, 30.00,
    35.00, 35.00, 35.00,
    40.00, 40.00,
    55.00
])

hmax_exp = np.array([
    10.57, 11.40,
    12.45, 11.79,
    14.43, 13.16,
    14.56, 14.28, 14.31,
    14.28, 14.23,
    10.50
])

vplus_exp = np.array([
    11.07, 11.69,
    12.38, 12.93,
    13.46, 13.24,
    15.03, 14.36, 12.69,
    14.89, 13.94,
    14.41
])


from matplotlib.lines import Line2D

# === Scale Y uniformi come nel plot 2Bar originale ===
ymin = min(np.min(altitudine), np.min(velocita)) - 0.5
ymax = (max(np.max(altitudine), np.max(velocita)) + 0.5) * 1.05

# === Errori sperimentali ===
yerr_alt_val = 0.25      # ±0.25 m
yerr_vel_val = 3      # ±3 m/s
xerr_rel = 0.02         # ±2% su X

# Utility per serie replicate
from collections import defaultdict
def make_series(x_raw, y_raw, i_rep):
    grp = defaultdict(list)
    for x, y in zip(x_raw, y_raw):
        grp[x].append(y)
    xs, ys = [], []
    for x in sorted(grp.keys()):
        if len(grp[x]) > i_rep:
            xs.append(x)
            ys.append(grp[x][i_rep])
    return np.array(xs, dtype=float), np.array(ys, dtype=float)

# Palette serie (coerente con blu scuro e arancio del grafico)
series_colors = ['#59A14F', '#E15759', '#9C755F']   # verde, rosso caldo, marrone tenue
series_labels = ['Serie 1', 'Serie 2', 'Serie 3']

# Errori percentuali medi
err_alt = np.mean(np.abs((hmax_exp - np.interp(perc_exp, percentuale, altitudine)) / hmax_exp)) * 100
err_vel = np.mean(np.abs((vplus_exp - np.interp(perc_exp, percentuale, velocita)) / vplus_exp)) * 100
#Errori massimi

err_alt_max = np.max(np.abs((hmax_exp - np.interp(perc_exp, percentuale, altitudine)) / hmax_exp)) * 100
err_vel_max = np.max(np.abs((vplus_exp - np.interp(perc_exp, percentuale, velocita)) / vplus_exp)) * 100

fig, (ax_alt, ax_vel) = plt.subplots(2, 1, figsize=(11, 7.8), sharex=True, linewidth=4, edgecolor=color_alt)
fig.patch.set_facecolor('white')
ax_alt.set_facecolor('white')
ax_vel.set_facecolor('white')

# Spazio per legende esterne a destra
fig.subplots_adjust(right=0.78)

errkw = dict(ecolor='black', elinewidth=1.4, capsize=5, capthick=1.4, zorder=6)

# ================= ALTITUDINE =================
ax_alt.plot(percentuale, altitudine, color=color_alt, marker='o', zorder=3, label="Simulazione")
idx_max = np.argmax(altitudine)
ax_alt.scatter(percentuale[idx_max], altitudine[idx_max],
               color='#77966D', s=80, edgecolor='white', zorder=5, label='_nolegend_')

for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(perc_exp, hmax_exp, i_rep)
    if len(xs) == 0:
        continue
    ax_alt.errorbar(xs, ys, yerr=yerr_alt_val, xerr=xerr_rel*xs,
                    fmt='o', mfc=c, mec='black', mew=1.0, markersize=6,
                    **errkw, alpha=0.95, label=lab)
    ord_idx = np.argsort(xs)
    ax_alt.fill_between(xs[ord_idx], (ys - yerr_alt_val)[ord_idx], (ys + yerr_alt_val)[ord_idx],
                        alpha=0.18, edgecolor='none', color=c, zorder=2)

# Linee che congiungono i punti di ciascuna serie (Altitudine)
for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(perc_exp, hmax_exp, i_rep)
    if len(xs) == 0:
        continue
    ord_idx = np.argsort(xs)
    ax_alt.plot(xs[ord_idx], ys[ord_idx],
                 color=c, linestyle='-', linewidth=1.8,
                 alpha=0.7, zorder=1, label='_nolegend_')

ax_alt.set_ylabel("Altitudine [m]", color=color_alt)
ax_alt.tick_params(axis='y', labelcolor=color_alt)
ax_alt.set_ylim(ymin, ymax)
ax_alt.grid(which='both', linestyle='--', alpha=0.35)
ax_alt.minorticks_on()

# legenda esterna (a destra, centrata verticalmente)
handles_alt = [Line2D([], [], color=color_alt, marker='o', label='Simulazione')]
for c, lab in zip(series_colors, series_labels):
    handles_alt.append(Line2D([], [], marker='o', color='none', markerfacecolor=c,
                              markeredgecolor='black', label=lab))
ax_alt.legend(handles=handles_alt, loc='lower center',
              frameon=True, framealpha=0.92, title="Altitudine")

# ================= VELOCITÀ =================
ax_vel.plot(percentuale, velocita, color=color_vel, marker='s', zorder=3, label="Simulazione")
idx2_max = np.argmax(velocita)
ax_vel.scatter(percentuale[idx2_max], velocita[idx2_max],
               color='#CC444B', s=80, edgecolor='white', zorder=5, label='_nolegend_')

for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(perc_exp, vplus_exp, i_rep)
    if len(xs) == 0:
        continue
    ax_vel.errorbar(xs, ys, yerr=yerr_vel_val, xerr=xerr_rel*xs,
                    fmt='o', mfc=c, mec='black', mew=1.0, markersize=6,
                    **errkw, alpha=0.95, label=lab)
    ord_idx = np.argsort(xs)
    ax_vel.fill_between(xs[ord_idx], (ys - yerr_vel_val)[ord_idx], (ys + yerr_vel_val)[ord_idx],
                        alpha=0.18, edgecolor='none', color=c, zorder=2)

# Linee che congiungono i punti di ciascuna serie (Velocità)
for i_rep, (c, lab) in enumerate(zip(series_colors, series_labels)):
    xs, ys = make_series(perc_exp, vplus_exp, i_rep)
    if len(xs) == 0:
        continue
    ord_idx = np.argsort(xs)
    ax_vel.plot(xs[ord_idx], ys[ord_idx],
                 color=c, linestyle='-', linewidth=1.8,
                 alpha=0.7, zorder=1, label='_nolegend_')

ax_vel.set_xlabel(r"Percentuale di acqua (\%)")
ax_vel.set_ylabel("Velocità [m/s]", color=color_vel)
ax_vel.tick_params(axis='y', labelcolor=color_vel)
ax_vel.set_ylim(ymin, ymax)
ax_vel.grid(which='both', linestyle='--', alpha=0.35)
ax_vel.minorticks_on()

# legenda esterna (a destra)
handles_vel = [Line2D([], [], color=color_vel, marker='s', label='Simulazione')]
for c, lab in zip(series_colors, series_labels):
    handles_vel.append(Line2D([], [], marker='o', color='none', markerfacecolor=c,
                              markeredgecolor='black', label=lab))
ax_vel.legend(handles=handles_vel, loc='lower center',
              frameon=True, framealpha=0.92, title="Velocità")

# Linee guida verticali + X condivisa
for ax in [ax_alt, ax_vel]:
    ax.set_xlim(10, 65)
    ax.set_xticks(np.arange(10, 70, 5))
    for xref in [30, 40, 50]:
        ax.axvline(xref, color='gray', linestyle='--', alpha=0.3, zorder=1)

plt.suptitle(
    f"2 bar — Simulazione vs Sperimentale\n"
    f"Alt: medio {err_alt:.1f}\\%, max {err_alt_max:.1f}\\% | "
    f"Vel: medio {err_vel:.1f}\\%, max {err_vel_max:.1f}\\%",
    fontsize=16
)
plt.tight_layout()  # lascia spazio a destra per le legende
plt.show()

# Salvataggio
def save_figure():
    path = os.path.join("C:\\Users\\fanin\\Desktop\\Dati accelerometro\\Plots", "WaterRatio_2bar_Sperimentale.png")
    fig.savefig(path, dpi=300, edgecolor=fig.get_edgecolor())
    print(f"Grafico salvato in: {path}")

if input("Vuoi salvare il grafico (2 bar leggibile)? (s/n): ").strip().lower() == 's':
    save_figure()
