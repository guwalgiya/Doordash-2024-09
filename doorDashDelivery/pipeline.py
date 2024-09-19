import time
import pandas as pd
from sklearn.cluster import KMeans

from doorDashDelivery.configuration import configuration
from doorDashDelivery.model import mip_model
from doorDashDelivery.utils import data_utils as du

def run_pipeline(s_input_csv_path, s_output_csv_path):

    f_start_time = time.time()


    ### initalize configuration
    config = configuration.Config(
        s_input_csv_path, s_output_csv_path
    )

    ### parse input files
    l_input_data = parse_input(config)

    ### solve a mip for each batch
    l_results = []
    i_batch_idx = 1
    for i_batch_idx_start in range(0, len(l_input_data), config.i_num_order_each_batch):

        print('============= Batch {}'.format(i_batch_idx))
        i_batch_idx_end = min(
            i_batch_idx_start + config.i_num_order_each_batch, len(l_input_data)
        )
        l_input_data_batch = l_input_data[i_batch_idx_start : i_batch_idx_end]

        config.create_important_data(l_input_data_batch, i_batch_idx)
        optimization_model = mip_model.MIP(config, i_batch_idx)
        optimization_model.solve()
        d_solution_batch = optimization_model.produce_solution_file(config)

        l_batch_results = raw_solution_to_result(config, d_solution_batch)

        l_results += l_batch_results
        i_batch_idx += 1

    f_end_time = time.time()
    print('---------------------------------------------')
    print('The program takes {} second to run'.format(
        round(f_end_time - f_start_time, 0)
    ))

    df_results = pd.DataFrame(
        l_results,
        columns = [
            'Route ID',
            'Route Point Index',
            'Delivery ID',
            'Route Point Type',
            'Route Point Time'
        ]
    )
    df_results.to_csv(
        s_output_csv_path,
        index = False
    )




def parse_input(config):

    ### parse data, convert the raw data to a list of dictionary
    df_input_data = pd.read_csv(
        config.s_input_csv_path
    )

    df_input_data = basic_k_means(config, df_input_data)

    df_input_data = df_input_data.sort_values(
        ['region_id', 'cluster', 'created_at'],
        ascending =[True, True, True]
    )

    # convert to unix time
    df_input_data['created_at'] = pd.to_datetime(
        df_input_data['created_at'],
        format = "%m/%d/%y %H:%M"
    ).astype(int) // 10 ** 9 - config.df_0_time_unix
    df_input_data['food_ready_time'] = pd.to_datetime(
        df_input_data['food_ready_time'],
        format = "%m/%d/%y %H:%M"
    ).astype(int) // 10 ** 9 - config.df_0_time_unix

    l_input_data = df_input_data.to_dict('records')

    return l_input_data


def raw_solution_to_result(config, d_solution_batch):

    l_result_batch = []
    for s_dasher_id in d_solution_batch['dashers']:

        l_dasher_used_arcs = [
            s_key.split('_')[2 :]
            for s_key in d_solution_batch['used_arc']
            if (
                d_solution_batch['used_arc'][s_key] == 1.0
                and
                s_dasher_id in s_key
            )
        ]

        ### Form route
        s_current_stop = 'source'
        l_dasher_route = []
        b_while_continue  = True
        while b_while_continue:
            for l_arc in l_dasher_used_arcs:

                if s_current_stop == l_arc[0]:
                    s_current_stop = l_arc[1]

                    if s_current_stop == 'target':
                        b_while_continue = False
                        break
                    else:
                        l_dasher_route.append(l_arc[1])



        ### Form result details
        l_dasher_route_details = [
            [
                # route ID
                int(s_dasher_id[1:]),

                i,

                int(l_dasher_route[i][1:]),

                {
                    "r": "Pickup",
                    "c": "DropOff"
                }[l_dasher_route[i][0]],

                du.get_unix_time(
                    config,
                    d_solution_batch,
                    s_dasher_id,
                    l_dasher_route[i]
                )
            ]

            for i in range(len(l_dasher_route))
        ]
        print('-----------')
        print(s_dasher_id)
        print(l_dasher_route_details)
        l_result_batch += l_dasher_route_details

    return l_result_batch



def basic_k_means(config, df_input_data):

    kmeans = KMeans(n_clusters = config.i_num_clusters, random_state=42)
    df_input_data['cluster'] = kmeans.fit_predict(
        df_input_data[['pickup_lat', 'pickup_long']]
    )

    return df_input_data