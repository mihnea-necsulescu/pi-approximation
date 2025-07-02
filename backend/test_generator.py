from generator import generate_random_points


def test_correct_number_of_points():
    points = generate_random_points(10)
    assert len(points) == 10


def test_points_in_valid_range():
    points = generate_random_points(50)
    for x, y in points:
        assert 0 <= x <= 1
        assert 0 <= y <= 1
