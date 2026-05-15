# -*- coding: utf-8 -*-
"""
@author: psz2007
"""

# this code is for showing basic rules for aic factory
# its time complexity is too high to solve the problem
# so it is not used in the final solution

import sys

mach = [{
    "size": [2, 2]
}, {
    "size": [5, 5],
    -2: [[3, 1], [3, 3]],
    -1: [[2, 1], [2, 3]],
    1: [[0, 1], [0, 3]],
    2: [[1, 1], [1, 3]],
}, {
    "size": [3, 3],
    -2: [[3, 1]]
}, {
    "size": [3, 3],
    2: [[3, 1]]
}, {
    "size": [3, 3],
    1: [[0, 0], [0, 1], [0, 2]],
    -1: [[2, 0], [2, 1], [2, 2]]
}, {
    "size": [3, 3],
    1: [[0, 0], [0, 1], [0, 2]],
    -1: [[2, 0], [2, 1], [2, 2]]
}, {
    "size": [1, 3],
    1: [[0, 1]]
}, {
    "size": [1, 3],
    -1: [[0, 1]]
}]
belt = [
    [2, 1, 3],
    [2, 2, 1],
    [1, 7, 4],
    [1, 4, 5],
    [1, 5, 1],
    [1, 1, 6],
]
n = 10
a = [[-1 for i in range(n)] for i in range(n)]
b = [[[-1 for i in range(n)] for i in range(n)] for i in range(3)]
d = [[1, 0], [0, 1], [-1, 0], [0, -1]]
col = [[-1 for i in range(n)] for i in range(n)]
pos = [[-1, -1] for i in range(len(mach))]
dir = [-1 if i < 5 else 0 for i in range(len(mach))]


def print_map():
    print(dir)
    for i in range(n):
        for j in range(n):
            print(a[i][j] if a[i][j] >= 0 else '*', end=' ')
        print()
    print()
    for i in range(n):
        for j in range(n):
            print(b[1][i][j] if b[1][i][j] >= 0 else '*', end=' ')
        print()
    print()
    for i in range(n):
        for j in range(n):
            print(b[2][i][j] if b[2][i][j] >= 0 else '*', end=' ')
        print()
    print()


tmp = [[] for i in range(len(belt))]


def connect(px, py, bx, by, typ, cur):
    if px == bx and py == by:
        place_belt(cur + 1)
    for i in range(4):
        qx, qy = px+d[i][0], py+d[i][1]
        if qx < 0 or qy < 0 or qx >= n or qy >= n or a[qx][qy] >= 0 or b[typ][qx][qy] >= 0:
            continue
        b[typ][qx][qy] = cur
        tmp[cur].append([qx, qy])
        connect(qx, qy, bx, by, typ, cur)
        tmp[cur].pop()
        b[typ][qx][qy] = -1

    return False


def calc_pos(num, pos, n, m, x, y):
    return [[x+n-1, y+pos], [x+n-1-pos, y+m-1], [x, y+m-1-pos], [x+pos, y]][num]


cur_id = 0


def place_belt(id):
    global tmp, cur_id
    if id >= cur_id:
        cur_id = id + 1
        print(f'cur = {cur_id}')
        print_map()
    if id >= len(belt):
        sys.exit(0)
    typ, frm, to = belt[id]
    dir1, dir2 = [], []
    if dir[frm] < 0:
        dir1 = [0, 1, 2, 3]
    else:
        dir1 = [dir[frm]]
    if dir[to] < 0:
        dir2 = [0, 1, 2, 3]
    else:
        dir2 = [dir[to]]
    for i in dir1:
        for j in dir2:
            dir[frm], dir[to] = i, j
            for p1 in mach[frm][-typ]:
                for p2 in mach[to][typ]:
                    d1, d2 = (p1[0]+i) % 4, (p2[0]+j) % 4
                    ax, ay = calc_pos(
                        d1, p1[1], mach[frm]["size"][0], mach[frm]["size"][1], pos[frm][0], pos[frm][1])
                    bx, by = calc_pos(
                        d2, p2[1], mach[to]["size"][0], mach[to]["size"][1], pos[to][0], pos[to][1])
                    atx, aty, btx, bty = ax + \
                        d[d1][0], ay+d[d1][1], bx+d[d2][0], by+d[d2][1]
                    if atx < 0 or aty < 0 or btx < 0 or bty < 0 or atx >= n or aty >= n or btx >= n or bty >= n:
                        continue
                    if ax == btx and ay == bty:
                        continue
                    if col[atx][aty] != col[btx][bty]:
                        continue
                    connect(ax, ay, bx + d[d2][0], by + d[d2][1], typ, id)

    if len(dir1) > 1:
        dir[frm] = -1
    if len(dir2) > 1:
        dir[to] = -1


def paint_pos(px, py, c):
    global col
    col[px][py] = c
    for i in range(4):
        qx, qy = px+d[i][0], py+d[i][1]
        if qx < 0 or qy < 0 or qx >= n or qy >= n or a[qx][qy] >= 0 or col[qx][qy] >= 0:
            continue
        paint_pos(qx, qy, c)


def paint_map():
    global col
    col = [[-1 for i in range(n)] for i in range(n)]
    cur = 0
    for i in range(n):
        for j in range(n):
            if a[i][j] < 0 and col[i][j] < 0:
                paint_pos(i, j, cur)
                cur += 1


def place_mach(id):
    if id >= len(mach):
        paint_map()
        place_belt(0)
        return
    p, q = mach[id]["size"]
    for i in range(n-p+1):
        if mach[id]["size"][0] == 1 and i > 0:
            break
        for j in range(n-q+1):
            flg = True
            for x in range(i, i+p):
                for y in range(j, j+q):
                    if a[x][y] != -1:
                        flg = False
                        break
            if flg:
                for x in range(i, i+p):
                    for y in range(j, j+q):
                        a[x][y] = id
                pos[id] = [i, j]
                place_mach(id+1)
                pos[id] = [-1, -1]
                for x in range(i, i+p):
                    for y in range(j, j+q):
                        a[x][y] = -1


place_mach(0)
