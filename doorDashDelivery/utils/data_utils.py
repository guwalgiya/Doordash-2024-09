from math import radians, cos, sin, asin, sqrt
import json

def haversine(loc1, loc2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians

    (lat1, lon1) = loc1
    (lat2, lon2) = loc2

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def saveJson(data, path):
    file = open(path, 'w')
    json.dump(data, file, indent = 4)
    file.close()

def get_unix_time(config, d_solution_batch, s_dasher_id, s_stop):

    f_arrival_sec = d_solution_batch['arrival'][
        't_{}_{}'.format(
            s_dasher_id,
            s_stop
        )
    ]

    f_wait_sec = d_solution_batch['waiting'][
        'w_{}_{}'.format(
            s_dasher_id,
            s_stop
        )
    ]

    if s_stop[0] == 'c':
        return int(config.df_0_time_unix[0] + f_arrival_sec)
    else:
        return int(config.df_0_time_unix[0] + f_arrival_sec + f_wait_sec)