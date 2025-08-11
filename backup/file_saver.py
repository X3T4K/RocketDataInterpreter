import os

import numpy as np
import pandas as pd


class file_saver:
    def __init__(self, RP_id, folder_path, dataframe, df_bmp, time_start, time_stop, offset):
        self.folder_path = folder_path
        self.dataframe = dataframe
        self.df_bmp = df_bmp
        self.RP_id = RP_id
        self.time_start = time_start
        self.time_stop = time_stop
        self.offset = offset

    # Salva in Excel
    def excel_saver(self):
        excel_path = os.path.join(self.folder_path, f'imu_data_RP{self.RP_id}.xlsx')
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            # Riepilogo (solo valori convertiti)
            self.dataframe[['timestamp_sec', 'accel_x_g', 'accel_y_g', 'accel_z_g', 'gyro_x_dps', 'gyro_y_dps',
                'gyro_z_dps', ]].to_excel(writer, sheet_name='Riepilogo', index=False)
        print(f"Dati salvati in {excel_path}")

    # Salva in csv
    def csv_saver(self):
        csv_path = os.path.join(self.folder_path, f'imu_data_RP{self.RP_id}.csv')
        self.dataframe[['timestamp_sec',  'accel_x_g', 'accel_y_g', 'accel_z_g', 'gyro_x_dps', 'gyro_y_dps', 'gyro_z_dps']].to_csv(
            csv_path, index=False)

    def cutter_saver(self):
        timestamp_inizio = self.time_start - self.offset  # <-- estremo iniziale
        timestamp_fine = self.time_stop  # <-- estremo finale

        timestamp_sec = self.dataframe['timestamp_sec'].values  # Se hai una colonna 'timestamp_sec'
        # Trova l'indice dell'elemento più vicino a timestamp_inizio
        indice_corrispondente = (np.abs(timestamp_sec - timestamp_inizio)).argmin()
        # Recupera il valore corrispondente
        timestamp_corrispondente = timestamp_sec[indice_corrispondente]
        print("Timestamp inziale: " + str(timestamp_corrispondente))

        # Filtro il DataFrame in base all'intervallo di timestamp
        df_filtrato = self.dataframe[
            (self.dataframe['timestamp_sec'] >= timestamp_inizio) &
            (self.dataframe['timestamp_sec'] <= timestamp_fine)
            ]

        # Percorso file CSV
        csv_path = os.path.join(self.folder_path, f'imu_data_RP{self.RP_id}_tagliati.csv')
        # Salvo solo le colonne desiderate del DataFrame filtrato
        df_filtrato[
            ['timestamp_sec', 'accel_x_g', 'accel_y_g', 'accel_z_g', 'gyro_x_dps', 'gyro_y_dps', 'gyro_z_dps']
                    ].to_csv(csv_path, index=False)
        print(f"Dati filtrati salvati in {csv_path}")

    def save_data(self):
        self.excel_saver()
        self.csv_saver()
        if(self.time_start > self.time_stop):
            self.cutter_saver()

