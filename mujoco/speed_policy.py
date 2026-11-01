"""Engineering speed ceilings from observed timing and estimated stop margins."""
import math

def speed_limit(config,estimate,age_high_s,gap_high_s,source_window):
    r=config['reconfiguration']['adaptive']; e=config['estimator']; g=config['geometry']
    period=config['timing']['physics_step_s']*config['timing']['sample_steps']
    lo,hi=e['command_gain_range']
    age=age_high_s+r['age_guard_s']
    gap=max(period,gap_high_s)
    if not all(math.isfinite(v) and v>=0 for v in (age,gap)): raise ValueError('invalid timing envelope')
    # Rising-edge anchor reset: mean travel uses nominal gain, interval upper
    # travel uses high gain. Use gain extremes, not the true plant velocity.
    budget=e['pick_uncertainty_limit_m']-e['anchor_tolerance_m']-e['stop_coast_m']-r['pick_reserve_m']
    denominator=hi*age+(hi-lo/2)*gap
    pick_cap=max(0.0,budget/denominator)
    boundary_cap=config['motion']['test_speed_range_m_s'][1]
    remaining=None
    if estimate.y_m is not None:
        if source_window is None: raise ValueError('source-to-now command history required')
        values=(estimate.y_m,estimate.uncertainty_m,source_window['distance_m'],
                source_window['speed_variation_m_s'],source_window['stops'],source_window['end_s']-source_window['start_s'])
        if not all(v is not None and math.isfinite(v) for v in values): raise ValueError('invalid stop estimate')
        if any(v<0 for v in values[1:]): raise ValueError('negative uncertainty/history')
        past=(hi*source_window['distance_m']+e['command_response_uncertainty_s']*source_window['speed_variation_m_s']
              +source_window['stops']*e['stop_coast_m']+e['drift_m_s']*values[-1])
        limit=g['long_belt_y_m'][1]-g['product_size_m'][1]/2-config['prediction']['stop_margin_m']
        remaining=limit-estimate.y_m-estimate.uncertainty_m-past-e['stop_coast_m']
        boundary_cap=max(0.0,remaining/(hi*(period+max(config['prediction']['reaction_delays_s']))))
    raw=min(pick_cap,boundary_cap,config['motion']['test_speed_range_m_s'][1])
    step=r['speed_step_m_s']
    cap=math.floor((raw+1e-12)/step)*step
    minimum=config['motion']['test_speed_range_m_s'][0]
    if raw>=minimum and cap<minimum: cap=minimum
    return {'raw_cap_m_s':raw,'cap_m_s':cap,'pickup_cap_m_s':pick_cap,'boundary_cap_m_s':boundary_cap,
            'pickup_budget_m':budget,'pickup_denominator_s':denominator,'remaining_stop_margin_m':remaining,
            'age_envelope_s':age,'gap_envelope_s':gap}
