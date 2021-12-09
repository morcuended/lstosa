from datetime import datetime


def test_finished_assignments(sequence_list):
    from osa.report import finished_assignments

    finished_dict = finished_assignments(sequence_list)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    assert finished_dict["END"] == now
    assert finished_dict["NIGHT"] == "2020_01_17"
    assert finished_dict["TELESCOPE"] == "LST1"
    assert finished_dict["RAW_GB"] == 0
    assert finished_dict["FILES_RAW"] == 25
    assert finished_dict["SEQUENCES"] == 3


def test_history(base_test_dir):
    from osa.report import history

    run = "01800"
    prod_id = "v1.0.0"
    program = "r0_to_dl1"
    input_file = "r0_to_dl1_01800.fits"
    input_card = "r0_dl1.config"
    rc = 0
    history_file = base_test_dir / "r0_to_dl1_01800.history"
    date_string = datetime.utcnow().strftime("%a %b %d %X UTC %Y")

    history(run, prod_id, program, input_file, input_card, rc, history_file)

    logged_string = f"01800 r0_to_dl1 v1.0.0 {date_string} " \
        "r0_to_dl1_01800.fits r0_dl1.config 0\n"

    assert history_file.exists()
    assert history_file.read_text() == logged_string