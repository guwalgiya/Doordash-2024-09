from doorDashDelivery import pipeline

if __name__ == '__main__':

    pipeline.run_pipeline(
        s_input_csv_path  = 'optimization_tak_home.csv',
        s_output_csv_path = 'output.csv',
        s_video_html_path = 'output_vedio.html'
    )