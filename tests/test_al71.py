#!/usr/bin/env python3
"""yunzii-al71 board tests, driven through the patched uCsim simulator.

The AL71 port shares the aula-f65-v1 board code; these tests cover what the
AL71 changes: the image for sinowisp (-d yunzii-al71), the USB strings, the
boot-time ISP escape, the pins after boot against the stock AL71 init (P7.4,
P4.1, P7.5 inputs), every key of the 71-key matrix, the Win / Mac switch on
P7.4, the connection switch on P0.6 / P0.7, the Bluetooth names (one pair
per slot, at boot and on a slot change), the sleep
parking (P0.5, the switch pins), with SMK_AL71_STOCK_IMAGE the keymap
against the stock tables and, with SMK_AL71_STOCK_DUMP (a full 64 KB readout
of a board with the ISP bootloader 2d169670; only 0xF000-0xFFFF is used) and
sinowisp on PATH, the chain through that bootloader; the layer-tap keys and
the mouse keys of the VIA images (test_f65_via's and test_f65_mouse's tests on
the AL71 rig). Run from the repo root
after building:

    python3 -m unittest discover -s tests -p test_al71.py

SMK_AL71_FIRMWARE (usjis), SMK_AL71_ANSI_FIRMWARE (ansi) and the _VIA_ variants
override the images.
"""

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from sim import REPO_ROOT, Sim, skip_or_fail, load_symbols, get_descriptor, DESC_DEVICE, DESC_STRING
from devices import P5, P7
from test_air75 import read_ihex
from test_f65 import (report, ISP_ENTRY, IE, P4, P6, MOD_LCTL, MOD_LSFT, MOD_LALT, MOD_LGUI, MOD_RCTL, MOD_RSFT,
                      MOD_RALT, MOD_RGUI, PORT_SFR, CR_SFR, PCR_SFR, COL_PIN, ROW_PIN)
from f65_radio import SWITCH_USB, SWITCH_24G, SWITCH_BT, frame
from test_f65_radio import RadioCase, sel, ctl
from al71_board import (Al71Sim, OursAl71, need, stock_image, AL71_FW, AL71_ANSI_FW, AL71_VIA_FW,
                        AL71_ANSI_VIA_FW, AL71_DIAG_FW, ALL_FW, ESC, BSPC, V, FN)
import test_f65_via
import test_f65_mouse

# Stock AL71 GPIO init (0xA237): PxCR, PxPCR and the latches, P0..P7.
STOCK_CR = [0x24, 0x3F, 0x3F, 0x3F, 0x6D, 0x87, 0xFF, 0x40]
STOCK_PCR = [0xF8, 0x3F, 0x3F, 0x3F, 0x6F, 0x9F, 0xFF, 0xDF]
STOCK_LATCH = [0x04, 0x00, 0x00, 0x00, 0x6D, 0x87, 0xFF, 0x00]

# Every key of the ansi Win base layer: position (col, row) -> HID usage.
ANSI_WIN_KEYS = {
    (0, 0): 0x29, (1, 0): 0x1E, (2, 0): 0x1F, (3, 0): 0x20, (4, 0): 0x21, (5, 0): 0x22, (6, 0): 0x23,
    (7, 0): 0x24, (8, 0): 0x25, (9, 0): 0x26, (10, 0): 0x27, (11, 0): 0x2D, (12, 0): 0x2E, (13, 0): 0x2A,
    (14, 0): 0x49, (15, 0): 0x4A,
    (0, 1): 0x2B, (1, 1): 0x14, (2, 1): 0x1A, (3, 1): 0x08, (4, 1): 0x15, (5, 1): 0x17, (6, 1): 0x1C,
    (7, 1): 0x18, (8, 1): 0x0C, (9, 1): 0x12, (10, 1): 0x13, (11, 1): 0x2F, (12, 1): 0x30, (13, 1): 0x31,
    (14, 1): 0x4D, (15, 1): 0x4B,
    (0, 2): 0x39, (1, 2): 0x04, (2, 2): 0x16, (3, 2): 0x07, (4, 2): 0x09, (5, 2): 0x0A, (6, 2): 0x0B,
    (7, 2): 0x0D, (8, 2): 0x0E, (9, 2): 0x0F, (10, 2): 0x33, (11, 2): 0x34, (13, 2): 0x28, (14, 2): 0x4C,
    (15, 2): 0x4E,
    (1, 3): 0x1D, (2, 3): 0x1B, (3, 3): 0x06, (4, 3): 0x19, (5, 3): 0x05, (6, 3): 0x11, (7, 3): 0x10,
    (8, 3): 0x36, (9, 3): 0x37, (10, 3): 0x38, (14, 3): 0x52,
    (5, 4): 0x2C, (10, 4): 0x65, (13, 4): 0x50, (14, 4): 0x51, (15, 4): 0x4F,
}
ANSI_WIN_MODS = {(0, 3): MOD_LSFT, (13, 3): MOD_RSFT, (0, 4): MOD_LCTL, (1, 4): MOD_LGUI, (2, 4): MOD_LALT,
                 (8, 4): MOD_RALT, (12, 4): MOD_RCTL}
ANSI_MAC_MODS = {(0, 4): MOD_LCTL, (1, 4): MOD_LALT, (2, 4): MOD_LGUI, (8, 4): MOD_RGUI, (10, 4): MOD_RALT,
                 (12, 4): MOD_RCTL}
EMPTY = [(12, 2), (11, 3), (12, 3), (15, 3), (3, 4), (4, 4), (6, 4), (7, 4), (11, 4)]
KEYS = 71

NVM_BASE = 0xEC00


def _keymaps(fw):
    need(fw)
    data = read_ihex(fw)
    base = load_symbols(Path(fw).with_suffix(".map"))["keymaps"]

    def key(layer, row, col):
        a = base + ((layer * 5 + row) * 16 + col) * 2
        return data[a] | (data[a + 1] << 8)
    return key


class TestImage(unittest.TestCase):
    """The .hex written with `sinowisp write -d yunzii-al71 --force`."""

    FLASH_CFG_ADDR = 0xEC00   # settings sector; the marker sector (0xEE00) and bootloader (0xF000) follow

    def test_layout_for_sinowisp(self):
        for fw in ALL_FW:
            need(fw)
            data = read_ihex(fw)
            with self.subTest(fw=Path(fw).name):
                self.assertEqual(min(data), 0)
                self.assertLess(max(data), self.FLASH_CFG_ADDR)
                self.assertEqual(data.get(0), 0x02, "sinowisp relocates the LJMP at 0x0000 to 0xEFFB")

    def test_device_descriptor_in_rom(self):
        for fw in ALL_FW:
            need(fw)
            data = read_ihex(fw)
            rom = bytes(data.get(i, 0xFF) for i in range(max(data) + 1))
            with self.subTest(fw=Path(fw).name):
                self.assertIn(bytes([0x12, 0x01, 0x10, 0x01, 0x00, 0x00, 0x00, 0x08, 0x8A, 0x25, 0x0C, 0x01]), rom)

    def test_no_f65_names_or_os_keys(self):
        """The AL71 names in the image; no OS-key handling (the switch decides)."""
        for fw in ALL_FW:
            need(fw)
            data = read_ihex(fw)
            rom = bytes(data.get(i, 0xFF) for i in range(max(data) + 1))
            with self.subTest(fw=Path(fw).name):
                self.assertIn(b"AL71\x00", rom)
                self.assertIn(b" 3.0\x00", rom)
                self.assertNotIn(b"AULA F65", rom)


