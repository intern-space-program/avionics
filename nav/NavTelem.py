def make_nav_telem(time, position, velocity, attitude):
    '''
    Creates a nav state telemetry dictionary to be converted
    into the exported data type.
    '''

    return {
        'time': time,
        'position': position,
        'velocity': velocity,
        'attiude': attitude
    }

def format_nav_telem(nav_telem):
    '''
    Takes the output of make_nav_telem and converts it into
    the desired output format.
    '''
    pass
