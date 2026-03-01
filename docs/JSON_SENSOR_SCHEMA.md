# JSON Sensor Library Schema

This document represents the planned structure for the `sensors.json` file which will act as the local database for the 2SP LiDAR Calculator application.

```json
{
  "lidar_modules": [
    {
      "id": "hesai_xt32_m2x",
      "manufacturer": "Hesai",
      "model": "XT32-M2X",
      "laser_channels": 32,
      "horizontal_fov_deg": 360.0,
      "vertical_fov_deg": 40.0,
      "configurations": [
        {
          "name": "Single Return",
          "pulse_repetition_rate_khz": 640,
          "max_returns": 1
        },
        {
          "name": "Dual Return",
          "pulse_repetition_rate_khz": 640,
          "max_returns": 2
        }
      ]
    },
    {
      "id": "riegl_minivux_3uav",
      "manufacturer": "RIEGL",
      "model": "miniVUX-3UAV",
      "laser_class": "Class 1",
      "laser_wavelength_nm": 905,
      "max_fov_deg": 360,           
      "scan_speed_rpm_min": 10,
      "scan_speed_rpm_max": 100,
      "configurations": [
        {
          "name": "100 kHz Program",
          "pulse_repetition_rate_khz": 100,
          "effective_measurement_rate_khz": 100,
          "max_range_at_20_reflectivity_m": 150, 
          "max_returns_per_pulse": 5,
          "recommended_agl_m": 120
        },
        {
          "name": "200 kHz Program",
          "pulse_repetition_rate_khz": 200,
          "effective_measurement_rate_khz": 200,
          "max_range_at_20_reflectivity_m": 100, 
          "max_returns_per_pulse": 5,
          "recommended_agl_m": 85
        },
        {
          "name": "300 kHz Program",
          "pulse_repetition_rate_khz": 300,
          "effective_measurement_rate_khz": 300,
          "max_range_at_20_reflectivity_m": 80,  
          "max_returns_per_pulse": 5,
          "recommended_agl_m": 70
        }
      ]
    }
  ],

  "camera_modules": [
    {
      "id": "sony_a5100",
      "manufacturer": "Sony",
      "model": "a5100",
      "sensor_width_mm": 23.5,
      "sensor_height_mm": 15.6,
      "image_width_px": 6000,
      "image_height_px": 4000,
      "lens_configurations": [
        {
          "name": "16mm Lens",
          "focal_length_mm": 16.0
        },
        {
          "name": "24mm Lens",
          "focal_length_mm": 24.0
        }
      ]
    },
    {
      "id": "dji_l3_rgb",
      "manufacturer": "DJI",
      "model": "L3 Integrated RGB",
      "sensor_width_mm": 17.3, 
      "sensor_height_mm": 13.0,
      "image_width_px": 5280,
      "image_height_px": 3956,
      "lens_configurations": [
        {
          "name": "Integrated 24mm (Eq.) Lens",
          "focal_length_mm": 24.0 
        }
      ]
    }
  ],

  "pos_modules": [
    {
      "id": "applanix_apx15",
      "manufacturer": "Applanix",
      "model": "APX-15 UAV",
      "pitch_roll_accuracy_deg": 0.025,
      "heading_accuracy_deg": 0.08,
      "position_accuracy_m": 0.02
    },
    {
      "id": "pos_dji_l3",
      "manufacturer": "DJI",
      "model": "(L3 Integrated INS)",
      "pitch_roll_accuracy_deg": 0.03, 
      "heading_accuracy_deg": 0.08,
      "position_accuracy_m": 0.04    
    }
  ],

  "mapping_systems": [
    {
      "id": "resepi_hesai_xt32",
      "manufacturer": "Inertial Labs",
      "system_name": "RESEPI Hesai XT32",
      "lidar_module_id": "hesai_xt32_m2x",
      "camera_module_id": "sony_a5100_16mm",
      "pos_module_id": "applanix_apx15",
      "total_weight_kg": 1.6
    },
    {
      "id": "dji_zenmuse_l3",
      "manufacturer": "DJI",
      "system_name": "Zenmuse L3",
      "lidar_module_id": "dji_l3_lidar",
      "camera_module_id": "dji_l3_rgb",
      "pos_module_id": "pos_dji_l3",
      "total_weight_kg": 1.05
    }
  ]
}
```
