"""
AutoQ - ML Feature Mapping and Compatibility Layer
Explicitly translates AutoQ SQLite database records and API schemas into
strictly validated machine learning input vectors without altering the database schema.
"""
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd


class FeatureMappingLayer:
    """
    Translates application inspection schemas and database models into the exact
    feature representations required by the trained Scikit-learn pipeline.
    """

    # Category to variant mapping
    CATEGORY_TO_TYPE = {
        "chassis": "L",
        "chassis mounts": "L",
        "fasteners": "L",
        "interior": "L",
        "braking system": "M",
        "brakes": "M",
        "suspension": "M",
        "steering": "M",
        "powertrain": "H",
        "engine": "H",
        "transmission": "H",
        "structural": "H",
    }

    REQUIRED_RAW_FIELDS = [
        "component_category",
        "manufacturing_temperature",
        "pressure",
    ]

    def __init__(self):
        pass

    def map_request_to_features(
        self,
        raw_input: Dict[str, Any],
        strict: bool = True,
    ) -> pd.DataFrame:
        """
        Validates raw input payload and constructs a single-row DataFrame
        containing all 9 required features in strict canonical order:
        ['air_temperature', 'process_temperature', 'rotational_speed', 'torque',
         'tool_wear', 'temp_difference', 'mechanical_power', 'overstrain_index', 'component_type']
        """
        # Validate critical presence
        if strict:
            for field in self.REQUIRED_RAW_FIELDS:
                if field not in raw_input or raw_input[field] is None:
                    raise ValueError(f"Missing required inspection parameter: '{field}'")

        # 1. Map component variant (Type: L, M, H)
        cat_raw = str(raw_input.get("component_category", "")).strip().lower()
        component_type = raw_input.get("component_type")
        if not component_type or component_type not in ["L", "M", "H"]:
            component_type = self.CATEGORY_TO_TYPE.get(cat_raw, "M")

        # 2. Temperature Conversion & Normalization
        # Physical dataset uses Kelvin [295K to 315K]
        # AutoQ database stores manufacturing temperature in Celsius
        mfg_temp = float(raw_input["manufacturing_temperature"])
        if mfg_temp < -50.0 or mfg_temp > 2500.0:
            raise ValueError(f"Manufacturing temperature {mfg_temp}°C is physically impossible.")

        # If process_temperature is explicitly supplied (e.g. from benchmark test), use directly
        if "process_temperature" in raw_input and raw_input["process_temperature"] is not None:
            process_temp = float(raw_input["process_temperature"])
            if process_temp < 100.0:
                process_temp += 273.15
        elif mfg_temp <= 100.0:
            process_temp = mfg_temp + 273.15
        elif mfg_temp < 250.0:
            process_temp = mfg_temp
        else:
            # Foundry / Casting high-temp scaling to equivalent machining interface temperature (308K - 314K)
            process_temp = 308.0 + min(6.0, (mfg_temp - 600.0) / 100.0)

        air_temp = raw_input.get("air_temperature")
        if air_temp is None:
            # Calibrated nominal ambient factory temperature
            air_temp = round(process_temp - 10.0, 1)
        else:
            air_temp = float(air_temp)
            if air_temp < 100.0:
                air_temp += 273.15

        # 3. Torque and Pressure Mapping
        # Dataset uses Torque [Nm] from 3.8 to 76.6 Nm
        # AutoQ stores pressure in bar or torque_resistance in Nm
        if "torque" in raw_input and raw_input["torque"] is not None:
            torque = float(raw_input["torque"])
            if torque <= 0.0 or torque > 500.0:
                raise ValueError(f"Torque reading {torque} Nm is outside physical operational envelope [0.1, 500.0].")
        elif "torque_resistance" in raw_input and raw_input["torque_resistance"] is not None:
            torque = float(raw_input["torque_resistance"])
            if torque <= 0.0 or torque > 500.0:
                raise ValueError(f"Torque resistance {torque} Nm is outside physical operational envelope [0.1, 500.0].")
        else:
            # Clamping / injection pressure (bar) conversion to torque proxy
            pressure_bar = float(raw_input["pressure"])
            if pressure_bar <= 0.0 or pressure_bar > 1000.0:
                raise ValueError(f"Pressure reading {pressure_bar} bar is outside physical operational bounds.")
            torque = max(10.0, min(75.0, pressure_bar * 0.28))

        # 4. Rotational Speed (rpm)
        if "rotational_speed" in raw_input and raw_input["rotational_speed"] is not None:
            speed = float(raw_input["rotational_speed"])
            if speed <= 0.0 or speed > 10000.0:
                raise ValueError(f"Rotational speed {speed} rpm is outside physical operational bounds [1, 10000].")
        elif "cycle_time" in raw_input and raw_input["cycle_time"] is not None:
            cycle = float(raw_input["cycle_time"])
            if cycle <= 0.0:
                raise ValueError("Casting cycle time must be positive.")
            speed = max(1150.0, min(2850.0, 1500.0 + (45.0 - cycle) * 15.0))
        else:
            speed = 1538.0  # Nominal benchmark dataset median

        # 5. Tool Wear (min)
        if "tool_wear" in raw_input and raw_input["tool_wear"] is not None:
            tool_wear = float(raw_input["tool_wear"])
            if tool_wear < 0.0 or tool_wear > 1000.0:
                raise ValueError(f"Cumulative tool wear {tool_wear} min must be between 0 and 1000 minutes.")
        elif "stress_tolerance" in raw_input and raw_input["stress_tolerance"] is not None:
            stress = float(raw_input["stress_tolerance"])
            if stress <= 0.0:
                raise ValueError("Stress tolerance must be positive.")
            # Stress inversely correlates with accumulated tool wear
            tool_wear = max(0.0, min(250.0, (400.0 - stress) * 1.2))
        else:
            tool_wear = 108.0  # Nominal benchmark dataset median

        # 6. Engineered Features (Exact physical formulas)
        temp_diff = round(process_temp - air_temp, 2)
        power_w = round((2.0 * np.pi * speed * torque) / 60.0, 2)
        overstrain = round(tool_wear * torque, 2)

        feature_dict = {
            "air_temperature": float(air_temp),
            "process_temperature": float(process_temp),
            "rotational_speed": float(speed),
            "torque": float(torque),
            "tool_wear": float(tool_wear),
            "temp_difference": float(temp_diff),
            "mechanical_power": float(power_w),
            "overstrain_index": float(overstrain),
            "component_type": str(component_type),
        }

        return pd.DataFrame([feature_dict])

