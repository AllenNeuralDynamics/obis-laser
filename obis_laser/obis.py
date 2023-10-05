#!/usr/bin/env python3
"""Serial device driver for OBIS LS/LX lasers."""

import sys
import serial
from enum import Enum
from time import sleep

# Define StrEnums if we are using an earlier Python version.
if sys.version_info < (3,11):
    class StrEnum(str, Enum):
        pass

# Collect various sets of commands into enums.
# Commands are SCPI-based
# https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments


class IEEESCPI(StrEnum):
    WARM_BOOT = "*RST"

class SessionControlCmd(StrEnum):
    SYSTEM_COMMUNICATE_HANDSHAKING = "SYST:COMM:HAND"
    SYSTEM_COMMUNICATE_PROMPT = "SYST:COMM:PROM"
    SYSTEM_AUTOSTART = "SYST:AUT"
    SYSTEM_INFO_AMODULATION_TYPE = "SYST:INF:AMOD:TYP"

    SYSTEM_INDICATOR_LASER = "SYST:IND:LAS"

    SYSTEM_ERROR_CLEAR = "SYST:ERR:CLE"


class SessionControlQuery(StrEnum):
    SYSTEM_COMMUNICATE_HANDSHAKING = "SYST:COMM:HAND?"
    SYSTEM_COMMUNICATE_PROMPT = "SYST:COMM:PROM?"
    SYSTEM_AUTOSTART = "SYST:AUT?"
    SYSTEM_INFO_AMODULATION_TYPE = "SYST:INF:AMOD:TYP?"

    SYSTEM_STATUS = "SYST:STAT?"
    SYSTEM_FAULT = "SYST:FAUL?"
    SYSTEM_INDICATOR_LASER = "SYST:IND:LAS?"
    SYSTEM_ERROR_COUNT = "SYST:ERR:COUN?"
    SYSTEM_ERROR_NEXT = "SYST:ERR:NEX?"


class SysInfoCmd(StrEnum):
    USER = "SYST:INF:USER"
    FIELD_CALIBRATION_DATE = "SYST:INF:FCD"
    POWER = "SYST:INF:POW"


class SysInfoQuery(StrEnum):
    MODEL = "SYST:INF:MOD?"
    MANUFACTURING_DATE = "SYST:INF:MDAT?"
    CALIBRATION_DATE = "SYST:INF:CDAT?"
    SERIAL_NUMBER = "SYST:INF:SNUM?"
    MANUFACTURING_PART_NUMBER = "SYST:INF:PNUM?"
    FIRMWARE_VERSION = "SYST:INF:FVER?"
    PROTOCOL_VERSION = "SYST:INF:PVER?"
    WAVELENGTH = "SYST:INF:WAV?"
    POWER = "SYST:INF:POW?"
    TYPE = "SYST:INF:TYP?"
    SOURCE_POWER_NOMINAL = "SOUR:POW:NOM?"
    SOURCE_POWER_LOW = "SOUR:POW:LIM:LOW?"
    SOURCE_POWER_HIGH = "SOUR:POW:LIM:HIGH?"
    USER = "SYST:INF:USER?"
    FIELD_CALIBRATION_DATE = "SYST:INF:FCD?"


class SystemStateQuery(StrEnum):
    # All of these are read only.
    SYSTEM_CYCLES = "SYST:CYCL?"
    SYSTEM_HOURS = "SYST:HOUR?"
    SYSTEM_DIODE_HOURS = "SYST:DIOD:HOUR?"
    SOURCE_POWER_LEVEL = "SOUR:POW:LEV?"
    SOURCE_POWER_CURRENT = "SOUR:POW:CURR?"
    SOURCE_TEMPERATURE_BASEPLATE = "SOUR:TEMP:BAS?"
    SYSTEM_LOCK = "SYST:LOCK"


