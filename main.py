# -*- coding: utf-8 -*-
"""
@author: psz2007 (Entelecheia#2049)
"""

# environment constants
_max_timeout = 1200 # (s)
_worker_num = 12 # depends on your CPU core counts
_debug_on = True # set to False to avoid output spam
_optimal = False # setting this as True may lead to efficiency problems
_print_with_box_chars = True # set to False if box-drawing characters (┏┃┗┓━┛╋) are unavailable

# mach parameter meaning:
# Types:
# "mach": Machines. Use power.
# "stor": Storages. Don't need power.
# "port": Ports. Don't need power. Restricted position. (On the first row)
# "elec": Electric pylons. Provide power.
# "logi": Logistics (splitter/converger but not bridges). Don't need power. I/O can be set directly.
# Size: [n, m] for a nxm facility.
# Numbers: -2 for pipe output. -1 for belt output. 1 for belt input. 2 for pipe input.
# [[p, x]]: p = 0, 1, 2, 3 indicates the port is on the down/right/up/left side of the facility.
# x indicates how far the port is from the DL/DR/UR/UL corner.
# "dist": How far the pylon can transmit power.

# belt:
# [t, x, y] means there's a belt(t=1)/pipe(t=2) from the facility numbered x to one numbered y.

# === facility & belt data STARTS HERE ===
mach = [{
    "type": "mach",
    "size": [5, 5],
    -2: [[3, 1], [3, 3]],
    -1: [[2, 1], [2, 3]],
    1: [[0, 1], [0, 3]],
    2: [[1, 1], [1, 3]],
}, {
    "type": "stor",
    "size": [3, 3],
    -2: [[0, 1]]
}, {
    "type": "mach",
    "size": [3, 3],
    2: [[0, 1]]
}, {
    "type": "mach",
    "size": [3, 3],
    1: [[0, 0], [0, 1], [0, 2]],
    -1: [[2, 0], [2, 1], [2, 2]]
}, {
    "type": "mach",
    "size": [3, 3],
    1: [[0, 0], [0, 1], [0, 2]],
    -1: [[2, 0], [2, 1], [2, 2]]
}, {
    "type": "port",
    "size": [1, 3],
    1: [[0, 1]]
}, {
    "type": "port",
    "size": [1, 3],
    -1: [[0, 1]]
}, {
    "type": "elec",
    "size": [2, 2],
    "dist": 5
}]
belt = [
    [2, 0, 2],
    [2, 1, 0],
    [1, 6, 3],
    [1, 3, 4],
    [1, 4, 0],
    [1, 0, 5],
]
n = 10
m = 10
# === facility & belt data ENDS HERE ===

def print_vars(md):
    prt = md.Proto()
    print(f"Variables count: {len(prt.variables)}")
    print(f"Constraints count: {len(prt.constraints)}")
    var_cnt = {"int": 0, "bool": 0}
    for v in prt.variables:
        var_cnt["bool" if v.domain and len(v.domain) == 2 and v.domain[0] == 0 and v.domain[1] == 1 else "int"] += 1
    for i in var_cnt:
        print(f"Var {i} count: {var_cnt[i]}")

from ortools.sat.python import cp_model

md = cp_model.CpModel()

print("Data loaded")

