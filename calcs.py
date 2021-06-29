import requests
import datetime
import numpy as np

async def expected_date(name, rating, variant='Rapid'):
    variant = variant.capitalize()
    url = f'https://lichess.org/api/user/{name}/rating-history'
    response = requests.get(url)
    if not str(response.status_code).startswith('2'):
        return -1
    data = requests.get(url).json()
    rating_values = []
    exp_rating_values = []
    date_values = []
    points = []

    for game_type in data:
        if game_type['name'] != variant:
            continue
        else:
            points = game_type['points']

    if len(points) < 25:
        return None

    for point in points:
        date_values.append(datetime.date(point[0], point[1]+1, point[2]))
        exp_rating_values.append(3 ** (point[3] / 300))
        rating_values.append(point[3])

    # Compute the best-fit line
    start_date = min(date_values)
    days_since_start_values = [(date-start_date).days for date in date_values]

    coeffs = np.polyfit(days_since_start_values, exp_rating_values, 1)

    days_since_start = ((3 ** (rating/300)) - coeffs[1])/coeffs[0]
    return start_date + datetime.timedelta(days=days_since_start)
