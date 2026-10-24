#include "kbdef.h"
#include "layout.h"
#include "user_layout.h"
#include "report.h"
#include "kb.h"
#include <stdint.h>

// clang-format off

// Kcc_r = matrix column cc, row r. The physical layout (71 keys) is that of
// the AL71: a 65% block, two columns Ins / Home, End / PgUp, Del / PgDn on the
// right, the arrows below them. R2C12, R3C11, R3C12, R3C15 and R4C3/4/6/7/11
// carry no key.
#define LAYOUT_71( \
    K00_0, K01_0, K02_0, K03_0, K04_0, K05_0, K06_0, K07_0, K08_0, K09_0, K10_0, K11_0, K12_0, K13_0, K14_0, K15_0, \
    K00_1, K01_1, K02_1, K03_1, K04_1, K05_1, K06_1, K07_1, K08_1, K09_1, K10_1, K11_1, K12_1, K13_1, K14_1, K15_1, \
    K00_2, K01_2, K02_2, K03_2, K04_2, K05_2, K06_2, K07_2, K08_2, K09_2, K10_2, K11_2,        K13_2, K14_2, K15_2, \
    K00_3, K01_3, K02_3, K03_3, K04_3, K05_3, K06_3, K07_3, K08_3, K09_3, K10_3,               K13_3, K14_3,        \
    K00_4, K01_4, K02_4,               K05_4,               K08_4, K09_4, K10_4,        K12_4, K13_4, K14_4, K15_4  \
) { \
    { K00_0, K01_0, K02_0, K03_0, K04_0, K05_0, K06_0, K07_0, K08_0, K09_0, K10_0, K11_0, K12_0, K13_0, K14_0, K15_0 }, \
    { K00_1, K01_1, K02_1, K03_1, K04_1, K05_1, K06_1, K07_1, K08_1, K09_1, K10_1, K11_1, K12_1, K13_1, K14_1, K15_1 }, \
    { K00_2, K01_2, K02_2, K03_2, K04_2, K05_2, K06_2, K07_2, K08_2, K09_2, K10_2, K11_2, KC_NO, K13_2, K14_2, K15_2 }, \
    { K00_3, K01_3, K02_3, K03_3, K04_3, K05_3, K06_3, K07_3, K08_3, K09_3, K10_3, KC_NO, KC_NO, K13_3, K14_3, KC_NO }, \
    { K00_4, K01_4, K02_4, KC_NO, KC_NO, K05_4, KC_NO, KC_NO, K08_4, K09_4, K10_4, KC_NO, K12_4, K13_4, K14_4, K15_4 }  \
}

// leddiag: the ansi layout plus the LED diagnostic keys on the Fn-layer arrows
// (led_diag.c): Fn+Right / Fn+Left = next / previous cell, Fn+Up = next colour,
// Fn+Down = type what is lit, Fn+PgDn = dim / indicator level.

#define _WIN_BL 0
#define _MAC_BL 1
#define _WIN_FL 2
#define _MAC_FL 3

#define FN_WIN MO(_WIN_FL)
#define FN_MAC MO(_MAC_FL)

