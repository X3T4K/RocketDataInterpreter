import os
import glob
import tempfile
import webbrowser
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
from Filter import IMUFilter, process_rocket_data
from decoder import Decoder
from file_saver import file_saver

# ---------------------------
# FUNZIONE PER TROVARE IL FILE BINARIO
# ---------------------------
def find_log_file(rp_code_value, search_folder):
    """
    Cerca un file log corrispondente a un dato RP.
    Restituisce il percorso del file.
    """
    pattern_path = os.path.join(search_folder, f"log_*_{rp_code_value}.bin")
    matching_files_list = glob.glob(pattern_path)
    if not matching_files_list:
        raise FileNotFoundError(f"Nessun file trovato con codice {rp_code_value} in {search_folder}")
    return matching_files_list[0]

# ---------------------------
# RICERCA DEL FILE # da togliere lo spike RP60, RP307
# ---------------------------
RP_CODE_VALUE = "RP" + "285"
DATA_FOLDER_PATH = r"C:\Users\fanin\Desktop\Dati accelerometro\Lanci OGGI"

selected_file_path = find_log_file(RP_CODE_VALUE, DATA_FOLDER_PATH)
print(f"File selezionato: {selected_file_path}")

# ---------------------------
# DECODIFICA
# ---------------------------
decoder_instance = Decoder(selected_file_path)
RP_id, folder_path, df_imu, df_bmp = decoder_instance.decode()

# ---------------------------
# FILTRI
# ---------------------------
imu_filter = IMUFilter(
    sampling_rate=100, cutoff_frequency=5,
    butter_order=3, kalman_q=0.001,
    kalman_r=0.01, tempo_iniziale=1
)
df_imu = imu_filter.process(df_imu)

df_bmp = process_rocket_data(
    df_bmp,
    column='altitude', tempo_iniziale=1,
    cutoff_freq=1.5, savgol_window_sec=0.6,
    kalman_q=0.05, kalman_r=0.5)

#Genera colonna velocità
df_bmp['velocity'] = np.gradient(
        df_bmp['altitude_kalman'],df_bmp['timestamp_sec'])

df_bmp = process_rocket_data(
    df_bmp,
    column='velocity', tempo_iniziale=1,
    cutoff_freq=1.5, savgol_window_sec=0.6,
    kalman_q=0.05, kalman_r=0.5)

# ---------------------------
# TAGLIO AUTOMATICO INTERVALLO VOLO
# ---------------------------
def get_flight_interval_strict(df, threshold_start=1.0, threshold_end=0.5, margin=3.0):
    """
    Determina l'intervallo del volo e aggiunge un margine prima e dopo.
    Applica un offset temporale al dataframe.
    Inoltre, azzera la velocità fuori dall'intervallo di volo.

    threshold_start: altezza (m) che definisce il decollo
    threshold_end: altezza (m) per considerare atterraggio
    margin: secondi da aggiungere prima e dopo l'intervallo
    """
    alt = df['altitude_kalman']
    time = df['timestamp_sec']

    # Trova t_start (primo punto sopra threshold_start)
    above_start = alt > threshold_start
    if not above_start.any():
        return df, time.iloc[0], time.iloc[-1]

    t_start_flight = time.loc[above_start].iloc[0]

    # Trova il massimo di altitudine
    idx_max = alt.idxmax()

    # Trova t_end (primo punto dopo il max in cui scende sotto threshold_end)
    below_end = (alt < threshold_end) & (time > time.loc[idx_max])
    if not below_end.any():
        t_end_flight = time.iloc[-1]
    else:
        t_end_flight = time.loc[below_end].iloc[0]

    # Applica margini
    t_start = max(time.iloc[0], t_start_flight - margin)
    t_end = min(time.iloc[-1], t_end_flight + margin)

    # Taglia il dataframe
    df_cut = df[(df['timestamp_sec'] >= t_start) & (df['timestamp_sec'] <= t_end)].copy()

    # Applica offset temporale
    df_cut['timestamp_sec'] = df_cut['timestamp_sec'] - t_start

    return df_cut, t_start, t_end

df_bmp, t_start, t_end = get_flight_interval_strict(df_bmp, threshold_start=1.0, threshold_end=0.5, margin=3.0)
df_imu = df_imu[(df_imu['timestamp_sec'] >= t_start) & (df_imu['timestamp_sec'] <= t_end)].copy()
df_imu['timestamp_sec'] = df_imu['timestamp_sec'] - t_start
print(f"Segmento selezionato: {t_start:.2f}s - {t_end:.2f}s (con margini e offset)")


