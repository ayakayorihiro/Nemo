#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import xml.etree.ElementTree
import json

cov_fname = 'cov.info'
fault_fname = 'fault.info'
rtime_fname = 'rtime.info'
proj_path = sys.argv[1]
sol_fname = sys.argv[2]  # linear.sol.cplex | nonlinear.sol.couenne | minisat | obpdp
out_file = sys.argv[3]
assert proj_path
assert sol_fname


def load_mints_mapping():
    tc_to_newid = dict()
    newid_to_tc = dict()
    assert os.path.exists(os.path.join(proj_path, 'linear_so.mints.mapping.json'))
    with open(os.path.join(proj_path, 'linear_so.mints.mapping.json'), 'r') as f:
        tc_to_newid = json.load(f)
    for tc, newid in tc_to_newid.items():
        k = 't' + str(newid)
        if k not in newid_to_tc.keys():
            newid_to_tc[k] = tc
    return newid_to_tc
    
def get_selected_tcs(fname):
    selected_tcs = list()
    if fname.endswith('.sol'):
        with open(os.path.join(proj_path, fname), 'r') as f:
            for line in f:
                if line.startswith('t'):
                    # e.g. t6                              0
                    #      t57                             1
                    if line.split()[1] == '1':
                        selected_tcs.append(line.split()[0])
                    else:
                        assert line.split()[1] == '0'
    elif fname.endswith('.soplex'):
        with open(os.path.join(proj_path, fname), 'r') as f:
            is_start = False
            for line in f:
                if line.startswith('Primal solution'):
                    is_start = True
                    continue
                if is_start and line.startswith('All other variables'):
                    is_start = False
                if not is_start:
                    continue
                else:
                    assert line.startswith('t')
                    # e.g. t1854                                       0.1e1
                    #      t1854                                       0.1e1
                    selected_tcs.append(line.split()[0])
    elif fname.endswith('.bpmpd'):
        with open(os.path.join(proj_path, fname), 'r') as f:
            is_start = False
            for line in f:
                if line.startswith(' -------------C-O-L-U-M-N-S'):
                    is_start = True
                    continue
                if is_start and line.startswith(' ---------------S-L-A-C-K---R-E-'):
                    is_start = False
                if not is_start:
                    continue
                else:
                    if line.startswith(' t'):
                        # e.g. t1459     0.00000000000E+00 CHEPDU  0.10000000000E+01
                        #      t1453     0.10000000000E+01 CHEPDU  0.96153800000E+00
                        if line.split()[1] == '0.10000000000E+01':
                            selected_tcs.append(line.split()[0])
                        elif line.split()[1] != '0.00000000000E+00':
                            print line.split()[1]
    elif fname.endswith('.cplex'):
        with open(os.path.join(proj_path, fname), 'r') as f:
            is_start = False
            for line in f:
                if line.startswith('CPLEX> Variable Name') or line.startswith('CPLEX> Incumbent solution'):
                    is_start = True
                    continue
                if is_start and line.startswith('All other variables'):
                    is_start = False
                if not is_start:
                    continue
                else:
                    assert line.startswith('t') or line.startswith('Variable Name') or line.startswith('v_')
                    if line.startswith('t'):
                        assert line.split()[1] == '1.000000'
                        # e.g. t1431                         1.000000
                        selected_tcs.append(line.split()[0])
                    elif line.startswith('v_'):
                        assert line.split()[1] == '1.000000'
    elif fname.endswith('.xml'):
        e = xml.etree.ElementTree.parse(os.path.join(proj_path, fname)).getroot()
        for v in e.find('variables').findall('variable'):
            if v.get('name').startswith('t'):
                if v.get('value') == '1':
                    selected_tcs.append(v.get('name'))
                else:
                    assert v.get('value') == '0' or v.get('value') == '-0'
    elif fname.endswith('minisat'):  # for MINTS-minisat+
        newid_to_tc = load_mints_mapping()
        with open(os.path.join(proj_path, fname), 'r') as f:
            for line in f:
                if line.startswith('v'):
                    tcs = line.split()[1:]
            for tc in tcs:
                if tc.startswith('x'):
                    selected_tcs.append(newid_to_tc[tc.replace('x', 't')])
    elif fname.endswith('opbdp'):  # for MINTS-opbdp
        # 0-1 Variables fixed to 1 : x1 x6 x21 x33
        newid_to_tc = load_mints_mapping()
        with open(os.path.join(proj_path, fname), 'r') as f:
            for line in f:
                if line.startswith('0-1 Variables'):
                    tcs = line.split()[5:]
            for tc in tcs:
                if tc.startswith('x'):
                    selected_tcs.append(newid_to_tc[tc.replace('x', 't')])
    elif fname.endswith('couenne'):
        with open(os.path.join(proj_path, fname), 'r') as f:
            is_var_start = False
            for line in f:
                if line.startswith(':') and '_varname' in line:
                    is_var_start = True
                    continue
                if not is_var_start:
                    continue
                if line.startswith(';'):
                    break
                # 488   t424     0
                # t_index, t_id, t_value = line.split()
                if line.split()[2] == '1':
                    selected_tcs.append(line.split()[1])
                else:
                    assert line.split()[2] == '0' or line.split()[2][-4:] in ['e-15', 'e-14', 'e-47']
    elif 'Neos' in fname:
        with open(fname, 'rU') as f:
            for line in f:
                sp = ',' if ',' in line else '='
                tc, value = line.split(sp)
                value = value.strip()
                if value in ['1', '1.00E+00']:
                    selected_tcs.append(tc)
                elif value in ['0', '2.22E-16', '0.00E+00', '1.11E-15', '1.03E-09', '1.12E-09', '1.11E-09', '1.14E-09', '5.11E-10']:
                    pass
                else:
                    print value
                    assert False
    else:
        print 'Wrong solution file'
        assert False
    return selected_tcs


