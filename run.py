from doorDashDelivery import pipeline

if __name__ == '__main__':

    pipeline.run_pipeline(
        s_input_csv_path  = 'optimization_take_home.csv',
        s_output_csv_path = 'output.csv'
    )