# ---------------------------
# CALCOLO METRICHE ALTITUDINE E VELOCITÀ
# ---------------------------
def compute_altitude_velocity_metrics(df_bmp_local):
    # Trova il valore massimo di altitude (incluso spike)
    alt_max_idx = df_bmp_local['altitude'].idxmax()
    t_spike = df_bmp_local.at[alt_max_idx, 'timestamp_sec']


    # Calcola metriche su questo intervallo
    altitude_max_val = df_bmp_local['altitude_kalman'].max()

    vmax_idx = df_bmp_local['velocity_kalman'].idxmax()
    vmax_val = df_bmp_local.at[vmax_idx, 'velocity_kalman']
    t_vmax_val = df_bmp_local.at[vmax_idx, 'timestamp_sec']

    vmin_idx = df_bmp_local['velocity_kalman'].idxmin()
    vmin_val = df_bmp_local.at[vmin_idx, 'velocity_kalman']
    t_vmin_val = df_bmp_local.at[vmin_idx, 'timestamp_sec']

    print(f"Altitudine massima: {altitude_max_val:.2f} m")
    print(f"Velocità massima positiva: {vmax_val:.2f} m/s (a t = {t_vmax_val:.2f} s)")
    print(f"Velocità massima negativa: {vmin_val:.2f} m/s (a t = {t_vmin_val:.2f} s)")
    return altitude_max_val, vmax_val, t_vmax_val, vmin_val, t_vmin_val

altitude_max_val, vmax_val, t_vmax_val, vmin_val, t_vmin_val = compute_altitude_velocity_metrics(df_bmp)



# ---------------------------
# SALVATAGGIO TRACCIATI e IMMAGINI
# ---------------------------
#saver_instance = file_saver(RP_id, folder_path, df_imu, df_bmp, 0, 0, 0)
#saver_instance.save_data()
def save_altitude_velocity_plot(df_bmp, altitude_max_val, vmax_val, t_vmax_val, vmin_val, t_vmin_val, pressure, ratio):
    """
    Salva un grafico PNG con altitudine e velocità (2 pannelli),
    usando i valori massimi/minimi già calcolati.
    """
    t = df_bmp['timestamp_sec']
    h = df_bmp['altitude_kalman']
    v = df_bmp['velocity_kalman']

    # Colori pastello
    color_alt = '#0C4767'  # blu pastello
    color_vel = '#FE9920'  # arancione pastello
    color_marker = '#77966D'  # verde pastello

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle("Tracciati  Altitudine e Velocità", fontsize=16, fontweight='bold')
    fig.text(0.5, 0.93, f"{pressure} Bar, {ratio} %", ha='center', fontsize=12)

    # Altitudine
    ax1.plot(t, h, color=color_alt, linewidth=2.5, label="Altitudine (m)")
    ax1.scatter(t[h.idxmax()], altitude_max_val, color=color_marker, s=70,
                edgecolor='black', zorder=5, label=f"Hmax = {altitude_max_val:.2f} m")
    ax1.axhline(altitude_max_val, color=color_marker, linestyle=':', linewidth=1.2, alpha=0.7)
    ax1.set_ylabel("Altitudine (m)")
    ax1.grid(which='both', linestyle='--', alpha=0.5)
    ax1.minorticks_on()
    ax1.legend()

    # Velocità
    ax2.plot(t, v, color=color_vel, linewidth=2.5, label="Velocità (m/s)")
    #MAX
    ax2.scatter(t_vmax_val, vmax_val, color='#CC444B', s=50, edgecolor='black', zorder=5, label=f"V+ = {vmax_val:.2f} m/s")
    #MIN
    ax2.scatter(t_vmin_val, vmin_val, color='#4281A4', s=50, edgecolor='black', zorder=5, label=f"V- = {vmin_val:.2f} m/s")
    ax2.axhline(0, color='gray', linestyle='--', linewidth=1.2, alpha=0.6)
    ax2.set_xlabel("Tempo (s)")
    ax2.set_ylabel("Velocità (m/s)")
    ax2.grid(which='both', linestyle='--', alpha=0.5)
    ax2.minorticks_on()
    ax2.legend()

    # Migliora layout
    output_path = os.path.join("C:\\Users\\fanin\\Desktop\\Dati accelerometro\\Plots", f"{pressure}Bar_{ratio}%.png")

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Immagine salvata: {output_path}")

    #Salva max di altitudine e velocità
    # ---------------------------
    # Salvataggio metriche su file (con controllo campo Extra)
    # ---------------------------
    metrics_txt_path = r"C:\Users\fanin\Desktop\Dati accelerometro\metrics.txt"
    try:
        last_extra_filled = False
        if os.path.exists(metrics_txt_path):
            with open(metrics_txt_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                if lines:
                    last_line = lines[-1]
                    if "RatioWat/Air = " in last_line:
                        extra_part = last_line.split("RatioWat/Air =")[-1].strip()
                        if extra_part:  # Se non vuoto
                            last_extra_filled = True

        if not last_extra_filled:
            with open(metrics_txt_path, 'a', encoding='utf-8') as f:
                f.write(f"Hmax = {altitude_max_val:.2f} m, "
                        f"V+ = {vmax_val:.2f} m/s, "
                        f"V- = {vmin_val:.2f} m/s, "
                        f"Pressure = {pressure} Bar, "
                        f"Ratio Wat/Air = {ratio} % \n")
            print(f"Metriche salvate in {metrics_txt_path}")
        else:
            print(f"Campo Extra già compilato nell'ultima riga di {metrics_txt_path}, non salvo.")
    except Exception as e:
        print(f"Errore nel salvataggio metriche: {e}")



# ---------------------------
# PLOTTING
# ---------------------------
def plot_altitude_and_velocity(df_bmp_local, altitude_max_val, vmax_val, t_vmax_val, vmin_val, t_vmin_val):
    fig_plot = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Altitudine", "Velocità", "Accelerometro (filtrato)")
    )

    # Altitudine
    t_hmax_val = df_bmp_local.loc[df_bmp_local['altitude_kalman'].idxmax(), 'timestamp_sec']
    fig_plot.add_trace(go.Scatter(
        x=df_bmp_local['timestamp_sec'], y=df_bmp_local['altitude'],
        name='Altitudine', line=dict(color='blue')
    ), row=1, col=1)

    fig_plot.add_trace(go.Scatter(
        x=df_bmp_local['timestamp_sec'], y=df_bmp_local['altitude_kalman'],
        name='Kalman Finale', line=dict(color='red', width=3)
    ), row=1, col=1)

    fig_plot.add_trace(go.Scatter(
        x=[t_hmax_val], y=[altitude_max_val],
        mode='markers+text',
        text=[f"Hmax = {altitude_max_val:.2f} m"],
        textposition="top center",
        marker=dict(color='black', size=10, symbol='x'),
        name='Altezza Massima'
    ), row=1, col=1)

    # Velocità
    fig_plot.add_trace(go.Scatter(
        x=df_bmp_local['timestamp_sec'], y=df_bmp_local['velocity'],
        name='Velocità', line=dict(color='blue', width=2)
    ), row=2, col=1)

    fig_plot.add_trace(go.Scatter(
        x=df_bmp_local['timestamp_sec'], y=df_bmp_local['velocity_kalman'],
        name='Velocità', line=dict(color='red', width=2)
    ), row=2, col=1)

    fig_plot.add_trace(go.Scatter(
        x=[t_vmax_val], y=[vmax_val],
        mode='markers+text',
        text=[f"V+ = {vmax_val:.2f} m/s"],
        textposition="top center",
        marker=dict(color='orange', size=10, symbol='triangle-up'),
        name='Velocità Max +'
    ), row=2, col=1)

    fig_plot.add_trace(go.Scatter(
        x=[t_vmin_val], y=[vmin_val],
        mode='markers+text',
        text=[f"V- = {vmin_val:.2f} m/s"],
        textposition="bottom center",
        marker=dict(color='blue', size=10, symbol='triangle-down'),
        name='Velocità Max -'
    ), row=2, col=1)

    # Legenda
    for color, label in zip(['red', 'orange', 'blue'],
                            [f"Hmax = {altitude_max_val:.2f} m", f"V+ = {vmax_val:.2f} m/s", f"V- = {vmin_val:.2f} m/s"]):
        fig_plot.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            marker=dict(size=10, color=color),
            name=label
        ))

    return fig_plot

