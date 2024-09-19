import time
import pandas as pd

from doorDashDelivery.configuration import configuration
from doorDashDelivery.model import mip_model

def run_pipeline(s_input_csv_path, s_output_csv_path, s_video_html_path, s_solving_method):

    f_start_time = time.time()


    ### initalize configuration
    config = configuration.Config(
        s_input_csv_path, s_output_csv_path, s_video_html_path
    )

    ### parse input files
    l_input_data = parse_input(config)

    ### solve a mip for each batch
    i_batch_idx = 1
    for i_batch_idx_start in range(0, len(l_input_data), config.i_num_order_each_batch):

        i_batch_idx_end = min(
            i_batch_idx_start + config.i_num_order_each_batch, len(l_input_data)
        )
        l_input_data_batch = l_input_data[i_batch_idx_start : i_batch_idx_end]

        config.create_important_data(l_input_data_batch)
        optimization_model = mip_model.MIP(config, i_batch_idx)
        optimization_model.solve()
        optimization_model.produce_solution_file(config)

        i_batch_idx += 1

    f_end_time = time.time()
    print('---------------------------------------------')
    print('The program takes {} second to run'.format(
        round(f_end_time - f_start_time, 0)
    ))
    print('Now run an additional visualizer')


def parse_input(config):

    ### parse data, convert the raw data to a list of dictionary
    df_input_data = pd.read_csv(
        config.s_input_csv_path
    )

    # convert to unix time
    df_input_data['created_at'] = pd.to_datetime(
        df_input_data['created_at'],
        format = "%m/%d/%y %H:%M"
    ).astype(int) // 10 ** 9 - config.i_0_time_unix
    df_input_data['food_ready_time'] = pd.to_datetime(
        df_input_data['food_ready_time'],
        format = "%m/%d/%y %H:%M"
    ).astype(int) // 10 ** 9 - config.i_0_time_unix

    l_input_data = df_input_data.to_dict('records')

    return l_input_data
