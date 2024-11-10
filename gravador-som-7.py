import soundcard as sc
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import filedialog, messagebox
import wave
import threading
import os
import time
import sys

# Configurações iniciais
sample_rate = 44100  # Taxa de amostragem em Hz
frames = []  # Lista para armazenar os frames de áudio
is_recording = False
is_paused = False

# Função para selecionar a pasta de destino com tratamento de erro
def select_folder():
    try:
        # Garante que a janela principal está ativa
        root.lift()
        root.focus_force()
        
        # Tenta abrir o diálogo de seleção de pasta
        folder_selected = filedialog.askdirectory(
            title='Selecione a pasta para salvar as gravações',
            initialdir=os.path.expanduser("~")  # Começa na pasta do usuário
        )
        
        if folder_selected:
            # Verifica se a pasta existe e tem permissão de escrita
            if os.path.exists(folder_selected) and os.access(folder_selected, os.W_OK):
                file_path_entry.delete(0, tk.END)
                file_path_entry.insert(0, folder_selected)
            else:
                messagebox.showerror(
                    "Erro de Acesso",
                    "Não há permissão de escrita na pasta selecionada. Por favor, escolha outra pasta."
                )
    except Exception as e:
        messagebox.showerror(
            "Erro",
            f"Erro ao selecionar pasta: {str(e)}\nPor favor, tente novamente."
        )