def add_accelerometer_traces(fig_plot, df_imu_local):
    axes_colors = {'accel_x_g': 'yellow', 'accel_y_g': 'green', 'accel_z_g': 'red'}
    for axis, color in axes_colors.items():
        fig_plot.add_trace(go.Scatter(
            x=df_imu_local['timestamp_sec'], y=df_imu_local[axis],
            name=f'{axis} (filt)', line=dict(color=color)
        ), row=3, col=1)
    return fig_plot

def finalize_plot(fig_plot):
    fig_plot.update_layout(height=1000, title_text="Altitudine, Accelerometro e Giroscopio filtrati")
    fig_plot.update_yaxes(title_text="Altitudine (m)", row=1, col=1)
    fig_plot.update_yaxes(title_text="Velocità (m/s)", row=2, col=1)
    fig_plot.update_yaxes(title_text="Accel (g)", row=3, col=1)
    fig_plot.update_xaxes(title_text="Tempo (s)", row=3, col=1)
    return fig_plot

plot_figure = plot_altitude_and_velocity(df_bmp, altitude_max_val, vmax_val, t_vmax_val, vmin_val, t_vmin_val)
plot_figure = add_accelerometer_traces(plot_figure, df_imu)
plot_figure = finalize_plot(plot_figure)

# ---------------------------
# SALVATAGGIO E APERTURA PLOT
# ---------------------------
temp_file_instance = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
plot_figure.write_html(temp_file_instance.name)
webbrowser.open('file://' + os.path.realpath(temp_file_instance.name))
if input("Vuoi eseguire il salvataggio? (s/n): ").strip().lower() == "s":
    pressure = float(input("Pressure: "))
    ratio = float(input("Ratio: "))
    save_altitude_velocity_plot(df_bmp, altitude_max_val, vmax_val, t_vmax_val, vmin_val, t_vmin_val, pressure, ratio)