class TestUsb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        need(AL71_FW)
        cls.sim = Sim(AL71_FW)

    def _string(self, index):
        desc = self.sim.reassemble(self.sim.control_in(get_descriptor(DESC_STRING, index=index)))
        return bytes(desc[2:desc[0]]).decode("utf-16le")

    def test_device_descriptor(self):
        desc = self.sim.reassemble(self.sim.control_in(get_descriptor(DESC_DEVICE)))
        self.assertEqual((desc[8] | desc[9] << 8, desc[10] | desc[11] << 8), (0x258A, 0x010C))

    def test_strings(self):
        self.assertEqual(self._string(1), "SMK")
        self.assertEqual(self._string(2), "YUNZII AL71 (SMK)")

    def test_isp_report_jumps_to_bootloader(self):
        out = self.sim.trigger_isp_jump()
        self.assertEqual(self.sim.stopped_at(out), ISP_ENTRY)
        self.assertEqual((self.sim.acc(out), self.sim.reg_b(out)), (0x5A, 0xA5))


class TestBootEscape(unittest.TestCase):
    """Esc (C0 x R0 = P6.0 x P7.1) held at power-up reaches the ISP entry."""

    def _boot_with(self, fw, *keys):
        kb = Al71Sim(fw)
        self.addCleanup(kb.close)
        kb.reset_fast()
        for k in keys:
            kb.matrix.press(*k)
        self.assertEqual(kb.run_until(kb._a("user_boot_escape"), kb._a("usb_init")), kb._a("user_boot_escape"))
        rr = kb._a("user_matrix_read_rows")
        kb.brk(rr)
        kb.brk(ISP_ENTRY)
        kb.brk(kb._a("usb_init"))
        while True:
            at = kb.stopped_at(kb.run())
            if at != rr:
                break
            kb.matrix.inject(kb)
        kb.cmd("delete")
        return kb, at

    def test_esc_held_jumps_to_isp(self):
        for fw in ALL_FW:
            need(fw)
            with self.subTest(fw=Path(fw).name):
                kb, at = self._boot_with(fw, ESC)
                self.assertEqual(at, ISP_ENTRY)
                self.assertEqual(kb.regs(), (0x5A, 0xA5))
                self.assertEqual(kb.get_sfr(IE) & 0x80, 0)

    def test_other_keys_boot_normally(self):
        need(AL71_FW)
        for keys in [(), ((1, 0),), (FN,), (BSPC,)]:
            with self.subTest(keys=keys):
                _, at = self._boot_with(AL71_FW, *keys)
                self.assertNotEqual(at, ISP_ENTRY)


class TestPinsAfterBoot(unittest.TestCase):
    """Directions, pull-ups and output latches after boot are the stock AL71 init;
    P7.4 (the OS switch), P4.1 and P7.5 stay inputs."""

    def test_pins_match_the_stock_init(self):
        for fw in ALL_FW:
            for mac in (False, True):
                need(fw)
                kb = Al71Sim(fw)
                self.addCleanup(kb.close)
                kb.boot(mac=mac)
                kb.brk(kb._a("usb_task"))
                kb.run()
                kb.cmd("delete")
                for port in range(8):
                    with self.subTest(fw=Path(fw).name, mac=mac, port=port):
                        cr, pcr = kb.get_sfr(CR_SFR[port]), kb.get_sfr(PCR_SFR[port])
                        if port == 0:
                            self.assertEqual(cr & 0x04, 0, "P0.2 released after the boot names")
                            cr |= 0x04
                        self.assertEqual(cr, STOCK_CR[port], f"P{port}CR")
                        self.assertEqual(pcr, STOCK_PCR[port], f"P{port}PCR")
                        mask = cr & (0xBF if port == 7 else 0xFF)   # P7.6 follows !P4.4
                        self.assertEqual(kb.get_sfr(PORT_SFR[port]) & mask, STOCK_LATCH[port] & mask)
                p4, p7 = kb.get_sfr(PORT_SFR[4]), kb.get_sfr(PORT_SFR[7])
                self.assertEqual((p7 >> 6) & 1, 1 - ((p4 >> 4) & 1), "P7.6 = !P4.4")

    def test_os_switch_pin_is_never_an_output_while_running(self):
        """With keys, the LEDs and the matrix scan running (OS switch at Mac:
        the pin is held low by the switch), P7CR bit 4 stays clear."""
        need(AL71_FW)
        kb = Al71Sim(AL71_FW)
        self.addCleanup(kb.close)
        kb.boot(mac=True)
        for _ in range(4):
            kb.tap((1, 2))
            self.assertEqual(kb.get_sfr(CR_SFR[7]) & 0x10, 0)
            self.assertEqual(kb.get_sfr(CR_SFR[4]) & 0x02, 0, "P4.1 stays an input")


class KeymapCase(unittest.TestCase):
    FW = AL71_FW

    def session(self, mac=False, fw=None):
        fw = fw or self.FW
        need(fw)
        kb = Al71Sim(fw)
        self.addCleanup(kb.close)
        kb.boot(mac=mac)
        return kb

    def assertTap(self, kb, keys, expected):
        rpt = kb.tap(*keys)
        self.assertIsNotNone(rpt, f"keys {keys} produced no EP1 report")
        self.assertEqual(rpt, expected, f"keys {keys}")


class TestAnsiMatrix(KeymapCase):
    FW = AL71_ANSI_FW

    def test_key_count(self):
        self.assertEqual(len(ANSI_WIN_KEYS) + len(ANSI_WIN_MODS) + 1, KEYS, "plus Fn")
        self.assertEqual(len(set(ANSI_WIN_KEYS) | set(ANSI_WIN_MODS) | {FN} | set(EMPTY)), 80)

    def test_every_key(self):
        keys = list(ANSI_WIN_KEYS.items())
        for i in range(0, len(keys), 8):
            kb = self.session()
            for key, code in keys[i:i + 8]:
                with self.subTest(key=key):
                    self.assertTap(kb, [key], report(0, code))

    def test_modifiers_win_and_mac(self):
        for mac, mods in ((False, ANSI_WIN_MODS), (True, ANSI_MAC_MODS)):
            kb = self.session(mac=mac)
            for key, mod in mods.items():
                with self.subTest(mac=mac, key=key):
                    self.assertTap(kb, [key], report(mod))

    def test_empty_positions_send_nothing(self):
        kb = self.session()
        for key in EMPTY:
            kb.matrix.press(*key)
        self.assertEqual(kb.step(), [])


