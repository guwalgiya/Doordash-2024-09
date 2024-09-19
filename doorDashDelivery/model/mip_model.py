import os

from doorDashDelivery.utils import data_utils

from gurobipy import GRB, Model, quicksum

class MIP():

    def __init__(self, config, i_batch_idx):

        self.i_batch_idx = i_batch_idx
        self._construct_MIP(config)


    def _construct_MIP(self, config):

        print('Start to construct MIP {}'.format(self.i_batch_idx))
        self.model = Model('DoorDash')
        self.model.modelSense = GRB.MINIMIZE
        self._create_variables(config)
        self._set_objective(config)
        self._wirte_constraints(config)
        self.model.update()
        self.model.write(
            os.path.join(
                config.l_solution_dir,
                'mip_{:03d}.lp'.format(self.i_batch_idx)
            )
        )

    def solve(self):
        self.model.setParam(GRB.Param.Threads, 8)
        self.model.optimize()

    def _create_variables(self, config):


        ### x: if a dasher has complete the arc orig -> dest
        ### y: if a dasher has at least an order to work on
        ### t: a dasher's arrival time at a location
        ### w: a dasher's wait duration at a location
        ### u: order of stop of a dasher
        self.d_var_x = {}
        self.d_var_t = {}
        self.d_var_w = {}
        self.d_var_u = {}
        for s_dasher_id in config.l_dashers:

            for s_arc_orig in config.l_nodes:

                # construct t variables
                if s_arc_orig in config.l_customers:
                    f_lb = config.d_pickup_time_for_customers[s_arc_orig]
                else:
                    f_lb = 0

                self.d_var_t[s_dasher_id, s_arc_orig] = self.model.addVar(
                    vtype = GRB.CONTINUOUS,
                    name  = 't_{}_{}'.format(s_dasher_id, s_arc_orig),
                    lb    = f_lb
                )

                # construct w variables
                self.d_var_w[s_dasher_id, s_arc_orig] = self.model.addVar(
                    vtype = GRB.CONTINUOUS,
                    name  = 'w_{}_{}'.format(s_dasher_id, s_arc_orig),
                    lb    = 0
                )

                # construct u variables
                self.d_var_u[s_dasher_id, s_arc_orig] = self.model.addVar(
                    vtype = GRB.CONTINUOUS,
                    name  = 'u_{}'.format(s_dasher_id, s_arc_orig),
                    lb    = 0
                )

                for s_arc_dest in config.l_nodes:

                    # construct x variables
                    self.d_var_x[s_dasher_id, s_arc_orig, s_arc_dest] = self.model.addVar(
                        vtype = GRB.BINARY,
                        name  = 'x_{}_{}_{}'.format(s_dasher_id, s_arc_orig, s_arc_dest)
                    )


    def _set_objective(self, config):

        obj = self.model.addVar(
            vtype = GRB.CONTINUOUS,
            name  = 'objective',
            obj   = 1
        )

        self.model.addConstr(
            quicksum(
                self.d_var_t[s_dasher_id, i_customer] - config.d_order_create_time_for_customers[i_customer]
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

        # flow balance at each location
        self.model.addConstrs(
            quicksum(
                self.d_var_x[s_dasher_id, s_node, s_next]
                for s_next in config.l_nodes
                if s_next != s_node
            )
            ==
            quicksum(
                self.d_var_x[s_dasher_id, s_prev, s_node]
                for s_prev in config.l_nodes
                if s_prev != s_node
            )
            for s_dasher_id in config.l_dashers
            for s_node in config.l_physical_locations
        )

        # respect order
        self.model.addConstrs(
            self.d_var_u[s_dasher_id, s_arc_orig] + 1
            <=
            (
                self.d_var_u[s_dasher_id, s_arc_dest]
                +
                len(config.l_nodes)
                *
                (1 - self.d_var_x[s_dasher_id, s_arc_orig, s_arc_dest])
            )
            for s_dasher_id in config.l_dashers
            for s_arc_orig in config.l_nodes
            for s_arc_dest in config.l_nodes
        )

        # include travel time
        self.model.addConstrs(
            self.d_var_t[s_dasher_id, s_arc_orig]
            +
            self.d_var_w[s_dasher_id, s_arc_orig]
            +
            config.d_time_sec[s_arc_orig, s_arc_dest]
            <=
            (
                self.d_var_t[s_dasher_id, s_arc_dest]
                +
                1000000
                *
                (1 - self.d_var_x[s_dasher_id, s_arc_orig, s_arc_dest])
            )
            for s_dasher_id in config.l_dashers
            for s_arc_orig in config.l_nodes
            for s_arc_dest in config.l_nodes
        )



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

                # must pick-up first then deliver to customer
                self.model.addConstr(
                    self.d_var_t[s_dasher_id, s_restaurtant_id]
                    +
                    self.d_var_w[s_dasher_id, s_restaurtant_id]
                    +
                    config.d_time_sec[s_restaurtant_id, s_customer_id]
                    <=
                    self.d_var_t[s_dasher_id, s_customer_id]
                )

                # must pick-up and deliver by the same dasher
                self.model.addConstrs(
                    quicksum(
                        self.d_var_x[s_dasher_id, s_node, s_restaurtant_id]
                        for s_node in config.l_nodes
                    )
                    ==
                    quicksum(
                        self.d_var_x[s_dasher_id, s_node, s_customer_id]
                        for s_node in config.l_nodes
                    )
                    for s_dasher_id in config.l_dashers
                )


    def produce_solution_file(self, config):

        d_all_sol = {
            'obj': self.model.ObjVal,
            'dashers': config.l_dashers,
            'arrival': self._get_1_var_group_sol('t', self.d_var_t, i_round = 5),
            'waiting': self._get_1_var_group_sol('w', self.d_var_w),
            'visit_order': self._get_1_var_group_sol('u', self.d_var_u),
            'used_arc': self._get_1_var_group_sol('x', self.d_var_x)
        }

        data_utils.saveJson(
            d_all_sol,
            os.path.join(
                config.l_solution_dir,
                'mip_solution_batch_{:03d}.json'.format(self.i_batch_idx)
            )
        )

        return d_all_sol

    def _get_1_var_group_sol(self, s_name, d_var, i_round = 0):

        return {
            s_name + '_' + '_'.join(var_key) : round(d_var[var_key].x, i_round)
            for var_key in d_var.keys()
        }