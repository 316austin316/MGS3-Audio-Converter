import wave

def write_to_wav(pcm_data, file_path, channel_count, sample_rate):
    with wave.open(file_path, 'w') as wav_file:
        wav_file.setnchannels(channel_count)
        wav_file.setsampwidth(2)  # Assuming 16-bit samples
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
