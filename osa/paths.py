"""Handle the paths of the analysis products."""

import logging
from pathlib import Path
from astropy.table import Table

from osa.configs import options
from osa.configs.config import cfg
from osa.utils.logging import myLogger
from osa.utils import utils
from osa.configs.config import DEFAULT_CFG

log = myLogger(logging.getLogger(__name__))

__all__ = [
    "get_time_calibration_file",
    "get_calibration_file",
    "get_drs4_pedestal_file",
    "get_systematic_correction_file",
    "pedestal_ids_file_exists",
    "get_run_date",
    "drs4_pedestal_exists",
    "calibration_file_exists",
    "sequence_calibration_files",
    "destination_dir",
    "datacheck_directory",
    "get_datacheck_files",
    "get_drive_file",
    "get_summary_file",
    "get_pedestal_ids_file",
    "DATACHECK_WEB_BASEDIR",
    "DEFAULT_CFG",
    "create_source_directories",
    "analysis_path"
]


DATACHECK_WEB_BASEDIR = Path(cfg.get("WEBSERVER", "DATACHECK"))


def analysis_path(tel) -> Path:
    """
    Path of the running_analysis directory for a certain date

    Returns
    -------
    directory : Path
        Path of the running_analysis directory for a certain date
    """
    log.debug(f"Getting analysis path for telescope {tel}")
    flat_date = utils.date_to_dir(options.date)
    options.prod_id = utils.get_prod_id()
    directory = Path(cfg.get(tel, "ANALYSIS_DIR")) / flat_date / options.prod_id

    if not options.simulate:
        directory.mkdir(parents=True, exist_ok=True)
    else:
        log.debug("SIMULATE the creation of the analysis directory.")

    log.debug(f"Analysis directory: {directory}")
    return directory


def get_run_date(run_id: int, merged_run_summaries_file: Path) -> str:
    """
    Return the date (YYYYMMDD) when the given run was taken. The search for this date
    is done by looking at the date corresponding to each run in the merged run summaries file.
    """
    summary_table = Table.read(merged_run_summaries_file)
    date_string = summary_table[summary_table['run_id']==run_id]['date'][0]
    return date_string.replace("-", "")


def get_time_calibration_file(run_id: int) -> Path:
    """
    Return the time calibration file corresponding to a calibration run taken before
    the run id given. If run_id is smaller than the first run id from the time
    calibration files, return the first time calibration file available, which
    corresponds to 1625.
    """
    time_calibration_dir = Path(cfg.get("LST1", "TIMECALIB_DIR"))
    file_list = sorted(time_calibration_dir.rglob("pro/time_calibration.Run*.h5"))

    if not file_list:
        raise IOError("No time calibration file found")

    for file in file_list:
        run_in_list = int(file.name.split(".")[1].strip("Run"))
        if run_id < 1625:
            time_calibration_file = file_list[0]
        elif run_in_list <= run_id:
            time_calibration_file = file
        else:
            break

    return time_calibration_file.resolve()


def get_systematic_correction_file(date: str) -> Path:
    """
    Return the systematic correction file for a given date.

    Parameters
    ----------
    date : str
        Date in the format YYYYMMDD.

    Notes
    -----
    The search for the proper systematic correction file is based on
    lstchain/scripts/onsite/onsite_create_calibration_file.py
    """
    sys_dir = Path(cfg.get("LST1", "SYSTEMATIC_DIR"))

    # Search for the first sys correction file before the run, if nothing before,
    # use the first found
    dir_list = sorted(sys_dir.rglob('*/pro/ffactor_systematics*'))
    if not dir_list:
        raise IOError(
            f"No systematic correction file found for production pro in {sys_dir}\n"
        )
    sys_date_list = sorted([file.parts[-3] for file in dir_list], reverse=True)
    selected_date = next(
        (day for day in sys_date_list if day <= date), sys_date_list[-1]
    )

    return Path(
        f"{sys_dir}/{selected_date}/pro/ffactor_systematics_{selected_date}.h5"
    ).resolve()


def get_drs4_pedestal_file(run_id: int, merged_run_summaries_file: Path) -> Path:
    """
    Return the drs4 pedestal file corresponding to a given run id
    regardless of the date when the run was taken.
    """
    drs4_pedestal_dir = Path(cfg.get("LST1", "PEDESTAL_DIR"))
    date = get_run_date(run_id, merged_run_summaries_file)
    file = drs4_pedestal_dir / date / f"pro/drs4_pedestal.Run{run_id:05d}.0000.h5"
    return file.resolve()


def get_calibration_file(run_id: int, merged_run_summaries_file: Path) -> Path:
    """
    Return the drs4 pedestal file corresponding to a given run id
    regardless of the date when the run was taken.
    """
    calib_dir = Path(cfg.get("LST1", "CALIB_DIR"))
    date = get_run_date(run_id, merged_run_summaries_file)
    file = calib_dir / date / f"pro/calibration_filters_52.Run{run_id:05d}.0000.h5"
    return file.resolve()


def pedestal_ids_file_exists(run_id: int) -> bool:
    """Look for the files with pedestal interleaved event identification."""
    pedestal_ids_dir = Path(cfg.get("LST1", "PEDESTAL_FINDER_DIR"))
    file_list = sorted(pedestal_ids_dir.rglob(f"pedestal_ids_Run{run_id:05d}.*.h5"))
    return bool(file_list)


