# YUNZII AL71

## Specs

- MCU: SinoWealth SH68F90 family ([SH68F90](../platforms/sh68f90.md)). Original USB ID 258a:010c, manufacturer "BY Tech", product "Gaming Keyboard"
- The board is wired like the [AULA F65 V1](aula-f65-v1.md) and runs the same board code (`src/keyboards/aula-f65-v1`, on the include path of `src/keyboards/yunzii-al71`); what differs is set in `src/keyboards/yunzii-al71/kbdef.h`
- Matrix: 5 rows × 16 columns, 71 keys: a 65% block, two columns Ins / Home, End / PgUp, Del / PgDn on the right, the arrows below them. Rows and columns are the F65's pins; P4.6 is an LED-only column
- Connection switch (3 positions; seen from the back, left to right): Bluetooth (P0.7 low), USB (both high; printed Line), 2.4 GHz (P0.6 low)
- Win / Mac switch: P7.4 (pulled up), high = Win, low = Mac
- Power: P4.4 reads high with USB power, P7.6 is driven to its inverse, P7.7 reads low while charging (as on the F65). P0.5 is held low while running and goes high before a sleep. P4.1 and P7.5 are inputs and never driven
- Backlight: the F65's LED matrix and timing. Side lights on four pairs of cells, (0-3, 0) and (12-15, 0), slot order G, R, B. The three LEDs on the case sit on two cells off the keys in the bottom LED row: column 4 (two white LEDs, on its first and second channels) and column 6 (an RGB LED)
- Radio: the F65's module link (EUART0, P0.2, P4.7, the same frames). Bluetooth names, one pair per slot: "AL71-1" (BT5.0, profile 0) and "AL71-1 3.0" (BT3.0, profile 1) for slot 1, and so on. The saved slot's names go out at boot, a slot's again on the press of its key (Fn + Q / W / E) when the module has another slot's, so a hold that pairs follows them by 3 s and a select by at least 32 ms (`rf_name_slot`). A Mac paired under an earlier name showed the new one after a boot, without pairing again

## Status

Checked on an AL71 (`ansi` and `usjis-via`): writing with sinowisp and the read-back, sinowisp's report 5 and Esc held while plugging the cable in (both reach the bootloader), the keys, the Win / Mac switch, the IME keys (Mac layer), US-JIS switched on and off (Fn + Tab; the typing under US-JIS, Windows layer only, in the simulator), Bluetooth on a Mac with the names per slot ("AL71-1" from the boot; "AL71-2" sent on the press of Fn + W, then paired with a hold and typing; back to "AL71-1" with Fn + Q), VIA with a layer-tap key on Space and mouse keys on its layer (over USB, Bluetooth and 2.4 GHz), 2.4 GHz, the backlight and the status LEDs (all three LEDs on the case, the middle one with a layer-tap key held and with Fn held), the wireless sleep and the wake by a key. Not yet on the board: the wired sleep (USB power without a host). The rest is checked in the simulator (`tests/test_al71.py` and the shared F65 code's tests).

## Layouts

| Layout | What it is |
| --- | --- |
| `ansi` | US ANSI as printed |
| `usjis` | `ansi` plus US-JIS (`USJIS`), the IME mod-taps on both sides of Space (`TAP_HOLD`), Caps Lock and Left Ctrl swapped |
| `ansi-via` | `ansi` with the keymap editable from VIA (`src/keyboards/yunzii-al71/via.json`) |
| `usjis-via` | `usjis` with the keymap editable from VIA |
| `leddiag` | `ansi` with the LED diagnostic of the F65 (`LED_DIAG`): the cells include the side-light pairs and columns 3, 4, 6 and 7 of the bottom LED row (the three LEDs on the case and the two cells beside them) |

## Keys

