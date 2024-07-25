import unittest
import os
from download import download_video_audio


class DownloadVideoAudio(unittest.TestCase):
    """
    Tests for the download.py module, specifically the download_video_audio function.
    """

    # def test_file(self):
    #     # Arrange
    #     url = "https://www.youtube.com/watch?v=SZorAJ4I-sA"
    #     output_path = "./downloads/audio/Transformers, explained: Understand the model behind GPT, BERT, and T5.mp4"

    #     # Act
    #     download_video_audio(url)

    #     # Assert
    #     if self.assertTrue(os.path.exists(output_path)):
    #         os.remove(output_path)

    def test_filename_with_invalid_characters(self):
        # Arrange
        url = "https://www.youtube.com/watch?v=SZorAJ4I-sA"
        expected_filename = "Transformers, explained Understand the model behind GPT, BERT, and T5"

        # Act
        _, filename = download_video_audio(url)

        # Assert
        self.assertEqual(filename, expected_filename)


if __name__ == "__main__":
    unittest.main()
