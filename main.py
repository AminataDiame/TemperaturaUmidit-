import serial
import time
import dearpygui.dearpygui as dpg


def leggi_dati_seriale(ser):
    try:
        linea = ser.readline().decode('utf-8').strip()
        temp, hum = map(int, linea.split(';'))  # Divide la stringa e converte i valori in interi
        return temp, hum
    except:
        return None, None




def genera_grafici():
    temperature = []
    humidity = []
    time_values = []
    dpg.create_context()

    with dpg.window(label="Grafico Temperatura", width=600, height=400, pos=(0, 0)):
        plot_temp = dpg.add_plot(label="Temperatura", height=300, width=500)
        x_axis_temp = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_temp)
        y_axis_temp = dpg.add_plot_axis(dpg.mvYAxis, label="Temperatura (°C)", parent=plot_temp)
        dpg.set_axis_limits(y_axis_temp, 0, 50)
        dpg.set_axis_limits(x_axis_temp, 0, 10)
        series_temp = dpg.add_line_series([], [], label="Temperatura", parent=y_axis_temp)

    with dpg.window(label="Grafico Umidità", width=600, height=400, pos=(620, 0)):
        plot_hum = dpg.add_plot(label="Umidità", height=300, width=500)
        x_axis_hum = dpg.add_plot_axis(dpg.mvXAxis, label="Tempo", parent=plot_hum)
        y_axis_hum = dpg.add_plot_axis(dpg.mvYAxis, label="Umidità (%)", parent=plot_hum)
        dpg.set_axis_limits(y_axis_hum, 0, 100)
        dpg.set_axis_limits(x_axis_hum, 0, 10)
        series_hum = dpg.add_line_series([], [], label="Umidità", parent=y_axis_hum)

    dpg.create_viewport(title='Grafici Temperatura e Umidità', width=1240, height=420)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    ser = serial.Serial('COM3', 9600, timeout=1)  # cambiamo com
    time.sleep(2)  # Attendi la connessione della seriale

    try:
        while dpg.is_dearpygui_running():
            temp, hum = leggi_dati_seriale(ser)
            if temp is not None and hum is not None:
                time_values.append(len(time_values))
                temperature.append(temp)
                humidity.append(hum)

                dpg.set_value(series_temp, [time_values, temperature])
                if len(temperature)>10:
                    dpg.set_axis_limits(x_axis_temp, max(0, len(time_values) - 10), len(time_values))

                dpg.set_value(series_hum, [time_values, humidity])
                if len(humidity)>10:
                    dpg.set_axis_limits(x_axis_hum, max(0, len(time_values) - 10), len(time_values))

            dpg.render_dearpygui_frame()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente.")
    finally:
        ser.close()
        dpg.destroy_context()


if __name__ == "__main__":
    genera_grafici()
