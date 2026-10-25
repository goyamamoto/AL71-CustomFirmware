#pragma once

#include "sh68f90.h"
#include "keycodes.h"
#include <stdint.h>
#include <stdbool.h>

// YUNZII AL71 (USB 258A:010C, product "Gaming Keyboard"; 71 keys). The same
// MCU, key rows and columns, LED drive and radio module link as the AULA F65
// V1; the board-wide code is shared with aula-f65-v1 (its directory is on the
// include path). It differs in the switch pins (connection P0.6 / P0.7, Win /
// Mac P7.4), the sleep power pin (P0.5) and the LED-only columns (P4.6 only).

// Six row lines; P7.0 has no key on it, so the 5 key rows are scanned only.
#define MATRIX_ROWS 5
#define MATRIX_COLS 16

// Row Pin Bits (inputs, pulled up, low when a key on the driven column is down)
#define KB_R0_P7_1 _P7_1
#define KB_R1_P7_2 _P7_2
#define KB_R2_P7_3 _P7_3
#define KB_R3_P5_3 _P5_3
#define KB_R4_P5_4 _P5_4

// Row Pins
#define KB_R0 P7_1
#define KB_R1 P7_2
#define KB_R2 P7_3
#define KB_R3 P5_3
#define KB_R4 P5_4

// Column Pin Bits (active low). P4.6 is an LED-only column with no key on it;
// the key scan leaves it idle high.
#define KB_C0_P6_0  _P6_0
#define KB_C1_P6_1  _P6_1
#define KB_C2_P6_2  _P6_2
#define KB_C3_P6_3  _P6_3
#define KB_C4_P6_4  _P6_4
#define KB_C5_P6_5  _P6_5
#define KB_C6_P6_6  _P6_6
#define KB_C7_P6_7  _P6_7
#define KB_C8_P5_0  _P5_0
#define KB_C9_P5_1  _P5_1
#define KB_C10_P5_2 _P5_2
#define KB_C11_P5_7 _P5_7
#define KB_C12_P4_0 _P4_0
#define KB_C13_P4_2 _P4_2
#define KB_C14_P4_3 _P4_3
#define KB_C15_P4_5 _P4_5

// Column Pins
#define KB_C0  P6_0
#define KB_C1  P6_1
#define KB_C2  P6_2
#define KB_C3  P6_3
#define KB_C4  P6_4
#define KB_C5  P6_5
#define KB_C6  P6_6
#define KB_C7  P6_7
#define KB_C8  P5_0
#define KB_C9  P5_1
#define KB_C10 P5_2
#define KB_C11 P5_7
#define KB_C12 P4_0
#define KB_C13 P4_2
#define KB_C14 P4_3
#define KB_C15 P4_5

#define KB_C_P4_MASK (uint8_t)(KB_C12_P4_0 | KB_C13_P4_2 | KB_C14_P4_3 | KB_C15_P4_5)
#define KB_C_P5_MASK (uint8_t)(KB_C8_P5_0 | KB_C9_P5_1 | KB_C10_P5_2 | KB_C11_P5_7)
#define KB_C_P6_MASK (uint8_t)0xFF

// LED-only column slot (idle high = LEDs off). P7.4 is the OS switch here.
#define LED_COL16_P4_6 _P4_6

// Backlight anodes: P1.0-P1.5, P2.0-P2.5, P3.0-P3.5, the 18 PWM outputs
// (PWM20-25, PWM10-15, PWM00-05). Only a PWM pulse on one of them, with a
// column low, lights an LED. The latches stay 0 (dark whenever the PWM is off); led.c drives the PWM.
#define LED_P1_MASK (uint8_t)0x3F
#define LED_P2_MASK (uint8_t)0x3F
#define LED_P3_MASK (uint8_t)0x3F

// Connection switch, 3 positions (pulled-up inputs):
// P0.6 low = 2.4 GHz, P0.7 low = Bluetooth, both high = USB; read every 10 ms
// by f65_power.c (f65_switch_tick).
#define CONN_SW_24G P0_6
#define CONN_SW_BT  P0_7

