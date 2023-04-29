# variable lines
def variable_line(names):
    if len(names) != 0:
        # variables
        var_lines = []
        var_types = list(names.keys())
        for v in var_types:
            temp_line = []
            temp_line.append(str(v))
            cnt = 0
            for t in names[v]:
                cnt += 1
                if cnt == len(names[v]):
                    temp_line.append(str(t))
                    break
                else:
                    temp_line.append(str(t))
                    temp_line.append(',')

            temp_line.append(';')

            var_lines.append(" ".join(temp_line))

        return var_lines
    else:
        return


# temp lines
def temp_variable_line(temps):
    if len(temps) != 0:
        res = []
        temp_lines = []
        temp_lines.append('int')
        cnt = 0
        for t in temps:
            cnt += 1
            if cnt == len(temps):
                temp_lines.append(t)
                break
            else:
                temp_lines.append(t)
                temp_lines.append(',')
        temp_lines.append(';')
        res.append(" ".join(temp_lines))
        return res
    else:
        return


def quad_line(quadruples):
    res = []
    for q in quadruples:
        if q[0] == 'endblock':
            continue
        elif 'goto' in q[0] and len(q[0]) == 4:
            res.append('goto' + str(q[1]) + ';')
        elif 'goto' in q[0] and len(q[0]) > 4:
            res.append(q[0] + str(q[1]) + ';')
        else:
            res.append(q[0] + ';')
    return res


def c_code_generator(quadruples, names, temps):
    program_lines = []

    names_line = variable_line(names)
    temps_line = temp_variable_line(temps)

    header = '#include <stdio.h>'

    program_lines.append(header)
    if names_line is not None:
        program_lines.append(names_line[0])
    if temps_line is not None:
        program_lines.append(temps_line[0])
    main = 'int main()'
    program_lines.append(main)
    program_lines.append('{')

    quad_lines = quad_line(quadruples)
    program_lines.extend(quad_lines)

    program_lines.append('}')

    # writing to file
    file = open('main.c', 'w')
    for item in program_lines:
        file.write(str(item) + "\n")
    file.close()