class TestUsjisLayout(KeymapCase):
    """usjis = ansi but Caps / Left Ctrl swapped and the IME mod-taps beside Space."""

    def test_differs_only_where_intended(self):
        for ansi_fw, usjis_fw in ((AL71_ANSI_FW, AL71_FW), (AL71_ANSI_VIA_FW, AL71_VIA_FW)):
            ansi, usjis = _keymaps(ansi_fw), _keymaps(usjis_fw)
            intended = {(0, 2), (0, 4), (2, 4), (8, 4), (0, 1)}   # (0, 1): Fn + Tab = US-JIS
            for layer in range(4):
                for row in range(5):
                    for col in range(16):
                        if (col, row) in intended:
                            continue
                        with self.subTest(fw=Path(usjis_fw).name, layer=layer, key=(col, row)):
                            self.assertEqual(usjis(layer, row, col), ansi(layer, row, col))

    def _tap_reports(self, kb, key):
        kb.matrix.press(*key)
        reps = kb.step()
        kb.matrix.clear()
        return reps + kb.step()

    def test_ime_keys_tap(self):
        """A tap of the mod-tap sends its key on release."""
        for mac, taps in ((False, (((2, 4), 0x8B), ((8, 4), 0x8A))), (True, (((2, 4), 0x91), ((8, 4), 0x90)))):
            kb = self.session(mac=mac)
            for key, code in taps:
                with self.subTest(mac=mac, key=key):
                    self.assertIn(report(0, code), self._tap_reports(kb, key))
        kb = self.session()
        self.assertTap(kb, [(0, 2)], report(MOD_LCTL))


class TestFnLayer(KeymapCase):
    def test_fn_esc_is_grave(self):
        for fw in (AL71_FW, AL71_ANSI_FW):
            kb = self.session(fw=fw)
            with self.subTest(fw=Path(fw).name):
                self.assertTap(kb, [FN, ESC], report(0, 0x35))

    def test_fn_number_row_is_f_keys_on_win(self):
        kb = self.session()
        self.assertTap(kb, [FN, (1, 0)], report(0, 0x3A))
        self.assertTap(kb, [FN, (12, 0)], report(0, 0x45))

    def test_nav_cluster_under_fn_is_the_nav_key(self):
        kb = self.session()
        for key, code in (((14, 0), 0x49), ((15, 0), 0x4A), ((14, 1), 0x4D), ((15, 1), 0x4B), ((14, 2), 0x4C),
                          ((15, 2), 0x4E)):
            with self.subTest(key=key):
                self.assertTap(kb, [FN, key], report(0, code))

    def test_fn_a_and_fn_s_send_nothing(self):
        """No OS keys: Fn + A / S are transparent to the base A / S."""
        kb = self.session()
        self.assertTap(kb, [FN, (1, 2)], report(0, 0x04))
        self.assertTap(kb, [FN, (2, 2)], report(0, 0x16))

    def test_settings_reset_chord_sends_nothing(self):
        kb = self.session()
        kb.down(FN)
        self.assertEqual([r for r in kb.down(BSPC) if r != report()], [])
        self.assertEqual([r for r in kb.down(V) if r != report()], [])
        kb.matrix.clear()
        kb.step()


class TestOsSwitch(KeymapCase):
    """P7.4: high = Win, low = Mac; read at boot and every 10 ms (10 samples),
    never saved."""

    FW = AL71_ANSI_FW

    def _os(self, kb):
        return kb.setting("os_mac")

    def test_boot_follows_the_switch(self):
        for mac in (False, True):
            kb = self.session(mac=mac)
            with self.subTest(mac=mac):
                self.assertEqual(self._os(kb), int(mac))
                self.assertTap(kb, [(1, 4)], report(MOD_LALT if mac else MOD_LGUI))

    def _timed(self):
        need(self.FW)
        r = OursAl71(self.FW)
        self.addCleanup(r.close)
        r.start(SWITCH_USB)
        r.ms(50)
        return r

    def _lwin_key(self, r):
        """The modifier the key right of Left Ctrl sends."""
        n = len(r.ep1_reports())
        r.tap((1, 4))
        mods = [rep[0] for rep in r.ep1_reports()[n:] if rep[0]]
        return mods[0] if mods else None

    def test_switch_moved_while_running(self):
        r = self._timed()
        self.assertEqual(self._lwin_key(r), MOD_LGUI)
        for mac, mod in ((True, MOD_LALT), (False, MOD_LGUI)):
            with self.subTest(mac=mac):
                r.radio.os(mac)
                r.ms(150)                     # 10 samples, 10 ms apart
                self.assertEqual(r.setting("os_mac"), int(mac))
                self.assertEqual(self._lwin_key(r), mod)

    def test_short_glitch_does_not_switch(self):
        r = self._timed()
        r.radio.os(True)
        r.ms(50)                              # 5 samples
        r.radio.os(False)
        r.ms(200)
        self.assertEqual(r.setting("os_mac"), 0)

    def test_switch_change_writes_no_flash(self):
        r = self._timed()
        n = len(re.findall(r"\[SIE\] FLASH", r.stderr_text()))
        r.radio.os(True)
        r.ms(4000)                            # past the settings save delay
        self.assertEqual(r.setting("os_mac"), 1)
        self.assertEqual(len(re.findall(r"\[SIE\] FLASH", r.stderr_text())), n)


class TestConnectionSwitch(unittest.TestCase):
    """P0.6 low = 2.4 GHz, P0.7 low = Bluetooth, both high = USB."""

    def rig(self, pos, fw=AL71_FW):
        need(fw)
        r = OursAl71(fw)
        self.addCleanup(r.close)
        r.start(pos)
        return r

    def test_boot_positions(self):
        for pos, transport in ((SWITCH_USB, 0), (SWITCH_24G, 1), (SWITCH_BT, 2)):
            with self.subTest(pos=pos):
                r = self.rig(pos)
                r.ms(300)
                self.assertEqual(r.transport(), transport)
                self.assertEqual(r.usb_enabled(), transport == 0)

    def test_moving_the_switch(self):
        r = self.rig(SWITCH_USB)
        r.ms(200)
        for pos, transport in ((SWITCH_BT, 2), (SWITCH_24G, 1), (SWITCH_USB, 0)):
            with self.subTest(pos=pos):
                r.switch(pos)
                r.ms(100)
                self.assertEqual(r.transport(), transport)

    def test_boot_names(self):
        """01 09 <profile> <length> "AL71-1" / "AL71-1 3.0" 00..., 32 bytes: slot 1 when nothing is saved."""
        r = self.rig(SWITCH_USB)
        names = [f for f in r.frames() if len(f) > 1 and f[1] == 0x09]
        self.assertEqual(names, slot_names(1))
        self.assertEqual(names[0][2:4], [0, 6])
        self.assertEqual(bytes(names[0][4:10]), b"AL71-1")
        self.assertEqual(names[1][2:4], [1, 10])
        self.assertEqual(bytes(names[1][4:14]), b"AL71-1 3.0")
        self.assertEqual(names[1][14:31], [0] * 17)


def slot_names(slot):
    """The two name frames of a Bluetooth slot: "AL71-<slot>" (BT5.0) and "AL71-<slot> 3.0" (BT3.0)."""
    return [frame(0x09, profile, len(text), *text.encode(), length=32)
            for profile, text in ((0, f"AL71-{slot}"), (1, f"AL71-{slot} 3.0"))]


def name_frames(frames):
    return [f for f in frames if len(f) > 1 and f[1] == 0x09]


def links(frames):
    """The control frames other than the names (test_f65_radio.ctl keeps them)."""
    return [f for f in ctl(frames) if f[1] != 0x09]


