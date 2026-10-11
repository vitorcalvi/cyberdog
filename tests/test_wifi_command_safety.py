"""Pure-Python regression tests for the Bluetooth Wi-Fi shell boundary."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'src/cyberdog_interaction/cyberdog_wireless/bluetooth/bluetooth/btwifitool.py'

sys.modules.setdefault('record', types.SimpleNamespace(logAll=None))
spec = importlib.util.spec_from_file_location('tested_btwifitool', MODULE)
wifi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wifi)


class WifiCommandsTest(unittest.TestCase):
    def test_ssid_and_password_are_arguments_not_shell(self):
        ssid = "attack'; echo unsafe; #"
        password = "secret'; echo unsafe; #"
        with patch.object(wifi.subprocess, 'run', return_value=types.SimpleNamespace(stdout='done')) as runner:
            self.assertEqual(wifi.nmcliConnectWifi(ssid, password), 'done')
            argv = runner.call_args.args[0]
            self.assertEqual(argv, ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password])
            self.assertFalse(runner.call_args.kwargs.get('shell', False))

    def test_psk_update_cannot_inject_shell(self):
        ssid = 'work network'
        password = "bad'; touch /tmp/no; #"
        with patch.object(wifi.subprocess, 'run', return_value=types.SimpleNamespace(stdout='ok')) as runner:
            wifi.exchangePSK(ssid, password)
            self.assertEqual(runner.call_args.args[0], ['sudo', 'nmcli', 'connection', 'modify', ssid, 'wifi-sec.psk', password])
            self.assertFalse(runner.call_args.kwargs.get('shell', False))

    def test_connection_activation_is_argv(self):
        with patch.object(wifi.subprocess, 'run', return_value=types.SimpleNamespace(stdout='ok')) as runner:
            wifi.connectUpWifi("ssid'; echo injected")
            self.assertEqual(runner.call_args.args[0][0:4], ['sudo', 'nmcli', 'connection', 'up'])
            self.assertFalse(runner.call_args.kwargs.get('shell', False))


if __name__ == '__main__':
    unittest.main()
