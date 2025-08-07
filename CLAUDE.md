# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SIMPLIKit is a MicroPython IoT firmware project designed for Quectel cellular modules. It implements a sensor monitoring and data transmission system that connects to IoT platforms via MQTT. The project is built on the Qth IoT platform framework.

## Architecture

### Core Components

- **Application Framework** (`code/libs/__init__.py`): Singleton-based application class with extension system
- **SIM Service** (`code/extensions/sim_service.py`): Intelligent dual SIM management with vSIM/physical SIM auto-switching and hot-plug support
- **Qth Client** (`code/extensions/qth_client.py`): MQTT-based IoT platform client with OTA support
- **Sensor Service** (`code/extensions/sensor_service.py`): Multi-sensor data collection and transmission with hot-plug support
- **Location Services**: GNSS (`code/extensions/gnss_service.py`) and LBS (`code/extensions/lbs_service.py`) positioning services  
- **Hardware Drivers** (`code/drivers/`): I2C sensor drivers for SHTC3, LPS22HB, TCS34725, ICM20948

### Key Patterns

1. **Extension System**: Services register themselves with the main application using `app.register(name, service)`
2. **Service Initialization**: Each service implements `init_app(app)` and `load()` methods
3. **Thread-based Services**: Sensor monitoring runs in background threads
4. **Configuration-driven**: Uses JSON config files for platform credentials and settings
5. **Callback Architecture**: Qth client uses event callbacks for device events, TSL commands, and OTA updates
6. **Hot-plug Support**: All hardware components support connection/disconnection during runtime

## Development Setup

### Main Entry Point
```bash
# Run the main application (for MicroPython environment)
python code/main.py
```

### Configuration Files
- `code/config.json` / `code/config2.json`: Qth platform credentials (QTH_PRODUCT_KEY, QTH_PRODUCT_SECRET, QTH_SERVER)
- `code/system_config.json`: System-level configuration  
- `code/qth_config.ini`: Additional Qth configuration (encrypted/encoded)

### Hardware Requirements
- Quectel cellular module with MicroPython support
- I2C sensors: SHTC3 (temp/humidity), LPS22HB (pressure), TCS34725 (color), ICM20948 (IMU)
- Network connectivity (cellular data via vSIM or physical SIM)

## Key Implementation Details

### Network Initialization Sequence
The `code/main.py` handles cellular network setup:
1. **SIM Initialization**: Intelligent SIM selection (vSIM priority, physical SIM fallback)
2. **Network Configuration**: Configure APN ('BICSAPN') and activate PDP context
3. **LTE Connection**: Wait for LTE network connection
4. **Service Initialization**: Initialize application services with SIM service registered first

### Sensor Data Flow
1. Sensors are initialized in `SensorService.__init__()` with hot-plug error handling
2. Background thread in `start_update()` continuously reads sensors
3. Data changes trigger transmission via `qth_client.sendTsl()` 
4. Platform can request sensor readings via TSL callbacks

### TSL Command Mapping

**Implemented Sensor Properties (Read-only):**
- ID 3: Temperature1 (SHTC3) - °C
- ID 4: Humidity (SHTC3) - %RH  
- ID 5: Temperature2 (LPS22HB) - °C
- ID 6: Pressure (LPS22HB) - hPa
- ID 7: RGB888 color values (TCS34725) - struct with R,G,B (format: {1:r, 2:g, 3:b}) *Note: RGB data is read but not transmitted to cloud platform*
- ID 9: Gyroscope (ICM20948) - rad/s, struct with X,Y,Z components (format: {1:x, 2:y, 3:z})
- ID 10: Accelerometer (ICM20948) - m/s², struct with X,Y,Z components (format: {1:x, 2:y, 3:z})

### SIM Management Architecture
- **Intelligent Switching**: vSIM priority with automatic physical SIM fallback
- **Hot-plug Support**: Real-time SIM status monitoring every 30 seconds
- **Fault Recovery**: Automatic SIM switching when current SIM fails
- **Test Mode**: Configurable test mode for forcing specific SIM type usage
- **Backward Compatibility**: Falls back to simple vSIM logic if SIM service fails

### Hot-plug Architecture
- **SIM Service**: Dual SIM auto-switching and hot-plug monitoring
- **Sensor Service**: Individual sensor failure doesn't affect others, automatic reconnection every 30 seconds
- **Location Services**: GNSS and LBS services handle hardware availability dynamically
- **Error Handling**: All I2C communication wrapped in try-catch blocks, graceful degradation

### File Structure
- `code/Qth/`: Compiled MicroPython modules (.mpy) for Qth platform integration
- `code/libs/`: Core framework libraries (application, threading, logging, collections)
- `code/extensions/`: Service modules that extend the application  
- `code/drivers/`: Hardware-specific sensor drivers
- `fw/`: Compiled firmware packages (.pac files) for device flashing

## Testing

No formal test framework is present. Testing is done via:
- `code/vsim_test.py`: Virtual SIM testing script
- **SIM Testing**: Modify `TEST_PHYSICAL_SIM_ONLY` in `sim_service.py` to test specific SIM types
- Direct hardware testing on cellular modules
- Debug logging throughout the application
- Hot-plug testing: Connect/disconnect sensors and SIM cards during runtime

## Development Notes

- Uses MicroPython-specific imports (`utime`, `machine.I2C`, `quecgnss`)
- Designed for resource-constrained embedded environments  
- Heavy use of exception handling for hardware communication
- Implements change detection to minimize unnecessary data transmission
- OTA (Over-The-Air) update capability built into Qth client
- Clean logging: minimal output when hardware is not connected