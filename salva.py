import serial  # Libreria per la comunicazione seriale
import time  # Libreria per la gestione del tempo
import dearpygui.dearpygui as dpg  # Libreria per l'interfaccia grafica
import json  # Libreria per la gestione dei file JSON
import threading  # Libreria per la gestione dei thread
import queue  # Libreria per gestire la comunicazione tra thread

# Coda per passare i dati dal thread della seriale alla GUI
data_queue = queue.Queue()
running = True  # Variabile per gestire l'esecuzione del thread


def leggi_dati_seriale(ser):
    # Thread che legge i dati dalla porta seriale e li mette nella coda
    global running
    while running:
        if ser.in_waiting > 0:
            try:
                linea = ser.readline().decode('utf-8').strip()
                dati = linea.split(';')
                dati_interi = [int(x) for x in dati]
                data_queue.put(dati_interi)  # Inserisce i dati nella coda
            except Exception as e:
                print(f"Errore lettura seriale: {e}")
        time.sleep(1)  # Attende 1 secondo tra le letture


def salva_dati_json(temp, hum, filename="dati_temperatura_umidita.json"):
    try:
        with open(filename, "r") as file:
            existing_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    existing_data.append({"temperatura": temp, "umidita": hum, "timestamp": timestamp})

    with open(filename, "w") as file:
        json.dump(existing_data, file, indent=4)


def genera_grafici():
    global running

    temperature, humidity, time_values = [], [], []
    tempo_inizio = time.time()

    dpg.create_context()

    # Creazione della finestra per il grafico della temperatura
    with dpg.window(label="Grafico Temperatura", width=600, height=300, pos=(0, 0)):
        dpg.add_text("LED: SPENTO", tag="led_text1")
        dpg.add_text("Temperatura: --°C", tag="temp_text")
        plot_temp = dpg.add_plot(label="Temperatura", height=250, width=500)  # Grafico per la temperatura
        x_axis_temp = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_temp)  # Asse X per il tempo
        y_axis_temp = dpg.add_plot_axis(dpg.mvYAxis, label="Temperatura (°C)",
                                        parent=plot_temp)  # Asse Y per la temperatura
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

    with dpg.window(label="Grafico Umidità e Temperatura", width=1200, height=300, pos=(10, 350), tag="window_3"):
        plot_num = dpg.add_plot(label="Umidità e Temperatura", height=300, width=1100)

        # Creazione assi
        x_axis_num = dpg.add_plot_axis(dpg.mvXAxis, label="Posizione", parent=plot_num)
        y_axis_num = dpg.add_plot_axis(dpg.mvYAxis, label="Valore", parent=plot_num)

        # Imposta i limiti iniziali
        dpg.set_axis_limits(y_axis_num, -20, 100)
        dpg.set_axis_limits(x_axis_num, 0, 30)

        # Serie per numeri positivi e negativi
        series_temp1 = dpg.add_line_series([], [], label="Numeri Positivi", parent=y_axis_num)
        series_hum1 = dpg.add_line_series([], [], label="Numeri Negativi", parent=y_axis_num)

    dpg.create_viewport(title='Grafici Temperatura e Umidità', width=1240, height=720)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    ser = serial.Serial('COM6', 9600, timeout=1)
    time.sleep(2)

    # Avvio del thread per la lettura della seriale
    serial_thread = threading.Thread(target=leggi_dati_seriale, args=(ser,))
    serial_thread.start()

    try:
        while dpg.is_dearpygui_running():
            while not data_queue.empty():
                dati = data_queue.get()
                if len(dati) == 3:
                    temp, hum, led = dati
                    dpg.set_value("temp_text", f"Temperatura: {temp}°C")
                    dpg.set_value("hum_text", f"Umidità: {hum}%")

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
                    time_values.append(tempo_corrente)
                    temperature.append(temp)
                    humidity.append(hum)

                    dpg.set_value(series_temp, [time_values, temperature])
                    if tempo_corrente + 1 > 15:
                        dpg.set_axis_limits(x_axis_temp, max(0, len(time_values) - 15), tempo_corrente + 1)

                    # Aggiorno il grafico dell'umidità
                    dpg.set_value(series_hum, [time_values, humidity])
                    if tempo_corrente + 1 > 15:
                        dpg.set_axis_limits(x_axis_hum, max(0, len(time_values) - 15), tempo_corrente + 1)

                    # Aggiorno il grafico con entrambi
                    dpg.set_value(series_temp1, [time_values, temperature])
                    dpg.set_value(series_hum1, [time_values, humidity])

                    if tempo_corrente + 1 > 30:
                        dpg.set_axis_limits(x_axis_num, max(0, len(time_values) - 30), tempo_corrente + 1)

                    salva_dati_json(temp, hum)

            dpg.render_dearpygui_frame()
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Interrotto dall'utente.")

    finally:
        running = False
        serial_thread.join()
        ser.close()
        dpg.destroy_context()


if __name__ == "__main__":
    genera_grafici()
