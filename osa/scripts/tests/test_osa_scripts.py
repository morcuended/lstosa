import datetime
import os
import subprocess as sp
from pathlib import Path
from textwrap import dedent

import pytest

from osa.configs import options
from osa.configs.config import cfg
from osa.scripts.closer import is_sequencer_successful, is_finished_check

ALL_SCRIPTS = [
    "sequencer",
    "closer",
    "calibrationsequence",
    "copy_datacheck",
    "datasequence",
    "show_run_summary",
    "provprocess",
    "simulate_processing",
]


def remove_provlog():
    log_file = Path("prov.log")
    if log_file.is_file():
        log_file.unlink()


def run_program(*args):
    result = sp.run(args, stdout=sp.PIPE, stderr=sp.STDOUT, encoding="utf-8", check=True)

    if result.returncode != 0:
        raise ValueError(
            f"Running {args[0]} failed with return code {result.returncode}"
            f", output: \n {result.stdout}"
        )

    return result


@pytest.mark.parametrize("script", ALL_SCRIPTS)
def test_all_help(script):
    """Test for all scripts if at least the help works."""
    run_program(script, "--help")


def test_simulate_processing():

    remove_provlog()
    rc = run_program("simulate_processing", "-p", "--force")
    assert rc.returncode == 0

    prov_dl1_path = Path("./test_osa/test_files0/DL1/20200117/v0.1.0/tailcut84/log")
    prov_dl2_path = Path("./test_osa/test_files0/DL2/20200117/v0.1.0/tailcut84_model1/log")
    prov_file_dl1 = prov_dl1_path / "r0_to_dl1_01807_prov.log"
    prov_file_dl2 = prov_dl2_path / "r0_to_dl2_01807_prov.log"
    json_file_dl1 = prov_dl1_path / "r0_to_dl1_01807_prov.json"
    json_file_dl2 = prov_dl2_path / "r0_to_dl2_01807_prov.json"
    pdf_file_dl1 = prov_dl1_path / "r0_to_dl1_01807_prov.pdf"
    pdf_file_dl2 = prov_dl2_path / "r0_to_dl2_01807_prov.pdf"

    assert prov_file_dl1.exists()
    assert prov_file_dl2.exists()
    assert json_file_dl1.exists()
    assert json_file_dl2.exists()
    assert pdf_file_dl1.exists()
    assert pdf_file_dl2.exists()

    rc = run_program("simulate_processing", "-p")
    assert rc.returncode == 0

    remove_provlog()
    rc = run_program("simulate_processing", "-p")
    assert rc.returncode == 0


def test_simulated_sequencer():
    rc = run_program("sequencer", "-c", "cfg/sequencer.cfg", "-d", "2020_01_17", "-s", "-t", "LST1")
    assert rc.returncode == 0
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    assert rc.stdout == dedent(
        f"""\
        ================================== Starting sequencer.py at {now} UTC for LST, Telescope: LST1, Night: 2020_01_17 ==================================
        Tel   Seq  Parent  Type      Run   Subruns  Source  Wobble  Action  Tries  JobID  State  Host  CPU_time  Walltime  Exit  DL1%  MUONS%  DL1AB%  DATACHECK%  DL2%  
        LST1    0  None    PEDCALIB  1805  5        None    None    None    None   None   None   None  None      None      None  None  None    None    None        None  
        LST1    1       0  DATA      1807  11       None    None    None    None   None   None   None  None      None      None     0       0       0           0     0  
        LST1    2       0  DATA      1808  9        None    None    None    None   None   None   None  None      None      None     0       0       0           0     0  
        """)


def test_sequencer(sequence_file_list):
    for sequence_file in sequence_file_list:
        assert sequence_file.exists()


def test_autocloser(running_analysis_dir):
    result = run_program(
        "python",
        "osa/scripts/autocloser.py",
        "-c",
        "cfg/sequencer.cfg",
        "-d",
        "2020_01_17",
        "-t",
        "LST1",
    )
    assert os.path.exists(running_analysis_dir)
    assert result.stdout.split()[-1] == "Exit"
    assert os.path.exists(
        "./test_osa/test_files0/running_analysis/20200117/v0.1.0/"
        "AutoCloser_Incidences_tmp.txt"
    )