class TestSlotNames(RadioCase):
    """One pair of Bluetooth names per slot: the saved slot's at boot, a slot's
    again on the press of its key (Fn + Q / W / E) when the module has another
    slot's, never between that press and the pairing request of a hold. Every
    scenario also gets RadioCase's frame checks (sums, P0.2 lead and gap)."""

    def dev(self, fw=None, position=SWITCH_USB, **kw):
        fw = fw or AL71_FW
        need(fw)
        d = OursAl71(fw)
        self.addCleanup(self._check_and_close, d)
        d.start(position, **kw)
        return d

    def linked(self, slot=1, **kw):
        d = self.dev(**kw)
        self.into(d, SWITCH_BT, slot)
        d.ms(700)
        return d

    def hold(self, d, key, ms):
        d.press(d.fn, ms=20)
        d.press(key, ms=ms)
        d.release(key, ms=20)
        d.release(d.fn, ms=50)

    def test_other_slot_names_on_the_press_then_the_select(self):
        d = self.linked()
        d.press(d.fn, ms=20)
        m = d.mark()
        d.press(d.BT2, ms=50)
        got = d.frames(m)
        self.assertEqual(name_frames(got), slot_names(2), "the names on the press")
        self.assertEqual(links(got), [], "no select before the release")
        d.release(d.BT2, ms=20)
        d.release(d.fn, ms=20)
        got = d.frames(m)
        self.assertEqual(name_frames(got), slot_names(2))
        self.assertEqual(links(got), [sel(0, 2)])
        self.assertLess(max(i for i, f in enumerate(got) if f[1] == 0x09), got.index(sel(0, 2)))
        self.assertEqual(d.bt_slot(), 2)

    def test_the_current_slot_sends_no_names(self):
        d = self.linked()
        m = d.mark()
        self.hold(d, d.BT1, 100)
        self.assertEqual(name_frames(d.frames(m)), [])
        self.assertEqual(links(d.frames(m)), [sel(0, 1)])
        m = d.mark()
        self.hold(d, d.BT1, 3200)
        self.assertEqual(ctl(d.frames(m)), [sel(1, 1)], "a pairing hold on the current slot: the request alone")

    def test_hold_on_another_slot_names_it_seconds_before_the_pairing_request(self):
        d = self.linked()
        m = d.mark()
        self.hold(d, d.BT3, 3200)
        env = [e for e in self.envelopes(d)[m:] if e["bytes"]]
        got = [e["bytes"] for e in env]
        self.assertEqual(name_frames(got), slot_names(3))
        self.assertEqual(links(got), [sel(1, 3)])
        last_name = max(i for i, f in enumerate(got) if f[1] == 0x09)
        pair = next(i for i, f in enumerate(got) if f[:4] == sel(1, 3)[:4])
        self.assertLess(last_name, pair)
        self.assertGreaterEqual(self.cycles_ms(env[last_name]["t"], env[pair]["t"]), 3000)

    def test_back_and_forth(self):
        d = self.linked()
        m = d.mark()
        for key, slot in ((d.BT2, 2), (d.BT1, 1), (d.BT1, 1), (d.BT3, 3)):
            self.hold(d, key, 50)
            d.status(slot, 3)
            d.ms(700)
        got = d.frames(m)
        self.assertEqual(name_frames(got), slot_names(2) + slot_names(1) + slot_names(3))
        self.assertEqual(links(got), [sel(0, 2), sel(0, 1), sel(0, 1), sel(0, 3)])

    def test_select_keeps_32_ms_after_the_names(self):
        """With the busy-wait delays running: each name is followed by 32 ms
        (as at boot), so the select on a quick release comes no sooner."""
        d = self.linked(stub_delays=False)
        m = d.mark()
        d.press(d.fn, ms=20)
        d.press(d.BT2, ms=40)
        d.release(d.BT2, ms=200)
        d.release(d.fn, ms=20)
        env = [e for e in self.envelopes(d)[m:] if e["bytes"]]
        got = [e["bytes"] for e in env]
        self.assertEqual(name_frames(got), slot_names(2))
        i_name = max(i for i, f in enumerate(got) if f[1] == 0x09)
        i_sel = got.index(sel(0, 2))
        self.assertGreaterEqual(self.cycles_ms(env[i_name]["t"], env[i_sel]["t"]), 32)

    def test_saved_slot_named_at_boot(self):
        d = self.linked()
        self.hold(d, d.BT3, 50)
        d.ms(50)
        for pos in (SWITCH_BT, SWITCH_USB):
            with self.subTest(pos=pos):
                m = d.mark()
                d.reboot(pos)
                d.ms(300)
                self.assertEqual(d.bt_slot(), 3)
                self.assertEqual(name_frames(d.frames(m)), slot_names(3))

    def test_no_names_in_24g(self):
        d = self.dev()
        self.into(d, SWITCH_24G, 0)
        d.ms(700)
        m = d.mark()
        for key in (d.BT2, d.P24):
            self.hold(d, key, 50)
        self.into(d, SWITCH_BT, 1)
        d.ms(300)
        self.assertEqual(name_frames(d.frames(m)), [], "the slot keys do nothing in 2.4 GHz, slot 1 already named")


