import pandas as pd

class Config:

    def __init__(self, s_input_csv_path, s_output_csv_path, s_video_html_path):

        # input file path
        self.s_input_csv_path  = s_input_csv_path
        self.s_output_csv_path = s_output_csv_path
        self.s_video_html_path = s_video_html_path

        self._load_hard_coded_parameters()

    def _load_hard_coded_parameters(self):

        # 4.5 meters / second
        self.f_drive_speed_mps = 4.5

        self.i_0_time_unix = (
            pd.to_datetime(['2015-02-03 02:00:00'])
        ).astype(int) // 10 ** 9