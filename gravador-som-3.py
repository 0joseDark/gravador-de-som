import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
import wave
import threading
import os

# Configurações iniciais
duration = 10  # Duração da gravação em segundos
sample_rate = 44100  # Taxa de amostragem em Hz
frames = []  # Lista para armazenar os frames de áudio
is_recording = False
is_paused = False

# Função para iniciar a gravação
def start_recording():
    global is_recording, is_paused, frames
    is_recording = True
    is_paused = False
    frames = []  # Redefine frames como uma lista vazia para cada gravação
    threading.Thread(target=record_audio).start()

# Função para gravar o áudio
def record_audio():
    global frames
    def callback(indata, frame_count, time_info, status):
        if not is_paused:
            frames.append(indata.copy())
    with sd.InputStream(samplerate=sample_rate, channels=1, callback=callback):
        sd.sleep(int(duration * 1000))

# Função para pausar a gravação
def pause_recording():
    global is_paused
    is_paused = not is_paused

# Função para parar a gravação e salvar o áudio
def stop_recording():
    global is_recording
    is_recording = False
    folder_path = file_path_entry.get()
    if folder_path:
        filepath = generate_sequential_filename(folder_path)
        save_audio(filepath)
        open_file(filepath)

# Função para gerar nomes de arquivo sequenciais
def generate_sequential_filename(folder_path):
    base_name = "recording"
    extension = ".wav"
    counter = 1
    filepath = os.path.join(folder_path, f"{base_name}_{counter}{extension}")
    while os.path.exists(filepath):  # Verifica se o arquivo já existe
        counter += 1
        filepath = os.path.join(folder_path, f"{base_name}_{counter}{extension}")
    return filepath

# Função para salvar o áudio gravado num ficheiro WAV
def save_audio(filepath):
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join([np.int16(frame * 32767) for frame in frames]))
    wf.close()
    plot_waveform(filepath)

# Função para plotar o gráfico do som usando Matplotlib
def plot_waveform(filepath):
    with wave.open(filepath, 'rb') as wf:
        n_frames = wf.getnframes()
        data = np.frombuffer(wf.readframes(n_frames), dtype=np.int16)
        time = np.linspace(0, len(data) / sample_rate, num=len(data))
    plt.plot(time, data)
    plt.title("Waveform")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.show()

# Função para abrir o arquivo de som
def open_file(filepath):
    os.startfile(filepath)

# Interface gráfica
root = tk.Tk()
root.title("Gravador de Som")

# Campo para definir o caminho da pasta onde o arquivo será salvo
tk.Label(root, text="Caminho da pasta para salvar:").pack()
file_path_entry = tk.Entry(root, width=40)
file_path_entry.pack()

# Botões de gravação, pausa e sair
record_button = tk.Button(root, text="Gravar", command=start_recording)
record_button.pack()

pause_button = tk.Button(root, text="Pausa", command=pause_recording)
pause_button.pack()

stop_button = tk.Button(root, text="Sair", command=root.quit)
stop_button.pack()

root.mainloop()
