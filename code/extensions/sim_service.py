import utime
import sim
from sim import vsim
from usr.libs.logging import getLogger
from usr.libs.threading import Thread

logger = getLogger(__name__)

class SIMService:
    def __init__(self):
        self.current_sim_type = None  # 'vsim' or 'physical' or None
        self.is_initialized = False
        self.monitoring = False
        self.monitor_thread = None
        
    def init_app(self, app):
        self.app = app
        app.register('sim_service', self)
        
    def load(self):
        self.initialize_sim()
        self.start_monitoring()
        
    def initialize_sim(self):
        logger.info("Starting SIM card initialization...")
        
        # Test mode: Force physical SIM usage (change back to normal logic after testing)
        TEST_PHYSICAL_SIM_ONLY = False  # Set to True for testing, False for normal use
        
        if TEST_PHYSICAL_SIM_ONLY:
            logger.info("*** Test mode: Physical SIM card only ***")
            if self._try_physical_sim():
                self.current_sim_type = 'physical'
                self.is_initialized = True
                logger.info("Physical SIM card initialization successful")
                return True
            else:
                logger.error("Physical SIM card initialization failed in test mode")
                self.current_sim_type = None
                self.is_initialized = False
                return False
        
        # Normal mode: vSIM priority, physical SIM fallback
        # Try vSIM first
        if self._try_vsim():
            self.current_sim_type = 'vsim'
            self.is_initialized = True
            logger.info("vSIM initialization successful")
            return True
            
        # vSIM failed, try physical SIM card
        if self._try_physical_sim():
            self.current_sim_type = 'physical'
            self.is_initialized = True
            logger.info("Physical SIM card initialization successful")
            return True
            
        logger.error("No available SIM card detected")
        self.current_sim_type = None
        self.is_initialized = False
        return False
        
    def _try_vsim(self):
        try:
            logger.debug("Trying to enable vSIM...")
            vsim.enable()
            utime.sleep(1)
            
            # Wait up to 10 seconds for vSIM to enable
            for i in range(10):
                state = vsim.queryState()
                if state == 1:  # vSIM enabled successfully
                    logger.debug("vSIM status check successful")
                    return True
                utime.sleep(1)
                
            logger.debug("vSIM enable timeout")
            return False
            
        except Exception as e:
            logger.debug("vSIM initialization failed: {}".format(e))
            return False
            
    def _try_physical_sim(self):
        try:
            logger.debug("Trying to use physical SIM card...")
            
            # Ensure vSIM is disabled
            try:
                vsim.disable()
                utime.sleep(3)  # Increase wait time
                logger.debug("vSIM disabled, waiting for physical SIM initialization...")
            except:
                pass
                
            # Check physical SIM status multiple times, allowing sufficient initialization time
            for attempt in range(15):  # Maximum 15 attempts, total 30 seconds
                sim_status = sim.getStatus()
                logger.debug("Physical SIM check [{}/15]: status={}".format(attempt+1, sim_status))
                
                # SIM status meanings: 0=not inserted/initializing, 1=ready, 2=needs PIN, 3=PUK locked, 4=fault
                if sim_status == 1:
                    logger.info("Physical SIM card ready!")
                    return True
                elif sim_status == 2:
                    logger.warning("Physical SIM card requires PIN code")
                    return False
                elif sim_status == 3:
                    logger.warning("Physical SIM card is PUK locked")
                    return False
                elif sim_status == 4:
                    logger.warning("Physical SIM card fault")
                    return False
                    
                # Status is 0, continue waiting
                if attempt < 14:  # Not the last attempt
                    utime.sleep(2)
                    
            logger.warning("Physical SIM card not ready within 30 seconds, final status: {}".format(sim_status))
            return False
                
        except Exception as e:
            logger.debug("Physical SIM card check exception: {}".format(e))
            return False
            
    def start_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = Thread(target=self._monitor_sim_status)
            self.monitor_thread.start()
            logger.info("SIM card hot-plug monitoring started")
            
    def stop_monitoring(self):
        self.monitoring = False
        if self.monitor_thread:
            logger.info("Stopping SIM card monitoring...")
            
    def _monitor_sim_status(self):
        while self.monitoring:
            try:
                # Check if current SIM status is still valid
                current_valid = self._check_current_sim_valid()
                
                if not current_valid:
                    logger.warning("Current {} SIM connection lost, trying to reinitialize".format(self.current_sim_type))
                    self.is_initialized = False
                    
                    # Reinitialize SIM
                    if self.initialize_sim():
                        logger.info("SIM card automatically switched to: {}".format(self.current_sim_type))
                    else:
                        logger.warning("No available SIM card")
                        
                utime.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error("SIM monitoring thread exception: {}".format(e))
                utime.sleep(10)
                
    def _check_current_sim_valid(self):
        try:
            if self.current_sim_type == 'vsim':
                return vsim.queryState() == 1
            elif self.current_sim_type == 'physical':
                return sim.getStatus() == 1
            else:
                return False
        except:
            return False
            
    def get_sim_info(self):
        return {
            'type': self.current_sim_type,
            'initialized': self.is_initialized,
            'monitoring': self.monitoring
        }
        
    def force_switch_to_vsim(self):
        logger.info("Force switching to vSIM")
        if self._try_vsim():
            self.current_sim_type = 'vsim'
            self.is_initialized = True
            logger.info("Switched to vSIM")
            return True
        logger.warning("vSIM switch failed")
        return False
        
    def force_switch_to_physical(self):
        logger.info("Force switching to physical SIM card")
        if self._try_physical_sim():
            self.current_sim_type = 'physical'
            self.is_initialized = True
            logger.info("Switched to physical SIM card")
            return True
        logger.warning("Physical SIM card switch failed")
        return False

