from converter import constants
from logging.handlers import RotatingFileHandler
from converter.convert import ConvertCsvToXml
import logging
import sys


def check_python_version():
    major = sys.version_info.major
    minor = sys.version_info.minor
    minor_min = 6
    minor_max = 9
    if major == 3 and minor_min <= minor <= minor_max:
        return
    raise AssertionError(f"your python version = {major}.{minor}. Please use python 3.{minor_min} to 3.{minor_max}")


def setup_logging() -> None:
    """Adds 3 configured handlers to the root logger: stream, one_time_file_handler, log_rotating_file."""

    # https://stackoverflow.com/questions/30861524/logging-basicconfig-not-creating-log-file-when-i-run-in-pycharm
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)

    # handler: stream
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"))

    # handler: rotating file
    rotating_file_handler = RotatingFileHandler(
        filename=constants.LOG_FILE_PATH.as_posix(),
        mode="a",  # we append to this file
        maxBytes=1024 * 1024 * 1,  # 1 MB
        backupCount=1,  # rotate within one file
    )
    rotating_file_handler.setLevel(logging.INFO)
    rotating_file_handler.setFormatter(
        logging.Formatter(fmt="%(asctime)s %(filename)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S",)
    )

    # handler: one time file (since rotating file is not created when I&A runs this app(?!?!)
    one_time_file_path = constants.LOG_FILE_PATH.parent / "one_time.log"
    one_time_file_handler = logging.FileHandler(filename=one_time_file_path.as_posix(), mode="w")
    one_time_file_handler.setLevel(logging.INFO)
    one_time_file_handler.setFormatter(
        logging.Formatter(fmt="%(asctime)s %(filename)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S",)
    )

    # root logger (with 3 handlers)
    root_logger = logging.getLogger()
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(one_time_file_handler)
    root_logger.addHandler(rotating_file_handler)
    root_logger.setLevel(min([handler.level for handler in root_logger.handlers]))
    root_logger.info("setup logging done")


if __name__ == "__main__":
    check_python_version()
    constants.check_constants()
    setup_logging()
    logger = logging.getLogger(__name__)

    latest_gis_export_peilmarges_csv = constants.get_last_gis_export_peilmarges_csv()
    assert latest_gis_export_peilmarges_csv.is_file()
    data_converter = ConvertCsvToXml(orig_csv_path=latest_gis_export_peilmarges_csv)
    data_converter.run()
    logger.info("shutting down app")
