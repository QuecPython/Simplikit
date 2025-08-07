import utime
from machine import I2C
from usr.libs import CurrentApp
from usr.libs.threading import Thread
from usr.libs.logging import getLogger
from usr.drivers.shtc3 import Shtc3, SHTC3_SLAVE_ADDR
from usr.drivers.lps22hb import Lps22hb, LPS22HB_SLAVE_ADDRESS
from usr.drivers.tcs34725 import Tcs34725, TCS34725_SLAVE_ADDR
from usr.drivers.icm20948 import ICM20948, I2C_ADD_ICM20948



logger = getLogger(__name__)


class SensorService(object):

    def __init__(self, app=None):
        # i2c channel 0 
        self.i2c_channel0 = I2C(I2C.I2C1, I2C.STANDARD_MODE)
        
        # Sensor availability tracking
        self.sensor_available = {
            'shtc3': False,
            'lps22hb': False,
            'tcs34725': False,
            'icm20948': False
        }
        
        # Initialize sensors with hot-plug support
        self._init_sensors()

        print('\nSENSOR SERVICE INITIALIZED\n')

        if app is not None:
            self.init_app(app)

    def _init_sensors(self):
        """Initialize sensors with error handling for hot-plug support"""
        # SHTC3
        try:
            self.shtc3 = Shtc3(self.i2c_channel0, SHTC3_SLAVE_ADDR)
            self.shtc3.init()
            self.sensor_available['shtc3'] = True
            logger.info("SHTC3 sensor initialized successfully")
        except Exception as e:
            self.shtc3 = None
            self.sensor_available['shtc3'] = False
        
        # LPS22HB
        try:
            self.lps22hb = Lps22hb(self.i2c_channel0, LPS22HB_SLAVE_ADDRESS)
            self.lps22hb.init()
            self.sensor_available['lps22hb'] = True
            logger.info("LPS22HB sensor initialized successfully")
        except Exception as e:
            self.lps22hb = None
            self.sensor_available['lps22hb'] = False
        
        # TCS34725
        try:
            self.tcs34725 = Tcs34725(self.i2c_channel0, TCS34725_SLAVE_ADDR)
            self.tcs34725.init()
            self.sensor_available['tcs34725'] = True
            logger.info("TCS34725 sensor initialized successfully")
        except Exception as e:
            self.tcs34725 = None
            self.sensor_available['tcs34725'] = False
        
        # ICM20948
        try:
            self.icm20948 = ICM20948(self.i2c_channel0)
            self.sensor_available['icm20948'] = True
            logger.info("ICM20948 sensor initialized successfully")
        except Exception as e:
            self.icm20948 = None
            self.sensor_available['icm20948'] = False

    def _try_reconnect_sensor(self, sensor_name):
        """Attempt to reconnect a specific sensor"""
        try:
            if sensor_name == 'shtc3' and not self.sensor_available['shtc3']:
                self.shtc3 = Shtc3(self.i2c_channel0, SHTC3_SLAVE_ADDR)
                self.shtc3.init()
                self.sensor_available['shtc3'] = True
                logger.info("SHTC3 sensor reconnected successfully")
                return True
            elif sensor_name == 'lps22hb' and not self.sensor_available['lps22hb']:
                self.lps22hb = Lps22hb(self.i2c_channel0, LPS22HB_SLAVE_ADDRESS)
                self.lps22hb.init()
                self.sensor_available['lps22hb'] = True
                logger.info("LPS22HB sensor reconnected successfully")
                return True
            elif sensor_name == 'tcs34725' and not self.sensor_available['tcs34725']:
                self.tcs34725 = Tcs34725(self.i2c_channel0, TCS34725_SLAVE_ADDR)
                self.tcs34725.init()
                self.sensor_available['tcs34725'] = True
                logger.info("TCS34725 sensor reconnected successfully")
                return True
            elif sensor_name == 'icm20948' and not self.sensor_available['icm20948']:
                self.icm20948 = ICM20948(self.i2c_channel0)
                self.sensor_available['icm20948'] = True
                logger.info("ICM20948 sensor reconnected successfully")
                return True
        except Exception as e:
            pass
        return False

    def __str__(self):
        return '{}'.format(type(self).__name__)

    def init_app(self, app):
        app.register('sensor_service', self)

    def load(self):
        logger.info('loading {} extension, init sensors will take some seconds'.format(self))
        Thread(target=self.start_update).start()


    def get_temp1_and_humi(self):
        """Get temperature and humidity from SHTC3 sensor with hot-plug support"""
        if not self.sensor_available['shtc3']:
            raise Exception("SHTC3 sensor not available")
        return self.shtc3.getTempAndHumi()
    
    def get_press_and_temp2(self):
        """Get pressure and temperature from LPS22HB sensor with hot-plug support"""
        if not self.sensor_available['lps22hb']:
            raise Exception("LPS22HB sensor not available")
        return self.lps22hb.getTempAndPressure()
    
    def get_rgb888(self):
        """Get RGB color values from TCS34725 sensor with hot-plug support"""
        if not self.sensor_available['tcs34725']:
            raise Exception("TCS34725 sensor not available")
        rgb888 = self.tcs34725.getRGBValue()

        r = (rgb888 >> 16) & 0xFF
        g = (rgb888 >> 8) & 0xFF
        b = rgb888 & 0xFF
        return r, g, b       
    
    def get_accel_gyro(self):
        """Get accelerometer and gyroscope data from ICM20948 sensor with hot-plug support
        Returns:
            accel: (x, y, z) acceleration in m/s²
            gyro: (x, y, z) angular velocity in rad/s
        """
        if not self.sensor_available['icm20948']:
            raise Exception("ICM20948 sensor not available")
        
        # Get raw ADC values
        accel_raw, gyro_raw = self.icm20948.icm20948_Gyro_Accel_Read()
        
        # Convert accelerometer from ADC to m/s²
        # ICM20948 configured for ±2g range: 16384 LSB/g
        # Convert: raw_value / 16384 * 9.8 (m/s²)
        accel_ms2 = [
            (accel_raw[0] / 16384.0) * 9.8,
            (accel_raw[1] / 16384.0) * 9.8,
            (accel_raw[2] / 16384.0) * 9.8
        ]
        
        # Convert gyroscope from ADC to rad/s
        # ICM20948 configured for ±1000dps range: 32.8 LSB/dps
        # Convert: raw_value / 32.8 * (π/180) (rad/s)
        gyro_rads = [
            (gyro_raw[0] / 32.8) * 0.0174533,  # π/180 = 0.0174533
            (gyro_raw[1] / 32.8) * 0.0174533,
            (gyro_raw[2] / 32.8) * 0.0174533
        ]
        
        return accel_ms2, gyro_rads
    
    def count_decimal_digits(self, value):
        s = str(value)
        if '.' not in s:
            return 0
        decimal_part = s.split('.')[1]
        return len(decimal_part)
    
    def round_if_needed(self,value):
        if self.count_decimal_digits(value) > 15:    
            for precision in range(15, 7, -1):
                rounded = round(value, precision)
                digits = self.count_decimal_digits(rounded)
                if digits <= 15:
                    return rounded
            return 0.0
        else:
            return value 


    def start_update(self):
        prev_temp1 = None
        prev_humi = None
        prev_press = None
        prev_temp2 = None
        prev_rgb888 = None
        prev_accel = None
        prev_gyro = None
        reconnect_counter = 0

        while True:
            data = {}

            # Try to reconnect sensors every 30 seconds
            if reconnect_counter % 30 == 0:
                self._try_reconnect_all_sensors()
                
            # Log sensor status every 30 seconds (when not at startup)
            if reconnect_counter > 0 and reconnect_counter % 30 == 0:
                logger.info("Sensor status - SHTC3:{}, LPS22HB:{}, TCS34725:{}, ICM20948:{}".format(
                    self.sensor_available['shtc3'], self.sensor_available['lps22hb'], 
                    self.sensor_available['tcs34725'], self.sensor_available['icm20948']))
                    
            reconnect_counter += 1

            # ICM20948 sensor (Accelerometer and Gyroscope)
            try:
                accel, gyro = self.get_accel_gyro()           
                
                # Check for significant acceleration changes (>0.5 m/s² total change)
                if prev_accel is None or abs(prev_accel[0] - accel[0]) + abs(prev_accel[1] - accel[1]) + abs(prev_accel[2] - accel[2]) > 0.5:
                    data.update({10: {1: self.round_if_needed(accel[0]), 2: self.round_if_needed(accel[1]), 3: self.round_if_needed(accel[2])}})
                    prev_accel = [accel[0], accel[1], accel[2]]
                    logger.debug("Acceleration changed: X={:.3f}, Y={:.3f}, Z={:.3f} m/s²".format(accel[0], accel[1], accel[2]))
                
                # Check for significant gyroscope changes (>0.1 rad/s total change)
                if prev_gyro is None or abs(prev_gyro[0] - gyro[0]) + abs(prev_gyro[1] - gyro[1]) + abs(prev_gyro[2] - gyro[2]) >= 0.1:
                    data.update({9: {1: self.round_if_needed(gyro[0]), 2: self.round_if_needed(gyro[1]), 3: self.round_if_needed(gyro[2])}})
                    prev_gyro = [gyro[0], gyro[1], gyro[2]]
                    logger.debug("Gyroscope changed: X={:.3f}, Y={:.3f}, Z={:.3f} rad/s".format(gyro[0], gyro[1], gyro[2]))
                    
            except Exception as e:
                self._mark_sensor_disconnected('icm20948')

            utime.sleep_ms(100)

            # SHTC3 sensor (Temperature and Humidity)
            try:
                temp1, humi = self.get_temp1_and_humi()

                if prev_temp1 is None or abs(prev_temp1 - temp1) > 1:
                    data.update({3: round(temp1, 2)})
                    prev_temp1 = temp1
                    logger.debug("Temperature1 changed: {:.2f}°C".format(temp1))

                if prev_humi is None or abs(prev_humi - humi) > 1:
                    data.update({4: round(humi, 2)})
                    prev_humi = humi
                    logger.debug("Humidity changed: {:.2f}%RH".format(humi))

            except Exception as e:
                self._mark_sensor_disconnected('shtc3')

            utime.sleep_ms(100)

            # LPS22HB sensor (Pressure and Temperature)
            try:
                press, temp2 = self.get_press_and_temp2()

                if prev_temp2 is None or abs(prev_temp2 - temp2) > 1:
                    data.update({5: round(temp2, 2)})
                    prev_temp2 = temp2
                    logger.debug("Temperature2 changed: {:.2f}°C".format(temp2))

                if prev_press is None or abs(prev_press - press) > 1:
                    data.update({6: round(press, 2)})
                    prev_press = press
                    logger.debug("Pressure changed: {:.2f} hPa".format(press))

            except Exception as e:
                self._mark_sensor_disconnected('lps22hb')

            utime.sleep_ms(100)

            # TCS34725 sensor (RGB Color)
            try:
                r, g, b = self.get_rgb888()
                rgb888 = (r << 16) | (g << 8) | b

                if prev_rgb888 is None:
                    data.update({7: {1: r, 2: g, 3: b}})
                    prev_rgb888 = rgb888
                else:
                    prev_r = (prev_rgb888 >> 16) & 0xFF
                    dr = abs(r - prev_r)
                    
                    prev_g = (prev_rgb888 >> 8) & 0xFF
                    dg = abs(g - prev_g)
                    
                    prev_b = prev_rgb888 & 0xFF
                    db = abs(b - prev_b)

                    # 色差超过 200 即认为颜色有变化
                    if pow(sum((dr*dr, dg*dg, db*db)), 0.5) >= 200:
                        # data.update({7: {1: r, 2: g, 3: b}})
                        prev_rgb888 = rgb888

            except Exception as e:
                self._mark_sensor_disconnected('tcs34725')

            # Send data to IoT platform if any sensor data is available
            if data:
                with CurrentApp().qth_client:
                    for _ in range(3):
                        if CurrentApp().qth_client.sendTsl(1, data):
                            break
                        else:
                            # Reset previous values on transmission failure
                            prev_temp1 = None
                            prev_humi = None
                            prev_press = None
                            prev_temp2 = None
                            prev_rgb888 = None
                            prev_accel = None
                            prev_gyro = None

            utime.sleep(1)

    def _mark_sensor_disconnected(self, sensor_name):
        """Mark a sensor as disconnected when communication fails"""
        if self.sensor_available[sensor_name]:
            self.sensor_available[sensor_name] = False

    def _try_reconnect_all_sensors(self):
        """Try to reconnect all disconnected sensors"""
        for sensor_name in self.sensor_available:
            if not self.sensor_available[sensor_name]:
                self._try_reconnect_sensor(sensor_name)
