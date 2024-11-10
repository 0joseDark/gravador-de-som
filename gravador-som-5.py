import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import filedialog, messagebox
import wave
import threading
import os

# Configurações iniciais
duration = 10  # Duração da gravação em segundos
sample_rate = 44100  # Taxa de amostragem em Hz
frames = []  # Lista para armazenar os frames de áudio
is_recording = False
is_paused = False

# Função para selecionar a pasta de destino
def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        file_path_entry.delete(0, tk.END)
        file_path_entry.insert(0, folder_selected)

# Função para iniciar a gravação
def start_recording():
    global is_recording, is_paused, frames
    
    # Verificar se um diretório foi selecionado
    if not file_path_entry.get():
        messagebox.showerror("Erro", "Por favor, selecione uma pasta para salvar a gravação.")
        return
        
    is_recording = True
    is_paused = False
    frames = []  # Redefine frames como uma lista vazia para cada gravação
    record_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    pause_button.config(state=tk.NORMAL)
    status_label.config(text="Status: Gravando...")
    threading.Thread(target=record_audio).start()

# Função para gravar o áudio
def record_audio():
    global frames, is_recording
    def callback(indata, frame_count, time_info, status):
        if is_recording and not is_paused:
            frames.append(indata.copy())
            
    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, callback=callback):
            while is_recording:
                sd.sleep(100)  # Dormir por 100ms para não sobrecarregar a CPU
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gravar áudio: {str(e)}")
        stop_recording()

# Função para pausar a gravação
def pause_recording():
    global is_paused
    is_paused = not is_paused
    if is_paused:
        pause_button.config(text="Continuar")
        status_label.config(text="Status: Pausado")
    else:
        pause_button.config(text="Pausar")
        status_label.config(text="Status: Gravando...")

# Função para parar a gravação e salvar o áudio
def stop_recording():
    global is_recording
    if is_recording:
        is_recording = False
        folder_path = file_path_entry.get()
        
        if folder_path and frames:
            try:
                filepath = generate_sequential_filename(folder_path)
                save_audio(filepath)
                plot_waveform(filepath)
                status_label.config(text=f"Status: Gravação salva em: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar arquivo: {str(e)}")
        
        # Resetar botões
        record_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)
        pause_button.config(state=tk.DISABLED)
        pause_button.config(text="Pausar")

# Função para gerar nomes de arquivo sequenciais
def generate_sequential_filename(folder_path):
    base_name = "recording"
    extension = ".wav"
    counter = 1
    filepath = os.path.join(folder_path, f"{base_name}_{counter}{extension}")
    while os.path.exists(filepath):
        counter += 1
        filepath = os.path.join(folder_path, f"{base_name}_{counter}{extension}")
    return filepath

# Função para salvar o áudio gravado num ficheiro WAV
def save_audio(filepath):
    if not frames:
        raise ValueError("Nenhum áudio foi gravado")
    
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    audio_data = np.concatenate(frames, axis=0)
    wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
    wf.close()

# Função para plotar o gráfico do som na janela Tkinter
def plot_waveform(filepath):
    with wave.open(filepath, 'rb') as wf:
        n_frames = wf.getnframes()
        data = np.frombuffer(wf.readframes(n_frames), dtype=np.int16)
        time = np.linspace(0, len(data) / sample_rate, num=len(data))

    # Limpar gráfico anterior
    for widget in graph_frame.winfo_children():
        widget.destroy()

    # Criar a figura do gráfico
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(time, data)
    ax.set_title("Forma de Onda do Áudio")
    ax.set_xlabel("Tempo (segundos)")
    ax.set_ylabel("Amplitude")
    plt.tight_layout()

    # Exibir o gráfico na interface Tkinter
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Interface gráfica
root = tk.Tk()
root.title("Gravador de Som")
root.geometry("800x600")

# Frame principal
main_frame = tk.Frame(root, padx=10, pady=10)
main_frame.pack(fill=tk.BOTH, expand=True)

# Frame para controles
control_frame = tk.Frame(main_frame)
control_frame.pack(fill=tk.X, pady=(0, 10))

# Campo para definir o caminho da pasta onde o arquivo será salvo
path_frame = tk.Frame(control_frame)
path_frame.pack(fill=tk.X, pady=5)

tk.Label(path_frame, text="Pasta de destino:").pack(side=tk.LEFT)
file_path_entry = tk.Entry(path_frame)
file_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
browse_button = tk.Button(path_frame, text="Procurar", command=select_folder)
browse_button.pack(side=tk.LEFT)

# Frame para botões
button_frame = tk.Frame(control_frame)
button_frame.pack(fill=tk.X, pady=5)

record_button = tk.Button(button_frame, text="Gravar", command=start_recording)
record_button.pack(side=tk.LEFT, padx=5)

pause_button = tk.Button(button_frame, text="Pausar", command=pause_recording, state=tk.DISABLED)
pause_button.pack(side=tk.LEFT, padx=5)

stop_button = tk.Button(button_frame, text="Parar", command=stop_recording, state=tk.DISABLED)
stop_button.pack(side=tk.LEFT, padx=5)

# Label de status
status_label = tk.Label(control_frame, text="Status: Pronto", anchor='w')
status_label.pack(fill=tk.X, pady=5)

# Frame para o gráfico
graph_frame = tk.Frame(main_frame)
graph_frame.pack(fill=tk.BOTH, expand=True)

# Executa a interface
root.mainloop()