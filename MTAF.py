
import tkinter as tk
from tkinter import filedialog, messagebox
import struct
import os
import mtaf_decoder
import wav_encoder
from mtaf_decoder import decode_mtaf_audio


def read_mtaf(file_path):
    try:
        with open(file_path, 'rb') as file:
            # Read and validate the signature
            if file.read(4) != b'MTAF':
                raise ValueError("Not a valid MTAF file")

            # Skip to HEAD chunk (0x40)
            file.seek(0x40)

            # Validate HEAD chunk
            if file.read(4) != b'HEAD':
                raise ValueError("HEAD chunk not found")
            
            # Read HEAD chunk size and validate (expected size 0xB0)
            if struct.unpack('<I', file.read(4))[0] != 0xB0:
                raise ValueError("Unexpected HEAD chunk size")
            
            # Reading additional metadata (volume and pan)
            file.seek(0x50)  # Assuming volume is at 0x50 and pan at 0x54
            volume = struct.unpack('<I', file.read(4))[0]
            pan = struct.unpack('<H', file.read(2))[0]
            

            # Skip to channel count (0x61)
            file.seek(0x61)
            channel_count = 2 * struct.unpack('<B', file.read(1))[0]

            # Read loop start and end points
            file.seek(0x58)
            loop_start = struct.unpack('<I', file.read(4))[0]
            loop_end = struct.unpack('<I', file.read(4))[0]

            # Validate loop points
            file.seek(0x64)
            if loop_start // 0x100 != struct.unpack('<I', file.read(4))[0] or \
               loop_end // 0x100 != struct.unpack('<I', file.read(4))[0]:
                raise ValueError("Invalid loop points")
            
            # Read loop flag (1 byte) and validate
            file.seek(0x70)
            loop_flag = struct.unpack('<B', file.read(1))[0] & 1
            
            # Hardcoded sample rate
            sample_rate = 48000

            # Interleave block size (for stereo interleaving)
            interleave_block_size = 0x110 // 2

            # Read DATA chunk header
            file.seek(0x7f8)
            if file.read(4) != b'DATA':
                raise ValueError("DATA chunk not found")
            file.seek(0x7fc)
            data_size = struct.unpack('<I', file.read(4))[0]

            # DATA chunk starts at 0x800
            start_offset = 0x800

            print("MTAF File Parsed Successfully")
            print("Channel Count:", channel_count)
            print("Loop Start:", loop_start)
            print("Loop End:", loop_end)
            print("Data Start Offset:", start_offset)
            print("Sample Rate:", sample_rate)
            print("Interleave Block Size:", interleave_block_size)
            print("Loop Flag:", loop_flag)
            print("Volume:", volume)
            print("Pan:", pan)
            print("Data Size:", data_size)
            
        return {
            "channel_count": channel_count,
            "loop_start": loop_start,
            "loop_end": loop_end,
            "start_offset": start_offset,
            "sample_rate": sample_rate,
            "interleave_block_size": interleave_block_size,
            "loop_flag": loop_flag,
            "volume": volume,
            "pan": pan,
            "data_size": data_size
        }

    except IOError as e:
        print("Error opening or reading the file:", e)

# Example usage
def open_file():
    file_path = filedialog.askopenfilename(title="Open MTAF File", filetypes=[("MTAF Files", "*.mtaf")])
    if file_path:
        mtaf_data = read_mtaf(file_path)

        with open(file_path, 'rb') as file:
            file.seek(mtaf_data["start_offset"])
            raw_audio_data = file.read(mtaf_data["data_size"])

        pcm_data = []
        for channel in range(mtaf_data["channel_count"]):
            channel_pcm = decode_mtaf_audio(
                frame=raw_audio_data,
                channel=channel,
                first_sample=0,
                samples_to_do=mtaf_data["data_size"] // mtaf_data["interleave_block_size"],
                interleave_block_size=mtaf_data["interleave_block_size"]
            )
            pcm_data.append(channel_pcm)

        # Correct place to call interleave_channels
        combined_pcm_data = interleave_channels(pcm_data, mtaf_data["channel_count"])

        # Export interleaved PCM data to a file
        pcm_file_path = "output_pcm.raw"
        with open(pcm_file_path, "wb") as pcm_file:
            for sample in combined_pcm_data:
                pcm_file.write(struct.pack('<h', sample))

        # Convert PCM data to bytes and write to WAV
        pcm_bytes = b''.join(struct.pack('<h', sample) for sample in combined_pcm_data)
        wav_file_path = "output.wav"
        wav_encoder.write_to_wav(pcm_bytes, wav_file_path, mtaf_data["channel_count"], mtaf_data["sample_rate"])

        result_label.config(text=f"Converted to PCM and WAV: {pcm_file_path}, {wav_file_path}")

# Function to interleave PCM data from multiple channels
def interleave_channels(pcm_data, channel_count):
    combined_pcm = []
    for i in range(len(pcm_data[0])):
        for channel in range(channel_count):
            combined_pcm.append(pcm_data[channel][i])
    return combined_pcm

# Set up the tkinter GUI
root = tk.Tk()
root.title("MTAF File Parser")

open_button = tk.Button(root, text="Open MTAF File", command=open_file)
open_button.pack(pady=10)

result_label = tk.Label(root, text="", justify=tk.LEFT)
result_label.pack(pady=10)

root.mainloop()



# Set up the tkinter GUI
root = tk.Tk()
root.title("MTAF File Parser")

open_button = tk.Button(root, text="Open MTAF File", command=open_file)
open_button.pack(pady=10)

result_label = tk.Label(root, text="", justify=tk.LEFT)
result_label.pack(pady=10)

root.mainloop()
