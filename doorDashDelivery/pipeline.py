from doorDashDelivery.configuration import configuration

def run_pipeline(s_input_csv_path, s_output_csv_path, s_video_html_path):

    ### initalize configuration
    config = configuration.Config(
        s_input_csv_path, s_output_csv_path, s_video_html_path
    )