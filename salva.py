import queue
import threading
import serial
import time
import dearpygui.dearpygui as dpg
import json
# Coda per comunicare tra il thread della seriale e la GUI
data_queue = queue.Queue()
# Flag per terminare il thread
running = True
# 🔹 Funzione per leggere i dati dalla porta seriale nel thread separato
def leggi_dati_seriale(ser):
   global running
   while running:
       try:
           if ser.in_waiting > 0:
               linea = ser.readline().decode('utf-8').strip()
               dati = linea.split(';')
               if len(dati) == 3:  # Assicuriamoci che siano presenti tutti i dati
                   temp, hum, stato_led = [int(x) for x in dati]
                   data_queue.put((temp, hum, stato_led))  # Mettiamo i dati nella coda
       except serial.SerialException:
           pass
       time.sleep(2)  # Evitiamo di sovraccaricare la CPU
# 🔹 Funzione per salvare i dati in JSON
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
# 🔹 Funzione per generare i grafici
def genera_grafici():
   global running
   temperature = []
   humidity = []
   time_values = []
   tempo_inizio = time.time()
   dpg.create_context()
   with dpg.window(label="Grafico Temperatura", width=600, height=400, pos=(0, 0)):
       dpg.add_text("LED: SPENTO", tag="led_text")
       dpg.add_text("Temperatura: --°C", tag="temp_text")
       plot_temp = dpg.add_plot(label="Temperatura", height=300, width=500)
       x_axis_temp = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_temp)
       y_axis_temp = dpg.add_plot_axis(dpg.mvYAxis, label="Temperatura (°C)", parent=plot_temp)
       dpg.set_axis_limits(y_axis_temp, -20, 50)
       dpg.set_axis_limits(x_axis_temp, 0, 20)
       series_temp = dpg.add_line_series([], [], label="Temperatura", parent=y_axis_temp)
   with dpg.window(label="Grafico Umidità", width=600, height=400, pos=(620, 0)):
       dpg.add_text("Umidità: --%", tag="hum_text")
       plot_hum = dpg.add_plot(label="Umidità", height=300, width=500)
       x_axis_hum = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_hum)
       y_axis_hum = dpg.add_plot_axis(dpg.mvYAxis, label="Umidità (%)", parent=plot_hum)
       dpg.set_axis_limits(y_axis_hum, 0, 100)
       dpg.set_axis_limits(x_axis_hum, 0, 20)
       series_hum = dpg.add_line_series([], [], label="Umidità", parent=y_axis_hum)
   dpg.create_viewport(title='Grafici Temperatura e Umidità', width=1240, height=420)
   dpg.setup_dearpygui()
   dpg.show_viewport()
   # 🔹 Connessione alla porta seriale (MODIFICA 'COM3' con la tua porta)
   ser = serial.Serial('COM3', 9600, timeout=1)
   time.sleep(2)
   # 🔹 Creiamo e avviamo il thread per la lettura seriale
   serial_thread = threading.Thread(target=leggi_dati_seriale, args=(ser,))
   serial_thread.start()
   try:
       while dpg.is_dearpygui_running():
           # Controlliamo se ci sono dati nella coda senza bloccare
           while not data_queue.empty():
               temp, hum, led = data_queue.get()
               dpg.set_value("temp_text", f"Temperatura: {temp}°C")
               dpg.set_value("hum_text", f"Umidità: {hum}%")
               if led == 2:
                   dpg.set_value("led_text", "LED: ROSSO (Alta temperatura)")
               elif led == 1:
                   dpg.set_value("led_text", "LED: VERDE (Normale)")
               else:
                   dpg.set_value("led_text", "LED: SPENTO (Bassa temperatura)")
               tempo_corrente = time.time() - tempo_inizio
               time_values.append(tempo_corrente)
               temperature.append(temp)
               humidity.append(hum)
               dpg.set_value(series_temp, [time_values, temperature])
               dpg.set_value(series_hum, [time_values, humidity])
               salva_dati_json(temp, hum)
           dpg.render_dearpygui_frame()
           time.sleep(0.1)
   except KeyboardInterrupt:
       print("\nInterrotto dall'utente.")
   finally:
       running = False
       serial_thread.join()
       ser.close()
       dpg.destroy_context()
if __name__ == "__main__":
   genera_grafici()