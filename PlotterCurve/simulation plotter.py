import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. Caricamento e Pulizia dei Dati ---

# Definisci il percorso del file CSV
file_path = 'simulation.csv'

try:
    # Legge il file CSV, usando la prima riga come header e saltando la seconda (unità di misura)
    data = pd.read_csv(file_path, header=0, skiprows=[1])
except FileNotFoundError:
    print(f"Errore: Il file '{file_path}' non è stato trovato.")
    print("Assicurati che il file CSV sia nella stessa cartella dello script.")
    exit()

# Pulisce e rinomina le colonne per chiarezza nel grafico.
# Pandas gestisce le colonne duplicate aggiungendo ".1", quindi la seconda 'Altitude' diventa 'Altitude.1'.
colonne_nuove = {
    'Time': 'Time (s)',
    'Acceleration': 'Acceleration (m/s^2)',
    'Altitude': 'Altitude (m)',
    'Velocity': 'Velocity (m/s)',
    'Altitude.1': 'Altitude (ft)',
    'Thrust': 'Thrust (N)'
}
data.rename(columns=colonne_nuove, inplace=True)

# Converte tutte le colonne in formato numerico, gestendo eventuali errori
for col in data.columns:
    data[col] = pd.to_numeric(data[col], errors='coerce')

# Rimuove le righe che contengono valori non validi (NaN)
data.dropna(inplace=True)


# --- 2. Creazione del Grafico Interattivo ---

print("Creazione del grafico interattivo in corso...")

# Crea una figura con 2 subplot verticali che condividono lo stesso asse X (il tempo)
fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    subplot_titles=('Cinematica: Posizione e Velocità', 'Dinamica: Accelerazione e Spinta')
)

# --- Aggiungi le tracce al primo subplot (riga 1) ---
# Traccia per l'Altitudine
fig.add_trace(go.Scatter(
    x=data['Time (s)'],
    y=data['Altitude (m)'],
    name='Altitudine (m)',
    mode='lines',
    line=dict(color='cyan')
), row=1, col=1)

# Traccia per la Velocità
fig.add_trace(go.Scatter(
    x=data['Time (s)'],
    y=data['Velocity (m/s)'],
    name='Velocità (m/s)',
    mode='lines',
    line=dict(color='lime')
), row=1, col=1)


# --- Aggiungi le tracce al secondo subplot (riga 2) ---
# Traccia per l'Accelerazione
fig.add_trace(go.Scatter(
    x=data['Time (s)'],
    y=data['Acceleration (m/s^2)'],
    name='Accelerazione (m/s²)',
    mode='lines',
    line=dict(color='magenta')
), row=2, col=1)

# Traccia per la Spinta
fig.add_trace(go.Scatter(
    x=data['Time (s)'],
    y=data['Thrust (N)'],
    name='Spinta (N)',
    mode='lines',
    line=dict(color='orange')
), row=2, col=1)


# --- 3. Personalizzazione e Visualizzazione ---

# Aggiorna il layout generale del grafico per un aspetto migliore
fig.update_layout(
    title_text='Analisi Completa della Simulazione del Razzo 🚀',
    template='plotly_dark',  # Tema scuro, molto leggibile
    legend_title_text='Variabili',
    height=800  # Altezza del grafico in pixel
)

# Aggiorna i titoli degli assi
fig.update_yaxes(title_text='Valori Cinematici', row=1, col=1)
fig.update_yaxes(title_text='Valori Dinamici', row=2, col=1)
fig.update_xaxes(title_text='Tempo (s)', row=2, col=1)

# Mostra il grafico. Si aprirà una nuova scheda nel tuo browser.
fig.show()

print("Grafico generato. Controlla la finestra del browser.")