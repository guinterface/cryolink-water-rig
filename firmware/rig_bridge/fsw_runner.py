"""Run installed FSW classes without editing fsw/. Explicit Earth-water FDIR adapter."""
import importlib
import math
import sys
import rclpy
from cryolink_fsw.base import run


class WaterVaporReference:
    """ASSUMPTION: open receiver at atmospheric pressure, no oxygen phase inference.

    Water vapor at wall < 15 C cannot be inferred from these two wall/inlet probes.
    Retain FDIR's temperature check as a > 100 C wall proxy; this is NOT a vapor detector.
    """
    @staticmethod
    def tsat(_pressure):
        return 373.15

    @staticmethod
    def psat(temperature):
        c = temperature - 273.15
        return 133.322 * math.pow(10., 8.07131 - 1730.63 / (233.426 + c))


def main():
    name = sys.argv.pop(1)
    module = importlib.import_module('cryolink_fsw.' + name)
    if name == 'transfer_sequencer':
        rclpy.init()
        node = module.TransferSequencer()
        node.trigger_configure()
        node.trigger_activate()
        try:
            rclpy.spin(node)
        except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
            pass
        finally:
            node.destroy_node()
            rclpy.try_shutdown()
    elif name == 'fdir_monitor':
        module.P = WaterVaporReference  # process local; installed FSW files unchanged
        run(module.FdirMonitor)
    else:
        module.main()


if __name__ == '__main__':
    main()