class OperationalCmd(StrEnum):
    MODE_INTERNAL_CW = "SOUR:AM:INT"
    MODE_EXTERNAL = "SOUR:AM:EXT"
    POWER_LEVEL_AMPLITUDE = "SOUR:POW:LEV:IMM:AMPL"
    LASER_OUTPUT_STATE = "SOUR:AM:STAT"
    EMISSION_DELAY = "SYST:CDRH"


class OperationalQuery(StrEnum):
    OPERATING_MODE = "SOUR:AM:SOUR?"
    LASER_OUTPUT_STATE = "SOUR:AM:STAT?"
    EMISSION_DELAY = "SYST:CDRH?"
    POWER_LEVEL_AMPLITUDE = "SOUR:POW:LEV:IMM:AMPL?"


class OptionalCmd(StrEnum):
    DIODE_TEMPERATURE_CTRL = "SOUR:TEMP:APR"


class OptionalQuery(StrEnum):
    DIODE_TEMPERATURE_CTRL = "SOUR:TEMP:APR?"


class BoolStrEnum(StrEnum):
    # For bool-like settings the device takes "ON" and "OFF", not 0 and 1.
    ON = "ON"
    OFF = "OFF"


class SystemStatus(StrEnum):
    # KEY OUT: CE000___
    # KEY ON: C8001___
    # KEY ON on Powerup: C8000___ (This needs to be cleared.)
    KEY_OUT_INT_WARMUP = 'CE000100'
    KEY_OUT_INT_STANDBY = 'CE000008'
    KEY_OUT_EXT_WARMUP = 'CE000500'
    KEY_OUT_LASER_READY_INT_MODE = 'CE000008'
    KEY_OUT_LASER_READY_EXT_MODE = 'CE000408'
    KEY_OUT_FAULT = 'CE000001'  # Laser RED, Fault RED, KEY OFF

    KEY_ON_INT_WARMUP = 'C8001100'
    KEY_ON_EXT_WARMUP = 'C8001500'
    KEY_ON_LASER_READY_INT_MODE = 'C8001002'
    KEY_ON_LASER_READY_EXT_MODE = 'C8001402'
    # Open Interlock cannot be detected with the Key out.
    KEY_ON_LASER_READY_INT_MODE_INTERLOCK_OPEN = 'CC000008' # Status RED
    KEY_ON_LASER_READY_EXT_MODE_INTERLOCK_OPEN = 'CC000408'
    KEY_ON_FAULT = 'C8001001'  # Laser RED, Fault RED

    # if AUTOSTART was not set, then powering up the device with the key armed
    # will put the device in these special states. Status LED will blink blue.
    KEY_ARMED_EARLY_INT_WARMUP = 'C8000100'
    KEY_ARMED_EARLY_EXT_WARMUP = 'C8000500' # 'CE000500'
    KEY_ARMED_EARLY_LASER_READY_INT_MODE = 'C8000008'
    KEY_ARMED_EARLY_LASER_READY_EXT_MODE = 'C8000408'
    # what is 'C8001442' and 'C8001042'?
    # what is: 'C8001008' # warm up done with key on. key was just flipped off and then back on. 5-second delay?
    # what is: 'CC000008' # ?? was Fault RED ??
    # what is ______4_ and ______0_  as in 'CE000448' and 'CE000048'
    # what is 'C8001408'?


# Analog input impedance setting is model-agnostic.
class AnalogInputImpedanceType(StrEnum):
    FIFTY_OHM = "1"
    TWO_THOUSAND_OHM = "2"

# Modulation Setting (Operating Mode) depends on Model.
# See pg 143 in datasheet Part 1.
class LSModulationType(StrEnum):
    CW_POWER = "CWP"
    DIGITAL = "DIGITAL"
    ANALOG = "ANALOG"
    MIXED = "MIXED"


class LXModulationType(StrEnum):
    CW_POWER = "CWP"
    CW_CURRENT = "CWC"
    DIGITAL = "DIGITAL"
    DIGITAL_POWER = "DIGSO"
    ANALOG = "ANALOG"
    MIXED_POWER = "MIXSO"
    MIXED = "MIXED"


