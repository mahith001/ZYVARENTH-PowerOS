# ============================================================
# ZYVARENTH POWEROS
# BATTERY ENERGY MANAGEMENT ENGINE
# ============================================================

import pandas as pd


# ============================================================
# DEFAULT BATTERY CONFIGURATION
# ============================================================

BATTERY_CAPACITY_KWH = 100.0

INITIAL_SOC = 0.80

MIN_SOC = 0.20

MAX_SOC = 1.00

MAX_CHARGE_KW = 20.0

MAX_DISCHARGE_KW = 20.0

CHARGE_EFFICIENCY = 0.95

DISCHARGE_EFFICIENCY = 0.95


CHEAP_PRICE_THRESHOLD = 6.0

EXPENSIVE_PRICE_THRESHOLD = 10.0


# ============================================================
# BATTERY CLASS
# ============================================================

class Battery:

    def __init__(
        self,
        capacity_kwh: float = BATTERY_CAPACITY_KWH,
        initial_soc: float = INITIAL_SOC,
        min_soc: float = MIN_SOC,
        max_soc: float = MAX_SOC,
        max_charge_kw: float = MAX_CHARGE_KW,
        max_discharge_kw: float = MAX_DISCHARGE_KW,
        charge_efficiency: float = CHARGE_EFFICIENCY,
        discharge_efficiency: float = DISCHARGE_EFFICIENCY,
    ):

        # ----------------------------------------------------
        # Validate configuration
        # ----------------------------------------------------

        if capacity_kwh <= 0:
            raise ValueError(
                "Battery capacity must be greater than zero."
            )

        if not 0.0 <= min_soc <= 1.0:
            raise ValueError(
                "min_soc must be between 0 and 1."
            )

        if not 0.0 <= max_soc <= 1.0:
            raise ValueError(
                "max_soc must be between 0 and 1."
            )

        if min_soc > max_soc:
            raise ValueError(
                "min_soc cannot be greater than max_soc."
            )

        if max_charge_kw < 0:
            raise ValueError(
                "max_charge_kw cannot be negative."
            )

        if max_discharge_kw < 0:
            raise ValueError(
                "max_discharge_kw cannot be negative."
            )

        if not 0.0 < charge_efficiency <= 1.0:
            raise ValueError(
                "charge_efficiency must be between 0 and 1."
            )

        if not 0.0 < discharge_efficiency <= 1.0:
            raise ValueError(
                "discharge_efficiency must be between 0 and 1."
            )


        # ----------------------------------------------------
        # Store configuration
        # ----------------------------------------------------

        self.capacity_kwh = float(
            capacity_kwh
        )

        self.min_soc = float(
            min_soc
        )

        self.max_soc = float(
            max_soc
        )

        self.max_charge_kw = float(
            max_charge_kw
        )

        self.max_discharge_kw = float(
            max_discharge_kw
        )

        self.charge_efficiency = float(
            charge_efficiency
        )

        self.discharge_efficiency = float(
            discharge_efficiency
        )


        # ----------------------------------------------------
        # Initial state of charge
        # ----------------------------------------------------

        self.soc = max(
            self.min_soc,
            min(
                self.max_soc,
                float(initial_soc)
            )
        )


        self.energy_kwh = (
            self.capacity_kwh
            * self.soc
        )


        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        self.total_charged_kwh = 0.0

        self.total_discharged_kwh = 0.0


    # ========================================================
    # CHARGE BATTERY
    # ========================================================

    def charge(
        self,
        available_power_kw: float,
        duration_hours: float = 1.0,
    ) -> float:

        available_power_kw = max(
            0.0,
            float(available_power_kw)
        )

        duration_hours = max(
            0.0,
            float(duration_hours)
        )

        if duration_hours <= 0:
            return 0.0


        # ----------------------------------------------------
        # Maximum charging power
        # ----------------------------------------------------

        charge_power = min(
            available_power_kw,
            self.max_charge_kw
        )


        requested_input_energy = (
            charge_power
            * duration_hours
        )


        # ----------------------------------------------------
        # Available storage space
        # ----------------------------------------------------

        maximum_energy = (
            self.capacity_kwh
            * self.max_soc
        )

        remaining_capacity = (
            maximum_energy
            - self.energy_kwh
        )


        if remaining_capacity <= 0:

            return 0.0


        # ----------------------------------------------------
        # Account for charging efficiency
        # ----------------------------------------------------

        maximum_input_energy = (
            remaining_capacity
            / self.charge_efficiency
        )


        actual_input_energy = min(
            requested_input_energy,
            maximum_input_energy
        )


        stored_energy = (
            actual_input_energy
            * self.charge_efficiency
        )


        # ----------------------------------------------------
        # Update battery state
        # ----------------------------------------------------

        self.energy_kwh += (
            stored_energy
        )


        self.energy_kwh = min(
            self.energy_kwh,
            maximum_energy
        )


        self.soc = (
            self.energy_kwh
            / self.capacity_kwh
        )


        self.soc = max(
            self.min_soc,
            min(
                self.max_soc,
                self.soc
            )
        )


        self.total_charged_kwh += (
            actual_input_energy
        )


        return actual_input_energy


    # ========================================================
    # DISCHARGE BATTERY
    # ========================================================

    def discharge(
        self,
        requested_power_kw: float,
        duration_hours: float = 1.0,
    ) -> float:

        requested_power_kw = max(
            0.0,
            float(requested_power_kw)
        )

        duration_hours = max(
            0.0,
            float(duration_hours)
        )

        if duration_hours <= 0:
            return 0.0


        # ----------------------------------------------------
        # Maximum discharge power
        # ----------------------------------------------------

        discharge_power = min(
            requested_power_kw,
            self.max_discharge_kw
        )


        requested_output_energy = (
            discharge_power
            * duration_hours
        )


        # ----------------------------------------------------
        # Energy that must remain in battery
        # ----------------------------------------------------

        minimum_energy = (
            self.capacity_kwh
            * self.min_soc
        )


        available_energy = (
            self.energy_kwh
            - minimum_energy
        )


        if available_energy <= 0:

            return 0.0


        # ----------------------------------------------------
        # Account for discharge efficiency
        # ----------------------------------------------------

        maximum_output_energy = (
            available_energy
            * self.discharge_efficiency
        )


        actual_output_energy = min(
            requested_output_energy,
            maximum_output_energy
        )


        battery_energy_used = (
            actual_output_energy
            / self.discharge_efficiency
        )


        # ----------------------------------------------------
        # Update battery state
        # ----------------------------------------------------

        self.energy_kwh -= (
            battery_energy_used
        )


        self.energy_kwh = max(
            self.energy_kwh,
            minimum_energy
        )


        self.soc = (
            self.energy_kwh
            / self.capacity_kwh
        )


        self.soc = max(
            self.min_soc,
            min(
                self.max_soc,
                self.soc
            )
        )


        self.total_discharged_kwh += (
            actual_output_energy
        )


        return actual_output_energy


    # ========================================================
    # AVAILABLE ENERGY
    # ========================================================

    def available_discharge_kwh(self) -> float:

        minimum_energy = (
            self.capacity_kwh
            * self.min_soc
        )

        available_energy = max(
            0.0,
            self.energy_kwh
            - minimum_energy
        )


        return (
            available_energy
            * self.discharge_efficiency
        )


    # ========================================================
    # AVAILABLE CHARGING CAPACITY
    # ========================================================

    def available_charge_kwh(self) -> float:

        maximum_energy = (
            self.capacity_kwh
            * self.max_soc
        )

        return max(
            0.0,
            maximum_energy
            - self.energy_kwh
        )


    # ========================================================
    # BATTERY STATUS
    # ========================================================

    def status(self) -> dict:

        return {

            "capacity_kwh":
                self.capacity_kwh,

            "soc":
                self.soc,

            "soc_percent":
                self.soc * 100.0,

            "energy_kwh":
                self.energy_kwh,

            "energy_percent":
                self.soc * 100.0,

            "min_soc":
                self.min_soc,

            "max_soc":
                self.max_soc,

            "max_charge_kw":
                self.max_charge_kw,

            "max_discharge_kw":
                self.max_discharge_kw,

            "charge_efficiency":
                self.charge_efficiency,

            "discharge_efficiency":
                self.discharge_efficiency,

            "total_charged_kwh":
                self.total_charged_kwh,

            "total_discharged_kwh":
                self.total_discharged_kwh,

            "available_discharge_kwh":
                self.available_discharge_kwh(),

            "available_charge_kwh":
                self.available_charge_kwh(),
        }


