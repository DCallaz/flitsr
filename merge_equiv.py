
def merge_on_row(row, groups):
    """Given one row in the table, merge the groups"""
    new_groups = []
    for group in groups:
        eq = [group[0]]
        neq = []
        for elem in group[1:]:
            if (row[elem+1] == row[group[0]+1]):
                eq.append(elem)
            else:
                neq.append(elem)
        if (eq != []):
            new_groups.append(eq)
        if (neq != []):
            new_groups.append(neq)
    return new_groups

def remove_from_table(groups, table, counts):
    """Remove the unnecessary elements that are within the groups from the table"""
    remove = []
    for group in groups:
        remove.extend(group[1:])
    remove.sort(reverse=True)
    counts["locs"] -= len(remove)
    for rem in remove:
        counts["p"].pop(rem)
        counts["f"].pop(rem)
        for row in table:
            row.pop(rem+1)
