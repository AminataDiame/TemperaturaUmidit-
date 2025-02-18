

import serial  # Importa la libreria per la comunicazione seriale
import time  # Importa la libreria per la gestione del tempo
import dearpygui.dearpygui as dpg  # Importa la libreria per creare interfacce grafiche
import json  # Importa la libreria per gestire i file JSON


# Funzione per leggere i dati dalla porta seriale
def leggi_dati_seriale(ser):
    if ser.in_waiting > 0:
        linea = ser.readline().decode('utf-8').strip()  # Leggi e decodifica la linea dalla porta seriale
        print(linea)
        dati = linea.split(';')  # Dividi la stringa in temperatura e umidità e convertila in interi
        dati_interi = [int(x) for x in dati]
        print(dati_interi)
        print(dati_interi[0])
        print(dati_interi[1])
        return dati_interi  # Restituisci i valori letti



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
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # Data e ora leggibili
        existing_data.append({"temperatura": temp, "umidita": hum, "timestamp": timestamp})

        # Scrivi i dati aggiornati nel file JSON
        with open(filename, "w") as file:
            json.dump(existing_data, file, indent=4)

        print(f"Dati salvati: Temperatura={temp}°C, Umidità={hum}%")
    except Exception as e:
        print(f"Errore durante il salvataggio dei dati: {e}")


# Funzione per generare i grafici in tempo reale
def genera_grafici():
    temperature = []  # Lista per memorizzare i valori di temperatura
    humidity = []  # Lista per memorizzare i valori di umidità
    time_values = [] # Lista per memorizzare i valori di tempo
    tempo_inizio = time.time()
    dpg.create_context()
    temp=0# Crea il contesto per la GUI di DearPyGui
    hum=0
    led=0

    # Creazione della finestra per il grafico della temperatura
    with dpg.window(label="Grafico Temperatura", width=600, height=300, pos=(0, 0)):
        dpg.add_text("LED: SPENTO", tag="led_text1")
        dpg.add_text("Temperatura: --°C", tag="temp_text")
        plot_temp = dpg.add_plot(label="Temperatura", height=250, width=500)  # Grafico per la temperatura
        x_axis_temp = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_temp)  # Asse X per il tempo
        y_axis_temp = dpg.add_plot_axis(dpg.mvYAxis, label="Temperatura (°C)", parent=plot_temp)  # Asse Y per la temperatura
        dpg.set_axis_limits(y_axis_temp, -20, 50)  # Limiti dell'asse Y
        dpg.set_axis_limits(x_axis_temp, 0, 15)  # Limiti dell'asse X
        series_temp = dpg.add_line_series([], [], label="Temperatura", parent=y_axis_temp)  # Serie per la temperatura

    # Creazione della finestra per il grafico dell'umidità
    with dpg.window(label="Grafico Umidità", width=600, height=300, pos=(620, 0)):
        dpg.add_text("LED: SPENTO", tag="led_text2")
        dpg.add_text("Umidità: --%", tag="hum_text")
        plot_hum = dpg.add_plot(label="Umidità", height=250, width=500)  # Grafico per l'umidità
        x_axis_hum = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_hum)  # Asse X per il tempo
        y_axis_hum = dpg.add_plot_axis(dpg.mvYAxis, label="Umidità (%)", parent=plot_hum)  # Asse Y per l'umidità
        dpg.set_axis_limits(y_axis_hum, 0, 100)  # Limiti dell'asse Y
        dpg.set_axis_limits(x_axis_hum, 0, 15)  # Limiti dell'asse X
        series_hum = dpg.add_line_series([], [], label="Umidità", parent=y_axis_hum)  # Serie per l'umidità

    with dpg.window(label="Grafico Numeri", width=1200, height=300, pos=(10, 350), tag="window_3"):
        plot_num = dpg.add_plot(label="Numeri", height=300, width=1100)

        # Creazione assi
        x_axis_num = dpg.add_plot_axis(dpg.mvXAxis, label="Posizione", parent=plot_num)
        y_axis_num = dpg.add_plot_axis(dpg.mvYAxis, label="Valore", parent=plot_num)

        # Imposta i limiti iniziali
        dpg.set_axis_limits(y_axis_num, -20, 100)
        dpg.set_axis_limits(x_axis_num, 0, 30)

        # Serie per numeri positivi e negativi
        series_temp1 = dpg.add_line_series([], [], label="Numeri Positivi", parent=y_axis_num)
        series_hum1 = dpg.add_line_series([], [], label="Numeri Negativi", parent=y_axis_num)
    # Crea e visualizza
    dpg.create_viewport(title='Grafici Temperatura e Umidità', width=1240, height=720)
    dpg.setup_dearpygui()
    dpg.show_viewport()


    ser = serial.Serial('COM6', 9600, timeout=1)
    time.sleep(1)  # Attendi che la connessione venga stabilita

    try:
        while dpg.is_dearpygui_running():
            # Leggi i dati dalla porta seriale
            dati = leggi_dati_seriale(ser)
            if dati is not None:
                temp=dati[0]
                hum=dati[1]
                led=dati[2]
                if temp is not None and hum is not None and led is not None:
                    dpg.set_value("temp_text", f"Temperatura: {temp}°C")
                    dpg.set_value("hum_text", f"Umidità: {hum}%")
                    # Modifico lo stato del led
                    if led == 2:
                        dpg.set_value("led_text1", "LED: ROSSO (Alta temperatura)")
                        dpg.set_value("led_text2", "LED: ROSSO (Alta temperatura)")
                    elif led == 1:
                        dpg.set_value("led_text1", "LED: VERDE (Normale)")
                        dpg.set_value("led_text2", "LED: VERDE (Normale)")
                    else:
                        dpg.set_value("led_text1", "LED: SPENTO (Bassa temperatura)")
                        dpg.set_value("led_text2", "LED: SPENTO (Bassa temperatura)")

                    tempo_corrente = time.time() - tempo_inizio

                    # Aggiungo il tempo e i dati alla lista
                    time_values.append(tempo_corrente)
                    temperature.append(temp)
                    humidity.append(hum)

                    # Aggiorno il grafico della temperatura

                    dpg.set_value(series_temp, [time_values, temperature])
                    if tempo_corrente+1 > 15:
                        dpg.set_axis_limits(x_axis_temp, max(0, len(time_values) - 15), tempo_corrente+1)

                    # Aggiorno il grafico dell'umidità
                    dpg.set_value(series_hum, [time_values, humidity])
                    if tempo_corrente+1 > 15:
                        dpg.set_axis_limits(x_axis_hum, max(0, len(time_values) - 15), tempo_corrente+1)

                    # Aggiorno il grafico con entrambi
                    dpg.set_value(series_temp1, [time_values, temperature])
                    dpg.set_value(series_hum1, [time_values, humidity])

                    if tempo_corrente+1 > 30:
                        dpg.set_axis_limits(x_axis_num, max(0, len(time_values) - 30), tempo_corrente+1)

                    # Salvo i dati di temperatura e umidità nel file JSON
                    salva_dati_json(temp, hum)

                # Ridisegna
                dpg.render_dearpygui_frame()

                # Pausa di 2 secondi tra le letture
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente.", temperature, humidity)  # Messaggio di interruzione
    finally:
        ser.close()  # Chiudo la connessione seriale
        dpg.destroy_context()  # Distruggo il contesto della GUI


if __name__ == "__main__":
    genera_grafici()