// Win / Mac switch (pulled-up input): high = Win, low = Mac (kb.c).
#define OS_SWITCH_MAC P7_4

// Power pins. P4.4 (input, no pull-up) reads high while USB power is present;
// P7.6 is driven to its inverse. P7.7 (pulled up) reads low while charging.
// P0.5 is an output held low while running that goes high before sleep; what
// it switches is not known.

// Sleep (f65_power.c): the pin set high before the power-down, and the P0 / P7
// pins the wireless sleep also drives low without pull-up (the connection
// switch P0.6 / P0.7 and P0.5; the OS switch P7.4 and P7.7).
#define SLEEP_PWR_PIN P0_5
#define SLEEP_P0_PARK 0xE0
#define SLEEP_P7_PARK 0x90

// Side lights (backlight.c): cells (i, 0) and (SIDE_RIGHT_COL + i, 0) for i <
// SIDE_PAIRS, slot order G, R, B.
#define SIDE_PAIRS     4
#define SIDE_RIGHT_COL 12
#define SIDE_SLOTS_GRB 1

// Status LEDs off the keys (indicators.c), in the bottom LED row: Caps Lock at
// column 4, the link at column 6 (smk matrix row STATUS_ROW; no key there).
// Columns 3 and 7 of that row have no key either; the effects leave them dark.
#define STATUS_CAPS_COL  4
#define STATUS_LINK_COL  6
#define STATUS_DARK_COL0 3
#define STATUS_DARK_COL1 7
#define STATUS_ROW       4

// The case's three LEDs: the top one is column 4's first (red) channel, the
// middle one its second (green) channel, the bottom one column 6 (RGB).
#define STATUS_MID_ON_CAPS_GREEN 1

// leddiag (led_diag.c): the cells it steps through, LED row 0 = side lights.
// clang-format off
#define LED_DIAG_CELLS                                                                                                   \
    {                                                                                                                    \
        {0, 1, "esc"}, {0, 2, "tab"}, {0, 3, "caps"}, {0, 4, "lshift"}, {0, 5, "lctrl"}, {6, 2, "y"}, {13, 3, "enter"}, \
        {14, 4, "up"}, {9, 5, "fn"}, {15, 5, "right"}, {0, 0, "side l0"}, {12, 0, "side r0"},                          \
        {4, 5, "status caps"}, {6, 5, "status link"}, {3, 5, "status 3"}, {7, 5, "status 7"},                        \
    }
// clang-format on
#define USB_PWR_DET P4_4
#define PWR_AUX_OUT P7_6
#define CHG_STAT    P7_7

// Radio module (f65_rf.c): EUART0 TXD P5.5 / RXD P5.6 at ~260870 baud, P0.2
// pulled low around each frame the MCU sends (the send request), P4.7 low
// while the module sends (high = module idle).

// Bluetooth names the radio module is given (f65_rf.c), one pair per slot:
// "AL71-1" (BT5.0) and "AL71-1 3.0" (BT3.0) for slot 1, and so on. The saved
// slot's at boot, a slot's again when Fn + Q / W / E moves to it.
#define RF_NAME_SLOT_BASE "AL71"

// user_settings.rf_link: bits 5:4 the transport (0 USB, 1 2.4 GHz, 2
// Bluetooth), bits 1:0 the Bluetooth slot; the default is USB, slot 1.
#define RF_LINK_DEFAULT 0x01

// Boot escape: the key held while the board powers up that jumps to the ISP
// bootloader (user_boot_escape). Matrix position (column, row): Esc.
#define BOOT_ESCAPE_KEY_COL 0
#define BOOT_ESCAPE_KEY_ROW 0

// Settings reset: hold Fn + SETTINGS_RESET_HOLD_KEY, then press Fn +
// SETTINGS_RESET_KEY (kb.c). Both are base-layer keycodes whose Fn-layer
// position must stay transparent; under Fn they send nothing.
#define SETTINGS_RESET_HOLD_KEY KC_BSPC
#define SETTINGS_RESET_KEY      KC_V

