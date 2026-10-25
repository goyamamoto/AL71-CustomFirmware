# YUNZII AL71 custom firmware

[日本語](README.ja.md)

Open-source firmware for the YUNZII AL71 keyboard, written over USB without opening the case.

> [!WARNING]
> This replaces the vendor's firmware. Going back to it needs a backup of your own board (step 3); the vendor's firmware is not distributed here. With this firmware, holding Esc while plugging the cable in starts the bootloader before any of its USB code runs, so the bootloader stays reachable even if the firmware's USB does not work. Use at your own risk.

> [!CAUTION]
> This firmware is made for and checked on an AL71 whose USB version is 20.02 (step 1 shows it). A board with another version may be wired differently; check it the same way before writing.

## What it does

- All 71 keys; the Windows or Mac layer from the Win / Mac switch; settings kept across power cycles
- USB, Bluetooth (three slots, named "AL71-1", "AL71-2" and "AL71-3", so a host shows which slot it is) and the 2.4 GHz dongle, through the keyboard's radio module
- The backlight effects (14 of them), colours, brightness, speed and the side lights; the status indicators (Caps Lock, the link keys while Fn is held, pairing, battery level on Fn+B, low battery, charging) shown over the backlight and on the three LEDs on the case
- Sleep on battery after about a minute idle (a key wakes it), the backlight off after 30 s idle on battery, and a low-battery cutoff
- US-JIS (Fn+Tab, `usjis` layouts): type what the US keycaps show on a host set to the Japanese keyboard layout (Windows layer)
- IME keys on both sides of Space (`usjis` layouts): tap for Muhenkan/Henkan (Windows) or Eisu/Kana (Mac), hold for Alt and Right Ctrl (Windows) or Command and Right Command (Mac)
- VIA (`-via` layouts): the keymap can be changed from [VIA](https://usevia.app) over USB and is kept in flash, with layer-tap keys and mouse keys
- Boot escape: hold Esc while the keyboard powers up and it starts the bootloader instead, before any of this firmware's own USB code runs
- Wired, the keyboard keeps its original USB ID, so `sinowisp` finds it as `yunzii-al71`

## Pick a layout

Every image has the same hardware support, the boot escape, the Bluetooth names and sleep.

| Layout | Adds | Image |
| --- | --- | --- |
| `ansi` | nothing: US ANSI as printed | `yunzii-al71_ansi_smk.hex` in `firmware/` |
| `usjis` | US-JIS (Fn+Tab), the IME keys on both sides of Space, Caps Lock and Left Ctrl swapped | `yunzii-al71_usjis_smk.hex` in `firmware/` |
| `usjis-via` | `usjis` with the keymap editable from VIA | `yunzii-al71_usjis-via_smk.hex` in `firmware/` |
| `ansi-via` | `ansi` with the keymap editable from VIA | `yunzii-al71_ansi-via_smk.hex` in `firmware/` |

The VIA layouts start with the same keymap as `ansi` / `usjis`. See [Using VIA](#using-via). The `usjis-via` image is the one checked on the board; `ansi` was checked on the board in an earlier build (the same keys, before the middle LED on the case, the Bluetooth names per slot and the later changes to the layer-tap keys, the mouse keys and the names); `usjis` and `ansi-via` are checked in the simulator.

## Supported keyboards

| Keyboard | USB ID | Status |
| --- | --- | --- |
| YUNZII AL71, USB version 20.02 | 258a:010c, manufacturer "BY Tech", product "Gaming Keyboard" | Works; checked on the board with macOS hosts over USB, Bluetooth and the 2.4 GHz dongle |

## Steps

The switch on the back chooses the connection; seen from the back, left to right: Bluetooth, Line (USB), 2.4 GHz. Every step below is done in the Line position, with the cable plugged in. After a sinowisp command that started from the original firmware, the keyboard stays off USB (the backlight off) until you unplug the cable and plug it in again; do that before the next command. With this firmware running, it comes back by itself within a few seconds.

1. Check the keyboard. It shows up as USB ID `258a:010c`, manufacturer "BY Tech", product "Gaming Keyboard", version 20.02 (macOS: System Information > USB).
2. Install the tools. Install [sinowisp](https://github.com/carlossless/sinowisp) with `cargo install sinowisp` (this needs [Rust](https://rustup.rs/); sinowisp reads and writes the flash through the keyboard's bootloader over USB). On macOS, run it from a terminal app that has Input Monitoring permission (System Settings > Privacy & Security > Input Monitoring); without it the keyboard cannot be opened. Unplug any other keyboard with USB ID 258a:010c (many keyboards share it and sinowisp takes the last match).
3. Back up the original firmware. The first file is the way back to it. Plug the cable in again after each command.
   ```sh
   sinowisp read -d yunzii-al71 al71-stock.hex                        # the firmware, for restoring (step 8)
   sinowisp read -d yunzii-al71 -s full --format bin al71-full.bin    # firmware and bootloader, for the check below
   tail -c 4096 al71-full.bin | md5                                   # Linux: md5sum
   ```
   The last line must print `2d169670eae0d36eae8188562c1f66e8`, the AL71's bootloader as sinowisp lists it. Reading the firmware twice and comparing the files shows that the read is stable.
4. Get the firmware. Pick a layout (above) and either use its image in [firmware/yunzii-al71](firmware/yunzii-al71) (check it with `shasum -a 256 -c SHA256SUMS`), or build it (see [Building](#building)).
5. Write it, then plug the cable in again.
   ```sh
   sinowisp write -d yunzii-al71 --force yunzii-al71_usjis-via_smk.hex    # or another image
   ```
   `--force` is needed because the image is smaller than the flash; sinowisp fills the rest with zeros, which also resets the settings and a keymap changed in VIA (after every write: Fn+Tab for US-JIS, if you use it; save a VIA keymap first with VIA's Save + Load).
6. Check the ways back.
   - With the new firmware running, `sinowisp read -d yunzii-al71 check.hex` works, and the keyboard comes back by itself.
   - Unplug the cable (in the Line position that cuts the power), wait a few seconds, hold Esc, plug in, and let go of Esc after two seconds: the keyboard shows up as `0603:1020`, the bootloader (no strings). Unplug and plug in again without Esc to go back to the firmware.

   The second way does not depend on this firmware's USB code. From a wireless position, move the switch to Line first (the battery keeps the board running otherwise).
7. Use it. See [Key map](#key-map). Pair the dongle with Fn+R held 3 s in the 2.4 GHz position, a Bluetooth slot with Fn+Q / W / E held 3 s in the Bluetooth position.
8. Back to the original firmware at any time (Line position):
   ```sh
   sinowisp write -d yunzii-al71 al71-stock.hex
   ```

## Key map

| Where | What |
| --- | --- |
| Base layer | US ANSI 65 % with Ins / Home, End / PgUp and Del / PgDn on the right, as printed. The Win / Mac switch chooses the layer (read at power-up and whenever it moves; held keys are released first) |
| Bottom row | Windows: Ctrl, Win, Alt, Space, Alt, Fn, App, Ctrl as printed. Mac: Ctrl, Option, Command, Space, Command, Fn, Option, Ctrl |
| Keys beside Space | `usjis`: tap and hold keys. Windows: left = tap Muhenkan, hold Alt; right (the printed Right Alt) = tap Henkan, hold Right Ctrl. Mac: left = tap Eisu, hold Command; right = tap Kana, hold Right Command. They become the modifier when held for about 0.4 s or as soon as another key is pressed. Fn stays where it is printed; Caps Lock and Left Ctrl swap places |
| Fn + 1 … = | Windows: F1-F12. Mac: brightness, Mission Control, Launchpad, previous / play / next, mute, volume (Apple's order) |
| Fn + Right Shift + 1 … = | The other set: media keys on Windows, F1-F12 on Mac |
| Fn + Esc | `` ` `` (with Shift: `~`) |
| Fn + Tab | `usjis`: US-JIS on / off (saved; Windows layer only). `ansi`: Tab |
| Fn + Q / W / E | Bluetooth slot 1 / 2 / 3 (Bluetooth position): a short press selects it, a 3 s hold pairs it (the key blinks blue) |
| Fn + R | 2.4 GHz: a 3 s hold pairs the dongle (the key blinks) |
| Fn (held) | The active link's key lights: Y white (USB), R green (2.4 GHz), the slot's key blue (Bluetooth) |
| Fn + B (held) | Battery level on the number row, in a wireless position on battery |
| Fn + \\ , ] , [ | Next effect (through off), next colour (7 colours and rainbow), all lighting off / on |
| Fn + ↑ ↓ ← → | Brightness (5 levels) and speed (5 levels; the side lights follow) |
| Fn + / . , | Side lights: next effect, colour, brightness |
| Fn + U / I / O | PrtSc / ScrLk / Pause |
| Fn + Backspace (held), then Fn + V | Reset of the settings (US-JIS off, lighting defaults; on the VIA layouts also the built-in keymap) |

The three LEDs on the case: the top one is Caps Lock. The bottom one (RGB) is red while charging, blinks red on low battery, blinks while pairing or reconnecting (2.4 GHz cyan, Bluetooth blue) and stays on for 3 s once connected. The middle one is on while a layer-tap key (VIA) holds its layer; on the `usjis` layouts, while Fn is held (and for about a second after Fn+Tab), it shows US-JIS as the Tab key does: on for on, blinking for off.

Everything works the same over USB and over the radio. Lighting changes are saved about 3 s after the last change; the whole backlight blinks once at that moment (the flash write).

## Using VIA

With a `-via` image written and the switch in the Line position (USB):

1. Open [usevia.app](https://usevia.app) in a browser with WebHID (Chrome, Edge).
2. In Settings, turn on "Show Design tab". In Design, load [via.json](src/keyboards/yunzii-al71/via.json) from this repository.
3. In Configure, click "Authorize device" and pick "YUNZII AL71 (SMK)".

The four layers are Windows base, Mac base, Windows Fn and Mac Fn. Changes are saved to flash about 0.5 s after the last one and are used over Bluetooth and 2.4 GHz too. VIA can set basic keys, modified keys (such as Ctrl+C), mod-taps, `MO`, layer-taps (`LT`, for example Space held for a layer of mouse keys), mouse keys, media keys and this keyboard's own keys (US-JIS, the link, battery, Fn-row and lighting keys); toggles, one-shot keys and macros are not supported, and the lighting stays on its Fn keys. Layers 2 and 3 can hold any keys; the board treats both as Fn layers (the Fn indicators, the settings-reset chord on Backspace and V). VIA keeps one definition per USB ID, and other keyboards (the F65 among them) share 258a:010c: load this file again after using VIA with one of them. Details: [docs/keyboards/yunzii-al71.md](docs/keyboards/yunzii-al71.md) and [docs/keyboards/aula-f65-v1.md](docs/keyboards/aula-f65-v1.md#via).

## Building

The images in `firmware/` are release builds made with the steps below on macOS. The same commit built the same way gives the same bytes, so you can check a download against your own build (a build on another platform can differ by a few bytes).

### Release build, step by step

1. Get the source.
   ```sh
   git clone https://github.com/goyamamoto/AL71-CustomFirmware.git
   cd AL71-CustomFirmware
   ```
2. Install the toolchain. You need SDCC 4.5.0 exactly (other versions stop at smk's `--Werror` or give a different image), meson, ninja and Python 3.
   - With [Nix](https://nixos.org/) (Linux or macOS): run `nix develop` in the repository. It provides everything, including sinowisp and the simulator.
   - On macOS without Nix: with [Homebrew](https://brew.sh/) installed, run [tools/macos/setup-toolchain.sh](tools/macos/setup-toolchain.sh) once. It installs meson and ninja with Homebrew and builds SDCC 4.5.0 and the simulator into `~/.local/smk`, which takes a while. Then, in every new terminal:
     ```sh
     . ~/.local/smk/env.sh
     sdcc --version    # must show 4.5.0
     ```
   - Elsewhere: install meson, ninja, Python 3 and SDCC 4.5.0 (from source if your package manager has another version).
3. Set up a release build, once. `build-release` is the output folder; `--buildtype=release` is what leaves out the debug console and logging.
   ```sh
   meson setup build-release --buildtype=release
   ```
4. Build the layouts you want:
   ```sh
   meson compile -C build-release yunzii-al71_usjis_smk.hex yunzii-al71_ansi_smk.hex yunzii-al71_usjis-via_smk.hex yunzii-al71_ansi-via_smk.hex
   ```
   The images are written to `build-release/`. After changing the source, run this step again; step 3 is not needed again.
5. Check it (optional, macOS). Unchanged source gives the same files as `firmware/`; each image you built must say `OK`:
   ```sh
   (cd build-release && shasum -a 256 --ignore-missing -c ../firmware/yunzii-al71/SHA256SUMS)
   ```
6. Write it as in [Steps](#steps) 5 and 6, with the path to your image, for example `sinowisp write -d yunzii-al71 --force build-release/yunzii-al71_usjis_smk.hex`.

### Release and debug builds

| | Release | Debug |
| --- | --- | --- |
| Set up with | `meson setup build-release --buildtype=release` | `meson setup build` (meson's default) |
| Meant for | Daily use; the images in `firmware/` | Development |
| HID debug console (`tools/smk-console`) | No | Yes: reports chip IDs, mode changes and settings to the host |
| Logging | No | Yes |
| Source-level simulator tests | Skipped (no `.cdb`) | Yes |

A keyboard sees everything typed on it; the debug build reports to the host over its console, the release build has no console.

### Technical notes and tests

The pins, the LEDs, the radio link, VIA, sleep and recovery, and how to run the simulator tests, are in [docs/keyboards/yunzii-al71.md](docs/keyboards/yunzii-al71.md) and [docs/keyboards/aula-f65-v1.md](docs/keyboards/aula-f65-v1.md).

## Known limitations

- Writing any image resets the settings (sinowisp erases the flash and writes the image padded with zeros): US-JIS off, lighting defaults, and the keymap VIA changed.
- Not included: the vendor driver's protocol (no per-key custom lighting, no configuration from the vendor's software).
- The backlight is dimmer than the original firmware's: the default brightness is 2 of 4 (the original starts at 4), and at the same level the LEDs are lit for a smaller share of the time (roughly half as bright, estimated).
- US-JIS works only in the Windows layer: macOS drops the JIS-only keys some of the substitutions need.
- VIA: no macros and no lighting menu; the keymap is changed over USB only (Line position). Two keys that send the same key (for example C and Ctrl+C) share it: releasing one releases it for both.
- Not yet checked on a board: the sleep with USB power but no host, and the typing under US-JIS (its switching on and off is). The firmware's other functions are checked on the board or in the simulator, as the docs say.
- Only the ANSI AL71 is known.

## Source

This is [smk](https://github.com/carlossless/smk), the open firmware for SinoWealth keyboards, at [69373bb](https://github.com/carlossless/smk/commit/69373bbb633bd1159f4541f486ff7506563a38ec) (2026-09-16), with changes made from 2026-09 to 2026-10. The AL71 is in `src/keyboards/yunzii-al71/`; it shares its board code with the EPOMAKER x AULA F65 V1 (`src/keyboards/aula-f65-v1/`, [goyamamoto/F65-CustomFirmware](https://github.com/goyamamoto/F65-CustomFirmware)). The other keyboards smk supports still build from this tree; the upstream README is in [docs/README-smk.md](docs/README-smk.md).

## Credits and license

- [smk](https://github.com/carlossless/smk), [sinowisp](https://github.com/carlossless/sinowisp) and [sinodude](https://github.com/carlossless/sinodude) by Karolis Stasaitis, whose work on SinoWealth keyboards made this possible.
- [Thaolia/smk_aulaF75](https://github.com/Thaolia/smk_aulaF75), the smk port for the AULA F75, showed that this family's radio module speaks over EUART0 the way it does.
- VIA's command handling and the keymap interface follow QMK's `quantum/via.c` and `quantum/dynamic_keymap.c`, and the mouse keys QMK's accelerated mouse keys ([QMK](https://github.com/qmk/qmk_firmware), GPL-2.0-or-later); [VIA](https://github.com/the-via/app) is the configurator.
- The US-JIS rules follow [goyamamoto/zmk-kb1-usjis](https://github.com/goyamamoto/zmk-kb1-usjis).
- License: GPL-2.0, as smk ([LICENSE](LICENSE)).

YUNZII, EPOMAKER and AULA are trademarks of their owners. This project is not affiliated with or endorsed by them.