def get_coverage(fname, crio_type, is_multiple, selected_tcs):
    crio_set = set()
    tc_to_crio = dict()
    crio_to_tc = dict()
    with open(os.path.join(proj_path, fname), 'r') as f:
        for line in f:
            # e.g. t2:
            #      t3:1 3
            tc = line.split(':')[0]
            if is_multiple:
                c_list = line.split(':')[1].split()
                tc_to_crio[tc] = c_list
                if len(c_list) > 0:
                    for c in c_list:
                        crio_set.add(c)
                        if crio_type == 'faults':
                            if c not in crio_to_tc.keys():
                                crio_to_tc[c] = [tc]
                            else:
                                crio_to_tc[c].append(tc)
            else:
                if line.split(':')[1].replace('\n', ''):
                    value = int(line.split(':')[1])
                    tc_to_crio[tc] = value
    if is_multiple:
        print '# %s by original suite: %d' % (crio_type, len(crio_set))
    else:
        print '# %s by original suite: %d' % (crio_type, sum([v for _, v in tc_to_crio.items()]))

    # Reduced test suite
    selected_crio_set = set()
    for tc in selected_tcs:
        if is_multiple:
            for crio in tc_to_crio[tc]:
                selected_crio_set.add(crio)
    if is_multiple:
        print '# %s by minimized suite: %d' % (crio_type, len(selected_crio_set))
    else:
        print '# %s by minimized suite: %d' % (crio_type, sum([tc_to_crio[tc] for tc in selected_tcs]))

def output_selected_tcs(selected_tcs):
    with open(out_file, "w") as f:
        for tst in selected_tcs:
            f.write(tst + "\n")

if __name__ == '__main__':
    selected_tcs = get_selected_tcs(sol_fname)
    output_selected_tcs(selected_tcs)
    print 'Minimized test suite:', selected_tcs
    print '# Minimized test suite:', len(selected_tcs)
    get_coverage(cov_fname, 'Statements', True, selected_tcs)
    get_coverage(fault_fname, 'Faults', True, selected_tcs)
    # get_coverage(rtime_fname, 'Running time', False, selected_tcs)

