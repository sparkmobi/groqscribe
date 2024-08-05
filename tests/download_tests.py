import unittest
import os
from download import download_video_audio


class TestDownloadVideoAudio(unittest.TestCase):

    def setUp(self):
        self.url = 'https://www.youtube.com/watch?v=eduYP83eZwE'
        self.url_1 = 'https://www.youtube.com/watch?v=SZorAJ4I-sA'
        self.expected_file_extension = '.ogg'
        self.file_path = None

    def tearDown(self):
        if self.file_path and os.path.exists(self.file_path):
            os.remove(self.file_path)

    def test_filename_with_invalid_characters(self):
        try:
            # Arrange
            expected_filename = "Transformers, explained Understand the model behind GPT, BERT, and T5"

            # Act
            self.filepath, filename = download_video_audio(self.url_1)

            # Assert
            self.assertTrue(os.path.exists(self.filepath))
            self.assertEqual(filename, expected_filename)
        except Exception as error:
            self.fail(f"An error occurred: {str(error)}")

    def test_file_size_exceeds_limit(self):
        try:
            # Act
            self.file_path, _ = download_video_audio(self.url)

            # Assert
            self.assertIsNotNone(self.file_path,
                                 "File path should not be None")
            self.assertTrue(os.path.exists(self.file_path),
                            "File should exist")
            self.assertEqual(
                os.path.splitext(self.file_path)[1],
                self.expected_file_extension)
        except Exception as e:
            self.fail(f"Test failed due to an unexpected exception: {e}")


if __name__ == '__main__':
    unittest.main()
