"""
pravda
@license: GPLv3
"""

import logging
import re
import os
import random

from datetime import datetime, timedelta
from typing import List, Tuple

import ffmpeg

from utils import get_bits, get_rand_chars, get_srt_from_youtube, get_video_from_youtube


def get_timing(srt_file: str) -> Tuple[List[datetime], List[int]]:
    """
    Given an SRT file path, processes all the information regarding the times a subtitle is displayed and returns a list
    with all timing.
    :param srt_file: Path to the input SRT file.
    """

    datetimes = []
    pointers = []

    with open(srt_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

        for line in lines:
            line = line.strip()

            if re.search(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})?', line):  # If line starts with HH:MM:SS,mmm.
                # Extract times foreach line.
                from_str = line.split()[0]
                to_str = line.split()[2]

                # Convert to datetime objects.
                from_dt = datetime.strptime(from_str, '%H:%M:%S,%f')
                to_dt = datetime.strptime(to_str, '%H:%M:%S,%f')

                datetimes += [from_dt, to_dt]

                # Take only last milisecond from "from_ms" and "to_ms".
                from_ms = int(from_str[-1])
                to_ms = int(to_str[-1])

                pointers += [from_ms, to_ms]

    return datetimes, pointers


def get_random_positions(logger: logging.Logger, hashed_pass: str, pointers_len: int, bits_len: int) -> List[int]:
    """
    Given a seed, it returns a pseudo-random list of N integers in the range from 0 to the number defined by the
    variable pointers_len, where N is the number defined in the variable bits_len.
    :param logger: Program logger.
    :param hashed_pass: Password SHA-256 hash used as seed in the random number generator.
    :param pointers_len: Length of the array of pointers.
    :param bits_len: Bit length of the message.
    """

    logger.debug('Getting random positions by password, num of pointers and num of bits in message.')

    random.seed(hashed_pass)

    return random.sample(range(0, pointers_len), bits_len)


def get_new_datetimes(
        logger: logging.Logger, datetimes: List[datetime], pointers: List[int], msg_bits: List[int],
        rand_positions: List[int]
) -> List[datetime]:
    """
    Given a seed, returns a pseudo-random list of N integers in the range from 0 to number of bits stored in the
    variable msg_bits.
    :param logger: Program logger.
    :param datetimes: List with all datetimes extracted from subtitles.
    :param pointers: List with all pointers from subtitules to work.
    :param msg_bits: List with the bits of the message.
    :param rand_positions: Pseudo-random list of integers.
    """

    logger.debug('Getting new timing for subtitles.')

    new_datetimes = datetimes[:]

    for i, bin_flag in enumerate(msg_bits):
        rand_position = rand_positions[i]
        pointer = pointers[rand_position]
        dt_index = rand_position
        dt_previous = new_datetimes[dt_index - 1] if dt_index > 0 else None
        dt_current = new_datetimes[dt_index]
        dt_next = new_datetimes[dt_index + 1] if dt_index < len(new_datetimes) - 1 else None
        dt_new = dt_current

        if pointer % 2 != bin_flag:
            if dt_previous is None or dt_next is None or dt_previous <= dt_current <= dt_next:
                if not dt_index % 2:  # Even (from datetime)
                    dt_new = dt_current + timedelta(microseconds=1000)
                else:  # Odd (to datetime)
                    dt_new = dt_current - timedelta(microseconds=1000)

        new_datetimes[dt_index] = dt_new

    return new_datetimes


def generate_new_srt(logger: logging.Logger, srt_file: str, new_srt_file: str, new_datetimes: List[datetime]) -> None:
    """
    Given an SRT file with the subtitles and a list with the new milliseconds, create a new SRT file with the modified
    times.
    :param logger: Program logger.
    :param srt_file: Path to the input SRT file.
    :param new_srt_file: Path to the new SRT file.
    :param new_datetimes: List with the new datetimes of the subtitles.
    """

    logger.debug(f'Generating new {new_srt_file} subtitles file.')

    with open(srt_file, 'r', encoding='utf-8') as file:
        with open(new_srt_file, 'w', encoding='utf-8') as new_file:
            lines = file.readlines()
            count = 0

            for line in lines:
                line = line.strip()

                if re.search(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})?', line):  # If line starts with HH:MM:SS,mmm.
                    new_from_dt = f'{new_datetimes[count].strftime("%H:%M:%S,%f")[:-3]}'
                    new_to_dt = f'{new_datetimes[count + 1].strftime("%H:%M:%S,%f")[:-3]}'
                    new_line = f'{new_from_dt} --> {new_to_dt}'
                    count += 2
                    new_file.write(f'{new_line}\n')
                else:
                    new_file.write(f'{line}\n')

    os.remove(srt_file)


def generate_new_video_with_subtitles(logger: logging.Logger, input_video: str, srt_file: str) -> str:
    """
    Given an MP4 file and an SRT file with the subtitles, creates a new MP4 file with the new subtitles and returns the
    name of the generated file.
    :param logger: Program logger.
    :param input_video: Path to the input MP4 file.
    :param srt_file: Path to the input SRT file.
    """

    output_file = input_video.replace('.mp4', '_new.mp4')

    logger.debug(f'Generating new {output_file} video file with subtitles.')

    # Load the video/audio master.
    input_ffmpeg = ffmpeg.input(input_video)

    # Load the subtitle master.
    input_ffmpeg_sub = ffmpeg.input(srt_file)

    # Refer to the master audio, video and subtitles streams separately.
    video_stream = input_ffmpeg['v']
    audio_stream = input_ffmpeg['a']
    subtitles_stream = input_ffmpeg_sub['s']

    output_ffmpeg = ffmpeg.output(
        video_stream,
        audio_stream,
        subtitles_stream,
        output_file,
        vcodec='copy',
        acodec='copy',
        scodec='mov_text',
        loglevel='error'
    )

    # If the destination file already exists, overwrite it.
    output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)

    # Print the equivalent ffmpeg command we could run to perform the same action as above.
    # print(ffmpeg.compile(output_ffmpeg))

    ffmpeg.run(output_ffmpeg)

    return output_file


