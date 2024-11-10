import soundcard as sc
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import wave
import threading
import os
import time
from pathlib import Path

# Configurações iniciais
sample_rate = 44100  # Taxa de amostragem em Hz
frames = []  # Lista para armazenar os frames de áudio
is_recording = False
is_paused = False

class AudioRecorderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gravador de Som do Sistema")
        self.root.geometry("800x600")
        self.setup_gui()
        
    def setup_gui(self):
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame para controles de arquivo
        self.file_frame = ttk.LabelFrame(self.main_frame, text="Configurações de Arquivo", padding="5")
        self.file_frame.pack(fill=tk.X, pady=(0, 10))

        # Campo de caminho do arquivo
        self.path_frame = ttk.Frame(self.file_frame)
        self.path_frame.pack(fill=tk.X, pady=5)
        
        self.path_var = tk.StringVar()
        self.path_var.set(str(Path.home() / "Gravações"))  # Pasta padrão
        
        ttk.Label(self.path_frame, text="Pasta de destino:").pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(self.path_frame, textvariable=self.path_var)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.browse_button = ttk.Button(self.path_frame, text="Procurar", command=self.select_folder)
        self.browse_button.pack(side=tk.LEFT)

        # Frame para controles de gravação
        self.control_frame = ttk.LabelFrame(self.main_frame, text="Controles", padding="5")
        self.control_frame.pack(fill=tk.X, pady=(0, 10))

        # Botões
        self.button_frame = ttk.Frame(self.control_frame)
        self.button_frame.pack(fill=tk.X, pady=5)

        self.record_button = ttk.Button(self.button_frame, text="Gravar", command=self.start_recording)
        self.record_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = ttk.Button(self.button_frame, text="Pausar", command=self.pause_recording, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(self.button_frame, text="Parar", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Status
        self.status_var = tk.StringVar(value="Status: Pronto")
        self.status_label = ttk.Label(self.control_frame, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X, pady=5)

        # Barra de som
        self.volume_bar = ttk.Progressbar(self.control_frame, orient='horizontal', length=300, mode='determinate')
        self.volume_bar.pack(pady=10)
        self.volume_label = ttk.Label(self.control_frame, text="Volume")
        self.volume_label.pack()

        # Frame para o gráfico
        self.graph_frame = ttk.Frame(self.main_frame)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)

        # Criar pasta padrão se não existir
        os.makedirs(self.path_var.get(), exist_ok=True)

    def select_folder(self):
        try:
            folder = filedialog.askdirectory(
                parent=self.root,
                initialdir=self.path_var.get(),
                title='Selecione a pasta para salvar as gravações'
            )
            if folder:
                self.path_var.set(folder)
                os.makedirs(folder, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao selecionar pasta: {str(e)}")

    def start_recording(self):
        global is_recording, is_paused, frames
        
        if not self.validate_folder():
            return
            
        try:
            speakers = sc.all_speakers()
            if not speakers:
                messagebox.showerror("Erro", "Nenhum dispositivo de áudio encontrado.")
                return
                
            is_recording = True
            is_paused = False
            frames = []
            
            self.record_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.NORMAL)
            self.status_var.set("Status: Gravando...")
            
            threading.Thread(target=self.record_audio, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar gravação: {str(e)}")

    def validate_folder(self):
        folder_path = self.path_var.get()
        try:
            os.makedirs(folder_path, exist_ok=True)
            test_file = os.path.join(folder_path, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Erro de acesso à pasta: {str(e)}")
            return False

    def record_audio(self):
        global frames, is_recording
        try:
            speakers = sc.all_speakers()
            default_speaker = speakers[0]
            
            with default_speaker.recorder(samplerate=sample_rate) as mic:
                while is_recording:
                    if not is_paused:
                        data = mic.record(int(sample_rate * 0.1))
                        frames.append(data)
                        volume = np.abs(data).mean() * 100
                        self.update_volume_bar(volume)
                    time.sleep(0.05)
        except Exception as e:
            is_recording = False
            error_message = f"Erro na gravação: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Erro", error_message))
        finally:
            self.root.after(0, self.update_ui_after_stop)

    def update_volume_bar(self, volume):
        self.root.after(0, lambda: self.volume_bar.config(value=min(volume, 100)))

    def pause_recording(self):
        global is_paused
        is_paused = not is_paused
        if is_paused:
            self.pause_button.config(text="Continuar")
            self.status_var.set("Status: Pausado")
        else:
            self.pause_button.config(text="Pausar")
            self.status_var.set("Status: Gravando...")

    def stop_recording(self):
        global is_recording
        if is_recording:
            is_recording = False
            try:
                if frames:
                    filepath = self.generate_filename()
                    self.save_audio(filepath)
                    self.plot_waveform(filepath)
                    self.status_var.set(f"Status: Gravação salva em: {os.path.basename(filepath)}")
                    messagebox.showinfo("Sucesso", f"Gravação salva em:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")
            finally:
                self.update_ui_after_stop()

    def update_ui_after_stop(self):
        self.record_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.DISABLED)
        self.pause_button.config(text="Pausar")
        self.status_var.set("Status: Pronto")
        self.volume_bar['value'] = 0  # Correção aqui

    def generate_filename(self):
        folder = self.path_var.get()
        counter = 1
        while True:
            filepath = os.path.join(folder, f"gravacao_{counter}.wav")
            if not os.path.exists(filepath):
                return filepath
            counter += 1

    def save_audio(self, filepath):
        if not frames:
            raise ValueError("Nenhum áudio gravado")
            
        audio_data = np.concatenate(frames, axis=0)
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            audio_data_int = (audio_data * 32767).astype(np.int16)
            wf.writeframes(audio_data_int.tobytes())

    def plot_waveform(self, filepath):
        try:
            with wave.open(filepath, 'rb') as wf:
                n_frames = wf.getnframes()
                data = np.frombuffer(wf.readframes(n_frames), dtype=np.int16)
                if wf.getnchannels() == 2:
                    data = data[::2]
                time = np.linspace(0, len(data) / sample_rate, num=len(data))

            for widget in self.graph_frame.winfo_children():
                widget.destroy()

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(time, data)
            ax.set_title("Forma de Onda do Áudio")
            ax.set_xlabel("Tempo (segundos)")
            ax.set_ylabel("Amplitude")
            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar gráfico: {str(e)}")

def main():
    try:
        root = tk.Tk()
        app = AudioRecorderGUI(root)
        
        def on_closing():
            if is_recording:
                if messagebox.askyesno("Confirmar", "Uma gravação está em andamento. Deseja sair?"):
                    app.stop_recording()
                    root.destroy()
            else:
                root.destroy()
                
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao iniciar aplicação: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