# ============================================================
# BATTERY DISPATCH ENGINE
# ============================================================

def dispatch_battery(
    schedule: pd.DataFrame,
    electricity_prices: list,
    solar_power: list,
) -> dict:

    """
    Simulate PowerOS energy dispatch.

    Energy priority:

    1. Solar -> AI workload
    2. Solar surplus -> battery
    3. Cheap grid -> battery
    4. Battery -> AI workload during expensive periods
    5. Grid -> remaining AI workload
    """


    # --------------------------------------------------------
    # Create battery
    # --------------------------------------------------------

    battery = Battery(
        capacity_kwh=100.0,
        initial_soc=0.80,
        min_soc=0.20,
        max_soc=1.00,
        max_charge_kw=20.0,
        max_discharge_kw=20.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )


    # --------------------------------------------------------
    # Build hourly AI demand
    # --------------------------------------------------------

    hourly_demand = [
        0.0
        for _ in range(24)
    ]


    for _, job in schedule.iterrows():

        start_hour = int(
            job["start_hour"]
        )

        duration = int(
            job["duration_hours"]
        )

        power_kw = float(
            job["power_kw"]
        )


        if start_hour < 0:
            continue


        for hour in range(
            start_hour,
            min(
                start_hour + duration,
                24
            )
        ):

            hourly_demand[hour] += (
                power_kw
            )


    # --------------------------------------------------------
    # Tracking
    # --------------------------------------------------------

    hourly_grid = [
        0.0
        for _ in range(24)
    ]

    hourly_solar = [
        0.0
        for _ in range(24)
    ]

    hourly_battery = [
        0.0
        for _ in range(24)
    ]

    hourly_charge = [
        0.0
        for _ in range(24)
    ]

    hourly_unserved = [
        0.0
        for _ in range(24)
    ]


    total_cost = 0.0


    # ========================================================
    # HOURLY DISPATCH
    # ========================================================

    for hour in range(24):

        load = (
            hourly_demand[hour]
        )

        solar_available = max(
            0.0,
            float(solar_power[hour])
        )

        price = float(
            electricity_prices[hour]
        )


        # ----------------------------------------------------
        # 1. Solar -> workload
        # ----------------------------------------------------

        solar_used = min(
            load,
            solar_available
        )

        hourly_solar[hour] = (
            solar_used
        )


        remaining_load = max(
            0.0,
            load - solar_used
        )


        # ----------------------------------------------------
        # 2. Solar surplus -> battery
        # ----------------------------------------------------

        solar_surplus = max(
            0.0,
            solar_available
            - solar_used
        )


        battery_charge = 0.0


        if solar_surplus > 0:

            battery_charge = (
                battery.charge(
                    solar_surplus,
                    1.0
                )
            )


        # ----------------------------------------------------
        # 3. Cheap electricity -> battery
        # ----------------------------------------------------

        elif price <= CHEAP_PRICE_THRESHOLD:

            battery_charge = (
                battery.charge(
                    battery.max_charge_kw,
                    1.0
                )
            )


        hourly_charge[hour] = (
            battery_charge
        )


        # ----------------------------------------------------
        # 4. Battery -> workload
        # ----------------------------------------------------

        battery_used = 0.0


        if (
            remaining_load > 0
            and price >= EXPENSIVE_PRICE_THRESHOLD
        ):

            battery_used = (
                battery.discharge(
                    remaining_load,
                    1.0
                )
            )


        battery_used = min(
            battery_used,
            remaining_load
        )


        hourly_battery[hour] = (
            battery_used
        )


        remaining_load = max(
            0.0,
            remaining_load
            - battery_used
        )


        # ----------------------------------------------------
        # 5. Grid -> remaining workload
        # ----------------------------------------------------

        grid_available = max(
            0.0,
            float(
                70.0
            )
        )


        grid_used = min(
            remaining_load,
            grid_available
        )


        hourly_grid[hour] = (
            grid_used
        )


        remaining_load = max(
            0.0,
            remaining_load
            - grid_used
        )


        # ----------------------------------------------------
        # 6. Unserved load
        # ----------------------------------------------------

        hourly_unserved[hour] = (
            remaining_load
        )


        # ----------------------------------------------------
        # 7. Electricity cost
        # ----------------------------------------------------

        total_cost += (
            grid_used
            * price
        )


    # ========================================================
    # FINAL STATUS
    # ========================================================

    status = battery.status()


    total_solar = sum(
        hourly_solar
    )

    total_grid = sum(
        hourly_grid
    )

    total_battery = sum(
        hourly_battery
    )

    total_charged = sum(
        hourly_charge
    )

    total_unserved = sum(
        hourly_unserved
    )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "total_cost":
            total_cost,

        "grid_energy_kwh":
            total_grid,

        "solar_energy_kwh":
            total_solar,

        "battery_energy_kwh":
            total_battery,

        "battery_charged_kwh":
            total_charged,

        "unserved_energy_kwh":
            total_unserved,

        "final_battery_soc_percent":
            status["soc_percent"],

        "remaining_battery_energy_kwh":
            status["energy_kwh"],

        "available_discharge_kwh":
            status[
                "available_discharge_kwh"
            ],

        "hourly_grid":
            hourly_grid,

        "hourly_solar":
            hourly_solar,

        "hourly_battery":
            hourly_battery,

        "hourly_battery_charge":
            hourly_charge,

        "hourly_unserved":
            hourly_unserved,
    }