class Obis:

    BAUDRATE = 9600

    def __init__(self, port, prefix=None, modulation_mode: LSModulationType = LSModulationType.CW_POWER):
        """Constructor. Connect to the device."""

        self.prefix = prefix
        self.ser = serial.Serial(port, baudrate=self.__class__.BAUDRATE) if self.prefix == None else port
        # Flush OS buffers.
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()

        self.set_modulation_mode(modulation_mode)

    @property  # TODO: make a @cached_property
    def wavelength(self):
        return self.get_sys_info_setting(SysInfoQuery.WAVELENGTH)

    @property
    def temperature(self):
        """Return the temperature of the baseplate in degrees C."""
        reply = self.get_state_setting(SystemStateQuery.SOURCE_TEMPERATURE_BASEPLATE)
        return float(reply.strip('C'))

    def enable(self):
        """Enable the laser once it is ready (i.e: not warming up or faulted).

        Note: this command does not provide any feedback. If enabled while
              the laser is warming up, the setting will take effect after
              warmup is complete.
        """
        return self.set_operational_setting(OperationalCmd.LASER_OUTPUT_STATE,
                                            BoolStrEnum.ON.value)

    def disable(self):
        """Disable the laser.

        Note: this command does not provide any feeback.
        """
        return self.set_operational_setting(OperationalCmd.LASER_OUTPUT_STATE,
                                            BoolStrEnum.OFF.value)

    def get_system_status(self) -> SystemStatus:
        """Return the status of the laser as an enum."""
        stat_str = \
            self.get_session_ctrl_setting(SessionControlQuery.SYSTEM_STATUS)
        try:
            return SystemStatus(stat_str)
        except ValueError:
            print(f"'{stat_str}' is an unrecognized state.")
            raise

    def wait_until_ready(self):
        """Block until the laser is enabled."""
        state = self.get_system_status()
        while True:
            if state.value[-1] == '0':  # Check for warmup states.
                sleep(0.05)
            elif state.value[-1] == '1':  # Check for fault states.
                raise RuntimeError("Error: device is in a fault state.")
            state = self.get_system_status()

    def disable_cdrh(self):
        """Disable emission delay"""
        self.set_operational_setting(OperationalCmd.EMISSION_DELAY,
                                     BoolStrEnum.OFF.value)

    def get_setpoint(self):
        """Return setpoint of laser"""
        return float(self.get_operational_setting(OperationalQuery.POWER_LEVEL_AMPLITUDE)) * 1000

    def set_setpoint(self, value):
        """Set power of laser"""
        self.set_operational_setting(OperationalCmd.POWER_LEVEL_AMPLITUDE, str(value/1000))

    def get_max_setpoint(self):
        """Get max setpoint of laser"""
        return float(self.get_sys_info_setting(SysInfoQuery.SOURCE_POWER_HIGH)) *1000

    def warm_boot(self):
        """Tell the laser to warm boot."""
        self._writecmd(IEEESCPI.WARM_BOOT, "")

    def set_analog_input_impedance(self, ohms: AnalogInputImpedanceType):
        """Set the input impedance of the SMB analog input."""
        self.set_session_ctrl_setting(
            SessionControlCmd.SYSTEM_INFO_AMODULATION_TYPE, ohms)

    def get_modulation_mode(self) -> StrEnum:
        """Get the laser's modulation mode."""
        raise NotImplementedError

    def set_modulation_mode(self, mode: StrEnum):
        """set the laser's modulation type."""
        raise NotImplementedError

    # ---- Utility funcs ----

    def get_sys_info_setting(self, sys_info_query: SysInfoQuery):
        return self._readcmd(sys_info_query)

    def set_sys_info_setting(self, sys_info_cmd: SysInfoCmd, value):
        return self._writecmd(sys_info_cmd, value)

    def get_session_ctrl_setting(self, setting: SessionControlQuery):
        return self._readcmd(setting)

    def set_session_ctrl_setting(self, setting: SessionControlCmd, value: str):
        # String value depends on what setting we are writing.
        return self._writecmd(setting, value)

    def get_state_setting(self, setting: SystemStateQuery):
        return self._readcmd(setting)

    def get_operational_setting(self, setting:OperationalQuery):
        return self._readcmd(setting)

    def set_operational_setting(self, setting: OperationalCmd, value: str):
        return self._writecmd(setting, value)

    def get_optional_info(self, setting: OptionalQuery):
        return self._readcmd(setting)

    def _writecmd(self, cmd: StrEnum, cmd_arg_val: str ) -> str:
        """Write a command. Confirm that the device responds with an OK."""
        cmd_bytes = f"{self.prefix} {cmd.value} {cmd_arg_val}\r\n".encode('ascii') if self.prefix != None \
            else f"{cmd.value} {cmd_arg_val}\r\n".encode('ascii')
        # print(f"Writing: {cmd_bytes}")
        self.ser.write(cmd_bytes)
        conf = self.ser.readline().decode('utf8').rstrip('\r\n')
        assert conf == 'OK', \
            "Error: did not receive an OK when attempting to " \
            f"write: {repr(cmd_bytes)}\r\n" \
            f"Instead received: {conf}"

    def _readcmd(self, cmd: StrEnum) -> str:
        """Read a setting and return reply as string without \r\n."""
        # Every read replies with '<some_relevant_response>\r\nOK\r\n'
        # We must read 2 lines to throw out the 'OK\r\n'
        cmd_bytes = f"{self.prefix} {cmd.value}\r\n".encode('ascii') if self.prefix != None \
            else f"{cmd.value}\r\n".encode('ascii')
        # print(f"sending: {repr(cmd_bytes)}")
        self.ser.write(cmd_bytes)
        val = self.ser.readline().decode('utf8').rstrip('\r\n')
        #print(f"received: {val}")
        conf = self.ser.readline().decode('utf8').rstrip('\r\n')
        assert conf == 'OK', \
            "Error: did not receive an OK when attempting to " \
            f"write: {repr(cmd_bytes)}.\r\n" \
            f"Instead received: {val}"
        return val