# define variables for the facilities & ports
port = {}
mach_var = []
rot = [[] for _ in range(len(mach))]
for i, ma in enumerate(mach):
    h, w = ma["size"]
    mach_var.append([
        md.new_int_var(0, n-1, f"mach_{i}_x"),
        md.new_int_var(0, m-1, f"mach_{i}_y"),
        md.new_int_var(0, 3, f"mach_{i}_r"),
        md.new_bool_var(f"mach_{i}_p"),
        md.new_int_var(0, n-1, f"mach_{i}__h"),
        md.new_int_var(0, m-1, f"mach_{i}__w")
    ])
    x, y, r, p, _h, _w = mach_var[-1]
    md.add(x == 0).only_enforce_if(ma["type"] == "port")
    md.add(r == 0).only_enforce_if(ma["type"] == "port" or ma["type"] == "elec")
    if h != w:
        md.add_linear_expression_in_domain(r, cp_model.Domain.from_values([0, 2])).only_enforce_if(p.Not())
        md.add_linear_expression_in_domain(r, cp_model.Domain.from_values([1, 3])).only_enforce_if(p)
    else:
        md.add(p == False)
    md.add(_h == h).only_enforce_if(p.Not())
    md.add(_w == w).only_enforce_if(p.Not())
    md.add(_h == w).only_enforce_if(p)
    md.add(_w == h).only_enforce_if(p)
    md.add(x + _h <= n)
    md.add(y + _w <= m)
    rot[i] = [md.new_bool_var(f"mach_{i}_rot_{k}") for k in range(4)]
    for k in range(4):
        md.add(r == k).only_enforce_if(rot[i][k])
        md.add(r != k).only_enforce_if(rot[i][k].Not())

    for d in [-2, -1, 1, 2]:
        if d in ma:
            for id, p in enumerate(ma[d]):
                num, pos = p
                x_list = [x + _h - 1, x + _h - 1 - pos, x, x + pos]
                y_list = [y + pos, y + _w - 1, y + _w - 1 - pos, y]
                tmp_x = md.new_int_var(0, n-1, f"mach_{i}_port_{d}_{id}_x")
                tmp_y = md.new_int_var(0, m-1, f"mach_{i}_port_{d}_{id}_y")
                tmp_d = md.new_int_var(0, 3, f"mach_{i}_port_{d}_{id}_d")
                for k in range(4):
                    md.add(tmp_x == x_list[k]).only_enforce_if(rot[i][(k-num+4) % 4])
                    md.add(tmp_y == y_list[k]).only_enforce_if(rot[i][(k-num+4) % 4])
                    md.add(tmp_d == k).only_enforce_if(rot[i][(k-num+4) % 4])
                port[(i, d, id)] = (tmp_x, tmp_y, tmp_d)

# an alternative way to make facilities not overlap
'''
x_intv = []
y_intv = []
for i, ma in enumerate(mach):
    x, y, r, p, _h, _w = mach_var[i]
    _x = md.new_int_var(0, n-1, f"mach_{i}__x")
    _y = md.new_int_var(0, m-1, f"mach_{i}__y")
    md.add(_x == x + _h)
    md.add(_y == y + _w)
    x_intv.append(md.new_interval_var(x, _h, _x, f"mach_{i}_x_intv"))
    y_intv.append(md.new_interval_var(y, _w, _y, f"mach_{i}_y_intv"))
md.add_no_overlap_2d(x_intv, y_intv)
'''

# make facilities not overlap
mp = {}
bmp = {}
for i in range(n):
    for j in range(m):
        tmp = []
        for k, ma in enumerate(mach_var):
            cur = md.new_bool_var(f"occ_{i}_{j}_{k}")
            b1 = md.new_bool_var(f"occ_{i}_{j}_{k}_1")
            b2 = md.new_bool_var(f"occ_{i}_{j}_{k}_2")
            b3 = md.new_bool_var(f"occ_{i}_{j}_{k}_3")
            b4 = md.new_bool_var(f"occ_{i}_{j}_{k}_4")
            x, y, r, p, _h, _w = ma
            md.add(x <= i).only_enforce_if(b1)
            md.add(x > i).only_enforce_if(b1.Not())
            md.add(y <= j).only_enforce_if(b2)
            md.add(y > j).only_enforce_if(b2.Not())
            md.add(x + _h - 1 >= i).only_enforce_if(b3)
            md.add(x + _h - 1 < i).only_enforce_if(b3.Not())
            md.add(y + _w - 1 >= j).only_enforce_if(b4)
            md.add(y + _w - 1 < j).only_enforce_if(b4.Not())
            md.add_bool_and([b1, b2, b3, b4]).only_enforce_if(cur)
            md.add_bool_or([b1.Not(), b2.Not(), b3.Not(), b4.Not()]).only_enforce_if(cur.Not())
            mp[(i, j, k)] = cur
            b = md.new_bool_var(f"b_{i}_{j}_{k}")
            md.add(cur == 0).only_enforce_if(b.Not())
            md.add(cur > 0).only_enforce_if(b)
            tmp.append(cur)

        bmp[(i, j)] = md.new_bool_var(f"bmp_{i}_{j}")
        md.add_bool_or(tmp).only_enforce_if(bmp[(i, j)])
        md.add_bool_and([t.Not() for t in tmp]).only_enforce_if(bmp[(i, j)].Not())
        md.add_at_most_one(tmp)

dir = [[1, 0], [0, 1], [-1, 0], [0, -1]]