def drs4_pedestal_exists(run_id: int) -> bool:
    """Return true if drs4 pedestal file was already produced."""
    file = get_drs4_pedestal_file(run_id, merged_run_summaries_file)
    return file.exists()


def calibration_file_exists(run_id: int) -> bool:
    """Return true if calibration file was already produced."""
    file = get_calibration_file(run_id, merged_run_summaries_file)
    return file.exists()


def get_drive_file(date: str) -> Path:
    """Return the drive file corresponding to a given date in YYYYMMDD format."""
    yy_mm_dd = utils.date_in_yymmdd(date)
    drive_dir = Path(cfg.get("LST1", "DRIVE_DIR"))
    return (drive_dir / f"drive_log_{yy_mm_dd}.txt").resolve()


def get_summary_file(date) -> Path:
    """Return the run summary file corresponding to a given date in YYYYMMDD format."""
    run_summary_dir = Path(cfg.get("LST1", "RUN_SUMMARY_DIR"))
    return (run_summary_dir / f"RunSummary_{date}.ecsv").resolve()


def get_pedestal_ids_file(run_id: int, date: str) -> Path:
    """
    Return the pedestal ids file path corresponding to a given run
    from a date in format YYYYMMDD.
    """
    pedestal_ids_dir = Path(cfg.get("LST1", "PEDESTAL_FINDER_DIR")) / date
    file = pedestal_ids_dir / f"pedestal_ids_Run{run_id:05d}.{{subruns:04d}}.h5"
    return file.resolve()


def sequence_calibration_files(sequence_list, merged_run_summaries_file: Path):
    """Build names of the calibration files for each sequence in the list."""
    flat_date = utils.date_to_dir(options.date)

    for sequence in sequence_list:

        if not sequence.parent_list:
            drs4_pedestal_run_id = sequence.previousrun
            pedcal_run_id = sequence.run
        else:
            drs4_pedestal_run_id = sequence.parent_list[0].previousrun
            pedcal_run_id = sequence.parent_list[0].run

        # Assign the calibration files to the sequence object
        sequence.pedestal = get_drs4_pedestal_file(drs4_pedestal_run_id, merged_run_summaries_file)
        sequence.calibration = get_calibration_file(pedcal_run_id, merged_run_summaries_file)
        sequence.time_calibration = get_time_calibration_file(pedcal_run_id)
        sequence.systematic_correction = get_systematic_correction_file(flat_date)


def get_datacheck_files(pattern: str, directory: Path) -> list:
    """Return a list of files matching the pattern."""
    return sorted(directory.glob(pattern))


def datacheck_directory(data_type: str, date: str) -> Path:
    """Returns the path to the datacheck directory given the data type."""
    if data_type in {"PEDESTAL", "CALIB"}:
        directory = Path(cfg.get("LST1", f"{data_type}_DIR")) / date / "pro/log"
    elif data_type == "DL1AB":
        directory = destination_dir("DL1AB", create_dir=False)
    elif data_type == "LONGTERM":
        directory = Path(cfg.get("LST1", f"{data_type}_DIR")) / options.prod_id / date
    else:
        raise ValueError(f"Unknown data type: {data_type}")
    return directory


def destination_dir(concept: str, create_dir: bool = True) -> Path:
    """
    Create final destination directory for each data level.
    See Also osa.utils.register_run_concept_files

    Parameters
    ----------
    concept : str
        Expected: MUON, DL1AB, DATACHECK, DL2, PEDESTAL, CALIB, TIMECALIB
    create_dir : bool
        Set it to True (default) if you want to create the directory.
        Otherwise, it just returns the path

    Returns
    -------
    path : pathlib.Path
        Path to the directory
    """
    nightdir = utils.date_to_dir(options.date)

    if concept == "MUON":
        directory = (
            Path(cfg.get(options.tel_id, concept + "_DIR")) / nightdir / options.prod_id
        )
    elif concept in {"DL1AB", "DATACHECK"}:
        directory = (
            Path(cfg.get(options.tel_id, concept + "_DIR"))
            / nightdir
            / options.prod_id
            / options.dl1_prod_id
        )
    elif concept in {"DL2", "DL3"}:
        directory = (
            Path(cfg.get(options.tel_id, concept + "_DIR"))
            / nightdir
            / options.prod_id
            / options.dl2_prod_id
        )
    elif concept in {"PEDESTAL", "CALIB", "TIMECALIB"}:
        directory = (
            Path(cfg.get(options.tel_id, concept + "_DIR"))
            / nightdir
            / options.calib_prod_id
        )
    elif concept == "HIGH_LEVEL":
        directory = (
            Path(cfg.get(options.tel_id, concept + "_DIR"))
            / nightdir
            / options.prod_id
        )
    else:
        log.warning(f"Concept {concept} not known")
        directory = None

    if not options.simulate and create_dir:
        log.debug(f"Destination directory created for {concept}: {directory}")
        directory.mkdir(parents=True, exist_ok=True)
    else:
        log.debug(f"SIMULATING creation of final directory for {concept}")

    return directory


def create_source_directories(source_list: list, cuts_dir: Path):
    """Create a subdirectory for each source."""
    for source in source_list:
        if source is not None:
            source_dir = cuts_dir / source
            source_dir.mkdir(parents=True, exist_ok=True)
