import os
import pandas as pd

from doorDashDelivery.utils import data_utils as du

class Config:

    def __init__(self, s_input_csv_path, s_output_csv_path):

        # input file path
        self.s_input_csv_path  = s_input_csv_path
        self.s_output_csv_path = s_output_csv_path

        self._load_hard_coded_parameters()

    def _load_hard_coded_parameters(self):

        # 4.5 meters / second
        self.f_drive_speed_mps = 4.5

        self.i_available_dasher_each_batch = 2
        self.i_num_order_each_batch = 6
        self.i_num_clusters = 10
        self.df_0_time_unix = (
            pd.to_datetime(['2015-02-03 02:00:00'])
        ).astype(int) // 10 ** 9

        self.l_solution_dir = './raw_solutions'
        try:
            os.mkdir(self.l_solution_dir)
        except:
            pass

    def create_important_data(self, l_input_data, i_batch_idx):

        self.l_input_data = l_input_data

        ### this is the worst case, that means every dash handles one order
        self.l_dashers = [
            'd{:03d}'.format(i)
            for i in range(
                self.i_available_dasher_each_batch * (i_batch_idx - 1),
                self.i_available_dasher_each_batch * i_batch_idx
            )
        ]
        self.d_pickup_time_for_customers = {
            # the lower bound for customer x, is the food ready time
            'c{:03d}'.format(d['delivery_id']): d['food_ready_time']
            for d in l_input_data
        }
        self.d_order_create_time_for_customers = {
            'c{:03d}'.format(d['delivery_id']): d['created_at']
            for d in l_input_data
        }

        d_r_coords = {
            'r{:03d}'.format(d['delivery_id']): (
                (d['pickup_lat'], d['pickup_long'])
            )
            for d in l_input_data
        }

        d_c_coords = {
            'c{:03d}'.format(d['delivery_id']): (
                [d['dropoff_lat'], d['dropoff_long']]
            )
            for d in l_input_data
        }

        d_coords = {
            **d_r_coords, **d_c_coords
        }


        self.l_restaurants = list(d_r_coords.keys())
        self.l_customers   = list(d_c_coords.keys())
        self.l_physical_locations = (
            self.l_restaurants
            +
            self.l_customers
        )
        self.l_nodes = self.l_physical_locations + ['target', 'source']

        self.d_time_sec =  {
            (s_orig, s_dest): round(du.haversine(
                d_coords[s_orig], d_coords[s_dest]
            ) / 4.5, 0)
            for s_orig in self.l_physical_locations
            for s_dest in self.l_physical_locations
        }

        for s_loc in self.l_nodes:
            self.d_time_sec['source', s_loc] = 0
            self.d_time_sec['target', s_loc] = 0
            self.d_time_sec[s_loc, 'source'] = 0
            self.d_time_sec[s_loc, 'target'] = 0