const uint16_t keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    /* Keymap _WIN_BL: Windows base layer (the Win / Mac switch at Win), as
     * printed.
     * ,-----------------------------------------------------------------------.
     * |Esc|  1|  2|  3|  4|  5|  6|  7|  8|  9|  0|  -|  =|  Bksp |Ins|Hom|
     * |-----------------------------------------------------------------------|
     * |Tab  |  Q|  W|  E|  R|  T|  Y|  U|  I|  O|  P|  [|  ]|    \|End|PgU|
     * |-----------------------------------------------------------------------|
     * |Caps  |  A|  S|  D|  F|  G|  H|  J|  K|  L|  ;|  '|  Enter |Del|PgD|
     * |-----------------------------------------------------------------------|
     * |Shift   |  Z|  X|  C|  V|  B|  N|  M|  ,|  .|  /| Shift|   |Up |
     * |-----------------------------------------------------------------------|
     * |Ctl |Win |Alt |        Space          |Alt| Fn|App|Ctl|Lef|Dow|Rig|
     * `-----------------------------------------------------------------------'
     */
    [_WIN_BL] = LAYOUT_71(
        KC_ESC,  KC_1,    KC_2,    KC_3,    KC_4,    KC_5,    KC_6,    KC_7,    KC_8,    KC_9,    KC_0,    KC_MINS, KC_EQL,  KC_BSPC, KC_INS,  KC_HOME,
        KC_TAB,  KC_Q,    KC_W,    KC_E,    KC_R,    KC_T,    KC_Y,    KC_U,    KC_I,    KC_O,    KC_P,    KC_LBRC, KC_RBRC, KC_BSLS, KC_END,  KC_PGUP,
        KC_CAPS, KC_A,    KC_S,    KC_D,    KC_F,    KC_G,    KC_H,    KC_J,    KC_K,    KC_L,    KC_SCLN, KC_QUOT,          KC_ENT,  KC_DEL,  KC_PGDN,
        KC_LSFT, KC_Z,    KC_X,    KC_C,    KC_V,    KC_B,    KC_N,    KC_M,    KC_COMM, KC_DOT,  KC_SLSH,                   KC_RSFT, KC_UP,
        KC_LCTL, KC_LGUI, KC_LALT,                   KC_SPC,                    KC_RALT, FN_WIN,  KC_APP,  KC_RCTL, KC_LEFT, KC_DOWN, KC_RGHT
    ),

    /* Keymap _MAC_BL: Mac base layer (the switch at Mac), the Mac modifiers:
     * the key right of Left Ctrl is Option, the next one Command; right of
     * Space Command, and the printed App key is Right Option.
     * |Ctl |Opt |Cmd |        Space          |Cmd| Fn|Opt|Ctl|Lef|Dow|Rig|
     */
    [_MAC_BL] = LAYOUT_71(
        KC_ESC,  KC_1,    KC_2,    KC_3,    KC_4,    KC_5,    KC_6,    KC_7,    KC_8,    KC_9,    KC_0,    KC_MINS, KC_EQL,  KC_BSPC, KC_INS,  KC_HOME,
        KC_TAB,  KC_Q,    KC_W,    KC_E,    KC_R,    KC_T,    KC_Y,    KC_U,    KC_I,    KC_O,    KC_P,    KC_LBRC, KC_RBRC, KC_BSLS, KC_END,  KC_PGUP,
        KC_CAPS, KC_A,    KC_S,    KC_D,    KC_F,    KC_G,    KC_H,    KC_J,    KC_K,    KC_L,    KC_SCLN, KC_QUOT,          KC_ENT,  KC_DEL,  KC_PGDN,
        KC_LSFT, KC_Z,    KC_X,    KC_C,    KC_V,    KC_B,    KC_N,    KC_M,    KC_COMM, KC_DOT,  KC_SLSH,                   KC_RSFT, KC_UP,
        KC_LCTL, KC_LALT, KC_LGUI,                   KC_SPC,                    KC_RGUI, FN_MAC,  KC_RALT, KC_RCTL, KC_LEFT, KC_DOWN, KC_RGHT
    ),

    /* Keymap _WIN_FL / _MAC_FL: function layer (hold Fn), the keys that make
     * sense without lighting or radio, and the diagnostic keys.
     * `  = grave (Shift gives ~)   - = nothing
     * (reset) / (r): Fn + Backspace held, then Fn + V resets the settings.
     */
    [_WIN_FL] = LAYOUT_71(
        KC_GRV,  KC_F1,   KC_F2,   KC_F3,   KC_F4,   KC_F5,   KC_F6,   KC_F7,   KC_F8,   KC_F9,   KC_F10,  KC_F11,  KC_F12,  _______, _______, _______,
        _______, _______, _______, _______, _______, _______, _______, KC_PSCR, KC_SCRL, KC_PAUS, _______, _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______, _______, _______, _______, _______, _______, _______, _______,          _______, _______, DIAG_LEVEL,
        _______, _______, _______, _______, _______, _______, _______, KC_NO,   _______, _______, _______,                   _______, DIAG_COLOR,
        _______, _______, _______,                   _______,                   _______, _______, _______, _______, DIAG_PREV, DIAG_NAME, DIAG_NEXT
    ),

    [_MAC_FL] = LAYOUT_71(
        KC_GRV,  KC_F1,   KC_F2,   KC_F3,   KC_F4,   KC_F5,   KC_F6,   KC_F7,   KC_F8,   KC_F9,   KC_F10,  KC_F11,  KC_F12,  _______, _______, _______,
        _______, _______, _______, _______, _______, _______, _______, KC_PSCR, KC_SCRL, KC_PAUS, _______, _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______, _______, _______, _______, _______, _______, _______, _______,          _______, _______, DIAG_LEVEL,
        _______, _______, _______, _______, _______, _______, _______, KC_NO,   _______, _______, _______,                   _______, DIAG_COLOR,
        _______, _______, _______,                   _______,                   _______, _______, _______, _______, DIAG_PREV, DIAG_NAME, DIAG_NEXT
    ),
};

// clang-format on

_Static_assert(sizeof(keymaps) / sizeof(keymaps[0]) == DYNAMIC_KEYMAP_LAYER_COUNT, "kbdef.h: DYNAMIC_KEYMAP_LAYER_COUNT is the number of layers");

uint8_t layout_os_base_layer(bool is_mac)
{
    return is_mac ? _MAC_BL : _WIN_BL;
}

bool layout_is_fn_layer(uint8_t layer)
{
    return layer == _WIN_FL || layer == _MAC_FL;
}

bool layout_process_record(uint16_t keycode, bool key_pressed)
{
    keycode;
    key_pressed;
    return true;
}
