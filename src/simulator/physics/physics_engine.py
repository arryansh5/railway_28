"""
physics_engine.py — Phase 3: Physics-Based RTIS Simulator
Core kinematic equations for speed, position and braking distance.
All calculations use SI units: m/s, m/s², metres, seconds.
Convert to km/h and km only at output layer.
"""


def update_speed(
    current_speed_mps: float,
    acceleration_mps2: float,
    delta_t_sec: float
) -> float:
    """
    v_new = v_old + a * Δt  (clamped to >= 0)
    """
    return max(0.0, current_speed_mps + acceleration_mps2 * delta_t_sec)


def update_position(
    current_position_m: float,
    current_speed_mps: float,
    acceleration_mps2: float,
    delta_t_sec: float
) -> float:
    """
    d_new = d_old + v_old * Δt + 0.5 * a * (Δt)²  (never moves backward)
    """
    d_new = (
        current_position_m
        + current_speed_mps * delta_t_sec
        + 0.5 * acceleration_mps2 * (delta_t_sec ** 2)
    )
    return max(current_position_m, d_new)


def compute_braking_distance(
    current_speed_mps: float,
    braking_deceleration_mps2: float
) -> float:
    """
    d_brake = v² / (2 * a_brake)
    Returns distance in metres needed to stop from current speed.
    """
    if current_speed_mps <= 0.0:
        return 0.0
    return (current_speed_mps ** 2) / (2.0 * braking_deceleration_mps2)


def clamp_speed(speed_mps: float, target_mps: float, max_step_mps: float) -> float:
    """Moves speed toward target without overshooting."""
    if speed_mps < target_mps:
        return min(speed_mps + max_step_mps, target_mps)
    elif speed_mps > target_mps:
        return max(speed_mps - max_step_mps, target_mps)
    return speed_mps


def kmph_to_mps(kmph: float) -> float:
    """Converts km/h to m/s."""
    return kmph / 3.6


def mps_to_kmph(mps: float) -> float:
    """Converts m/s to km/h."""
    return mps * 3.6


if __name__ == "__main__":
    v_old   = kmph_to_mps(100.0)
    a       = -0.6
    dt      = 30.0
    pos_old = 50_000.0

    v_new   = update_speed(v_old, a, dt)
    d_new   = update_position(pos_old, v_old, a, dt)
    d_brake = compute_braking_distance(v_old, 0.6)

    print("=== Physics Engine Test ===")
    print(f"Initial speed   : {mps_to_kmph(v_old):.1f} km/h ({v_old:.2f} m/s)")
    print(f"Acceleration    : {a} m/s²")
    print(f"Timestep        : {dt}s")
    print(f"New speed       : {mps_to_kmph(v_new):.1f} km/h ({v_new:.2f} m/s)")
    print(f"Position before : {pos_old/1000:.2f} km")
    print(f"Position after  : {d_new/1000:.2f} km")
    print(f"Distance moved  : {(d_new - pos_old):.1f} m")
    print(f"Braking distance: {d_brake:.1f} m")
