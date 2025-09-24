import numpy as np
from pandasgui import show
from scipy.constants import fine_structure
from scipy.signal import butter, filtfilt, savgol_filter, sosfiltfilt, medfilt
from pykalman import KalmanFilter

# ---------------------------
# CLASSE IMUFilter
# ---------------------------
class IMUFilter:
    def __init__(self, sampling_rate=100, cutoff_frequency=5, butter_order=3,
                 kalman_q=0.001, kalman_r=0.01, tempo_iniziale=5):
        """
        :param sampling_rate: Frequenza di campionamento [Hz]
        :param cutoff_frequency: Frequenza di taglio passa basso [Hz]
        :param butter_order: Ordine del filtro Butterworth
        :param kalman_q: Rumore di processo Kalman
        :param kalman_r: Rumore di misura Kalman
        :param tempo_iniziale: Finestra iniziale [s] usata per il calcolo degli offset
        """
        self.fs = sampling_rate
        self.cutoff = cutoff_frequency
        self.butter_order = butter_order
        self.kalman_q = kalman_q
        self.kalman_r = kalman_r
        self.tempo_iniziale = tempo_iniziale

    # ---------------------------
    # CALIBRAZIONE OFFSET
    # ---------------------------
    def calibrate_offsets(self, df):
        """
        Calcola gli offset medi nei primi `tempo_iniziale` secondi e li applica come calibrazione.
        Restituisce un nuovo DataFrame con colonne corrette.
        """
        df_offset = df[df['timestamp_sec'] <= self.tempo_iniziale]

        accel_offset = df_offset[['accel_x_g', 'accel_y_g', 'accel_z_g']].mean()
        gyro_offset = df_offset[['gyro_x_dps', 'gyro_y_dps', 'gyro_z_dps']].mean()

        #print(f"\n🧭 Offset calcolati nei primi {self.tempo_iniziale} secondi:")
        #print("Accel [g]:")
        #print(accel_offset)
        #print("Gyro [rad/s]:")
        #print(gyro_offset)

        df['accel_x_g'] -= accel_offset['accel_x_g']
        df['accel_y_g'] -= accel_offset['accel_y_g']
        df['accel_z_g'] -= accel_offset['accel_z_g'] + 1

        df['gyro_x_dps'] -= gyro_offset['gyro_x_dps']
        df['gyro_y_dps'] -= gyro_offset['gyro_y_dps']
        df['gyro_z_dps'] -= gyro_offset['gyro_z_dps']

        return df

    # ---------------------------
    # FILTRI
    # ---------------------------
    def butterworth_filter(self, data):
        nyq = 0.5 * self.fs
        normal_cutoff = self.cutoff / nyq
        b, a = butter(self.butter_order, normal_cutoff, btype='low', analog=False)
        return filtfilt(b, a, data)

    def kalman_filter(self, data):
        x_est = 0
        p_est = 1
        filtered = []
        for z in data:
            p_est = p_est + self.kalman_q
            k = p_est / (p_est + self.kalman_r)
            x_est = x_est + k * (z - x_est)
            p_est = (1 - k) * p_est
            filtered.append(x_est)
        return np.array(filtered)

    def filter_axis(self, data):
        buttered = self.butterworth_filter(data)
        kalmaned = self.kalman_filter(buttered)
        return kalmaned

    def apply_filters(self, df, axes=('accel_x_g', 'accel_y_g', 'accel_z_g')):
        for axis in axes:
            df[f'{axis}_filtered'] = self.filter_axis(df[axis])
        return df

    # ---------------------------
    # PROCESS COMPLETE
    # ---------------------------
    def process(self, df, axes=('accel_x_g', 'accel_y_g', 'accel_z_g')):
        df = self.calibrate_offsets(df)
        df = self.apply_filters(df, axes)
        return df

# ---------------------------
# FUNZIONE DI FILTRAGGIO ALTITUDINE RAZZO
# ---------------------------
def process_rocket_data(
    dataframe,
    column='altitude',
    tempo_iniziale=1,
    cutoff_freq=1.5,
    savgol_window_sec=0.6,
    kalman_q=0.01,
    kalman_r=0.1):
    """
    Pipeline di filtraggio per altitudine di water rocket:
    1. Filtro anti-spike (mediana + controllo salti)
    2. Correzione offset
    3. Filtro passa-basso Butterworth (fase zero)
    4. Filtro Savitzky-Golay
    5. Filtro di Kalman adattivo
    """
    df = dataframe.copy()
    df = df.drop_duplicates(subset='timestamp_sec')
    df = df[df['timestamp_sec'].diff() > 0]

    dt = df['timestamp_sec'].diff().dropna()
    fs = 1.0 / dt.mean()
    print(f"Frequenza di campionamento: {fs:.2f} Hz")
    # STEP 1: filtro anti-spike
    finestra=10
    soglia=5
    data = df[column].values.copy()
    n = len(data)
    spike_idx = []
    for i in range(1, n - 1):
        # finestra locale
        start = max(0, i - finestra)
        end = min(n, i + finestra + 1)
        neighbors = np.concatenate([data[start:i], data[i + 1:end]])

        # Mediana locale (resistente agli spike)
        mediana_locale = np.median(neighbors)

        if abs(data[i] - mediana_locale) > soglia:
            data[i] = mediana_locale
            spike_idx.append(i)

    df[column] = data
    if spike_idx:
        print(
            f"⚠️ Rimossi {len(spike_idx)} spike in '{column}' agli indici {spike_idx[:10]}{'...' if len(spike_idx) > 10 else ''}")

    # STEP 2: OFFSET
    df_offset = df[df['timestamp_sec'] <= tempo_iniziale]
    alt_offset = df_offset[column].mean()
    df[column] -= alt_offset

    # STEP 3: BUTTERWORTH
    deltas = df['timestamp_sec'].diff().dropna()
    actual_fs = 1 / deltas.mean()
    print("Min delta t:", deltas.min(), "Max delta t:", deltas.max(), "Mean delta t:", deltas.mean())
    print("Actual fs:", actual_fs)
    nyquist = 0.5 * actual_fs
    normal_cutoff = cutoff_freq / nyquist
    sos = butter(4, normal_cutoff, btype='low', output='sos')
    y_butter = sosfiltfilt(sos, df[column].values)

    # STEP 4: SAVITZKY-GOLAY
    window_length = int(savgol_window_sec * actual_fs)
    if window_length % 2 == 0:
        window_length += 1
    if window_length < 5:
        window_length = 5
    y_savgol = np.asarray(savgol_filter(y_butter, window_length, 2))

    # STEP 5: KALMAN
    kf = KalmanFilter(
        initial_state_mean=float(y_savgol[0]),
        initial_state_covariance=1,
        transition_matrices=[1],
        observation_matrices=[1],
        transition_covariance=kalman_q,
        observation_covariance=kalman_r
    )
    state_means, _ = kf.filter(y_savgol)
    y_kalman = state_means.flatten()

    # OUTPUT
    df[column + '_raw'] = dataframe[column]
    df[column + '_kalman'] = y_kalman
    return df
