from src import defs

def test_def_can_load():
    assert defs.get_job_def("etl_job")
