"""
Unittest for pravda.src.utils
@license: GPLv3
"""
import logging
import unittest

from unittest import mock

from utils import get_args, get_bits, get_logger, get_rand_chars, get_video_from_youtube, sha_256


class UtilsTests(unittest.TestCase):
    """
    Test class for pravda.src.utils
    """
    @classmethod
    def setUpClass(cls) -> None:
        """ Set up common data for all tests. """

        cls.test_string = 'tests'
        cls.test_int = 3
        cls.args_write = ['/app/src/main.py', '-i', 'https://test.test', '-l', 'en', '-w', '-m', 'test']
        cls.args_read = ['/app/src/main.py', '-i', 'https://test.test', '-l', 'en', '-r']

    def test_get_args_write(self):
        """ Test src.utils.get_args function in write mode. """

        with mock.patch('sys.argv', self.args_write):
            args = get_args()

            self.assertTrue(args.input and args.lang and args.write and args.message)

    def test_get_args_read(self):
        """ Test src.utils.get_args function in read mode. """

        with mock.patch('sys.argv', self.args_read):
            args = get_args()

            self.assertTrue(args.input and args.lang and args.read)

    def test_init_logging(self):
        """
        Test src.utils.get_logger function.
        """

        logger = get_logger()

        self.assertTrue(logger)
        self.assertIsInstance(logger, logging.Logger)

    def test_sha_256(self) -> None:
        """ Test src.utils.sha_256 function. """

        result = sha_256(self.test_string)
        expected = '59830ebc3a4184110566bf1a290d08473dfdcbd492ce498b14cd1a5e2fa2e441'

        self.assertIsInstance(result, str)
        self.assertEqual(result, expected)
        self.assertEqual(len(result), 64)
        self.assertTrue(int(result, 16))

    def test_get_rand_chars(self) -> None:
        """ Test src.utils.get_rand_chars function. """

        result = get_rand_chars(self.test_int)

        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 3)
        self.assertTrue(result.isalnum())

    def test_get_bits(self) -> None:
        """
        Test src.utils.get_bits function.
        """

        result = get_bits(self.test_string)
        expected = [
            0, 1, 1, 1, 0, 1, 0, 0,  # t
            0, 1, 1, 0, 0, 1, 0, 1,  # e
            0, 1, 1, 1, 0, 0, 1, 1,  # s
            0, 1, 1, 1, 0, 1, 0, 0,  # t
            0, 1, 1, 1, 0, 0, 1, 1   # s
        ]

        self.assertIsInstance(result, list)
        self.assertEqual(result, expected)
        self.assertTrue(all(b in {0, 1} for b in result))

    def test_get_video_from_youtube(self):
        """ Test src.utils.get_video_from_youtube function. """
        logger = get_logger()
        get_video_from_youtube(logger, 'https://youtu.be/-npFIQSm27s')

    @classmethod
    def tearDownClass(cls) -> None:
        """ Tear down at the end of all tests. """

        mock.patch.stopall()
