from doorDashDelivery.utils import data_utils

from gurobipy import GRB, Model, quicksum

class MIP():

    def __init__(self, config):

        self._construct_MIP(config)


    def _construct_MIP(self, config):

        print('Start to construct MIP')
        self.model = Model('DoorDash')
        self.model.modelSense = GRB.MINIMIZE
        self._create_variables(config)
        self._set_objective(config)
        self._wirte_constraints(config)
        self.model.update()
        # self.model.write('mip_model.lp')

    def solve(self):
        self.model.setParam(GRB.Param.TimeLimit, 60)
        self.model.optimize()

    def _create_variables(self, config):


        ### x: if a dasher has complete the arc orig -> dest
        ### y: if a dasher has at least an order to work on
        ### t: a dasher's arrival time at a location
        ### w: a dasher's wait duration at a location
        self.d_var_x = {}
        self.d_var_y = {}
        self.d_var_t = {}
        self.d_var_w = {}
        for s_dasher_id in config.l_dashers:

            # construct x variable
            self.d_var_y[s_dasher_id] = self.model.addVar(
                vtype = GRB.BINARY,
                name  = '{}_works'.format(s_dasher_id)
            )


            for s_arc_orig in config.l_nodes:

                # construct t variables
                if s_arc_orig in config.l_customers:
                    f_lb = config.d_pickup_time_for_customers[s_arc_orig]
                else:
                    f_lb = 0

                self.d_var_t[s_dasher_id, s_arc_orig] = self.model.addVar(
                    vtype = GRB.CONTINUOUS,
                    name  = '{}_arrive_at_{}'.format(s_dasher_id, s_arc_orig),
                    lb    = f_lb
                )

                # construct w variables
                self.d_var_w[s_dasher_id, s_arc_orig] = self.model.addVar(
                    vtype = GRB.CONTINUOUS,
                    name  = '{}_wait_at_{}'.format(s_dasher_id, s_arc_orig),
                    lb    = 0
                )

                for s_arc_dest in config.l_nodes:

                    # construct x variables
                    self.d_var_x[s_dasher_id, s_arc_orig, s_arc_dest] = self.model.addVar(
                        vtype = GRB.BINARY,
                        name  = '{}_{}{}'.format(s_dasher_id, s_arc_orig, s_arc_dest)
                    )


    def _set_objective(self, config):

        obj = self.model.addVar(
            vtype = GRB.CONTINUOUS,
            name  = 'objective',
            obj   = 1
        )

        self.model.addConstr(
            quicksum(
                self.d_var_t[s_dasher_id, i_customer] - config.d_pickup_time_for_customers[i_customer]
                for s_dasher_id in config.l_dashers
                for i_customer in config.l_customers
            ) == obj
        )

    def _wirte_constraints(self, config):

        self._add_constraint_useless_arcs(config)
        self._add_constraint_flow(config)
        self._add_constraint_order_must_be_picked_by_1(config)
        self._add_constraint_customer_must_be_served_by_1(config)
        self._add_constraint_enforce_stop_order(config)


    def _add_constraint_useless_arcs(self, config):

        set_useless_arcs = set()

        for s_node in config.l_nodes:
            set_useless_arcs.add(
                (s_node, s_node)
            )
            set_useless_arcs.add(
                (s_node, 'source')
            )
            set_useless_arcs.add(
                ('target', s_node)
            )


        for s_restaurtant_id in config.l_restaurants:
            set_useless_arcs.add(
                (s_restaurtant_id, 'target')
            )

        for s_customer_id in config.l_customers:
            set_useless_arcs.add(
                ('source', s_customer_id)
            )

        for d in config.l_input_data:
            set_useless_arcs.add(
                ('c{:03d}'.format(d['delivery_id']),
                'r{:03d}'.format(d['delivery_id']))
            )

        self.model.addConstrs(
            self.d_var_x[s_dasher_id, s_arc_orig, s_arc_dest] == 0
            for s_dasher_id in config.l_dashers
            for (s_arc_orig, s_arc_dest) in set_useless_arcs
        )

    def _add_constraint_flow(self, config):

        self.model.addConstrs(
            quicksum(
                self.d_var_x[
                    s_dasher_id, 'source', s_node
                ]
                for s_node in config.l_nodes
            ) == 1
            for s_dasher_id in config.l_dashers
        )
        self.model.addConstrs(
            quicksum(
                self.d_var_x[
                    s_dasher_id, s_node, 'target'
                ]
                for s_node in config.l_nodes
            ) == 1
            for s_dasher_id in config.l_dashers
        )

        self.model.addConstrs(
            quicksum(self.d_var_x[s_dasher_id, s_node_in, s_loc]  for s_node_in in config.l_nodes)
            ==
            quicksum(self.d_var_x[s_dasher_id, s_loc, s_node_out] for s_node_out in config.l_nodes)
            for s_dasher_id in config.l_dashers
            for s_loc in config.l_physical_locations
        )

        # for s_dasher_id in config.l_dashers:
        #     for s_arc_orig in config.l_nodes:

        #         if s_arc_orig in config.l_customers:
        #             self.model.addConstr(
        #                 self.d_var_w[s_dasher_id, s_arc_orig] == 0
        #             )

        #         for s_arc_dest in config.l_nodes:

        #             lhs = (
        #                 self.d_var_t[s_dasher_id, s_arc_orig]
        #                 +
        #                 self.d_var_w[s_dasher_id, s_arc_orig]
        #                 +
        #                 config.d_time_sec[s_arc_orig, s_arc_dest]
        #             )

        #             self.model.addConstr(
        #                 lhs <= self.d_var_t[s_dasher_id, s_arc_dest]
        #             )




    def _add_constraint_order_must_be_picked_by_1(self, config):
        self.model.addConstrs(
            quicksum(
                self.d_var_x[
                    s_dasher_id, s_arc_orig, s_restaurtant_id
                ]
                for s_dasher_id in config.l_dashers
                for s_arc_orig in config.l_nodes
            ) == 1
            for s_restaurtant_id in config.l_restaurants
        )

    def _add_constraint_customer_must_be_served_by_1(self, config):
        self.model.addConstrs(
            quicksum(
                self.d_var_x[
                    s_dasher_id, s_arc_orig, s_customer_id
                ]
                for s_dasher_id in config.l_dashers
                for s_arc_orig in config.l_nodes
            ) == 1
            for s_customer_id in config.l_customers
        )

        self.model.addConstrs(
            self.d_var_w[s_dasher_id, s_customer_id] == 0
            for s_dasher_id in config.l_dashers
            for s_customer_id in config.l_customers
        )

    def _add_constraint_enforce_stop_order(self, config):

        for s_dasher_id in config.l_dashers:

            for d in config.l_input_data:

                s_restaurtant_id = 'r{:03d}'.format(d['delivery_id'])
                s_customer_id    = 'c{:03d}'.format(d['delivery_id'])

                # wait at restaurant if a dasher arrives early
                self.model.addConstr(
                    self.d_var_t[
                        s_dasher_id, s_restaurtant_id
                    ]
                    +
                    self.d_var_w[
                        s_dasher_id, s_restaurtant_id
                    ]
                    >=
                    d['food_ready_time']
                )

                #
                # self.model.addConstr(
                #     self.d_var_t[
                #         s_dasher_id, s_restaurtant_id
                #     ]
                #     +
                #     self.d_var_w[
                #         s_dasher_id, s_restaurtant_id
                #     ]
                #     +
                #     config.d_time_sec[(s_restaurtant_id, s_customer_id)]
                #     <=
                #     self.d_var_t[
                #         s_dasher_id, s_customer_id
                #     ]
                # )


    def produce_solution_file(self):

        d_all_sol = {
            'obj': self.model.ObjVal,
            # 'solving_time': self.solve_time_sec,
            'arrival': self._get_1_var_group_sol('t', self.d_var_t),
            # 'used_dasher': self._get_1_var_group_sol(self.d_var_y),
            'waiting': self._get_1_var_group_sol('w', self.d_var_w),
            'used_arc': self._get_1_var_group_sol('x', self.d_var_x, b_ignore_zero = True)
        }

        data_utils.saveJson(
            d_all_sol,
            'mip_solution.json'
        )

    def _get_1_var_group_sol(self, s_name, d_var, b_ignore_zero = False):

        return {
            s_name + '_' + '_'.join(var_key) : d_var[var_key].x
            for var_key in d_var.keys()
            if float(d_var[var_key].x) != 0.0 and b_ignore_zero
        }