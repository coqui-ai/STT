import unittest
from argparse import Namespace
from pathlib import Path

from coqui_stt_training.util import audio


def from_here(path):
    here = Path(__file__)
    return here.parent / path


class TestValidateReadAudio(unittest.TestCase):
    def test_flac(self):
        audio_path = from_here("../data/smoke_test/LDC93S1.flac")
        audio_type = audio.get_loadable_audio_type_from_extension(audio_path.suffix)
        result = audio.read_audio(audio_type, str(audio_path))
        self.assertIsInstance(result[0], audio.AudioFormat)

    def test_wav(self):
        audio_path = from_here("../data/smoke_test/LDC93S1.wav")
        audio_type = audio.get_loadable_audio_type_from_extension(audio_path.suffix)
        result = audio.read_audio(audio_type, str(audio_path))
        self.assertIsInstance(result[0], audio.AudioFormat)

    def test_ogg_opus(self):
        audio_path = from_here("../data/smoke_test/LDC93S1.opus")
        audio_type = audio.get_loadable_audio_type_from_extension(audio_path.suffix)
        result = audio.read_audio(audio_type, str(audio_path))
        self.assertIsInstance(result[0], audio.AudioFormat)


class TestValidateReadDuration(unittest.TestCase):
    def test_flac(self):
        audio_path = from_here("../data/smoke_test/LDC93S1.flac")
        audio_type = audio.get_loadable_audio_type_from_extension(audio_path.suffix)
        result = audio.read_duration(audio_type, str(audio_path))
        self.assertIsInstance(result, float)

    def test_wav(self):
        audio_path = from_here("../data/smoke_test/LDC93S1.wav")
        audio_type = audio.get_loadable_audio_type_from_extension(audio_path.suffix)
        result = audio.read_duration(audio_type, str(audio_path))
        self.assertIsInstance(result, float)

    def test_ogg_opus(self):
        audio_path = from_here("../data/smoke_test/LDC93S1.opus")
        audio_type = audio.get_loadable_audio_type_from_extension(audio_path.suffix)
        result = audio.read_duration(audio_type, str(audio_path))
        self.assertIsInstance(result, float)


if __name__ == "__main__":
    unittest.main()
