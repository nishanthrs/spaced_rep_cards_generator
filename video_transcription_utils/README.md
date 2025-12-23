# Whisper Inference Framework Comparisons

## [Mac] [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)
* The superior model with fastest inference speed on Apple Silicon
* Absolutely incredible performance! Comparable to insanely-fast-whisper on GPUs: https://github.com/Vaibhavs10/insanely-fast-whisper
  * insanely-fast-whisper takes ~100 s on A100 80GB on 150 mins of audio.
  * mlx-whisper takes ~120 s on Mac M4 64GB on 120 mins of audio

## [Mac, GPU] [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
* Utilizes Apple Silicon, but definitely slower than mlx-whisper
* Takes ~170 s to transcribe ~120 mins of audio
* Also offers GPU support, haven't tried it out yet
* [Comparison b/w whisper.cpp and mlx-whisper](https://notes.billmill.org/link_blog/2024/08/mlx-whisper.html)

## [GPU] [whisper (huggingface transformers)](https://huggingface.co/docs/transformers/model_doc/whisper)
*TODO*

## [GPU] [whisper (OpenAI)](https://github.com/openai/whisper)
*TODO*

## [TPU] [whisper JAX](https://github.com/sanchit-gandhi/whisper-jax)
*TODO*