class TestSleep(unittest.TestCase):
    """The wireless sleep parks the pins as the stock AL71 (0x4FA9): P0.5
    high, P0.5-P0.7 / P7.4 / P7.7 low without pull-up, P4.1 untouched; a key
    wakes it and the switch pins are pulled-up inputs again."""

    def rig(self, mac=False):
        need(AL71_FW)
        r = OursAl71(AL71_FW, mac=mac)
        self.addCleanup(r.close)
        r.start(SWITCH_BT)
        r.ms(200)
        r.status(1, 2)          # Bluetooth slot 1, reconnecting: (10 x 2 + 1) s idle
        r.ms(20)
        a = r._xdata_static("f65_rf", "idle_s")
        r.cmd("set mem xram 0x%x 0x%02x 0x00" % (a, 20))
        r.cmd("set mem xram 0x%x 0x00 0x00" % r._xdata_static("f65_rf", "idle_ms"))
        return r

    def sleep_now(self, r):
        pd = r.code("f65_power", "power_down")
        r.brk(pd)
        r.brk(r._a("pwm4_ms_tick_interrupt_handler"))
        try:
            for _ in range(5000):
                if r.stopped_at(r.run()) == pd:
                    return
            self.fail("no sleep")
        finally:
            r.cmd("delete")

    def test_wired_sleep_parking(self):
        """Middle position, no configured host, 10 s quiet: the common park and
        P0.5 high, P7.6 left as it is; a key wakes it and the pins come back."""
        need(AL71_FW)
        r = OursAl71(AL71_FW)
        self.addCleanup(r.close)
        r.start(SWITCH_USB)
        r.ms(100)
        r.cmd("set mem xram 0x%x 0x00" % r._a("usb_device_state"))
        a = r._xdata_static("f65_rf", "usb_quiet_ms")
        r.cmd("set mem xram 0x%x 0x%02x 0x%02x" % (a, 9990 & 0xFF, 9990 >> 8))
        self.sleep_now(r)
        p0, p0cr = r.get_sfr(0x80), r.get_sfr(CR_SFR[0])
        p7, p7cr = r.get_sfr(0xF8), r.get_sfr(CR_SFR[7])
        self.assertEqual((p0cr & 0xE0, p0 & 0xE0), (0xE0, 0x20), "P0.6 / P0.7 low, P0.5 high")
        self.assertEqual((p7cr & 0x90, p7 & 0x10), (0x10, 0x00), "P7.4 low; P7.7 stays an input")
        self.assertEqual(r.get_sfr(CR_SFR[4]) & 0x02, 0, "P4.1 stays an input")
        self.assertEqual(r.get_sfr(CR_SFR[0]) & 0x18, 0, "P0.3 / P0.4 stay inputs")
        r.radio.wake_key(True)
        r.ms(30)
        r.radio.wake_key(False)
        r.ms(300)
        self.assertEqual(r.get_sfr(CR_SFR[7]) & 0x10, 0)
        self.assertEqual(r.get_sfr(CR_SFR[0]) & 0xC0, 0)
        self.assertEqual(r.get_sfr(0x80) & 0x20, 0)

    def test_parking_and_wake(self):
        for mac in (False, True):
            with self.subTest(mac=mac):
                r = self.rig(mac)
                self.sleep_now(r)
                p0, p0cr, p0pcr = r.get_sfr(0x80), r.get_sfr(CR_SFR[0]), r.get_sfr(PCR_SFR[0])
                p7, p7cr, p7pcr = r.get_sfr(0xF8), r.get_sfr(CR_SFR[7]), r.get_sfr(PCR_SFR[7])
                self.assertEqual((p0cr & 0xE0, p0 & 0xE0, p0pcr & 0xC0), (0xE0, 0x20, 0x00),
                                 "P0.6 / P0.7 low without pull-up, P0.5 high")
                self.assertEqual((p7cr & 0x90, p7 & 0x90, p7pcr & 0x90), (0x90, 0x00, 0x00), "P7.4 / P7.7 low")
                self.assertEqual(p7 & 0x40, 0, "P7.6 low")
                self.assertEqual(r.get_sfr(CR_SFR[4]) & 0x02, 0, "P4.1 stays an input")
                self.assertEqual(p7cr & 0x0F, 0, "rows are inputs")
                self.assertEqual(r.get_sfr(CR_SFR[5]) & 0x18, 0, "rows are inputs")
                r.radio.wake_key(True)
                r.ms(30)
                r.radio.wake_key(False)
                self.assertIn("[SIE] wake from power-down", r.stderr_text())
                r.ms(200)
                self.assertEqual(r.get_sfr(CR_SFR[7]) & 0x10, 0, "P7.4 an input again")
                self.assertEqual(r.get_sfr(PCR_SFR[7]) & 0x10, 0x10)
                self.assertEqual(r.get_sfr(CR_SFR[0]) & 0xC0, 0, "the switch pins inputs again")
                self.assertEqual(r.get_sfr(0x80) & 0x20, 0, "P0.5 low while running")
                self.assertEqual(r.transport(), 2)
                self.assertEqual(r.setting("os_mac"), int(mac), "the OS switch read again after the wake")


class TestPinGuard(unittest.TestCase):
    """Every instruction of every image that writes a direction register:
    outside the GPIO init and the sleep parking, none makes an output of an
    AL71 input (the switches P0.6 / P0.7 / P7.4, P0.3, P0.4, P4.1, P4.4,
    P4.7, P7.5, P7.7, the rows); inside the parking only the pins the stock
    parks (P0.0 / P0.1, P0.5-P0.7, P7.4, P7.7 and the key columns)."""

    ALLOWED_FUNCS = ("user_gpio_init", "park_pins")
    # bits that must never become outputs outside ALLOWED_FUNCS
    FORBIDDEN = {"P0CR": 0xFB, "P4CR": 0x92, "P5CR": 0x78, "P6CR": 0x00, "P7CR": 0xBF}
    # bits park_pins may make outputs
    PARK = {"P0CR": 0xE3, "P4CR": 0x6D, "P5CR": 0x87, "P6CR": 0xFF, "P7CR": 0x90}
    WRITE = re.compile(r"^\s+[0-9A-F]{6}\s+(?:[0-9A-F]{2}\s+)*\[\s*\d+\]\s+\d+\s+(mov|orl|xrl|anl)\s+_(P\dCR),(\S+)", re.I)
    LABEL = re.compile(r"^\s+[0-9A-F]{6}\s+\d+\s+_(\w+):\s*$")

    def test_no_input_made_an_output(self):
        for fw in ALL_FW + (AL71_DIAG_FW,):
            need(fw)
            seen = 0
            for rst in sorted(Path(fw).with_suffix(".ihx.p").glob("*.rst")):
                func = None
                for line in rst.read_text().splitlines():
                    m = self.LABEL.match(line)
                    if m:
                        func = m.group(1)
                        continue
                    m = self.WRITE.match(line)
                    if not m:
                        continue
                    op, reg, src = m.group(1).lower(), m.group(2).upper(), m.group(3)
                    seen += 1
                    where = f"{Path(fw).name} {rst.stem}:{func}: {line.strip()}"
                    with self.subTest(where=where):
                        if op == "anl":
                            continue                        # clears direction bits: inputs
                        if reg in ("P1CR", "P2CR", "P3CR"):
                            continue                        # the LED anodes
                        imm = re.fullmatch(r"#0x([0-9a-fA-F]+)", src)
                        self.assertIsNotNone(imm, "a direction register written from a register")
                        v = int(imm.group(1), 16)
                        if func in self.ALLOWED_FUNCS:
                            if func == "park_pins":
                                self.assertEqual(v & ~self.PARK[reg] & 0xFF, 0)
                            continue
                        self.assertEqual(v & self.FORBIDDEN[reg], 0)
            self.assertGreater(seen, 10, f"{Path(fw).name}: the listings were read")


class TestSleepParkingStatic(unittest.TestCase):
    """park_pins in the image: the instructions that touch P0 / P7 / P4.1 /
    P0.5, from the linker listing of f65_power."""

    def test_park_pins_listing(self):
        for fw in (AL71_FW, AL71_ANSI_FW):
            need(fw)
            rst = (Path(fw).with_suffix(".ihx.p") / "f65_power.rst").read_text()
            body = rst[rst.index("_park_pins:"):]
            body = body[:body.index("ret")]
            with self.subTest(fw=Path(fw).name):
                self.assertRegex(body, r"anl\s+_P0PCR,#0x1f")
                self.assertRegex(body, r"orl\s+_P0CR,#0xe0")
                self.assertRegex(body, r"anl\s+_P0,#0x1f")
                self.assertRegex(body, r"anl\s+_P7PCR,#0x6f")
                self.assertRegex(body, r"orl\s+_P7CR,#0x90")
                self.assertRegex(body, r"anl\s+_P7,#0x6f")
                self.assertRegex(body, r"setb\s+_P0_5")
                self.assertNotRegex(body, r"_P4_1")


PHASE = [0xB5, 0xB4, 0xB6, 0xB8, 0xB7, 0xB9, 0xBB, 0xBA, 0xBC, 0xBE, 0xBD, 0xBF, 0xC1, 0xC0, 0xC2, 0xC4, 0xC3, 0xC5]
TABLES_H = REPO_ROOT / "src" / "keyboards" / "yunzii-al71" / "backlight_tables.h"


def header_table(name):
    m = re.search(r"%s\[\d+\] = \{(.*?)\n\};" % re.escape(name), TABLES_H.read_text(), re.S)
    return [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{2})", m.group(1))]


