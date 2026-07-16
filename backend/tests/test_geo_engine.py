from app.main import GeoEngine


def test_missing_coordinates_default_to_nyc():
    assert GeoEngine.get_borough(None, None) == "NYC"


def test_bronx_north_of_harlem_river():
    assert GeoEngine.get_borough(40.85, -73.90) == "Bronx"


def test_staten_island_isolated_west():
    assert GeoEngine.get_borough(40.58, -74.15) == "Staten Island"


def test_deep_queens_east_of_everything():
    assert GeoEngine.get_borough(40.75, -73.80) == "Queens"


def test_manhattan_midtown_west_of_east_river_diagonal():
    # Times Square, well west of the -73.96 border used for the 40.74-40.76 zone
    assert GeoEngine.get_borough(40.758, -73.985) == "Manhattan"


def test_queens_long_island_city_east_of_diagonal():
    # LIC sits north of 40.735 in the same latitude band as Midtown, but east
    # of the river boundary, so it must resolve to Queens, not Manhattan.
    assert GeoEngine.get_borough(40.75, -73.94) == "Queens"


def test_brooklyn_williamsburg_south_of_newtown_creek():
    assert GeoEngine.get_borough(40.714, -73.957) == "Brooklyn"


def test_queens_ridgewood_dips_south_of_newtown_creek():
    assert GeoEngine.get_borough(40.705, -73.895) == "Queens"


def test_queens_rockaway_far_south():
    assert GeoEngine.get_borough(40.58, -73.85) == "Queens"


def test_brooklyn_coney_island_far_south():
    assert GeoEngine.get_borough(40.58, -73.98) == "Brooklyn"