# Função para verificar a pasta antes de iniciar a gravação
def validate_folder():
    folder_path = file_path_entry.get().strip()
    
    if not folder_path:
        messagebox.showerror("Erro", "Por favor, selecione uma pasta para salvar a gravação.")
        return False
        
    try:
        # Tenta criar a pasta se não existir
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        # Testa permissão de escrita criando um arquivo temporário
        test_file = os.path.join(folder_path, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return True
        
    except PermissionError:
        messagebox.showerror(
            "Erro de Permissão",
            "Sem permissão para escrever na pasta selecionada. Por favor, escolha outra pasta."
        )
        return False
    except Exception as e:
        messagebox.showerror(
            "Erro",
            f"Erro ao acessar a pasta: {str(e)}\nPor favor, selecione outra pasta."
        )
        return False

# Função para iniciar a gravação
def start_recording():
    global is_recording, is_paused, frames
    
    # Verificar se um diretório foi selecionado e é válido
    if not validate_folder():
        return
        
    try:
        # Verificar se há dispositivos de áudio disponíveis
        speakers = sc.all_speakers()
        if not speakers:
            messagebox.showerror(
                "Erro",
                "Nenhum dispositivo de saída de áudio encontrado.\n"
                "Verifique se há alto-falantes ou fones conectados."
            )
            return
            
        is_recording = True
        is_paused = False
        frames = []
        record_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        pause_button.config(state=tk.NORMAL)
        status_label.config(text="Status: Gravando...")
        threading.Thread(target=record_audio, daemon=True).start()
        
    except Exception as e:
        messagebox.showerror(
            "Erro",
            f"Erro ao iniciar gravação: {str(e)}\n"
            "Verifique se o dispositivo de áudio está funcionando corretamente."
        )

# Função para gravar o áudio do sistema com tratamento de erro
def record_audio():
    global frames, is_recording
    try:
        # Obter o speaker default do sistema
        speakers = sc.all_speakers()
        default_speaker = speakers[0]
        
        # Iniciar gravação do speaker
        with default_speaker.recorder(samplerate=sample_rate) as mic:
            while is_recording:
                if not is_paused:
                    try:
                        data = mic.record(int(sample_rate * 0.1))
                        frames.append(data)
                    except Exception as e:
                        # Se houver erro na gravação, notificar e parar
                        is_recording = False
                        messagebox.showerror(
                            "Erro de Gravação",
                            f"Erro ao gravar áudio: {str(e)}\n"
                            "A gravação foi interrompida."
                        )
                        break
                time.sleep(0.05)
                
    except Exception as e:
        is_recording = False
        messagebox.showerror(
            "Erro",
            f"Erro ao acessar dispositivo de áudio: {str(e)}\n"
            "Verifique se o dispositivo está conectado e funcionando."
        )
    finally:
        # Garantir que a interface seja atualizada mesmo em caso de erro
        root.after(0, update_ui_after_stop)

def update_ui_after_stop():
    record_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    pause_button.config(state=tk.DISABLED)
    pause_button.config(text="Pausar")
    status_label.config(text="Status: Pronto")

# Função para pausar a gravação
def pause_recording():
    global is_paused
    try:
        is_paused = not is_paused
        if is_paused:
            pause_button.config(text="Continuar")
            status_label.config(text="Status: Pausado")
        else:
            pause_button.config(text="Pausar")
            status_label.config(text="Status: Gravando...")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao pausar/continuar: {str(e)}")

# Função para parar a gravação e salvar o áudio
def stop_recording():
    global is_recording
    if is_recording:
        is_recording = False
        folder_path = file_path_entry.get().strip()
        
        if folder_path and frames:
            try:
                filepath = generate_sequential_filename(folder_path)
                save_audio(filepath)
                plot_waveform(filepath)
                status_label.config(text=f"Status: Gravação salva em: {os.path.basename(filepath)}")
                messagebox.showinfo(
                    "Sucesso",
                    f"Gravação salva com sucesso em:\n{filepath}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Erro",
                    f"Erro ao salvar arquivo: {str(e)}\n"
                    "Verifique as permissões da pasta e o espaço em disco."
                )
        
        update_ui_after_stop()

# Função para gerar nomes de arquivo sequenciais
def generate_sequential_filename(folder_path):
    base_name = "system_audio"
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
    
    try:
        # Concatenar todos os frames
        audio_data = np.concatenate(frames, axis=0)
        
        # Converter para formato WAV
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            audio_data_int = (audio_data * 32767).astype(np.int16)
            wf.writeframes(audio_data_int.tobytes())
    except Exception as e:
        raise Exception(f"Erro ao salvar arquivo WAV: {str(e)}")

# Função para plotar o gráfico do som na janela Tkinter
def plot_waveform(filepath):
    try:
        with wave.open(filepath, 'rb') as wf:
            n_frames = wf.getnframes()
            data = np.frombuffer(wf.readframes(n_frames), dtype=np.int16)
            if wf.getnchannels() == 2:
                data = data[::2]
            time = np.linspace(0, len(data) / sample_rate, num=len(data))

        # Limpar gráfico anterior
        for widget in graph_frame.winfo_children():
            widget.destroy()

        # Criar a figura do gráfico
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(time, data)
        ax.set_title("Forma de Onda do Áudio do Sistema")
        ax.set_xlabel("Tempo (segundos)")
        ax.set_ylabel("Amplitude")
        plt.tight_layout()

        # Exibir o gráfico na interface Tkinter
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao criar gráfico: {str(e)}")

# Criação da interface gráfica com tratamento de erro
try:
    root = tk.Tk()
    root.title("Gravador de Som do Sistema")
    root.geometry("800x600")
    
    # Configurar ícone se disponível
    try:
        if os.name == 'nt':  # Windows
            root.iconbitmap('icon.ico')  # Substitua pelo caminho do seu ícone
    except:
        pass  # Ignora erro se não encontrar o ícone
    
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

    # Configurar tratamento de fechamento da janela
    def on_closing():
        if is_recording:
            if messagebox.askyesno("Confirmar Saída", "Uma gravação está em andamento. Deseja realmente sair?"):
                stop_recording()
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Executa a interface
    root.mainloop()

except Exception as e:
    messagebox.showerror(
        "Erro Fatal",
        f"Erro ao iniciar aplicação: {str(e)}\n"
        "O programa será encerrado."
    )
    sys.exit(1)