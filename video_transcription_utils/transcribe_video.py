import argparse
import os
import subprocess
from typing import Any, Dict, List

import mlx_whisper

import yt_dlp


TranscriptionChunks = List[Dict[str, Any]]

FILE_DIR = "/tmp"
PREFERRED_CODEC = "wav"


class VideoTranscriptionUtils:
    def __init__(self, whisper_model_name: str = "large-v3-turbo"):
        """
        Whisper model names:
        1. MLX models: https://huggingface.co/collections/mlx-community/whisper
        2. whisper.cpp model names: https://github.com/ggml-org/whisper.cpp/blob/master/models/download-ggml-model.sh#L35
        """
        self.whisper_model_name = whisper_model_name

    def _remove_file(self, ext: str) -> None:
        for file in list(filter(lambda f: os.path.isfile(f), os.listdir("."))):
            if file.endswith(ext):
                os.remove(file)

    def _get_ffmpeg_path(self) -> str:
        try:
            result = subprocess.run(
                ["which", "ffmpeg"],
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except Exception:
            raise Exception(
                "ffmpeg not found in `which ffmpeg`. Please make sure it's installed and in the PATH."
            )

    def extract_audio_and_metadata_from_video(self, yt_url: str) -> str:
        ffmpeg_path = self._get_ffmpeg_path()

        def download_audio_processor_hook(d):
            global audio_filepath
            global info_json_filepath
            if d['status'] == 'finished':
                audio_filepath = f"{os.path.splitext(d['info_dict']['filename'])[0]}.{PREFERRED_CODEC}"
                info_json_filepath = d['info_dict']['infojson_filename']

        yt_dlp_opts = {
            "format": "wav/bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": PREFERRED_CODEC,
                }
            ],
            "prefer_ffmpeg": True,
            "audioquality": 0,
            "restrictfilenames": True,
            "writeinfojson": True,
            "ffmpeg_location": ffmpeg_path,
            "outtmpl": os.path.join(FILE_DIR, "%(title)s.%(ext)s"),
            "postprocessor_hooks": [download_audio_processor_hook]
        }
        with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl:
            error_code = ydl.download(yt_url)
            if error_code != 0:
                raise Exception(
                    f"Error: {error_code} in downloading YT video: {yt_url}"
                )

        return (audio_filepath, info_json_filepath)

    def transcribe_video_via_mlx_whisper(self, audio_filepath: str, output_dir: str) -> str:
        print(f"Transcribing audio file: {audio_filepath}")
        transcription_data = mlx_whisper.transcribe(
            audio_filepath,
            path_or_hf_repo=self.whisper_model_name,
        )
        transcription_filepath = os.path.join(
            output_dir,
            f"{os.path.splitext(audio_filepath)[0]}.txt",
        )
        with open(transcription_filepath, "w") as f:
            f.write(transcription_data["text"])
        return transcription_filepath

    def transcribe_video_via_whisper_cpp(
        self, audio_filepath: str
    ) -> TranscriptionChunks:
        """TODO: There's a lot of installation and setup work to get this running:
        Check if whisper.cpp is installed, install it if it's not,
        installing dependencies (ffmpeg, ffmprobe, cmake), cd'ing into the right directory, etc.
        """
        subprocess.run(
            [
                "/Users/nishanthrs/SideProjects/whisper.cpp/build/bin/whisper-cli",
                "-m",
                "/Users/nishanthrs/SideProjects/whisper.cpp/models/ggml-large-v3-turbo.bin",
                "-f",
                audio_filepath,
            ],
            capture_output=True,
            text=True,
        )


def main():
    # Setup CLI
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--url",
        nargs=1,
        type=str,
        help="video URL to transcribe",
        required=True,
    )
    args = parser.parse_args()
    url = args.url

    video_transcription_utils = VideoTranscriptionUtils(
        whisper_model_name="mlx-community/whisper-large-v3-turbo"
    )
    audio_filepath, metadata_filepath = (
        video_transcription_utils.extract_audio_and_metadata_from_video(url)
    )

    # Transcribe audio from audio_filepath
    video_transcription_utils.transcribe_video_via_mlx_whisper(audio_filepath)



if __name__ == "__main__":
    main()
