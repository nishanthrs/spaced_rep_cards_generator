import argparse
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

import mlx_whisper

import yt_dlp


TranscriptionChunks = List[Dict[str, Any]]


class VideoTranscriptionUtils:
    def __init__(self, whisper_model_name: str = "large-v3-turbo"):
        """
        Whisper model names:
        1. MLX models: https://huggingface.co/collections/mlx-community/whisper
        2. whisper.cpp model names: https://github.com/ggml-org/whisper.cpp/blob/master/models/download-ggml-model.sh#L35
        """
        self.whisper_model_name = whisper_model_name

    def _find_file(self, ext: str) -> Optional[str]:
        """Find first file in curr dir with specific extension"""
        for file in list(filter(lambda f: os.path.isfile(f), os.listdir("."))):
            if file.endswith(ext):
                return file
        return None

    def _remove_file(self, ext: str) -> None:
        """Remove all files in curr dir of specific extension"""
        for file in list(filter(lambda f: os.path.isfile(f), os.listdir("."))):
            if file.endswith(ext):
                os.remove(file)

    def extract_audio_and_metadata_from_video(self, yt_url: str) -> str:
        """Download YT video as audio file"""
        try:
            result = subprocess.run(
                ["which", "ffmpeg"],
                capture_output=True,
                text=True,
            )
            ffmpeg_path = result.stdout.strip()
        except Exception:
            raise Exception(
                "ffmpeg not found in `which ffmpeg`. Please make sure it's installed and in the PATH."
            )

        yt_dlp_opts = {
            "format": "wav/bestaudio/best",
            "postprocessors": [
                {  # Extract audio using ffmpeg
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                }
            ],
            "prefer_ffmpeg": True,
            "audioquality": 0,
            "restrictfilenames": True,
            "writeinfojson": True,
            "ffmpeg_location": ffmpeg_path,
        }
        with yt_dlp.YoutubeDL(yt_dlp_opts) as ydl:
            error_code = ydl.download(yt_url)
            if error_code != 0:
                print(f"Error: {error_code} in downloading YT video: {yt_url}")

        audio_filepath = self._find_file(".wav")
        if audio_filepath is None:
            raise Exception("No audio filepath found!")
        metadata_filepath = self._find_file(".info.json")
        if metadata_filepath is None:
            raise Exception("No metadata filepath found!")
        return (audio_filepath, metadata_filepath)

    def transcribe_video_via_mlx_whisper(self, audio_filepath: str) -> None:
        """Transcribe audio from audio_filepath"""
        transcription_output = mlx_whisper.transcribe(
            audio_filepath,
            path_or_hf_repo=self.whisper_model_name,
        )
        for chunk in transcription_output:
            print(chunk)

    def transcribe_video_via_whisper_cpp(
        self, audio_filepath: str
    ) -> TranscriptionChunks:
        # TODO: Need to do setup work of checking if whisper.cpp is installed, installing it if it's not, cd'ing into the right directory, etc.
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

    # --------------------------------------------------------
    # MLX Whisper
    # Perf: currently takes ~120s for 115 mins video
    # --------------------------------------------------------

    # Download YT video as audio file and metadata as JSON
    video_transcription_utils = VideoTranscriptionUtils(
        whisper_model_name="mlx-community/whisper-turbo"
    )
    audio_filepath, metadata_filepath = (
        video_transcription_utils.extract_audio_and_metadata_from_video(url)
    )

    # Transcribe audio from audio_filepath
    start_time = time.time()
    video_transcription_utils.transcribe_video_via_mlx_whisper(audio_filepath)
    end_time = time.time()
    print(f"Time taken for MLX whisper: {end_time - start_time} seconds")

    # -------------------------------------------------------------------------
    # Whisper.cpp
    # Perf: currently takes ~192s for 115 mins video
    # TODO: Look into CoreML optimization for whisper.cpp; could make it faster
    # -------------------------------------------------------------------------

    # video_transcription_utils = VideoTranscriptionUtils(
    #     whisper_model_name="large-v3-turbo"
    # )
    # audio_filepath, metadata_filepath = (
    #     video_transcription_utils.extract_audio_and_metadata_from_video(url)
    # )
    # start_time_2 = time.time()
    # video_transcription_utils.transcribe_video_via_whisper_cpp(audio_filepath)
    # end_time_2 = time.time()
    # print(f"Time taken for whisper.cpp: {end_time_2 - start_time_2} seconds")


if __name__ == "__main__":
    main()