The keys work as on the [F65](aula-f65-v1.md#keys), with these differences:

- Win layer as printed: `Ctrl Win Alt Space Alt Fn App Ctrl ← ↓ →`. Mac layer: `Ctrl Option Command Space Command Fn Option Ctrl`
- The Win / Mac switch chooses the layer: read at power-up and every 10 ms, a change counts after 10 samples in a row (~100 ms), every held key is released first. The switch is not saved; there are no Fn + A / Fn + S keys (they are A and S under Fn)
- `usjis`: Win: left of Space = Alt held / Muhenkan (INT5) tapped, right of Space (the printed Right Alt) = Right Ctrl held / Henkan (INT4) tapped. Mac: Command / Eisu (LANG2) and Right Command / Kana (LANG1). Fn stays where it is printed
- The Fn layer is the F65's: Esc = `` ` ``, the number row (F-keys / media, Right Shift as a second Fn), Q / W / E / R link keys, U / I / O = PrtSc / ScrLk / Pause, Tab = US-JIS (`usjis`), B = battery display, the lighting keys, Fn + Backspace held then Fn + V = settings reset. Ins, Home, End, PgUp, Del and PgDn are the same keys under Fn
- VIA (`ansi-via`, `usjis-via`) as on the [F65](aula-f65-v1.md#via), with the definition `src/keyboards/yunzii-al71/via.json`. The layers are 0 Win base, 1 Mac base, 2 Win Fn, 3 Mac Fn; the Win / Mac switch chooses the base layer, and Fn (or a layer-tap key held) the layer given. Layer-tap keys and mouse keys work as on the F65
- USB: 258a:010c, manufacturer "SMK", product "YUNZII AL71 (SMK)"; `sinowisp -d yunzii-al71` finds the running board

## Indicators

The F65's key indicators (Caps Lock key, Fn for charging and low battery, the link keys, Tab, A / S for the layer in force, 1 … 0 for the battery) and the three LEDs on the case, which the backlight effects never paint:

| Status LED | Colour | When |
| --- | --- | --- |
| column 4 (the top of the three LEDs on the case, a white LED on the red channel) | red channel: white | the host's Caps Lock LED |
| column 6 (the bottom LED, RGB) | red | charging |
| column 6 | red, blinking | low battery |
| column 6 | the link key's colour, blinking / solid 3 s | pairing, reconnecting, just connected (2.4 GHz cyan, Bluetooth blue) |
| column 4's green channel (the middle LED) | on | while a layer-tap key (VIA) holds its layer |
| column 4's green channel | on / blinking | otherwise while the Tab key shows US-JIS (Fn held, or about a second after Fn + Tab): on for US-JIS on, blinking for off (`usjis`) |

Otherwise they are dark. Columns 3 and 7 of the same row have no key either and stay dark.

## Backlight

The F65's effects and keys ([Backlight](aula-f65-v1.md#backlight)), with the key positions of the AL71's own firmware (`src/keyboards/yunzii-al71/backlight_tables.h`): the rings, the ripple and wave positions follow the AL71's keys. The side-light effects are the F65's on the AL71's four pairs.

The backlight is dimmer than with the AL71's own firmware. The defaults are the F65's (brightness 2 of 0-4, side lights 2; the AL71's own firmware starts at 4 for both). At the same level the LED engine drives less: a pulse ends at DUTY2 0x0400 at most, and every LED is off during the matrix scans and for part of each subframe ([LEDs](aula-f65-v1.md#leds)). Level 4 here is roughly half as bright as level 4 there (estimated, not measured).

## Sleep

As on the F65. The pins parked for the power-down: the key columns, P4.6, P7.4 and P0.5-P0.7 driven low; in the wireless sleep also P0.0 / P0.1, P0.5-P0.7, P7.4 and P7.7 low without pull-up; then P0.5 high. After the wake the switch pins are pulled-up inputs again and the Win / Mac switch is read again.

## Recovery

- Esc held at power-up jumps to the ISP bootloader, as on the F65 (a watchdog reset passes through the same check)
- sinowisp's report 5 from the running firmware, in the USB position (both switch pins open)
- The AL71's bootloader is not the F65's: sinowisp lists it for `yunzii-al71` with the MD5 2d169670eae0d36eae8188562c1f66e8 (the last 4 KB of a full readout). It starts the firmware at power-up without a key or pin check. In ISP mode it enumerates as 0603:1020 without strings
- After the reboot at the end of a sinowisp read or write that entered the bootloader from the original firmware, the board stays off USB (no 258a:010c, no 0603:1020, the backlight off) until the cable is plugged in again. Entered from this firmware, the board comes back by itself within a few seconds
- The USB position is the centre one (printed Line). Unplugging the cable there stops the MCU: a board left off USB by the bootloader's reboot starts again from power-on when the cable is plugged in, so Esc held while plugging the cable in is a power-on
- The ICP pads are not known

## Building and testing

```sh
meson setup build-release --buildtype=release --werror
meson compile -C build-release yunzii-al71_usjis_smk.hex yunzii-al71_ansi_smk.hex yunzii-al71_usjis-via_smk.hex yunzii-al71_ansi-via_smk.hex
python3 -m unittest discover -s tests -p test_al71.py         # the AL71: pins, switches, keys, LEDs, sleep, VIA, layer-taps, mouse keys, recovery
python3 -m unittest discover -s tests -p 'test_f65*.py'       # the shared board code, on the F65 images
```

The tests run the images in a patched uCsim (from `nix develop` or `tools/macos/setup-toolchain.sh`) and use `build/` by default. `meson test -C <builddir>` runs every test file against that build directory's images and is strict: it fails, rather than skips, when an image or one of the original firmware's files below is missing; give those with `meson configure <builddir> -Dal71_stock_image=<bin> -Dal71_stock_dump=<bin>` (the F65 tests take `-Df65_stock_image=` and `-Df65_stock_dump=`).

`test_al71.py` takes `SMK_AL71_FIRMWARE`, `SMK_AL71_ANSI_FIRMWARE`, `SMK_AL71_VIA_FIRMWARE`, `SMK_AL71_ANSI_VIA_FIRMWARE` and `SMK_AL71_LEDDIAG_FIRMWARE`; the checks against the original firmware need its image (`SMK_AL71_STOCK_IMAGE`, the 61440-byte image from the vendor's updater, meson `-Dal71_stock_image=`), the chain through the bootloader a full readout of an AL71 (`SMK_AL71_STOCK_DUMP`, meson `-Dal71_stock_dump=`) and sinowisp on PATH; they are skipped without them. They need the simulator built from this tree's `tools/ucsim` (model version 11 or later).

## Flashing

The F65 and the AL71 (and many other boards) share 258a:010c; sinowisp, VIA and the `*_flash` targets cannot tell them apart. Unplug every other 258a:010c device first and set the connection switch to the USB position (Line). If the board does not come back after a sinowisp read or write, plug the cable in again (see [Recovery](#recovery)).

The way back is the board's own firmware readout taken before the first write (`sinowisp read -d yunzii-al71 al71-stock.hex`), which keeps its settings. This port was made for and checked on an AL71 with the USB version 20.02 (bcdDevice 0x2002) and the bootloader sinowisp lists for `yunzii-al71` (the MD5 of the last 4 KB of `sinowisp read -d yunzii-al71 -s full --format bin`); another revision may be wired differently. After writing, a readout compared with the image differs only in the settings sector (0xEC00-0xEDFF) and, on the VIA layouts, the keymap sectors (0xE800-0xEBFF) once the firmware has saved something. Writing an image erases the keymap VIA changed; VIA's Save + Load menu keeps a copy. The README gives the step-by-step procedure.
