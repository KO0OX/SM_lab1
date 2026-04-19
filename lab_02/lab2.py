import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class BaseStationSim:
    def __init__(self, root):
        self.root = root
        # Parametry domyślne
        self.running = False
        self.queue = []
        self.elapsed_time = 0
        self.channel_status = []
        self.history = {"Q": [], "W": [], "Ro": [], "T": [], "rho": []}
        
        # Zmienne na wyniki
        self.served_count = 0
        self.queue_sum = 0
        self.total_w = 0
        self.w_count = 0

        self.lambda_list = []
        self.mu_list = []

        self.params = {
            "Liczba kanałów": 12,
            "Kolejka": 10,
            "Lambda": 1.0,
            "Średni czas połączenia": 15,
            "Odchylenie standardowe": 3,
            "Minimalny czas połączenia": 10,
            "Maksymalny czas połączenia": 20,
            "Czas": 35
        }
        self.setup_ui()

    def setup_ui(self):
        # Przygotowanie okna symulatora
        main_frame = tk.Frame(self.root)
        main_frame.pack()

        left_frame = tk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="ns")

        param_box = tk.LabelFrame(left_frame, text="Parametry")
        param_box.pack(fill="x")

        # Pola na prametry progrmau
        self.entries = {}
        for i, (key, value) in enumerate(self.params.items()):
            tk.Label(param_box, text=key).grid(row=i, column=0, sticky="w")
            entry = tk.Entry(param_box, width=8)
            entry.grid(column=1, row=i)
            entry.insert(0, str(value))
            self.entries[key] = entry

        # Tabela na wygenerowane dane
        cols = ("Poisson", "Gauss", "Klienci", "Start", "Czas")
        self.tree = ttk.Treeview(left_frame, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=40)
        self.tree.pack()

        control_frame = tk.Frame(main_frame)
        control_frame.grid(row=0, column=1, padx=10, sticky="n")
        tk.Label(control_frame, text="Kanały").pack()
        self.channel_frame = tk.Frame(control_frame)
        self.channel_frame.pack()

        # Miejsce na kafelki kanałów
        self.channel_labels = []
        
        self.stats_label = tk.Label(control_frame,
                                    text="ρ: 0.00\nQ: 0.0\nW: 0.0\n\nObsłużeni klienci: 0\nCzas symulacji: 0/30")
        self.stats_label.pack()

        self.progress_bar = ttk.Progressbar(control_frame, length=150)
        self.progress_bar.pack(pady=10)
        tk.Button(control_frame, text="Start", command=self.start_sim, width=20).pack(pady=15)
        
        
        right_frame = tk.Frame(main_frame)
        right_frame.grid(row=0, column=2)

        # Inicjalizacja wykresów
        self.fig, (self.ax_rho, self.ax_q, self.ax_w) = plt.subplots(3, 1, figsize=(4, 6))
        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack()

    def generate_graph_data(self):
        # Generowanie odstępów w czasie oraz długości trwania rozmów w trakcie całej symulacji
        self.lambda_list = []
        self.mu_list = []
        max_time = 0

        while max_time <= self.params["Czas"] + 10:
            lambda_i = np.random.exponential(1.0 / self.params["Lambda"])
            mu = np.random.normal(self.params["Średni czas połączenia"], self.params["Odchylenie standardowe"])
            mu = int(max(self.params["Minimalny czas połączenia"], min(self.params["Maksymalny czas połączenia"], mu)))

            self.lambda_list.append(lambda_i)
            max_time += lambda_i
            self.mu_list.append(mu)

    def start_sim(self):
        # Pobranie parametrów wejściowych
        self.params = {key: float(value.get()) for key, value in self.entries.items()}
        self.channel_status = [0] * int(self.params["Liczba kanałów"])

        # Rysowanie podanej liczby kanałów
        for label in self.channel_labels:
            label.grid_forget()
        self.channel_labels = []
        for i in range(int(self.params["Liczba kanałów"])):
            label = tk.Label(self.channel_frame, text="", bg="green", fg="white", width=5, height=3)
            label.grid(row=i // 2, column=i % 2, padx=3, pady=3)
            self.channel_labels.append(label)

        # Resetowanie zmiennych i tabeli

        for i in self.tree.get_children():
            self.tree.delete(i)

        self.queue = []
        self.elapsed_time = 0
        self.served_count = 0
        self.queue_sum = 0
        self.w_count = 0
        self.total_w = 0
        self.history = {"Q": [], "W": [], "Ro": [], "T": [], "rho": []}

        self.generate_graph_data()
        self.running = True
        self.step()

    def step(self):
        # Sprawdzanie czy symulacji dobiegła końca
        if self.elapsed_time >= self.params["Czas"] or self.running == False:
            self.running = False
            self.save_report()
            return
        self.elapsed_time += 1

        # Sumowanie części czasu, aby pobrać zgłoszenia z tego okresu
        sum_lambda = 0
        k = 0
        while k < len(self.lambda_list):
            if sum_lambda + self.lambda_list[k] <= 1.0:
                sum_lambda += self.lambda_list[k]
                k += 1
            else:
                self.lambda_list[k] -= (1.0 - sum_lambda)
                break

        new_lambdas = self.lambda_list[:k]
        new_mus = self.mu_list[:k]

        # Usunięcie pobranych l i mu z list
        self.lambda_list = self.lambda_list[k:]
        self.mu_list = self.mu_list[k:]

        # Przydzielanie nowych zgłoszeń do kanałów lub koljeki
        for i in range(k):
            is_assigned = False
            for channel in range(len(self.channel_status)):
                if self.channel_status[channel] == 0:
                    self.channel_status[channel] = new_mus[i]
                    is_assigned = True
                    break

            if is_assigned == False and len(self.queue) < self.params["Kolejka"]:
                self.queue.append({'mu': new_mus[i], 'wait_time': 0})

            # Dodanie wpisu do tabeli
            if is_assigned or (len(self.queue) <= self.params["Kolejka"] and not is_assigned):
                total_clients = sum(1 for x in self.channel_status if x > 0) + len(self.queue)
                self.tree.insert("", "end",
                                 values=(f"{new_lambdas[i]:.2f}", new_mus[i], total_clients, self.elapsed_time,
                                         new_mus[i]))
                self.tree.yview_moveto(1)

        # Zmniejszanie czasu obsługi i pobieranie kolejnych zgłoszeń
        for i in range(len(self.channel_status)):
            if self.channel_status[i] > 0:
                self.channel_status[i] -= 1
                if self.channel_status[i] == 0:
                    self.served_count += 1
                    if self.queue:
                        next_client = self.queue.pop(0)
                        self.channel_status[i] = next_client['mu']
                        self.total_w += next_client['wait_time']
                        self.w_count += 1

        # Zwiększanie czasu oczekiwania dla połączeń w kolejce
        for q in self.queue:
            q['wait_time'] += 1

        # Obliczanie statystyk do wykresów
        occupied_channels = sum(1 for status in self.channel_status if status > 0)
        rho = occupied_channels / self.params["Liczba kanałów"]

        self.queue_sum += len(self.queue)
        q_avg = self.queue_sum / self.elapsed_time
        w_avg = (self.total_w / self.w_count) if self.w_count > 0 else 0

        self.history["T"].append(self.elapsed_time)
        self.history["Q"].append(q_avg)
        self.history["Ro"].append(rho)
        self.history["rho"].append(rho)
        self.history["W"].append(w_avg)

        self.update_app()

        # Wywołanie kolejnego kroku symulacji
        self.root.after(1000, self.step)

    def update_app(self):
        # Odświeżanie kolorów i wartości na kafelkach kanałów
        for i, value in enumerate(self.channel_status):
            if i < len(self.channel_labels):
                self.channel_labels[i].config(text=str(value), bg="red" if value > 0 else "green")

        self.progress_bar["value"] = (self.elapsed_time / self.params["Czas"]) * 100

        rho_current = self.history["rho"][-1]
        q_current = self.history["Q"][-1]
        w_current = self.history["W"][-1]

        # Aktualizacja statystyk chwilowych
        self.stats_label.config(
            text=f"ρ (chwilowe): {rho_current:.3f}\n\nQ (średnie): {q_current:.3f}\n\nW (średnie): {w_current:.2f}\n\n"
                 f"Obsłużone: {self.served_count}\n\n"
                 f"Czas: {self.elapsed_time}/{int(self.params['Czas'])}")

        # Rysowanie wykresów
        self.ax_rho.clear()
        self.ax_rho.set_title("ρ - Intensywność ruchu")
        self.ax_rho.set_ylim([0, 1.0])
        self.ax_rho.plot(self.history["T"], self.history["rho"], 'g', linewidth=3)
        self.ax_rho.grid(True, alpha=0.3)

        self.ax_q.clear()
        self.ax_q.set_title("Q - Średnia Kolejka")
        self.ax_q.plot(self.history["T"], self.history["Q"], 'r', linewidth=3)
        self.ax_q.grid(True, alpha=0.3)

        self.ax_w.clear()
        self.ax_w.set_title("W - Średni czas oczekiwania")
        self.ax_w.plot(self.history["T"], self.history["W"], 'b', linewidth=3)
        self.ax_w.grid(True, alpha=0.3)

        self.canvas.draw()

    def save_report(self):
        # Zapisanie wyników do pliku
        filename = "wyniki.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                for key, value in self.params.items():
                    file.write(f"{key}: {value}\n")
                file.write("-" * 30 + "\n\n")
                file.write("Czas\tp\tQ\tW\n")
                for i in range(len(self.history["T"])):
                    file.write(f"{self.history['T'][i]}\t{self.history['rho'][i]:.4f}\t"
                            f"{self.history['Q'][i]:.2f}\t{self.history['W'][i]:.2f}\n")
            print("Raport zapisany")
        except Exception as e:
            print("Błąd zapisu")


if __name__ == "__main__":
    root = tk.Tk()
    app = BaseStationSim(root)
    root.mainloop()