// The layer-tap keys (matrix.c): a release that waits for the decision although
// it is a basic key, because kb.c holds a state on it that the waiting keys
// need: SETTINGS_RESET_HOLD_KEY while it keeps the reset chord armed (a waiting
// SETTINGS_RESET_KEY press must find it armed), and the grave key while it
// gives ~ with a Shift of its own (a waiting key must still get that Shift);
// and every release while a US-JIS mode change waits for all keys up (the
// waiting presses must still see the old mode).
bool kb_lt_release_waits(uint16_t keycode);
#define LT_RELEASE_WAITS(keycode) kb_lt_release_waits(keycode)
// A key press the layer-tap keys hold or queue counts as activity at once (the
// idle sleep), before it reaches kb_process_record.
void kb_key_activity(void);
#define LT_PRESS_ACTIVITY() kb_key_activity()
// The middle status LED shows a held layer-tap key's layer (indicators.c):
// matrix.c keeps layer_tap_held for it.
#define LAYER_TAP_HELD 1

uint8_t layout_os_base_layer(bool is_mac);
bool    layout_is_fn_layer(uint8_t layer);

// The layers of keymaps[] (Win / Mac base, Win / Mac Fn): what VIA edits.
#define DYNAMIC_KEYMAP_LAYER_COUNT 4
// VIA's uptime: the 1 ms PWM4 tick, 32 bits (f65_rf.c)
#define VIA_MS32 rf_ms32
// The mouse keys' clock: the same tick, 16 bits (f65_rf.c)
#define MOUSEKEY_MS rf_ms

enum custom_keycodes {
#ifdef VIA_ENABLE
    // VIA numbers the customKeycodes of via.json from QK_KB_0, in this order
    USJIS_TOG = QK_KB_0, // US-JIS on/off (persisted; only in force in Win mode)
#else
    USJIS_TOG = SAFE_RANGE, // US-JIS on/off (persisted; only in force in Win mode)
#endif
    LNK_24G, // Fn + R: 2.4 GHz only - hold 3 s to pair the dongle
    LNK_BT1, // Fn + Q / W / E: Bluetooth only - slot 1 / 2 / 3,
    LNK_BT2, //   selected on release; hold 3 s to pair that slot
    LNK_BT3,
    FN_ALT, // Right Shift under Fn: the alternate number-row set, no Shift
    FR_1,   // Fn + 1 .. = : F1..F12 or media (kb.c, by OS mode and Right Shift)
    FR_2,
    FR_3,
    FR_4,
    FR_5,
    FR_6,
    FR_7,
    FR_8,
    FR_9,
    FR_10,
    FR_11,
    FR_12,
    BAT_SHOW, // Fn + B: the battery level on 1 .. 0 while held (wireless, on battery); sends nothing
    // Lighting (backlight.c; ansi / usjis):
    BL_TOG,    // Fn + [: backlight and side lights on / off
    BL_EFF,    // Fn + \: next key effect (0 = off, 1-17 without 6, 9, 14)
    BL_COL,    // Fn + ]: next colour (R G B Y M C W, 7 = rainbow / random)
    BL_BRI_UP, // Fn + Up / Down: brightness 0-4
    BL_BRI_DN,
    BL_SPD_UP, // Fn + Right / Left: speed 0-4 (faster / slower), the side lights' too
    BL_SPD_DN,
    SL_EFF, // Fn + /: next side effect (off, rainbow wave, rainbow cycle, static, breathing)
    SL_COL, // Fn + .: next side colour (static and breathing)
    SL_BRI, // Fn + ,: next side brightness 0-4
#ifdef LED_DIAG
    DIAG_NEXT,  // leddiag: next cell
    DIAG_PREV,  // leddiag: previous cell
    DIAG_COLOR, // leddiag: next colour
    DIAG_NAME,  // leddiag: type what is lit
    DIAG_LEVEL, // leddiag: dim / indicator level
#endif

    KB_SAFE_RANGE,
};