class LightRig(OursAl71):
    def bl_field(self, offset):
        """user_settings.bl_magic + offset (bl_on 1, bl_effect 2, sl_effect 39,
        sl_colour 40, sl_brightness 41)."""
        from test_f65 import field_offset
        return self._a("user_settings") + field_offset(self.firmware, "backlight", "backlight_defaults") + offset

    def fb8(self, col, row):
        return self.get_xram(self._a("led_fb8") + (col * 6 + row) * 3, 3)

    def duty(self, col, row):
        v = self.get_xram(self._xdata_static("led", "led_fb") + col * 36 + row * 6, 6)
        return [v[2 * c] << 8 | v[2 * c + 1] for c in range(3)]


class TestLighting(unittest.TestCase):
    """The side lights on the AL71's cells and slot order; the status LEDs;
    the key positions of the effects are the stock AL71's."""

    def rig(self, fw=AL71_FW):
        need(fw)
        r = LightRig(fw)
        self.addCleanup(r.close)
        r.start(SWITCH_USB)
        r.ms(50)
        return r

    def test_side_lights_cells_and_slot_order(self):
        """Static side colour: the four pairs (0-3, 0) / (12-15, 0) show it in
        slot order G, R, B; no other cell of LED row 0 is lit."""
        cols = header_table("bl_side_col")
        green = next(i for i in range(7) if cols[3 * i:3 * i + 3] == [0, 0xFF, 0])
        blue = next(i for i in range(7) if cols[3 * i:3 * i + 3] == [0, 0, 0xFF])
        r = self.rig()
        for colour, slots in ((green, (1, 0, 0)), (blue, (0, 0, 1))):
            with self.subTest(colour=colour):
                r.cmd("set mem xram 0x%x 0x03 0x%02x 0x04" % (r.bl_field(39), colour))
                r.ms(400)
                for col in range(16):
                    v = r.fb8(col, 0)
                    if col < 4 or col >= 12:
                        self.assertEqual([bool(x) for x in v], [bool(x) for x in slots], (col, v))
                    else:
                        self.assertEqual(v, [0, 0, 0], (col, v))

    def test_status_leds_dark_under_the_backlight(self):
        r = self.rig()
        r.ms(300)
        self.assertTrue(any(r.fb8(1, 2)), "the effect paints the keys")
        for col in (4, 6):
            self.assertEqual(r.duty(col, 5), PHASE[15:18], f"status cell ({col}, 5) dark")

    def test_cells_without_keys_in_the_status_row_stay_dark(self):
        r = self.rig()
        for _ in range(5):
            r.ms(200)
            for col in (3, 7):
                self.assertEqual(r.duty(col, 5), PHASE[15:18], f"({col}, 5)")

    def test_leddiag_steps_through_the_al71_cells(self):
        need(AL71_DIAG_FW)
        data = read_ihex(AL71_DIAG_FW)
        rom = bytes(data.get(i, 0xFF) for i in range(max(data) + 1))
        for name in (b"side l0", b"side r0", b"status caps", b"status link", b"status 3", b"status 7"):
            self.assertIn(name, rom)
        self.assertNotIn(b"side a0", rom)

    def test_caps_status_led(self):
        r = self.rig()
        r.cmd("set mem xram 0x%x 0x02" % r._a("keyboard_state"))   # host Caps Lock LED on
        r.ms(100)
        self.assertEqual(r.duty(4, 5), [0x0400, PHASE[16], PHASE[17]], "red")
        self.assertEqual(r.duty(6, 5), PHASE[15:18])
        r.cmd("set mem xram 0x%x 0x00" % r._a("keyboard_state"))
        r.ms(100)
        self.assertEqual(r.duty(4, 5), PHASE[15:18])

    def test_link_status_led_blinks_while_pairing(self):
        r = self.rig()
        r.switch(SWITCH_BT, 200)
        r.status(1, 1)                       # slot 1 pairing
        seen = set()
        for _ in range(12):
            r.ms(40)
            seen.add(tuple(r.duty(6, 5)))
        self.assertIn((PHASE[15], PHASE[16], 0x0400), seen, "blue")
        self.assertIn(tuple(PHASE[15:18]), seen, "dark between")

    def mid(self, r):
        """The middle LED: the Caps cell's second channel at the indicator level."""
        return r.duty(4, 5)[1] == 0x0400

    def test_middle_led_shows_us_jis_while_fn_is_held(self):
        """usjis: dark; Fn held: blinking while US-JIS is off; Fn + Tab: on
        while US-JIS is on, for about a second after Fn is up, then dark. The
        top LED (Caps, first channel) stays dark."""
        r = self.rig()
        self.assertFalse(self.mid(r))
        r.press(FN, ms=20)
        seen = set()
        for _ in range(12):
            r.ms(60)
            seen.add(self.mid(r))
        self.assertEqual(seen, {True, False}, "blinking: US-JIS off")
        r.tap((0, 1), hold=40, after=100)          # Fn + Tab: US-JIS on
        on = []
        for _ in range(5):
            r.ms(60)
            on.append(self.mid(r))
        self.assertEqual(on, [True] * 5, "on: US-JIS on")
        r.release(FN, ms=200)
        self.assertTrue(self.mid(r), "still shown just after the switch")
        r.ms(1500)
        self.assertFalse(self.mid(r))
        self.assertEqual(r.duty(4, 5)[0], PHASE[15], "the Caps LED stays dark")

    def test_effect_tables_are_the_stock_bytes(self):
        """The key positions and colour tables in the image are the stock
        AL71's (addresses in the stock image)."""
        stock = stock_image()
        for fw in (AL71_FW, AL71_ANSI_FW):
            need(fw)
            data = read_ihex(fw)
            rom = bytes(data.get(i, 0xFF) for i in range(max(data) + 1))
            for addr, n, what in ((0x3ECB, 117, "rings"), (0xA700, 96, "key positions"),
                                  (0x4363, 126, "position -> column"), (0x43E1, 126, "position -> row"),
                                  (0x3FA0, 576, "wheel"), (0xA680, 128, "breathing"), (0x41E3, 384, "palette"),
                                  (0xA800, 21, "colours"), (0x3EB3, 21, "side colours"), (0x3F40, 96, "scale")):
                with self.subTest(fw=Path(fw).name, table=what):
                    self.assertIn(stock[addr:addr + n], rom)


