import os
import re
import struct
from collections import namedtuple
from pandasgui import show

import pandas as pd


def rimuovi_salti(df_bmp):
    diffs = df_bmp['timestamp_sec'].diff().fillna(0)
    soglia_salto = 0.5
    delta_corretto = 0.02

    # Copia della colonna
    corrected_ts = df_bmp['timestamp_sec'].copy()
    correzione_cumulativa = 0.0

    for i in range(1, len(corrected_ts)):
        if diffs.iloc[i] > soglia_salto:
            eccesso = diffs.iloc[i] - delta_corretto
            correzione_cumulativa += eccesso
        corrected_ts.iloc[i] -= correzione_cumulativa

    df_bmp['timestamp_sec'] = corrected_ts
    return df_bmp



class Decoder:
    # 1. Fattori di conversione per MPU6886 da dati grezzi
    ACCEL_SCALE = 0.000488  # ±16g: 16384 LSB/g → 1/2048 (datasheet MPU6886)
    GYRO_SCALE = 0.00763  # ±2000°/s: 131 LSB/°/s → 1/131 (datasheet MPU6886)
    TEMP_SCALE = 1 / 326.8  # Datasheet MPU6886
    TEMP_OFFSET = 25.0  # Offset temperatura a 25°C

    def __init__(self, file_paths):
        self.file_paths = file_paths

    def findRP_id(self):
        #trova RP_identifier
        RP_id = ''
        match = re.findall(r'\d+', self.file_paths)
        if match:
            RP_id = match[-1]
            print(RP_id)
            #Crea la cartella per fare il salvataggio dati
            folder_path = os.path.join(r'C:\Users\fanin\Desktop\Dati accelerometro', f'RP {RP_id}')
            os.makedirs(folder_path, exist_ok=True)
        return RP_id, folder_path

    # 2. Struttura dati
    BinaryIMUData = namedtuple('BinaryIMUData', [
        'accel_x', 'accel_y', 'accel_z',
        'gyro_x', 'gyro_y', 'gyro_z',
        'mag_x', 'mag_y', 'mag_z',
        'temp',
        'timestamp'
    ])
    BinaryBMPData = namedtuple('BinaryBMPData', ['altitude', 'timestamp'])
    def decode(self):
            RP_id, folder_path = self.findRP_id()
            imu_records = []
            bmp_records = []

            with open(self.file_paths, 'rb') as f:
                header = f.read(4)  # 'M510' header check
                if header != b'M510':
                    raise ValueError('Invalid log file header!')

                while True:
                    marker = f.read(1)
                    if not marker:
                        break  # EOF

                    if marker == b'I':
                        # Legge i 24 byte successivi (10hI) dopo l'header
                        data = f.read(24)
                        if len(data) < 24:
                            break
                        accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, val7, val8, val9, temp, timestamp = struct.unpack(                            '<10hI', data)
                        imu_records.append(self.BinaryIMUData(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, val7, val8, val9, temp, timestamp))


                    elif marker == b'B':
                        # Legge i 8 byte successivi (fI) dopo l'header
                        data = f.read(8)
                        if len(data) < 8:
                            break
                        altitude, timestamp = struct.unpack('<fI', data)
                        bmp_records.append(self.BinaryBMPData(altitude, timestamp))
                    else:
                        # Header sconosciuto: interrompe la lettura
                        break

            # Convert IMU data to DataFrame
            df_imu = pd.DataFrame(imu_records, columns=self.BinaryIMUData._fields)
            df_imu['accel_x_g'] = df_imu['accel_x'] * self.ACCEL_SCALE
            df_imu['accel_y_g'] = df_imu['accel_y'] * self.ACCEL_SCALE
            df_imu['accel_z_g'] = df_imu['accel_z'] * self.ACCEL_SCALE
            df_imu['gyro_x_dps'] = df_imu['gyro_x'] * self.GYRO_SCALE
            df_imu['gyro_y_dps'] = df_imu['gyro_y'] * self.GYRO_SCALE
            df_imu['gyro_z_dps'] = df_imu['gyro_z'] * self.GYRO_SCALE
            df_imu['timestamp_sec'] = df_imu['timestamp'] / 1e6
            df_imu.drop(columns=[ 'accel_x', 'accel_y', 'accel_z',
                              'gyro_x', 'gyro_y', 'gyro_z',
                              'mag_x', 'mag_y', 'mag_z',
                              'temp'], inplace=True)

            # Convert BMP data to DataFrame
            df_bmp = pd.DataFrame(bmp_records, columns=self.BinaryBMPData._fields)
            df_bmp['timestamp_sec'] = df_bmp['timestamp'] / 1e6

            # === Ordinamento ===
            df_imu = df_imu.sort_values("timestamp")
            cols = ['timestamp_sec', 'accel_x_g', 'accel_y_g', 'accel_z_g', 'gyro_x_dps', 'gyro_y_dps', 'gyro_z_dps']
            df_imu = df_imu[cols]
            time_offset = df_imu['timestamp_sec'].iloc[0]  # primo elemento della colonna
            df_imu['timestamp_sec'] = df_imu['timestamp_sec'] - time_offset
            #show(df_imu)


            df_bmp = df_bmp.sort_values("timestamp")
            cols = ['timestamp_sec', 'altitude']
            df_bmp = df_bmp[cols]
            #show(df_bmp)
            time_offset = df_bmp['timestamp_sec'].iloc[0]  # primo elemento della colonna
            df_bmp['timestamp_sec'] = df_bmp['timestamp_sec'] - time_offset
            df_bmp = rimuovi_salti(df_bmp)
            #show(df_bmp)

            return RP_id, folder_path, df_imu, df_bmp