# check if the electric pylons can provide enough power
emp = [None for _ in range(n*m)]
for i in range(n):
    for j in range(m):
        pos = i*m+j
        emp[pos] = md.new_bool_var(f"emp_{i}_{j}")
        e_list = []
        for id, ma in enumerate(mach):
            if ma["type"] == "elec":
                # here we assume h == w
                x, y, r, _, h, w = mach_var[id]
                d = mach[id]["dist"]
                b1 = md.new_bool_var(f"elec_{i}_{j}_{id}_b1")
                b2 = md.new_bool_var(f"elec_{i}_{j}_{id}_b2")
                b3 = md.new_bool_var(f"elec_{i}_{j}_{id}_b3")
                b4 = md.new_bool_var(f"elec_{i}_{j}_{id}_b4")
                b5 = md.new_bool_var(f"elec_{i}_{j}_{id}_b5")
                md.add(i < x+h+d).only_enforce_if(b1)
                md.add(j < y+w+d).only_enforce_if(b2)
                md.add(i >= x+h+d).only_enforce_if(b1.Not())
                md.add(j >= y+w+d).only_enforce_if(b2.Not())
                md.add(i >= x-d).only_enforce_if(b3)
                md.add(j >= y-d).only_enforce_if(b4)
                md.add(i < x-d).only_enforce_if(b3.Not())
                md.add(j < y-d).only_enforce_if(b4.Not())
                md.add_bool_and([b1, b2, b3, b4]).only_enforce_if(b5)
                md.add_bool_or([b1.Not(), b2.Not(), b3.Not(), b4.Not()]).only_enforce_if(b5.Not())
                e_list.append(b5)
        md.add_bool_and(e_list).only_enforce_if(emp[pos])
        md.add_bool_or([a.Not() for a in e_list]).only_enforce_if(emp[pos].Not())
for id, ma in enumerate(mach):
    if ma["type"] == "mach":
        occ_list = []
        h, w = ma["size"]
        x, y, d, p, _h, _w = mach_var[id]
        for i in range(h):
            for j in range(w):
                cur_pos = md.new_int_var(0, n*m-1, f"emach_{id}_{i}_{j}_pos")
                cur_b = md.new_bool_var(f"emach_{id}_{i}_{j}_b")
                md.add(cur_pos == (x+i)*m+y+j).only_enforce_if(p.Not())
                md.add(cur_pos == (x+j)*m+y+i).only_enforce_if(p)
                md.add_element(cur_pos, emp, cur_b)
                occ_list.append(cur_b)
        md.add_bool_or(occ_list)

def gid(x, y, d): return [
    x*m+y if x < n-1 else -1,
    x*(m-1)+y+1+(n-1)*m if y < m-1 else -1,
    (x-1)*m+y if x > 0 else -1,
    x*(m-1)+y+(n-1)*m if y > 0 else -1][d]

