from mlx_audio.tts.generate import generate_audio

generate_audio(
    text="""Hello, fellow travellers.
    You're here to learn how machines find their voice,
    and how they listen. It's a curious thing, teaching
    silicon to speak. But every great journey begins
    with a single, well-chosen word. Welcome.""",
    model="mlx-community/chatterbox-turbo-fp16",
    ref_audio="morgan-freeman-voice-sample.wav",
    file_prefix="morgan",
    audio_format="wav",
    play=True,
)
