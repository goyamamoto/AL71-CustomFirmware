# Prebuilt images for the YUNZII AL71

| Image | Layout |
| --- | --- |
| `yunzii-al71_ansi_smk.hex` | `ansi`: US ANSI as printed |
| `yunzii-al71_usjis_smk.hex` | `usjis`: adds US-JIS (Fn+Tab), the IME keys on both sides of Space, and Caps Lock and Left Ctrl swapped |
| `yunzii-al71_usjis-via_smk.hex` | `usjis-via`: `usjis` with the keymap editable from VIA (load `src/keyboards/yunzii-al71/via.json` into VIA) |
| `yunzii-al71_ansi-via_smk.hex` | `ansi-via`: `ansi` with the keymap editable from VIA (the same `via.json`) |

All four are release builds of this repository's source: no debug console and no logging. They are built on macOS with SDCC 4.5.0 as below (a build on another platform can differ by a few bytes, see the top-level README); the top-level README's [Building](../../README.md#building) section has the full steps, including the toolchain and how to check your build against `SHA256SUMS`:

```sh
meson setup build-release --buildtype=release
meson compile -C build-release yunzii-al71_ansi_smk.hex yunzii-al71_usjis_smk.hex yunzii-al71_usjis-via_smk.hex yunzii-al71_ansi-via_smk.hex
```

Check a download with `shasum -a 256 -c SHA256SUMS`, back up the original firmware, and write one image as the top-level README describes (`sinowisp write -d yunzii-al71 --force <image>`). `usjis-via` is checked on the board as it is here; `ansi` is checked on the board in an earlier build (the same keys, before the middle status LED, the Bluetooth names per slot and the later changes to the layer-tap keys, the mouse keys and the names) and in the simulator for this one; `usjis` is `usjis-via` without VIA, checked in the simulator; `ansi-via` is `usjis-via`'s VIA support with the `ansi` keymap, checked in the simulator.
