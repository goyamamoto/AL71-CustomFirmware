"""The YUNZII AL71 board around the smk image in the patched uCsim: the F65
rigs (test_f65.F65Sim, f65_devices.OursF65) with the AL71's switches.

What differs from the F65 board model (tests/f65_radio.py RadioBoard):
  - the connection switch is on P0.6 (low = 2.4 GHz) and P0.7 (low = Bluetooth);
  - the Win / Mac switch is on P7.4 (high = Win, low = Mac), so the external
    P7 level the key matrix presents keeps P7.4 (and P7.7, charging) as set.
The key matrix, the radio module's UART and P4.4 / P4.7 are wired as on the F65."""

import os
from pathlib import Path

from sim import REPO_ROOT, skip_or_fail
from devices import P5, P7
from test_f65 import F65Sim, F65KeyMatrix, COL_PIN, ROW_PIN
from f65_devices import OursF65
from f65_radio import RadioBoard, ContactMatrix, Timeline, SWITCH_USB, SWITCH_24G, SWITCH_BT

BUILD = REPO_ROOT / "build"
AL71_FW = os.environ.get("SMK_AL71_FIRMWARE") or str(BUILD / "yunzii-al71_usjis_smk.hex")
AL71_ANSI_FW = os.environ.get("SMK_AL71_ANSI_FIRMWARE") or str(BUILD / "yunzii-al71_ansi_smk.hex")
AL71_VIA_FW = os.environ.get("SMK_AL71_VIA_FIRMWARE") or str(BUILD / "yunzii-al71_usjis-via_smk.hex")
AL71_ANSI_VIA_FW = os.environ.get("SMK_AL71_ANSI_VIA_FIRMWARE") or str(BUILD / "yunzii-al71_ansi-via_smk.hex")
AL71_DIAG_FW = os.environ.get("SMK_AL71_LEDDIAG_FIRMWARE") or str(BUILD / "yunzii-al71_leddiag_smk.hex")
ALL_FW = (AL71_FW, AL71_ANSI_FW, AL71_VIA_FW, AL71_ANSI_VIA_FW)

ESC, BSPC, V, B, A, S = (0, 0), (13, 0), (4, 3), (5, 3), (1, 2), (2, 2)
FN = (9, 4)        # right of the key right of Space, in both layouts
LSFT, RSFT = (0, 3), (13, 3)
P0_SW_24G, P0_SW_BT = 0x40, 0x80
P7_OS = 0x10


def need(fw):
    if not Path(fw).exists():
        skip_or_fail(f"no yunzii-al71 firmware at {fw}")


def stock_image():
    """The official AL71 image (SMK_AL71_STOCK_IMAGE), or skip / fail (strict)."""
    img = os.environ.get("SMK_AL71_STOCK_IMAGE")
    if not img or not Path(img).exists():
        skip_or_fail("set SMK_AL71_STOCK_IMAGE to the official YUNZII AL71 V20.02 image (61440 bytes)")
    data = Path(img).read_bytes()
    assert len(data) == 0xF000, "the official image is 61440 bytes (0x0000-0xEFFF)"
    return data


class Al71Board(RadioBoard):
    """RadioBoard with the AL71's switches."""

    MODEL_VERSION = 11   # tools/ucsim/sh68f90.cc: bit reads of P7.4 see the pin

    def __init__(self, sess, *args, **kw):
        super().__init__(sess, *args, **kw)
        self.os_mac = False

    def switch(self, pos):
        self.p0 |= P0_SW_24G | P0_SW_BT
        if pos == SWITCH_24G:
            self.p0 &= ~P0_SW_24G
        elif pos == SWITCH_BT:
            self.p0 &= ~P0_SW_BT
        self._push()

    def position(self):
        if not self.p0 & P0_SW_24G:
            return SWITCH_24G
        if not self.p0 & P0_SW_BT:
            return SWITCH_BT
        return SWITCH_USB

    def os(self, mac):
        """The Win / Mac switch (P7.4 low = Mac)."""
        self.os_mac = mac
        self.p7 = (self.p7 & ~P7_OS) if mac else (self.p7 | P7_OS)
        self.sess.set_pin(P7, self.p7)


class Al71KeyMatrix(F65KeyMatrix):
    """F65KeyMatrix whose P7 level keeps the board's P7.4 / P7.7."""

    def __init__(self, board):
        super().__init__()
        self.board = board

    def inject(self, sess):
        port_cache = {}
        low_rows = set()
        for (c, r) in self.pressed:
            if self._col_driven_low(sess, c, port_cache):
                low_rows.add(r)
        level = {P5: 0xFF, P7: self.board.p7}
        for r in low_rows:
            port, bit = ROW_PIN[r]
            level[port] &= ~(1 << bit)
        sess.set_pin(P7, level[P7])
        sess.set_pin(P5, level[P5])


class Al71Sim(F65Sim):
    """F65Sim on the AL71 board (step-wise scans, EP1 reports)."""

    def reset_fast(self, p5=0xFF, p7=None):
        super().reset_fast(p5, self.radio.p7 if p7 is None else p7)

    def __init__(self, firmware=None):
        super().__init__(firmware or AL71_FW)
        self.radio = Al71Board(self)
        self.matrix = Al71KeyMatrix(self.radio)
        self.fn = FN

    def boot(self, usb=True, mac=False):
        self.radio.os_mac = mac
        self.radio.p7 = (self.radio.p7 & ~P7_OS) if mac else (self.radio.p7 | P7_OS)
        self.reset_fast(p7=self.radio.p7)
        self.brk(self._a("kb_update_switches"))
        self.run()
        self.cmd("delete")
        self.apply_lighting()
        self.mark_usb_configured()


class OursAl71(OursF65):
    """The timed rig (f65_devices.OursF65: keys as contacts in the simulator,
    1 ms steps, the radio module) on the AL71 board."""

    def __init__(self, firmware=None, mac=False):
        super().__init__(firmware or AL71_FW)
        self.radio = Al71Board(self, self.radio.model)
        self.radio.os(mac)
        self.matrix = Al71KeyMatrix(self.radio)
        self.fn = FN
        self.keys = ContactMatrix(self, self.radio, COL_PIN, ROW_PIN)
        self.tl = Timeline(self, self._a("pwm4_ms_tick_interrupt_handler"), self._a("user_matrix_read_rows"),
                           self.keys)

    def reset_fast(self, p5=0xFF, p7=None):
        super().reset_fast(p5, self.radio.p7 if p7 is None else p7)

    @property
    def radio_position(self):
        return self.radio.position()