# set constraints for belts
tot = n*(m-1)+(n-1)*m
belt_var = []
for id in range(len(belt)):
    typ, frm, to = belt[id]
    cur = [md.new_bool_var(f"belt_{id}_{i}") for i in range(tot)]
    cur.append(0)
    belt_var.append(cur)
    frm_cnt = len(mach[frm][-typ])
    to_cnt = len(mach[to][typ])
    ch_frm = md.new_int_var(0, frm_cnt - 1, f"choice_{id}_out")
    ch_to = md.new_int_var(0, to_cnt - 1, f"choice_{id}_in")
    frm_x_lst = []
    frm_y_lst = []
    frm_d_lst = []
    to_x_lst = []
    to_y_lst = []
    to_d_lst = []
    for k in range(frm_cnt):
        frm_x_lst.append(port[(frm, -typ, k)][0])
        frm_y_lst.append(port[(frm, -typ, k)][1])
        frm_d_lst.append(port[(frm, -typ, k)][2])
    for k in range(to_cnt):
        to_x_lst.append(port[(to, typ, k)][0])
        to_y_lst.append(port[(to, typ, k)][1])
        to_d_lst.append(port[(to, typ, k)][2])

    tg_frm_x = md.new_int_var(0, n - 1, f"pos_{id}_out_x")
    tg_frm_y = md.new_int_var(0, m - 1, f"pos_{id}_out_y")
    tg_frm_d = md.new_int_var(0, 3, f"pos_{id}_out_d")
    tg_to_x = md.new_int_var(0, n - 1, f"pos_{id}_in_x")
    tg_to_y = md.new_int_var(0, m - 1, f"pos_{id}_in_y")
    tg_to_d = md.new_int_var(0, 3, f"pos_{id}_in_d")
    frm_dir = []
    to_dir = []
    for k in range(4):
        var = md.new_bool_var(f"dir_frm_{id}_{k}")
        md.add(tg_frm_d == k).only_enforce_if(var)
        md.add(tg_frm_d != k).only_enforce_if(var.Not())
        frm_dir.append(var)
    for k in range(4):
        var = md.new_bool_var(f"dir_to_{id}_{k}")
        md.add(tg_to_d == k).only_enforce_if(var)
        md.add(tg_to_d != k).only_enforce_if(var.Not())
        to_dir.append(var)

    md.add_element(ch_frm, frm_x_lst, tg_frm_x)
    md.add_element(ch_frm, frm_y_lst, tg_frm_y)
    md.add_element(ch_frm, frm_d_lst, tg_frm_d)
    md.add_element(ch_to, to_x_lst, tg_to_x)
    md.add_element(ch_to, to_y_lst, tg_to_y)
    md.add_element(ch_to, to_d_lst, tg_to_d)
    tg_dx = {}
    tg_dy = {}
    for d in [-1, 0, 1]:
        dx = md.new_bool_var(f"diff_{id}_x_{d}")
        dy = md.new_bool_var(f"diff_{id}_y_{d}")
        md.add(tg_to_x - tg_frm_x != d).only_enforce_if(dx.Not())
        md.add(tg_to_y - tg_frm_y != d).only_enforce_if(dy.Not())
        tg_dx[d] = dx
        tg_dy[d] = dy
    is_logi = md.new_bool_var(f"is_logi_{id}")
    md.add(mach[frm]["type"] == "logi" or mach[to]["type"] == "logi").only_enforce_if(is_logi)
    md.add(mach[frm]["type"] != "logi" and mach[to]["type"] != "logi").only_enforce_if(is_logi.Not())
    for k in range(4):
        md.add_bool_or([frm_dir[k].Not(), to_dir[k^2].Not(), tg_dx[dir[k][0]].Not(), tg_dy[dir[k][1]].Not()]).only_enforce_if(is_logi.Not())
    
    md.add(tg_frm_x < n-1).only_enforce_if(frm_dir[0])
    md.add(tg_frm_y < m-1).only_enforce_if(frm_dir[1])
    md.add(tg_frm_x > 0).only_enforce_if(frm_dir[2])
    md.add(tg_frm_y > 0).only_enforce_if(frm_dir[3])
    md.add(tg_to_x < n-1).only_enforce_if(to_dir[0])
    md.add(tg_to_y < m-1).only_enforce_if(to_dir[1])
    md.add(tg_to_x > 0).only_enforce_if(to_dir[2])
    md.add(tg_to_y > 0).only_enforce_if(to_dir[3])
    for i in range(n):
        for j in range(m):
            s = md.new_int_var(0, 4, f"belt_{id}_{i}_{j}")
            md.add(s == sum([cur[gid(i, j, _)] for _ in range(4)]))

            is_port = []
            b1 = md.new_bool_var(f"belt_{id}_{i}_{j}_port_b1")
            b2 = md.new_bool_var(f"belt_{id}_{i}_{j}_port_b2")
            md.add(i == tg_frm_x).only_enforce_if(b1)
            md.add(i != tg_frm_x).only_enforce_if(b1.Not())
            md.add(j == tg_frm_y).only_enforce_if(b2)
            md.add(j != tg_frm_y).only_enforce_if(b2.Not())
            for k in range(4):
                if gid(i, j, k) == -1:
                    continue
                port_rot = md.new_bool_var(f"belt_{id}_{i}_{j}_port_frm_{k}")
                md.add_bool_and([frm_dir[k], b1, b2]).only_enforce_if(port_rot)
                md.add_bool_or([frm_dir[k].Not(), b1.Not(), b2.Not()]).only_enforce_if(port_rot.Not())
                md.add(cur[gid(i, j, k)] == True).only_enforce_if(port_rot)
                is_port.append(port_rot)

            b3 = md.new_bool_var(f"belt_{id}_{i}_{j}_port_b3")
            b4 = md.new_bool_var(f"belt_{id}_{i}_{j}_port_b4")
            md.add(i == tg_to_x).only_enforce_if(b3)
            md.add(i != tg_to_x).only_enforce_if(b3.Not())
            md.add(j == tg_to_y).only_enforce_if(b4)
            md.add(j != tg_to_y).only_enforce_if(b4.Not())
            for k in range(4):
                if gid(i, j, k) == -1:
                    continue
                port_rot = md.new_bool_var(f"belt_{id}_{i}_{j}_port_to_{k}")
                md.add_bool_and([to_dir[k], b3, b4]).only_enforce_if(port_rot)
                md.add_bool_or([to_dir[k].Not(), b3.Not(), b4.Not()]).only_enforce_if(port_rot.Not())
                md.add(cur[gid(i, j, k)] == True).only_enforce_if(port_rot)
                is_port.append(port_rot)

            tmp1 = md.new_bool_var(f"belt_{id}_{i}_{j}_tmp1")
            tmp2 = md.new_bool_var(f"belt_{id}_{i}_{j}_tmp2")
            tmp3 = md.new_bool_var(f"belt_{id}_{i}_{j}_tmp3")
            md.add_bool_or(is_port).only_enforce_if(tmp1)
            md.add_bool_and([a.Not() for a in is_port]).only_enforce_if(tmp1.Not())
            md.add_bool_and([tmp1.Not(), bmp[(i, j)]]).only_enforce_if(tmp2)
            md.add_bool_or([tmp1, bmp[(i, j)].Not()]).only_enforce_if(tmp2.Not())
            md.add_bool_and([tmp1.Not(), bmp[(i, j)].Not()]).only_enforce_if(tmp3)
            md.add_bool_or([tmp1, bmp[(i, j)]]).only_enforce_if(tmp3.Not())
            md.add(s == 1).only_enforce_if(tmp1)
            md.add(s == 0).only_enforce_if(tmp2)
            md.add_linear_expression_in_domain(s, cp_model.Domain.from_values([0, 2])).only_enforce_if(tmp3)