class ObisLS(Obis):

    def set_modulation_mode(self, mode: LSModulationType):
        # Modes fall into 2 categories: internal or external.
        # CW type modes (only one for LS type) are internal.
        if mode == LSModulationType.CW_POWER:
            self._writecmd(OperationalCmd.MODE_INTERNAL_CW, mode)
        else:
            self._writecmd(OperationalCmd.MODE_EXTERNAL, mode)

    def get_modulation_mode(self) -> LSModulationType:
        # Read from device, and convert the string into one of the modes.
        return LSModulationType(self._readcmd(OperationalQuery.OPERATING_MODE))


class ObisLX(Obis):

    def set_modulation_mode(self, mode: LXModulationType):
        # Modes fall into 2 categories: internal or external.
        # CW type modes (only one for LS type) are internal.
        if mode in {LXModulationType.CW_POWER, LXModulationType.CW_CURRENT}:
            self._writecmd(OperationalCmd.MODE_INTERNAL_CW, mode)
        else:
            self._writecmd(OperationalCmd.MODE_EXTERNAL, mode)

    def get_modulation_mode(self) -> LXModulationType:
        # Read from device, and convert the string into one of the modes.
        return LXModulationType(self._readcmd(OperationalQuery.OPERATING_MODE))


if __name__ == "__main__":
    from inpromptu import Inpromptu
    obis = ObisLS("/dev/ttyACM0")
    # Create a REPL to interact with the object.
    Inpromptu(obis).cmdloop()

    # Connect.
    # Set analog modulation.
    # enable when we start imaging.
    # disable when we stop.
    # disable CDRH
    # TODO set power level
