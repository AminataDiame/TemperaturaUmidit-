import queue  # Importo la libreria per gestire le code (utile per il thread)
import threading  # Questa serve per gestire i thread (processi paralleli)
import serial  # Libreria per comunicare con la porta seriale (Arduino)
import time  # Per gestire i tempi e le attese
import dearpygui.dearpygui as dpg  # Libreria per creare l’interfaccia grafica
import json  # Per salvare i dati in un file JSON

# Coda per passare i dati dal thread della seriale alla GUI
data_queue = queue.Queue()

# Variabile globale per fermare il thread quando chiudiamo il programma
running = True


# 🔹 Funzione che legge i dati dalla porta seriale in un thread separato
def leggi_dati_seriale(ser):
    global running  # Dico che voglio usare la variabile globale "running"
    while running:
        try:
            if ser.in_waiting > 0:  # Se ci sono dati disponibili sulla seriale...
                linea = ser.readline().decode('utf-8').strip()  # Leggo la linea e la converto in stringa
                dati = linea.split(';')  # Divido i dati ricevuti separati da ";"
                if len(dati) == 3:  # Controllo che ci siano esattamente 3 valori
                    temp, hum, stato_led = map(int, dati)  # Converto i dati in numeri interi
                    data_queue.put((temp, hum, stato_led))  # Metto i dati nella coda per la GUI
        except serial.SerialException:
            pass  # Se c'è un errore nella lettura della seriale vado avanti
        time.sleep(2)  # Aspetto 2 secondi


# 🔹 Funzione per salvare i dati in un file JSON
def salva_dati_json(temp, hum, filename="dati_temperatura_umidita.json"):
    try:
        with open(filename, "r") as file:  # Provo ad aprire il file JSON
            existing_data = json.load(file)  # Carico i dati esistenti
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []  # Se il file non esiste, creo una lista vuota

    # Prendo la data e l'ora attuale per il salvataggio
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    existing_data.append({"temperatura": temp, "umidita": hum, "timestamp": timestamp})

    # Scrivo i nuovi dati nel file JSON
    with open(filename, "w") as file:
        json.dump(existing_data, file, indent=4)


# 🔹 Funzione per creare l'interfaccia grafica
def genera_grafici():
    global running  # Mi assicuro di usare la variabile globale

    # Liste per memorizzare i valori nel tempo
    temperature = []
    humidity = []
    time_values = []
    tempo_inizio = time.time()  # Memorizzo il tempo di inizio per il grafico

    dpg.create_context()  # Inizializzo la GUI

    # 🔹 Finestra per il grafico della temperatura
    with dpg.window(label="Grafico Temperatura", width=600, height=400, pos=(0, 0)):
        dpg.add_text("LED: SPENTO", tag="led_text")  # Testo per indicare lo stato del LED
        dpg.add_text("Temperatura: --°C", tag="temp_text")  # Testo per la temperatura
        plot_temp = dpg.add_plot(label="Temperatura", height=300, width=500)
        x_axis_temp = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_temp)
        y_axis_temp = dpg.add_plot_axis(dpg.mvYAxis, label="Temperatura (°C)", parent=plot_temp)
        dpg.set_axis_limits(y_axis_temp, -20, 50)
        dpg.set_axis_limits(x_axis_temp, 0, 20)
        series_temp = dpg.add_line_series([], [], label="Temperatura", parent=y_axis_temp)

    # 🔹 Finestra per il grafico dell'umidità
    with dpg.window(label="Grafico Umidità", width=600, height=400, pos=(620, 0)):
        dpg.add_text("Umidità: --%", tag="hum_text")  # Testo per l'umidità
        plot_hum = dpg.add_plot(label="Umidità", height=300, width=500)
        x_axis_hum = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_hum)
        y_axis_hum = dpg.add_plot_axis(dpg.mvYAxis, label="Umidità (%)", parent=plot_hum)
        dpg.set_axis_limits(y_axis_hum, 0, 100)
        dpg.set_axis_limits(x_axis_hum, 0, 20)
        series_hum = dpg.add_line_series([], [], label="Umidità", parent=y_axis_hum)

    # Imposto la finestra principale
    dpg.create_viewport(title='Grafici Temperatura e Umidità', width=1240, height=420)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    # 🔹 Apro la porta seriale (MODIFICA 'COM3' con la tua porta)
    ser = serial.Serial('COM3', 9600, timeout=1)
    time.sleep(2)  # Aspetto un attimo per la connessione

    # 🔹 Avvio il thread per leggere i dati dalla seriale
    serial_thread = threading.Thread(target=leggi_dati_seriale, args=(ser,))
    serial_thread.start()

    try:
        while dpg.is_dearpygui_running():  # Finché la GUI è aperta...
            # Controllo se ci sono dati nuovi nella coda
            while not data_queue.empty():
                temp, hum, led = data_queue.get()  # Prendo i dati dalla coda

                # 🔹 Aggiorno i valori nell'interfaccia
                dpg.set_value("temp_text", f"Temperatura: {temp}°C")
                dpg.set_value("hum_text", f"Umidità: {hum}%")

                # 🔹 Modifico il testo in base allo stato del LED
                if led == 2:
                    dpg.set_value("led_text", "LED: ROSSO (Alta temperatura)")
                elif led == 1:
                    dpg.set_value("led_text", "LED: VERDE (Normale)")
                else:
                    dpg.set_value("led_text", "LED: SPENTO (Bassa temperatura)")

                # 🔹 Aggiorno il grafico
                tempo_corrente = time.time() - tempo_inizio
                time_values.append(tempo_corrente)
                temperature.append(temp)
                humidity.append(hum)

                dpg.set_value(series_temp, [time_values, temperature])
                dpg.set_value(series_hum, [time_values, humidity])

                # 🔹 Salvo i dati in JSON
                salva_dati_json(temp, hum)

            dpg.render_dearpygui_frame()
            time.sleep(0.1)  # Aspetto 0.1 secondi per aggiornare

    except KeyboardInterrupt:  # Se premo Ctrl+C, interrompo tutto
        print("\nInterrotto dall'utente.")

    finally:
        running = False  # Fermo il thread
        serial_thread.join()  # Aspetto che il thread termini
        ser.close()  # Chiudo la porta seriale
        dpg.destroy_context()  # Chiudo la GUI


# 🔹 Avvio il programma
if __name__ == "__main__":
    genera_grafici()