class TestStockKeymap(unittest.TestCase):
    """The port against the stock AL71 image (SMK_AL71_STOCK_IMAGE): keymap
    tables at 0xBC00 / 0xBE00 (base Win / Mac) and 0xC400 / 0xC600 (Fn), index
    slot * 6 + row bit, 4 bytes per key; the column table at 0x6B49."""

    KBDEF = REPO_ROOT / "src" / "keyboards" / "yunzii-al71" / "kbdef.h"
    PORT_NAMES = {"P0": 0x80, "P4": P4, "P5": P5, "P6": P6, "P7": P7}

    @classmethod
    def setUpClass(cls):
        cls.stock = stock_image()
        cls.kbdef = dict(re.findall(r"^#define\s+(\w+)\s+(\S+)", cls.KBDEF.read_text(), re.M))

    def _entry(self, base, slot, bit):
        a = base + (slot * 6 + bit) * 4
        return int.from_bytes(self.stock[a:a + 4], "big")

    def _pin(self, macro):
        m = re.fullmatch(r"(P\d)_(\d)", self.kbdef[macro])
        return (self.PORT_NAMES[m.group(1)], int(m.group(2)))

    @staticmethod
    def _expected(entry, fn_layer):
        if entry == 0:
            return 0
        if entry == 0x0D000000:
            return 0x5220 | fn_layer
        if entry & 0xFFFFFF00 == 0:
            return entry
        mods = (entry >> 16) & 0xFF
        if entry & 0xFF00FFFF == 0 and bin(mods).count("1") == 1:
            return 0xE0 + mods.bit_length() - 1
        return None

    def test_pins_in_kbdef(self):
        self.assertEqual(self._pin("CONN_SW_24G"), (0x80, 6))
        self.assertEqual(self._pin("CONN_SW_BT"), (0x80, 7))
        self.assertEqual(self._pin("OS_SWITCH_MAC"), (P7, 4))
        self.assertEqual(self._pin("SLEEP_PWR_PIN"), (0x80, 5))
        for row, pin in enumerate([(P7, 1), (P7, 2), (P7, 3), (P5, 3), (P5, 4)]):
            self.assertEqual(ROW_PIN[row], pin)
            self.assertEqual(self._pin("KB_R%d" % row), pin)
        for col in range(16):
            self.assertEqual(self._pin("KB_C%d" % col), COL_PIN[col])

    def test_ansi_base_layers_are_the_stock_tables(self):
        """Every stock key at its position; Mac: right of Space Command and the
        App key Right Option (the stock keeps Right Alt and App there)."""
        key = _keymaps(AL71_ANSI_FW)
        mac_changes = {(8, 5): 0xE7, (10, 5): 0xE6}
        for layer, base in [(0, 0xBC00), (1, 0xBE00)]:
            keys = 0
            for slot in range(16):
                for bit in range(1, 6):
                    e = self._entry(base, slot, bit)
                    with self.subTest(table=hex(base), slot=slot, bit=bit):
                        if (slot, bit) == (12, 3):
                            self.assertEqual(e, 0x31, "stock second backslash (no key on the board)")
                            self.assertEqual(key(layer, bit - 1, slot), 0)
                            continue
                        if (slot, bit) in ((11, 4), (12, 4), (3, 5), (4, 5), (6, 5), (7, 5)):
                            self.assertIn(e, (0x87, 0x64, 0x91, 0x8B, 0x8A, 0x90),
                                          "stock JIS / ISO keys (no key on the board)")
                            self.assertEqual(key(layer, bit - 1, slot), 0)
                            continue
                        if layer == 1 and (slot, bit) in mac_changes:
                            self.assertEqual(key(layer, bit - 1, slot), mac_changes[(slot, bit)])
                        else:
                            self.assertEqual(key(layer, bit - 1, slot), self._expected(e, layer + 2))
                        keys += e != 0
            self.assertEqual(keys, KEYS, f"{hex(base)}: {KEYS} keys")

    def test_fn_layers_keep_the_stock_plain_keys(self):
        """Where the stock Fn table has a plain key, the port has it too (the
        number row as FR_n: F-keys or media by OS mode)."""
        for fw in (AL71_ANSI_FW, AL71_FW):
            key = _keymaps(fw)
            for layer, base in [(2, 0xC400), (3, 0xC600)]:
                fr1 = key(layer, 0, 1)
                for slot in range(16):
                    for bit in range(1, 6):
                        e = self._entry(base, slot, bit)
                        with self.subTest(fw=Path(fw).name, table=hex(base), slot=slot, bit=bit):
                            if bit == 1 and 0x3A <= e <= 0x45:
                                self.assertEqual(key(layer, 0, slot), fr1 + (e - 0x3A))
                            elif e and e & 0xFFFFFF00 == 0:
                                self.assertEqual(key(layer, bit - 1, slot), e)

    def test_boot_escape_key_is_stock_esc(self):
        col, row = int(self.kbdef["BOOT_ESCAPE_KEY_COL"]), int(self.kbdef["BOOT_ESCAPE_KEY_ROW"])
        self.assertEqual(self._entry(0xBC00, col, row + 1), 0x29)


# ISP bootloader 2d169670 (YUNZII AL71)
BL_MD5 = "2d169670eae0d36eae8188562c1f66e8"
BL_MARKER_OK = 0xF053     # LJMP found at 0xEFFB: run the firmware
BL_NO_MARKER = 0xF029     # no LJMP at 0xEFFB: stay in ISP mode
BL_ISP_MODE = 0xFB06      # USB started in ISP mode (both the power-on and the 0xFF00 path call it)
ISP_KEYS_OK = 0xFF0A      # 0xFF00 entry: A / B keys matched
ISP_KEYS_BAD = 0xFF30     # 0xFF00 entry: keys wrong, back to the firmware


