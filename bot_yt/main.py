import os
import sys
import tempfile
from pytubefix import YouTube
import ffmpeg
import openai

# Configura a API key da OpenAI a partir da variável de ambiente
openai.api_key = os.getenv("OPENAI_API_KEY")


def download_video(url: str, output_dir: str) -> str:
    """
    Baixa o vídeo do YouTube e retorna o caminho para o arquivo baixado.
    """
    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    out_path = stream.download(output_path=output_dir, filename='video')
    return out_path


def extract_audio(video_path: str, output_dir: str) -> str:
    """
    Usa ffmpeg para converter o vídeo em um arquivo de áudio WAV.
    """
    audio_path = os.path.join(output_dir, 'audio.wav')
    ffmpeg.input(video_path).output(audio_path, format='wav',
                                    acodec='pcm_s16le', ac=1, ar='16k').overwrite_output().run(quiet=True)
    return audio_path


def transcribe_audio(audio_path: str) -> str:
    """
    Usa o modelo Whisper da OpenAI para transcrever o áudio.
    """
    with open(audio_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file
        )
    return transcript['text']


def summarize_text(text: str) -> str:
    """
    Envia o texto transcrito ao ChatGPT para obter um resumo.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil que resume conteúdos de vídeos do YouTube."},
            {"role": "user", "content": f"Resuma o seguinte texto:\n\n{text}"}
        ],
        max_tokens=300,
        temperature=0.7
    )
    summary = response.choices[0].message.content.strip()
    return summary


def main():
    if len(sys.argv) != 2:
        print("Uso: python main.py <URL_DO_VIDEO>")
        sys.exit(1)

    url = sys.argv[1]

    with tempfile.TemporaryDirectory() as tmpdir:
        print("Baixando vídeo...")
        video_file = download_video(url, tmpdir)

        print("Extraindo áudio...")
        audio_file = extract_audio(video_file, tmpdir)

        print("Transcrevendo áudio...")
        transcript = transcribe_audio(audio_file)

        print("Gerando resumo...")
        summary = summarize_text(transcript)

        print("\n=== RESUMO ===\n")
        print(summary)


if __name__ == "__main__":
    main()
