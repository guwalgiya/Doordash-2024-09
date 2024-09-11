from doorDashDelivery import pipeline

if __name__ == '__main__':

    pipeline.run_pipeline(
        s_input_csv_path  = 'optimization_take_home.csv',
        s_output_csv_path = 'output.csv',
        s_video_html_path = 'output_vedio.html',

        ### this can be (1) naive, (2) basic, and (3) final
        s_solving_method  = 'basic'
    )