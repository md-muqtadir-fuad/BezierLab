import math
def get_bezier_poit_at_t(control_points, t):
    '''calculates a single point on the curve for a specific t(or u); value 0-1'''
    '''
    B(t) = Σ C(n, i) × (1 - t)^(n-i) × t^i × Pᵢ
            where
                t = value from 0 to 1
                Pᵢ = control point
                n = number of control points - 1
                i = index of current point
                C(n, i) = binomial coefficient
    '''
    if not control_points:
        return (0,0)
    n = len(control_points) - 1

    #B(t) starts from 0
    curve_x, curve_y = 0, 0
    for i, (px, py) in enumerate(control_points):
        binomial_coeff = math.comb(n, i)
        weight = binomial_coeff * ((1 - t) ** (n - i)) * (t ** i)
        curve_x += weight * px
        curve_y += weight * py
        
def get_calculate_bezier_curve():
    pass