for typ in [1, 2]:
    for i in range(tot):
        cur = []
        for j in range(len(belt)):
            if belt[j][0] == typ:
                cur.append(belt_var[j][i])
        md.add_at_most_one(cur)

# deal with intersection between belts and pipes
deg = {1: [None] * (n*m), 2: [None] * (n*m)}
intx = {1: [None] * (n*m), 2: [None] * (n*m)}
for typ in [1, 2]:
    for i in range(n):
        for j in range(m):
            deg[typ][i * m + j] = md.new_int_var(0, 4, f"deg_{i}_{j}")
            intx[typ][i * m + j] = md.new_bool_var(f"int_{i}_{j}")
            md.add(sum([belt_var[k][gid(i, j, d)] if gid(i, j, d) != -1 and belt[k][0] == typ else 0
                   for k in range(len(belt)) for d in range(4)]) == deg[typ][i * m + j])
            md.add(deg[typ][i * m + j] < 4).only_enforce_if(intx[typ][i * m + j].Not())
for i in range(n-1):
    for j in range(m-1):
        for k in range(len(belt)):
            typ = belt[k][0]
            md.add(belt_var[k][gid(i, j, 0)] == belt_var[k][gid(i, j, 2)]).only_enforce_if(intx[typ][i * m + j])
for i in range(1, n-1):
    for j in range(1, m-1):
        md.add(deg[1][i*m+j] == 0).only_enforce_if(intx[2][i*m+j])

if _optimal:
    md.minimize(sum(deg[typ][i * m + j] for typ in [1, 2] for i in range(n) for j in range(m)))
print("Constraints all set")
if _debug_on:
    print_vars(md)

print("Start solving")
solver = cp_model.CpSolver()
print(solver.parameters)
solver.parameters.max_time_in_seconds = _max_timeout
solver.parameters.num_search_workers = _worker_num
if _debug_on:
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    solver.parameters.log_subsolver_statistics = True
    solver.log_callback = print
status = solver.Solve(md)

