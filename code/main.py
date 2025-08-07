import utime
import dataCall
from usr.libs import Application
from usr.libs.logging import getLogger
from usr.extensions import (
    qth_client,
    gnss_service,
    lbs_service,
    sensor_service,
    sim_service,
)
from sim import vsim 


logger = getLogger(__name__)


def create_app(name="SimpliKit", version="1.0.0", config_path="/usr/config.json"):
    _app = Application(name, version)
    _app.config.init(config_path)

    # Register SIM service first for proper initialization order
    sim_service.init_app(_app)
    qth_client.init_app(_app)
    gnss_service.init_app(_app)
    lbs_service.init_app(_app)
    sensor_service.init_app(_app)

    return _app


if __name__ == "__main__":
    # Initialize SIM card using the SIM service
    logger.info("Starting SIM card initialization...")
    if sim_service.initialize_sim():
        sim_info = sim_service.get_sim_info()
        logger.info("Using {} SIM card".format(sim_info['type']))
    else:
        logger.error("SIM card initialization failed")
        # Fallback to original vSIM logic if SIM service fails
        logger.info("Using fallback vSIM initialization...")
        vsim.enable()
        while True:
            if vsim.queryState() == 1:
                logger.info("vSIM enabled successfully")
                break           
            vsim.enable()
            utime.sleep(2)
            logger.debug("Waiting for vSIM to enable...")

    # Configure data connection
    ret = dataCall.setPDPContext(1, 0, 'BICSAPN', '', '', 0)
    ret2 = dataCall.activate(1)
    
    while ret and ret2:
        ret = dataCall.setPDPContext(1, 0, 'BICSAPN', '', '', 0)
        ret2 = dataCall.activate(1)
        if not ret and not ret2:
            logger.info("Network connection successful")
            break
        logger.debug("Waiting for network connection...")
        utime.sleep(2)
        
    # Wait for LTE network to be ready
    while True:
        lte = dataCall.getInfo(1, 0)
        if lte[2][0] == 1:
            logger.debug('LTE network normal')
            break
        logger.debug('Waiting for LTE network to be normal...')
        utime.sleep(3)
    
    # Create and run application
    app = create_app()
    app.run()
