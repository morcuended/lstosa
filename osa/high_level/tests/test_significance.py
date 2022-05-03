import subprocess as sp


def test_significance(
        dl2_merged,
        run_summary_file,
        r0_data,
        run_catalog,
        drs4_time_calibration_files,
        systematic_correction_files,
        pedestal_ids_file,
):

    for file in dl2_merged:
        assert file.exists()

    assert run_summary_file.exists()
    assert run_catalog.exists()

    for file in r0_data:
        assert file.exists()

    for file in drs4_time_calibration_files:
        assert file.exists()

    for file in systematic_correction_files:
        assert file.exists()

    assert pedestal_ids_file.exists()

    output = sp.run(
        ["theta2_significance", "-d", "2020_01_17", "-s", "LST1"],
        text=True,
        stdout=sp.PIPE,
        stderr=sp.PIPE
    )
    assert output.returncode == 0
    assert "Source: MadeUpSource, runs: [1808]" in output.stderr.splitlines()[-1]