import time
import pandas as pd

from doorDashDelivery.configuration import configuration
from doorDashDelivery.model import mip_basic

def run_pipeline(s_input_csv_path, s_output_csv_path, s_video_html_path, s_solving_method):

    f_start_time = time.time()


    ### initalize configuration
    config = configuration.Config(
        s_input_csv_path, s_output_csv_path, s_video_html_path
    )

    ### parse input files
    l_input_data = parse_input(config)

    ### form MIP
    optimization_model = mip_basic.MIP()
    optimization_model.solve()
    optimization_model.report()

    f_end_time = time.time()
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
