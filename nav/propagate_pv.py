def propagate_pv(p_0, v_0, a_1, dt):
    ''' Propagates the position and velocity of the vehicle.
    
    :param p_0: The last known position of the vehicle.
    :type p_0: `numpy.array` [1x3]
    :param v_0: The last known velocity of the vehicle.
    :type v_0: `numpy.array` [1x3]
    :param a_1: The latest mean acceleration measurement.
    :type a_1: `numpy.array` [1x3]
    :param dt: The time step over which measured acceleration was averaged.
    :type dt: `float`
    :return: Propagated position (`numpy.array` [1x3]),
             propagated velocity (`numpy.array` [1x3]).
    '''
        
    v_1 = v_0 + a_1*dt
    p_1 = p_0 + v_0*dt + 0.5*a_1*dt*dt
    
    return p_1, v_1