def test_closer(r0_dir, running_analysis_dir, test_observed_data, test_calibration_data):
    # First assure that the end of night flag is not set and remove it otherwise
    night_finished_flag = Path(
        "./test_osa/test_files0/OSA/Closer/20200117/v0.1.0/NightFinished.txt"
    )
    if night_finished_flag.exists():
        night_finished_flag.unlink()

    assert r0_dir.exists()
    assert running_analysis_dir.exists()
    for cal_file in test_calibration_data:
        assert cal_file.exists()
    for obs_file in test_observed_data:
        assert obs_file.exists()

    run_program(
        "closer", "-c", "cfg/sequencer.cfg", "-y", "-v", "-t", "-d", "2020_01_17", "LST1"
    )
    conda_env_export = running_analysis_dir / "log" / "conda_env.yml"
    closed_seq_file = running_analysis_dir / "sequence_LST1_01805.closed"

    # Check that files have been moved to their final destinations
    assert os.path.exists(
        "./test_osa/test_files0/DL1/20200117/v0.1.0/muons_LST-1.Run01808.0011.fits"
    )
    assert os.path.exists(
        "./test_osa/test_files0/DL1/20200117/v0.1.0/tailcut84/dl1_LST-1.Run01808.0011.h5"
    )
    assert os.path.exists(
        "./test_osa/test_files0/DL1/20200117/v0.1.0/tailcut84/"
        "datacheck_dl1_LST-1.Run01808.0011.h5"
    )
    assert os.path.exists(
        "./test_osa/test_files0/DL2/20200117/v0.1.0/tailcut84_model1/"
        "dl2_LST-1.Run01808.0011.h5"
    )
    assert os.path.exists(
        "./test_osa/test_files0/calibration/20200117/v01/"
        "drs4_pedestal.Run01804.0000.fits"
    )
    assert os.path.exists(
        "./test_osa/test_files0/calibration/20200117/v01/"
        "calibration.Run01805.0000.h5"
    )
    assert os.path.exists(
        "./test_osa/test_files0/calibration/20200117/"
        "v01/time_calibration.Run01805.0000.h5"
    )
    # Assert that the link to dl1 and muons files have been created
    assert os.path.islink(
        "./test_osa/test_files0/running_analysis/20200117/"
        "v0.1.0/muons_LST-1.Run01808.0011.fits"
    )
    assert os.path.islink(
        "./test_osa/test_files0/running_analysis/20200117/"
        "v0.1.0/dl1_LST-1.Run01808.0011.h5"
    )

    assert night_finished_flag.exists()
    assert conda_env_export.exists()
    assert closed_seq_file.exists()


def test_datasequence(running_analysis_dir):
    drs4_file = "drs4_pedestal.Run00001.0000.fits"
    calib_file = "calibration.Run00002.0000.hdf5"
    timecalib_file = "time_calibration.Run00002.0000.hdf5"
    drive_file = "drive_log_20200117.txt"
    runsummary_file = "RunSummary_20200117.ecsv"
    prod_id = "v0.1.0"
    run_number = "00003.0000"
    options.directory = running_analysis_dir

    output = run_program(
        "datasequence",
        "-c",
        "cfg/sequencer.cfg",
        "-d",
        "2020_01_17",
        "-s",
        "--prod-id",
        prod_id,
        drs4_file,
        calib_file,
        timecalib_file,
        drive_file,
        runsummary_file,
        run_number,
        "LST1",
    )
    assert output.returncode == 0