# print results
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("OK")

    # ---- 导出结构化求解结果到 solution.json (供可视化编辑器使用) ----
    import json
    sol_machs = []
    for id, t in enumerate(mach_var):
        tx, ty, tr, tp, _h, _w = t
        sol_machs.append({
            "id": id,
            "type": mach[id]["type"],
            "size": list(mach[id]["size"]),
            "pos": [solver.value(tx), solver.value(ty)],   # 求解后的左上角格子 (行, 列)
            "rot": solver.value(tr),                        # 0/1/2/3 旋转 90° 的次数
            "p":   bool(solver.value(tp)),                  # 是否做了镜像 (h、w 互换)
            "occ_h": solver.value(_h),                      # 实际占用 h
            "occ_w": solver.value(_w),                      # 实际占用 w
            **({"dist": mach[id]["dist"]} if mach[id]["type"] == "elec" else {}),
        })
        # 端口实际位置（按求解器规则，参见 main.py 顶部 port[] 字典）
        sol_ports = []
        for d in [-2, -1, 1, 2]:
            if d in mach[id]:
                for pid, _ in enumerate(mach[id][d]):
                    px, py, pd = port[(id, d, pid)]
                    sol_ports.append({
                        "kind": d,                          # -2/-1/1/2
                        "orig": list(mach[id][d][pid]),     # 输入定义的 [side, pos]
                        "cell": [solver.value(px), solver.value(py)],  # 端口所在格子 (行,列)
                        "dir":  solver.value(pd),           # 旋转后端口朝向 0/1/2/3
                    })
        sol_machs[-1]["ports"] = sol_ports

    # 提取每条 belt 的实际占用边
    sol_belts = []
    for bi, (typ, frm, to) in enumerate(belt):
        edges = []  # 每条边记成 (cell_a, cell_b)，cell = [行, 列]
        for i in range(n):
            for j in range(m):
                # d=0: 向下到 (i+1, j) ; d=1: 向右到 (i, j+1)
                if i < n-1 and gid(i, j, 0) != -1 and solver.value(belt_var[bi][gid(i, j, 0)]):
                    edges.append([[i, j], [i+1, j]])
                if j < m-1 and gid(i, j, 1) != -1 and solver.value(belt_var[bi][gid(i, j, 1)]):
                    edges.append([[i, j], [i, j+1]])
        sol_belts.append({"type": typ, "frm": frm, "to": to, "edges": edges})

    solution = {"n": n, "m": m, "machs": sol_machs, "belts": sol_belts}
    try:
        with open("solution.json", "w", encoding="utf-8") as f:
            json.dump(solution, f, ensure_ascii=False, indent=2)
        print("Solution exported to solution.json")
    except Exception as e:
        print(f"Failed to write solution.json: {e}")
    # ---- 结构化输出结束 ----

    board = [["." for _ in range(m)] for _ in range(n)]
    for id, t in enumerate(mach_var):
        tx, ty, tr, tp, _h, _w = t
        x = solver.value(tx)
        y = solver.value(ty)
        h = solver.value(_h)
        w = solver.value(_w)
        for i in range(x, x+h):
            for j in range(y, y+w):
                board[i][j] = str(id) if id < 10 else chr(ord('a') + id - 10)

    for typ in [1, 2]:
        print(["Belt: ", "Pipe: "][typ - 1])
        if not _print_with_box_chars:
            for i, row in enumerate(board):
                if i > 0:
                    for j in range(m):
                        flg = False
                        for k in range(len(belt)):
                            if belt[k][0] == typ:
                                flg |= solver.value(belt_var[k][gid(i, j, 2)])
                        print('|' if flg else ' ', end=' ')
                    print()
                for j in range(m):
                    flg = False
                    if j > 0:
                        for k in range(len(belt)):
                            if belt[k][0] == typ:
                                flg |= solver.value(belt_var[k][gid(i, j, 3)])
                    print(('' if j == 0 else '-' if flg else ' ') + board[i][j], end='')
                print()
            print()
        else:
            for i in range(n):
                for j in range(m):
                    if board[i][j] == '.':
                        flg = sum([solver.value(belt_var[k][gid(i, j, d)] if gid(i, j, d) != -1 and belt[k][0] == typ else 0) * 2 ** d
                                for k in range(len(belt)) for d in range(4)])
                        chr = {0: '.', 3: '┏', 5: '┃', 6: '┗', 9: '┓', 10: '━', 12: '┛', 15: '╋'}.get(flg, '?')
                        print(chr, end='')
                    else:
                        print(board[i][j], end='')
                print()
            print()
    print()
elif status == cp_model.UNKNOWN:
    print("TL")
elif status == cp_model.INFEASIBLE:
    print("NO")
elif status == cp_model.MODEL_INVALID:
    print("Invalid model")
else:
    print("Return code: ", status)

if _debug_on:
    print(solver.response_stats())
