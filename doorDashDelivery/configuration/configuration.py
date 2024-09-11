import os, argparse

class Config:

    def __init__(self, s_input_csv_path, s_output_csv_path, s_video_html_path):

        # input file path
        self.s_input_csv_path  = s_input_csv_path
        self.s_output_csv_path = s_output_csv_path
        self.s_video_html_path = s_video_html_path