def test_calibrationsequence(r0_data, running_analysis_dir):
    drs4_file = "drs4_pedestal.Run01805.0000.fits"
    calib_file = "calibration.Run01806.0000.hdf5"
    runsummary_file = "RunSummary_20200117.ecsv"
    prod_id = "v0.1.0"
    drs4_run_number = "01805"
    pedcal_run_number = "01806"
    options.directory = running_analysis_dir

    # Check that the R0 files corresponding to calibration run exists
    for files in r0_data:
        assert os.path.exists(files)

    output = run_program(
        "calibrationsequence",
        "-c",
        "cfg/sequencer.cfg",
        "-d",
        "2020_01_17",
        "-s",
        "--prod-id",
        prod_id,
        drs4_file,
        calib_file,
        drs4_run_number,
        pedcal_run_number,
        runsummary_file,
        "LST1",
    )
    assert output.returncode == 0


def test_is_sequencer_successful(run_summary):
    seq_tuple = is_finished_check(run_summary)
    assert is_sequencer_successful(seq_tuple) is True


def test_drs4_pedestal_command(r0_data, test_calibration_data):
    from osa.scripts.calibrationsequence import drs4_pedestal_command
    input_file = r0_data[0]
    output_file = test_calibration_data[1]
    command = drs4_pedestal_command(input_file, output_file)
    expected_command = [
        "lstchain_data_create_drs4_pedestal_file",
        f"--input-file={input_file}",
        f"--output-file={output_file}",
        "--max-events=20000",
        "--overwrite"
    ]
    assert command == expected_command


def test_calibration_file_command(r0_data, test_calibration_data, running_analysis_dir):
    from osa.scripts.calibrationsequence import calibration_file_command
    options.directory = running_analysis_dir
    calibration_run = "01806"
    input_file = r0_data[2]  # Corresponds to run 01806
    calibration_output_file = Path(test_calibration_data[0])
    drs4_pedestal_file = Path(test_calibration_data[1])
    ffactor_systematics = cfg.get("lstchain", "ffactor_systematics")
    calib_config = cfg.get("lstchain", "calibration_config")
    run_summary = Path("extra/monitoring/RunSummary") / "RunSummary_20200117.ecsv"
    time_file_basename = Path(calibration_output_file).name.replace("calibration", "time_calibration")
    time_file = Path(running_analysis_dir) / time_file_basename
    log_dir = running_analysis_dir / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"calibration.Run{calibration_run}.0000.log"

    command = calibration_file_command(
        calibration_run,
        calib_config,
        drs4_pedestal_file,
        calibration_output_file,
        run_summary
    )

    expected_command = [
        "lstchain_create_calibration_file",
        f"--input_file={input_file}",
        f"--output_file={calibration_output_file}",
        "--EventSource.default_trigger_type=tib",
        f"--LSTCalibrationCalculator.systematic_correction_path={ffactor_systematics}",
        f"--LSTEventSource.EventTimeCalculator.run_summary_path={run_summary}",
        f"--LSTEventSource.LSTR0Corrections.drs4_time_calibration_path={time_file}",
        f"--LSTEventSource.LSTR0Corrections.drs4_pedestal_path={drs4_pedestal_file}",
        f"--log-file={log_file}",
        f"--config={calib_config}"
    ]
    assert command == expected_command


def test_time_calibration_command(r0_dir, test_calibration_data, running_analysis_dir):
    from osa.scripts.calibrationsequence import time_calibration_command
    options.directory = running_analysis_dir
    calibration_run = "01806"
    input_file = r0_dir.parent / "*/LST-1.1.Run01806.000*.fits.fz"
    calibration_output_file = Path(test_calibration_data[0])
    drs4_pedestal_file = Path(test_calibration_data[1])
    run_summary = Path("extra/monitoring/RunSummary") / "RunSummary_20200117.ecsv"
    time_file_basename = Path(calibration_output_file).name.replace("calibration", "time_calibration")
    time_calibration_file = Path(running_analysis_dir) / time_file_basename

    command = time_calibration_command(
        calibration_run,
        time_calibration_file,
        drs4_pedestal_file,
        run_summary
    )

    expected_command = [
        "lstchain_data_create_time_calibration_file",
        f"--input-file={input_file}",
        f"--output-file={time_calibration_file}",
        f"--pedestal-file={drs4_pedestal_file}",
        f"--run-summary-path={run_summary}",
        "--max-events=53000"
    ]
    assert command == expected_command
