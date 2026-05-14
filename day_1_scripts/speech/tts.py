from mlx_audio.tts.generate import generate_audio

generate_audio(
    text="Hello World",
    model="mlx-community/chatterbox-turbo-fp16",
    file_prefix="output",
    audio_format="wav",
    play=True,
)
