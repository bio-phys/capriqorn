import numpy as np

import pytest
from numpy.testing import assert_array_equal

from capriqorn.lib import refstruct


@pytest.fixture
def circle():
    # create a 2D circle embdded in 3D
    t = np.linspace(0, 2 * np.pi)
    x = np.cos(t) * 10
    y = np.sin(t) * 10
    z = np.zeros(t.shape)
    return np.vstack((x, y, z)).T


@pytest.fixture
def half_circle(circle):
    n_atoms = len(circle)
    half_circle = circle.copy()
    half_circle[:n_atoms // 2] += 30
    return half_circle


def test_queryDistance_same(circle):
    assert np.all(refstruct.queryDistance(circle, circle, 2))


def test_queryDistance_all_close(circle):
    xyz = circle + np.random.uniform(high=0.01, size=circle.shape)
    assert np.all(refstruct.queryDistance(xyz, circle, 2))


@pytest.mark.parametrize('R', (0, 2))
def test_queryDistance_none_close(R, circle):
    xyz = circle + np.ones(shape=circle.shape) * 10
    assert np.all(~refstruct.queryDistance(xyz, circle, R))


def test_queryDistance_some_close(circle, half_circle):
    query = refstruct.queryDistance(half_circle, circle, 1)
    n_atoms = len(circle)
    assert np.all(query[n_atoms // 2:])
    assert np.all(~query[:n_atoms // 2])


def test_selectBody(circle, half_circle):
    n_atoms = len(circle)
    body = refstruct.selectBody(circle, half_circle, 1)
    assert_array_equal((np.arange(n_atoms // 2, n_atoms),), body)


def test_selectCore():
    pass


def test_selectShell():
    pass


def test_maxInnerDistance(circle):
    max_dist = np.linalg.norm(circle[17] - circle[41])
    assert np.isclose(max_dist, refstruct.maxInnerDistance(circle), atol=1.e-15)


# def test_queryDistance_naive(circle, half_circle):
#     obj = half_circle
# #     obj = np.asarray([[1, 1, 1]])
# #     print circle[0], obj[0]
#     print refstruct.queryDistance_naive(circle, obj, 1.)
