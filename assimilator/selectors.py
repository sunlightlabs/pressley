from operator import attrgetter

def projected_selector(projection, selector, rows):
    """
    Selects the first row corresponding to the projected
    value returned by the selector function.

    (Row -> T) -> ([T] -> T) -> [Row] -> Row
    """
    projected_values = map(projection, rows)
    selected_value = selector(projected_values)
    return rows[projected_values.index(selected_value)]

def greatest_primary_key(fields, key, rows):
    return projected_selector(attrgetter('pk'), max, rows)

def lowest_primary_key(fields, key, rows):
    return projected_selector(attrgetter('pk'), min, rows)

def greatest_value(field, fields, key, rows):
    return projected_selector(attrgetter(field), max, rows)