def get_srt_from_file(logger: logging.Logger, input_video: str) -> str:
    """
    Extract subtitles as SRT file from input video and returns output file name.
    :param logger: Program logger.
    :param input_video: Path to the input MP4 file.
    """

    output_file = input_video.replace('/mp4/', '/srt/').replace('_new.mp4', '.srt')

    logger.debug(f'Extracting {output_file} subtitles file from video file.')

    # Load the video/audio/subtitles master.
    input_ffmpeg = ffmpeg.input(input_video)

    # Refer to the master subtitles stream.
    input_subtitles = input_ffmpeg['s']

    output_ffmpeg = ffmpeg.output(
        input_subtitles,
        output_file,
        loglevel='error'
    )

    # If the destination file already exists, overwrite it.
    output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)

    # Print the equivalent ffmpeg command we could run to perform the same action as above.
    # print(ffmpeg.compile(output_ffmpeg))

    ffmpeg.run(output_ffmpeg)

    return output_file


def get_hidden_msg(rand_positions: List[int], pointers: List[int]) -> str:
    """
    Returns text plain message as string from hidden message.
    :param rand_positions: Pseudo-random list of integers.
    :param pointers: List with all pointers from subtitules to work.
    """

    bin_hidden_msg = ''

    for position in rand_positions:
        bin_hidden_msg += str(pointers[position] % 2)

    int_hidden_msg = int(bin_hidden_msg, 2)
    hidden_msg = int_hidden_msg.to_bytes(
        (int_hidden_msg.bit_length() + 7) // 8, 'big'
    ).replace(b'\a', b'').replace(b'\b', b'').replace(b'\n', b'').replace(b'\r', b'').replace(b'\t', b'')

    return hidden_msg.decode('ISO-8859-1')


def write(logger: logging.Logger, hashed_pass: str, msg: str, input_video: str, lang: str) -> None:
    """
    Method to hide a message in the subtitles from MP4 input file.
    :param logger: Program logger.
    :param hashed_pass: Password SHA-256 hash.
    :param msg: Raw message.
    :param input_video: Input video. Can be a URL from YouTube or local path to MP4 file.
    :param lang: Subtitle languaje, for example "en", "es", etc.
    """

    video_file = get_video_from_youtube(logger, input_video)
    srt_file = video_file.replace('/mp4/', '/srt/').replace('.mp4', '.srt')
    get_srt_from_youtube(logger, input_video, srt_file, lang)

    if lang.startswith('a.'):  # Only for autogenerated subtitles.

        # The autogenerated subtitles can sometimes be chaotic, and I have been able to verify that there can be
        # overlapping times and blank subtitles that are useless. Here I have decided to normalize the subtitle times
        # by generating them again with the FFmpeg tool.

        logger.debug('Autogenerated subtitles need to be normalized.')

        fixed_input_video = generate_new_video_with_subtitles(logger, video_file, srt_file)
        srt_file = get_srt_from_file(logger, fixed_input_video)
        os.remove(fixed_input_video)

    if os.path.isfile(srt_file):
        datetimes, pointers = get_timing(srt_file)
        max_chars = int(len(pointers) / 8)

        logger.debug(f'Using {len(msg)} of {max_chars} chars.')

        if len(msg) > max_chars:
            logger.error(f'For this video the maximum number of characters is {max_chars}.')

            os.remove(srt_file)
            os.remove(video_file)

            return

        rand_chars = get_rand_chars(max_chars - len(msg))
        msg += rand_chars
        msg_bits = get_bits(msg)
        rand_positions = get_random_positions(logger, hashed_pass, len(pointers), len(msg_bits))
        new_datetimes = get_new_datetimes(logger, datetimes, pointers, msg_bits, rand_positions)
        new_srt_file = srt_file.replace('.srt', '_stego.srt')

        generate_new_srt(logger, srt_file, new_srt_file, new_datetimes)
        generate_new_video_with_subtitles(logger, video_file, new_srt_file)
        os.remove(video_file)


def read(logger, hashed_pass: str, input_video: str, lang: str) -> None:
    """
    Method to read a hidden message in MP4 input file.
    :param logger: Program logger.
    :param hashed_pass: Password SHA-256 hash.
    :param input_video: Input video. Can be a URL from YouTube or local path to MP4 file.
    :param lang: Subtitle languaje, for example "en", "es", etc.
    """

    video_file = get_video_from_youtube(logger, input_video)
    srt_file = video_file.replace('/mp4/', '/srt/').replace('.mp4', '.srt')

    if input_video.startswith('http'):
        get_srt_from_youtube(logger, input_video, srt_file, lang)
    else:
        get_srt_from_file(logger, video_file)

    if os.path.isfile(srt_file):
        _, pointers = get_timing(srt_file)
        max_chars = int(len(pointers) / 8) * 8  # <-- Hey, it looks dirty but... no.
        rand_positions = get_random_positions(logger, hashed_pass, len(pointers), max_chars)
        hidden_msg = get_hidden_msg(rand_positions, pointers)

        os.remove(srt_file)

        print(hidden_msg)
