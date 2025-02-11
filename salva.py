import serial  # Importa la libreria per la comunicazione seriale
import time  # Importa la libreria per la gestione del tempo
import dearpygui.dearpygui as dpg  # Importa la libreria per creare interfacce grafiche
import json  # Importa la libreria per gestire i file JSON


# Funzione per leggere i dati dalla porta seriale
def leggi_dati_seriale(ser):
    try:
        linea = ser.readline().decode('utf-8').strip()  # Leggi e decodifica la linea dalla porta seriale
        temp, hum = map(int, linea.split(';'))  # Dividi la stringa in temperatura e umidità e convertila in interi
        return temp, hum  # Restituisci i valori letti
    except:
        return None, None  # Se c'è un errore, restituisci None per entrambi i valori


# Funzione per salvare i dati di temperatura e umidità nel file JSON
def salva_dati_json(temp, hum, filename="dati_temperatura_umidita.json"):
    try:
        # Carica i dati esistenti dal file JSON, se esistono
        try:
            with open(filename, "r") as file:
                existing_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []  # Se il file non esiste o è vuoto, inizia con una lista vuota

        # Aggiungi i nuovi dati (temperatura e umidità) alla lista, insieme al timestamp
        existing_data.append({"temperatura": temp, "umidita": hum, "timestamp": time.time()})

        # Scrivi i dati aggiornati nel file JSON
        with open(filename, "w") as file:
            json.dump(existing_data, file, indent=4)  # Usa indent per formattare il JSON

        print(f"Dati salvati: Temperatura={temp}°C, Umidità={hum}%")
    except Exception as e:
        print(f"Errore durante il salvataggio dei dati: {e}")


# Funzione per generare i grafici in tempo reale
def genera_grafici():
    temperature = []  # Lista per memorizzare i valori di temperatura
    humidity = []  # Lista per memorizzare i valori di umidità
    time_values = []  # Lista per memorizzare i valori di tempo
    dpg.create_context()  # Crea il contesto per la GUI di DearPyGui

    # Creazione della finestra per il grafico della temperatura
    with dpg.window(label="Grafico Temperatura", width=600, height=400, pos=(0, 0)):
        plot_temp = dpg.add_plot(label="Temperatura", height=300, width=500)  # Grafico per la temperatura
        x_axis_temp = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_temp)  # Asse X per il tempo
        y_axis_temp = dpg.add_plot_axis(dpg.mvYAxis, label="Temperatura (°C)", parent=plot_temp)  # Asse Y per la temperatura
        dpg.set_axis_limits(y_axis_temp, 0, 50)  # Limiti dell'asse Y
        dpg.set_axis_limits(x_axis_temp, 0, 10)  # Limiti dell'asse X
        series_temp = dpg.add_line_series([], [], label="Temperatura", parent=y_axis_temp)  # Serie per la temperatura

    # Creazione della finestra per il grafico dell'umidità
    with dpg.window(label="Grafico Umidità", width=600, height=400, pos=(620, 0)):
        plot_hum = dpg.add_plot(label="Umidità", height=300, width=500)  # Grafico per l'umidità
        x_axis_hum = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_hum)  # Asse X per il tempo
        y_axis_hum = dpg.add_plot_axis(dpg.mvYAxis, label="Umidità (%)", parent=plot_hum)  # Asse Y per l'umidità
        dpg.set_axis_limits(y_axis_hum, 0, 100)  # Limiti dell'asse Y
        dpg.set_axis_limits(x_axis_hum, 0, 10)  # Limiti dell'asse X
        series_hum = dpg.add_line_series([], [], label="Umidità", parent=y_axis_hum)  # Serie per l'umidità

    # Crea e visualizza il viewport (finestra dell'app)
    dpg.create_viewport(title='Grafici Temperatura e Umidità', width=1240, height=420)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    # Connessione alla porta seriale (modifica 'COM3' con la porta corretta)
    ser = serial.Serial('COM3', 9600, timeout=1)
    time.sleep(2)  # Attendi che la connessione venga stabilita

    try:
        while dpg.is_dearpygui_running():
            # Leggi i dati dalla porta seriale
            temp, hum = leggi_dati_seriale(ser)
            if temp is not None and hum is not None:
                # Aggiungi il tempo e i dati alla lista
                time_values.append(len(time_values))
                temperature.append(temp)
                humidity.append(hum)

                # Aggiorna il grafico della temperatura
                dpg.set_value(series_temp, [time_values, temperature])
                if len(temperature) > 10:
                    dpg.set_axis_limits(x_axis_temp, max(0, len(time_values) - 10), len(time_values))

                # Aggiorna il grafico dell'umidità
                dpg.set_value(series_hum, [time_values, humidity])
                if len(humidity) > 10:
                    dpg.set_axis_limits(x_axis_hum, max(0, len(time_values) - 10), len(time_values))

                # Salva i dati di temperatura e umidità nel file JSON
                salva_dati_json(temp, hum)

            # Renderizza il frame della GUI
            dpg.render_dearpygui_frame()

            # Pausa di 2 secondi tra le letture
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente.")  # Messaggio di interruzione
    finally:
        ser.close()  # Chiudi la connessione seriale
        dpg.destroy_context()  # Distruggi il contesto della GUI


# Se lo script viene eseguito direttamente (non importato come modulo), avvia la funzione genera_grafici
if __name__ == "__main__":
    genera_grafici()
