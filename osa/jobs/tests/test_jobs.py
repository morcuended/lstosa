import os
from pathlib import Path

from osa.configs import options

test_data = Path(os.getenv("OSA_TEST_DATA", "extra"))
datasequence_history_file = test_data / "history_files/sequence_LST1_04185.0010.history"
calibration_history_file = test_data / "history_files/sequence_LST1_04183.history"


def test_historylevel():
    from osa.jobs.job import historylevel

    options.dl1_prod_id = "tailcut84"
    options.dl2_prod_id = "model1"

    level, rc = historylevel(datasequence_history_file, "DATA")
    assert level == 0
    assert rc == 0

    level, rc = historylevel(calibration_history_file, "PEDCALIB")
    assert level == 0
    assert rc == 0

    options.dl1_prod_id = "tailcut84"
    options.dl2_prod_id = "model2"

    level, rc = historylevel(datasequence_history_file, "DATA")
    assert level == 1
    assert rc == 0


def test_createjobtemplate(sequence_list):
    from osa.jobs.job import createjobtemplate

    options.simulate = True
    for sequence in sequence_list:
        createjobtemplate(sequence)


def test_preparejobs(sequence_list):
    from osa.jobs.job import preparejobs

    options.simulate = True
    preparejobs(sequence_list)
