"""
pravda
@license: GPLv3
"""
from utils import get_args, get_logger, sha_256
from pravda import write, read


if __name__ == '__main__':
    logger = get_logger()

    logger.info('Starting program.')

    ARGS = get_args()
    HASHED_PASS = sha_256(input('Password: '))

    if ARGS.write:
        write(logger=logger, hashed_pass=HASHED_PASS, msg=ARGS.message, input_video=ARGS.input, lang=ARGS.lang)
    elif ARGS.read:
        read(logger=logger, hashed_pass=HASHED_PASS, input_video=ARGS.input, lang=ARGS.lang)

    logger.info('Finish program.')
