# -*- coding: utf-8 -*-

import json
import sys
import os
import random
import string
import math
import re


class Formulator:
    def __init__(self, proj_dir, config_fname):
        self.proj_dir = proj_dir
        with open(os.path.join(proj_dir, config_fname), 'r') as f:
            self.config = json.load(f)
        self.tc_set = self.get_all_tc()

    def get_all_tc(self):  # get the ids of all test cases
        tcs = set()
        for crio in self.config['relative_cria']:
            with open(os.path.join(proj_dir, crio['file']), 'r') as f:
                for line in f:
                    tc = line.split(':')[0]
                    if line.split(':')[1].split():
                        tcs.add(tc)
        for crio in self.config['absolute_cria']:
            with open(os.path.join(proj_dir, crio['file']), 'r') as f:
                for line in f:
                    tc = line.split(':')[0]
                    if line.split(':')[1].split():
                        tcs.add(tc)
        return tcs

    def gen_model(self):
        constraints = self.gen_constraint()
        if self.config['nonlinear']:
            if self.config['relax']:
                obj_coeff, extra_constraints = self.gen_objective_aux()
                constraints += extra_constraints
            else:
                obj_coeff = self.gen_objective_nl()
        else:
            obj_coeff = self.gen_objective()
        self.save(obj_coeff, constraints)

    def get_crio_total_num(self, crio_fname):  # get total number of distinct crio_ids
        # e.g. t2:1 3 5  # crio_ids
        #      t3:
        #      t4:199
        crio_set = set()
        with open(os.path.join(self.proj_dir, crio_fname), 'r') as f:
            for line in f:
                for c in line.split(':')[1].split():
                    crio_set.add(c)
        return len(crio_set)

    def get_crio_max_num(self, crio_fname):  # get the maximum of the coefficients (e.g., max execution time of a test case)
        # e.g. t2:100  # one and only one positive integer
        #      t3:23
        max_num = -1
        with open(os.path.join(self.proj_dir, crio_fname), 'r') as f:
            for line in f:
                c = int(line.split(':')[1])
                if c > max_num:
                    max_num = c
        return max_num

    def gen_objective(self):
        tc_to_coefficient = dict()
        for crio in self.config['relative_cria']:
            fname = crio['file']
            weight = int(crio['weight'])
            is_invert = crio['invert']
            if crio['is_dependent']:
                q = self.get_crio_total_num(fname)
            else:
                q = self.get_crio_max_num(fname)
            with open(os.path.join(proj_dir, fname), 'r') as f:
                for line in f:
                    tc = line.split(':')[0]
                    if tc not in self.tc_set:
                        continue
                    if crio['is_dependent']:
                        # e.g. t2:
                        #      t3:1 3
                        c_list = line.split(':')[1].split()
                        if len(c_list) > 0:
                            c_coverage = len(c_list) / float(q)
                        else:
                            c_coverage = 0
                        if is_invert:
                            coeff = 1-round(c_coverage, 6)
                        else:
                            coeff = round(c_coverage, 6)
                    else:
                        # e.g. t2:100  # one and only one positive integer
                        #      t3:23
                        c = int(line.split(':')[1])
                        c_coverage = c/float(q)
                        if is_invert:
                            coeff = 1-round(c_coverage, 6)
                        else:
                            coeff = round(c_coverage, 6)
                    if coeff == 0:  
                        # if coeff=0, the test can be selected without penalty; 
                        # introduce penalty to avoid this, because we want a minimized suite
                        if self.config['min_or_max'].lower() == 'min':
                            coeff = 0.000001
                        else:  # max
                            coeff = -0.000001
                    if tc in tc_to_coefficient.keys():
                        tc_to_coefficient[tc] += weight*coeff
                    else:
                        tc_to_coefficient[tc] = weight*coeff
        return tc_to_coefficient

    def gen_objective_aux(self):
        tc_to_coefficient = dict()
        constraints = list()
        for crio in self.config['relative_cria']:
            prefix = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3))
            crio_to_tc = dict()
            fname = crio['file']
            weight = int(crio['weight'])
            is_invert = crio['invert']
            if crio['is_dependent']:
                q = self.get_crio_total_num(fname)
            else:
                q = self.get_crio_max_num(fname)
            with open(os.path.join(proj_dir, fname), 'r') as f:
                for line in f:
                    tc = line.split(':')[0]
                    if tc not in self.tc_set:
                        continue
                    if crio['is_dependent']:
                        # e.g. t2:
                        #      t3:1 3
                        coeff = -round((1/float(q)), 6) if is_invert else round((1/float(q)), 6)
                        tc_no = tc.replace('t', '')
                        c_list = line.split(':')[1].split()
                        v_i_j = ['v_' + prefix + '_' + tc_no + '_' + str(c_no) for c_no in c_list]
                        if is_invert:
                            if tc in tc_to_coefficient.keys():
                                tc_to_coefficient[tc] += weight
                            else:
                                tc_to_coefficient[tc] = weight
                        if len(v_i_j) > 0 and coeff != 0:
                            for k in v_i_j:  # k is unique in v_i_j
                                tc_to_coefficient[k] = weight*coeff
                        for c in c_list:
                            if c in crio_to_tc.keys():
                                crio_to_tc[c].append(tc_no)
                            else:
                                crio_to_tc[c] = [tc_no]
                    else:
                        # e.g. t2:100  # one and only one positive integer
                        #      t3:23
                        c = int(line.split(':')[1])
                        c_coverage = c/float(q)
                        if is_invert:
                            coeff = 1-round(c_coverage, 6)
                        else:
                            coeff = round(c_coverage, 6)
                        if tc in tc_to_coefficient.keys():
                            tc_to_coefficient[tc] += weight*coeff
                        else:
                            tc_to_coefficient[tc] = weight*coeff
            # extra constraints
            for j in crio_to_tc.keys():
                v_i_j = list()
                for tc_no in crio_to_tc[j]:
                    lhs = 'v_' + prefix + '_' + tc_no + '_' + j
                    rhs = 't' + tc_no
                    constraints.append((lhs, '<=', rhs))
                    v_i_j.append(lhs)
                lhs = '+'.join(v_i_j)
                if (lhs, '<=', 1) not in constraints:
                    constraints.append((lhs, '<=', 1))
        return tc_to_coefficient, constraints                                                                 

    def gen_objective_nl(self):
        equations = list()
        for crio in self.config['relative_cria']:
            fname = crio['file']
            weight = int(crio['weight'])
            is_invert = crio['invert']
            if crio['is_dependent']:
                q = self.get_crio_total_num(fname)
                coeff_denom = round(1/float(q), 6)
                # first pass
                crio_to_tc = dict()
                tc_to_crio = dict()
                with open(os.path.join(proj_dir, fname), 'r') as f:
                    for line in f:
                        tc = line.split(':')[0]
                        if tc not in self.tc_set:
                            continue
                        c_list = line.split(':')[1].split()
                        if c_list:
                            tc_to_crio[tc] = c_list
                            for c in c_list:
                                if c in crio_to_tc.keys():
                                    crio_to_tc[c].append(tc)
                                else:
                                    crio_to_tc[c] = [tc]
                        else:
                            tc_to_crio[tc] = list()
                # second pass
                equation = ''
                if is_invert:
                    for t, c_list in tc_to_crio.items():
                        inner_equations = list()
                        for c in c_list:
                            tcs = ['(1-' + t_i + ')' for t_i in crio_to_tc[c] if t_i != t]
                            if tcs:
                                inner_equations.append('*'.join(tcs))
                            else:
                                inner_equations.append('1')
                        if inner_equations:
                            equation += t + '*(1-' + str(coeff_denom) + '*('
                            equation += '\n+'.join(inner_equations)
                            equation += '))\n+'
                        else:
                            equation += t + '\n+'
                    equations.append(equation[:-2])  # remove the final '\n+'
                else:
                    for t, c_list in tc_to_crio.items():
                        inner_equations = list()
                        for c in c_list:
                            tcs = ['(1-' + t_i + ')' for t_i in crio_to_tc[c] if t_i != t]
                            if tcs:
                                inner_equations.append('*'.join(tcs))
                            else:
                                inner_equations.append('1')
                        if inner_equations:
                            equation += t + '*(' + str(coeff_denom) + '*('
                            equation += '\n+'.join(inner_equations)
                            equation += '))\n+'
                    equations.append(equation[:-2])  # remove the final '\n+'
            else:
                q = self.get_crio_max_num(fname)
                assert False  # not implemented yet
        return '+'.join(equations)

    def gen_constraint(self):
        constraints = list()
        for crio in self.config['absolute_cria']:
            fname = crio['file']
            if crio['is_coefficient']:
                tc_to_coeff = dict()
                with open(os.path.join(self.proj_dir, fname), 'r') as f:
                    # e.g. t33:50  # the coeffecient for the test case, instead of the crio_ids
                    #      t34:72
                    for line in f:
                        tc = line.split(':')[0]
                        tc_to_coeff[tc] = line.split(':')[1].strip()
                lhs = '+'.join([v + k for k, v in tc_to_coeff.items()]).replace('+-', '-')
                if (lhs, crio['crio_type'], crio['rhs']) not in constraints:
                    constraints.append((lhs, crio['crio_type'], crio['rhs']))
            else:
                # all of the crio_id have to be covered at least once
                crio_to_tcs = dict()
                with open(os.path.join(self.proj_dir, fname), 'r') as f:
                    for line in f:
                        # e.g. t2:390 395 396 400 401 405 406 409 412 413 450 ... (crio_ids)
                        tc = line.split(':')[0]
                        for crio_id in line.split(':')[1].split():
                            if crio_id in crio_to_tcs.keys():
                                crio_to_tcs[crio_id].append(tc)
                            else:
                                crio_to_tcs[crio_id] = [tc]                
                # for the classic minimization problem: statements are covered at least once
                for tc_list in crio_to_tcs.values():
                    lhs = '+'.join(tc_list)
                    if (lhs, '>=', 1) not in constraints:
                        constraints.append((lhs, '>=', 1))                
                '''
                # for the variant bi-criteria minimization problem:
                # some statements are covered multiple times
                crio_num_tcs = list()
                for k, v in crio_to_tcs.items():
                    crio_num_tcs.append((k, len(v)))
                crio_num_tcs.sort(key=lambda tup: tup[1], reverse=True)
                num_crio = len(crio_num_tcs)
                percent = 0.2
                # for the most frequently executed statements
                for i in range(int(percent*num_crio)):
                    lhs = '+'.join(crio_to_tcs[crio_num_tcs[i][0]])
                    covered_times = int(crio_num_tcs[i][1]*percent)
                    if (lhs, '>=', covered_times) not in constraints:
                        constraints.append((lhs, '>=', covered_times))
                # the rest statements
                for i in range(int(percent*num_crio), num_crio):
                    lhs = '+'.join(crio_to_tcs[crio_num_tcs[i][0]])
                    if (lhs, '>=', 1) not in constraints:
                        constraints.append((lhs, '>=', 1))
                '''
        return constraints

    def save(self, tc_to_coeff, constraints):
        if self.config['output_format'] == 'lp_solve':
            # tc_to_coeff is a dict here
            out_path = os.path.join(self.proj_dir, self.config['name'] + '.lp_solve')
            with open(out_path, 'w') as f:
                # objctive function
                obj_func = list()
                f.write('/*objective function*/\n')
                for tc, coeff in tc_to_coeff.items():
                    if coeff != 0:
                        coeff_str = '%0.6f' % coeff
                        obj_func.append(coeff_str + ' ' + tc)
                f.write(self.config['min_or_max']+ ': ')
                f.write('+'.join(obj_func).replace('+-', '-') + ';\n')
                # constraints
                f.write('/* constraints */\n')
                for lhs, ctype, rhs in constraints:
                    f.write(lhs + ctype + str(rhs) + ';\n')

                for tc in self.tc_set:
                    f.write('0<=' + tc + '<=1;\n')
                # assign variables as binary would make variables in single-variable equation (e.g. t2 >=1) are 'redefined'
                # by the solver when solving the equations and therefore produce wrong answer'
                f.write('/* variables */\n')
                f.write('int ' + ','.join(list(self.tc_set)) + ';\n')
        elif self.config['output_format'] == 'cplex_lp':
            # tc_to_coeff is a dict here
            out_path = os.path.join(self.proj_dir, self.config['name'] + '.cplex.lp')
            with open(out_path, 'w') as f:
                # objctive function
                if 'min' in self.config['min_or_max']:
                    f.write('minimize\n\n')
                else:
                    f.write('maximize\n\n')
                obj_func = list()
                for tc, coeff in tc_to_coeff.items():
                    if coeff != 0:
                        #coeff_str = str(coeff)
                        coeff_str = '%0.6f' % coeff
                        if coeff_str[0] != '-':
                            coeff_str = '+' + coeff_str
                        obj_func.append(coeff_str + ' ' + tc)
                num_group = int(math.floor(len(obj_func)/500)) + 1
                for i in range(0, num_group):
                    obj_str = ' '.join(obj_func[i*500:(i+1)*500]).replace('+ -', '-') + '\n'
                    f.write(obj_str)
                    #if i < num_group-1 and (i+1)*500 < len(obj_func) and not obj_str.startswith('-'):
                    #    f.write(' + ')
                f.write('\n')
                # constraints
                vij_set = set()
                f.write('subject to\n\n')
                for lhs, ctype, rhs in constraints:
                    for vij in re.findall('v_\w{3}_\d+_\d+', lhs):
                        vij_set.add(vij)
                    if str(rhs).isdigit():
                        f.write(lhs + ctype + str(rhs) + '\n')
                    else:
                        f.write(lhs + '-' + str(rhs) + ctype + '0\n')
                f.write('\n')
                # variable declaration
                all_tc = list(self.tc_set) + list(vij_set)
                num_group = int(math.floor(len(all_tc)/500)) + 1
                f.write('binary\n\n')
                for i in range(0, num_group):
                    f.write(' '.join(all_tc[i*500:(i+1)*500] + list(vij_set)) + '\n')
                f.write('\nend')
        elif self.config['output_format'] == 'ampl':
             # tc_to_coeff is a dict here
             out_path = os.path.join(self.proj_dir, self.config['name'] + '.ampl')
             with open(out_path, 'w') as f:
                # var declaration
                for t in self.tc_set:
                    f.write('var %s binary;\n' % t)
                # objective func
                obj_func = list()
                if 'min' in self.config['min_or_max']:
                    f.write('minimize obj:')
                else:
                    f.write('maximize obj:')
                for tc, coeff in tc_to_coeff.items():
                    if coeff != 0:
                        coeff_str = '%0.6f' % coeff
                        obj_func.append(coeff_str + '*' + tc)
                f.write('+'.join(obj_func).replace('+-', '-') + ';\n')
                # constraints
                c_no = 1
                for lhs, ctype, rhs in constraints:
                    f.write('subject to c%s: %s;\n' % (str(c_no), lhs + ctype + str(rhs)))
                    c_no += 1
        elif self.config['output_format'] == 'couenne_ampl':  # ampl format
            # tc_to_coeff is a string here
            assert self.config['nonlinear']
            assert not self.config['relax']
            out_path = os.path.join(self.proj_dir, self.config['name'] + '.ampl')
            with open(out_path, 'w') as f:
                # var declaration
                for t in self.tc_set:
                    f.write('var %s binary;\n' % t)
                if 'min' in self.config['min_or_max']:
                    f.write('minimize obj:')
                else:
                    f.write('maximize obj:')
                # objctive function
                f.write(tc_to_coeff + ';\n')
                # constraints
                c_no = 1
                for lhs, ctype, rhs in constraints:
                    f.write('subject to c%s: %s;\n' % (str(c_no), lhs + ctype + str(rhs)))
                    c_no += 1
        elif self.config['output_format'] == 'mints': 
            # reorder and remap all test cases sequentially
            tc_to_newid = dict()
            t_index = 1
            for t in self.tc_set:
                if t not in tc_to_newid.keys():
                    tc_to_newid[t] = t_index
                    t_index += 1
            out_path = os.path.join(self.proj_dir, self.config['name'] + '.mints.mapping.json')
            with open(out_path, 'w') as f:
                json.dump(tc_to_newid, f, indent=2, sort_keys=True)
            # objective function
            # tc_to_coeff is a dict here
            out_path = os.path.join(self.proj_dir, self.config['name'] + '.relative')
            with open(out_path, 'w') as f:
                f.write('1\n')
                tc_list = tc_to_coeff.keys()
                newid_list = [tc_to_newid[t] for t in tc_list]
                coeff_list = [tc_to_coeff[t] for t in tc_list]
                tmp_out = list()
                assert len(tc_to_newid) == len(tc_list)
                for i in range(1, len(tc_to_newid)+1):
                    assert i in newid_list
                    idx = newid_list.index(i)
                    coeff = int(coeff_list[idx] * 1000000)
                    tmp_out.append(str(coeff))
                f.write(' '.join(tmp_out) + '\n')
            # constraints
            out_path = os.path.join(self.proj_dir, self.config['name'] + '.absolute')
            with open(out_path, 'w') as f:
                for lhs, ctype, rhs in constraints:
                    assert ctype == '>=' and rhs == 1
                    f.write('b\n1\n')
                    tc_list = lhs.split('+')
                    newid_list = [tc_to_newid[tc] for tc in tc_list]
                    tmp_out = list()
                    for i in range(1, len(tc_to_newid)+1):
                        if i in newid_list:
                            tmp_out.append('1')
                        else:
                            tmp_out.append('0')
                    f.write(' '.join(tmp_out) + '\n')
        else:
            assert False  # not implemented yet
    

if __name__ == '__main__':
    proj_dir = sys.argv[1]
    config_fname = sys.argv[2]
    formulator = Formulator(proj_dir, config_fname)
    formulator.gen_model()