class TestStockBootloaderChain(unittest.TestCase):
    """The flash as it will look on the board: the firmware converted by
    sinowisp to the physical layout (reset vector -> 0xF000, the firmware's own
    vector at 0xEFFB) plus the ISP bootloader 2d169670 at 0xF000-0xFFFF."""

    @classmethod
    def setUpClass(cls):
        need(AL71_FW)
        stock = os.environ.get("SMK_AL71_STOCK_DUMP")
        if not stock or not Path(stock).exists():
            skip_or_fail("set SMK_AL71_STOCK_DUMP to a full readout with the bootloader 2d169670 "
                         "(meson: -Dal71_stock_dump=)")
        sinowisp = shutil.which("sinowisp")
        if not sinowisp:
            skip_or_fail("sinowisp not on PATH (its offline `convert` builds the flash image)")
        bootloader = Path(stock).read_bytes()[0xF000:0x10000]
        assert hashlib.md5(bootloader).hexdigest() == BL_MD5, "the addresses here are those of 2d169670"
        cls.tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls.tmp.name)
        fw_bin = tmp / "fw_jtag.bin"
        subprocess.run([sinowisp, "convert", "-d", "yunzii-al71", "--direction", "to_jtag",
                        "--output_format", "bin", AL71_FW, str(fw_bin)],
                       check=True, capture_output=True)
        image = bytearray(fw_bin.read_bytes().ljust(0xF000, b"\xff")) + bootloader
        assert len(image) == 0x10000
        cls.image = image
        cls.hex_path = tmp / "yunzii-al71_chain_smk.hex"
        shutil.copy(Path(AL71_FW).with_suffix(".map"), cls.hex_path.with_suffix(".map"))
        rst = Path(AL71_FW).with_suffix(".ihx.p")
        if rst.exists():
            shutil.copytree(rst, cls.hex_path.with_suffix(".ihx.p"))
        with open(cls.hex_path, "w") as f:
            for addr in range(0, 0x10000, 16):
                rec = bytes([16, addr >> 8, addr & 0xFF, 0]) + image[addr:addr + 16]
                f.write(":%s%02X\n" % (rec.hex().upper(), (-sum(rec)) & 0xFF))
            f.write(":00000001FF\n")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _kb(self):
        kb = Al71Sim(str(self.hex_path))
        self.addCleanup(kb.close)
        return kb

    def test_image_layout(self):
        self.assertEqual(self.image[0:3], bytes([0x02, 0xF0, 0x00]), "reset vector must enter the bootloader")
        self.assertEqual(self.image[0xEFFB], 0x02, "firmware-enabled marker (LJMP) at 0xEFFB")

    def test_power_on_runs_bootloader_then_firmware(self):
        kb = self._kb()
        kb.reset_fast()
        self.assertEqual(kb.run_until(BL_MARKER_OK, BL_NO_MARKER), BL_MARKER_OK)
        self.assertEqual(kb.run_until(ISP_ENTRY, kb._a("kb_update_switches")), kb._a("kb_update_switches"))

    def test_esc_held_is_accepted_by_the_bootloader(self):
        for mac in (False, True):
            with self.subTest(mac=mac):
                kb = self._kb()
                # R0 (P7.1) low: the static level while C0 is scanned; P7.4 is the Win / Mac switch
                kb.reset_fast(p7=0xFF & ~0x02 & ~(0x10 if mac else 0))
                stop = kb.run_until(ISP_KEYS_OK, ISP_KEYS_BAD, kb._a("kb_update_switches"))
                self.assertEqual(stop, ISP_KEYS_OK, "the bootloader must accept isp_jump() and start ISP mode")
                self.assertEqual(kb.run_until(BL_ISP_MODE, BL_MARKER_OK, kb._a("kb_update_switches")), BL_ISP_MODE)

    def test_isp_report_is_accepted_by_the_bootloader(self):
        sim = Sim(str(self.hex_path))
        main_loop = load_symbols(self.hex_path.with_suffix(".map"))["kb_update_switches"]
        out = sim.trigger_isp_jump(then=["echo ===KEYS===", "delete", f"break 0x{ISP_KEYS_OK:x}",
                                         f"break 0x{ISP_KEYS_BAD:x}", "run",
                                         "echo ===USB===", "delete", f"break 0x{BL_ISP_MODE:x}",
                                         f"break 0x{BL_MARKER_OK:x}", f"break 0x{main_loop:x}", "run"])
        entry, keys, usb = re.split(r"^===(?:KEYS|USB)===$", out, flags=re.M)
        self.assertEqual(sim.stopped_at(entry), ISP_ENTRY)
        self.assertEqual(sim.stopped_at(keys), ISP_KEYS_OK)
        self.assertEqual(sim.stopped_at(usb), BL_ISP_MODE)

    def test_missing_marker_stays_in_bootloader(self):
        kb = self._kb()
        kb.reset_fast()
        kb.cmd("set mem rom 0xeffb 0xff")
        stop = kb.run_until(BL_MARKER_OK, BL_NO_MARKER, kb._a("kb_update_switches"))
        self.assertEqual(stop, BL_NO_MARKER)


# ---------------------------------------------------------------- VIA
class ViaAl71(test_f65_via.ViaF65, OursAl71):
    """test_f65_via's VIA rig (raw HID on EP2, reports with ID 3) on the AL71 board."""


class Al71ViaRig:
    """The AL71's VIA images on the AL71 rig, for the tests taken from the
    F65's (the keys they use are at the F65's positions on the AL71 too; the
    Win / Mac switch is at Win)."""

    FW = AL71_VIA_FW

    def fn_key(self):
        return FN

    def kb(self, fw=None):
        fw = fw or self.FW
        need(fw)
        kb = ViaAl71(fw)
        self.addCleanup(kb.close)
        kb.start(SWITCH_USB)
        kb.ms(20)
        return kb


class ViaLightRig(test_f65_via.ViaF65, LightRig):
    """The VIA rig with LightRig's LED readers."""


class TestViaMiddleLed(Al71ViaRig, unittest.TestCase):
    """LT(3, KC_SPC) on Space from VIA: while Space holds layer 3 the middle
    LED (the Caps cell's second channel) is on, over the US-JIS display."""

    SPACE = (5, 4)

    def kb(self, fw=None):
        fw = fw or self.FW
        need(fw)
        kb = ViaLightRig(fw)
        self.addCleanup(kb.close)
        kb.start(SWITCH_USB)
        kb.ms(20)
        return kb

    def test_on_while_the_layer_tap_layer_is_in_force(self):
        kb = self.kb()
        kb.set_keycode(0, self.SPACE[1], self.SPACE[0], 0x4000 | 3 << 8 | 0x2C)
        kb.ms(50)
        self.assertNotEqual(kb.duty(4, 5)[1], 0x0400, "dark")
        kb.press(self.SPACE, ms=2000)                # past the tapping term: layer 3
        on = []
        for _ in range(6):
            kb.ms(60)
            on.append(kb.duty(4, 5)[1] == 0x0400)
        self.assertEqual(on, [True] * 6, "on, not blinking")
        kb.release(self.SPACE, ms=60)
        self.assertNotEqual(kb.duty(4, 5)[1], 0x0400, "dark again")
        kb.tap(self.SPACE, hold=40, after=60)        # a tap: Space, the LED stays dark
        self.assertNotEqual(kb.duty(4, 5)[1], 0x0400)


class TestViaIsp(unittest.TestCase):
    """sinowisp's report 5 on interface 1 of the VIA images (the keyboard and
    the other reports share it with report IDs) reaches the ISP entry."""

    def test_isp_report_on_interface_1_jumps_to_bootloader(self):
        for fw in (AL71_VIA_FW, AL71_ANSI_VIA_FW):
            need(fw)
            with self.subTest(fw=Path(fw).name):
                sim = Sim(fw)
                setup = [0x21, 0x09, 0x05, 0x03, 0x01, 0x00, 0x06, 0x00]
                sled = 0x900E
                cmds = sim._boot_to_post_init() + [
                    sim._set_xram(sim.EP0_OUT_BUF, setup), "set mem sfr 0x92 0x10",
                    "break 0x%x" % sled, "run",
                    sim._set_xram(sim.EP0_OUT_BUF, [0x05, 0x75, 0, 0, 0, 0, 0, 0]), "set mem sfr 0x93 0x10",
                    "pc 0x9000", "break 0x%x" % sled, "run",
                    "pc 0x%x" % sim.USB_TASK, "break 0x%x" % ISP_ENTRY, "run", "info registers",
                ]
                out = sim.run(cmds)
                self.assertEqual(sim.stopped_at(out), ISP_ENTRY)
                self.assertEqual((sim.acc(out), sim.reg_b(out)), (0x5A, 0xA5))


class TestViaLayerTap(Al71ViaRig, test_f65_via.TestViaLayerTap):
    """test_f65_via's layer-tap tests on the AL71."""


class TestViaLayerTapAnsi(Al71ViaRig, test_f65_via.TestViaLayerTap):
    FW = AL71_ANSI_VIA_FW


class TestMouseUsb(Al71ViaRig, test_f65_mouse.TestMouseUsb):
    """test_f65_mouse's USB tests on the AL71 (A and S at the F65's positions)."""


class TestMouseUsbAnsi(Al71ViaRig, test_f65_mouse.TestMouseUsb):
    FW = AL71_ANSI_VIA_FW


class TestMouseRadio(Al71ViaRig, test_f65_mouse.TestMouseRadio):
    """The short frame in the AL71's 2.4 GHz position (P0.6 low)."""


if __name__ == "__main__":
    unittest.main()
