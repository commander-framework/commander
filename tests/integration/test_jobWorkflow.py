import pytest


@pytest.mark.order(3)
def test_createJob():
    pass


@pytest.mark.order(4)
def test_agentCheckinNoJob():
    pass


@pytest.mark.order(5)
def test_assignJob():
    pass


@pytest.mark.order(6)
def test_fetchAndExecuteJob():
    pass


@pytest.mark.order(7)
def test_getJobHistory():
    pass
