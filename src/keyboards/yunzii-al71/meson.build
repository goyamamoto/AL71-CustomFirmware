kb_dir = meson.current_source_dir()
f65_dir = kb_dir / '../aula-f65-v1'

keyboards += {
    'yunzii-al71' : {
        'dir' : kb_dir,
        'platform' : 'sh68f90',
        # The board code shared with the AULA F65 V1 (the same MCU wiring but
        # for the switches and power pins, kbdef.h).
        'inc' : [f65_dir],
        'src' : files(
            '../aula-f65-v1/user_matrix.c',
            'user_init.c',
            '../aula-f65-v1/user_sleep.c',
            '../aula-f65-v1/kb.c',
            '../aula-f65-v1/f65_rf.c',
            '../aula-f65-v1/f65_power.c',
            '../aula-f65-v1/led.c',
        ),
        'layouts' : {
            # Plain US ANSI, as printed.
            'ansi' : {
                'dir' : kb_dir / 'layouts/ansi',
                'src' : files('layouts/ansi/layout.c', '../aula-f65-v1/indicators.c', '../aula-f65-v1/backlight.c'),
                'defines' : ['F65_LIGHTING=1', 'SETTINGS_F65_LIGHTING=1'],
            },
            # ANSI plus US-JIS (Fn+Tab), IME mod-taps on both sides of Space, Caps Lock / Left Ctrl swapped.
            'usjis' : {
                'dir' : kb_dir / 'layouts/usjis',
                'src' : files('layouts/usjis/layout.c', '../aula-f65-v1/indicators.c', '../aula-f65-v1/backlight.c'),
                'defines' : ['USJIS=1', 'TAP_HOLD=1', 'F65_LIGHTING=1', 'SETTINGS_F65_LIGHTING=1'],
            },
            # ansi and usjis with VIA (raw HID on interface 0, the keymap kept
            # in flash; the mod-taps, layer-taps and mouse keys VIA sets work);
            # via.json is the definition to load into VIA.
            'ansi-via' : {
                'dir' : kb_dir / 'layouts/ansi',
                'src' : files('layouts/ansi/layout.c', '../aula-f65-v1/indicators.c', '../aula-f65-v1/backlight.c'),
                'defines' : ['TAP_HOLD=1', 'F65_LIGHTING=1', 'SETTINGS_F65_LIGHTING=1', 'KB_KEYMAP_CHANGED_HOOK=1', 'MOUSEKEY_ENABLE=1'],
                'via' : true,
            },
            # CONSOLE_BUF_SIZE: the debug console's buffer (debug builds only),
            # halved so the debug build fits the 4 KB XDATA.
            'usjis-via' : {
                'dir' : kb_dir / 'layouts/usjis',
                'src' : files('layouts/usjis/layout.c', '../aula-f65-v1/indicators.c', '../aula-f65-v1/backlight.c'),
                'defines' : [
                    'USJIS=1',
                    'TAP_HOLD=1',
                    'F65_LIGHTING=1',
                    'SETTINGS_F65_LIGHTING=1',
                    'KB_KEYMAP_CHANGED_HOOK=1',
                    'MOUSEKEY_ENABLE=1',
                    'CONSOLE_BUF_SIZE=64',
                ],
                'via' : true,
            },
            # For the first hardware check of the LEDs: ansi, no indicators, one
            # channel of one cell lit dimly at a time (led_diag.c).
            'leddiag' : {
                'dir' : kb_dir / 'layouts/leddiag',
                'src' : files('layouts/leddiag/layout.c', '../aula-f65-v1/led_diag.c'),
                'defines' : ['LED_DIAG=1'],
            },
        },
        'options' : {
            # The original USB ID, so `sinowisp -d yunzii-al71` (258A:010C, interface 1, report 5) finds it.
            'vendor_id' : '0x258a',
            'product_id' : '0x010c',
            'defines' : [
                'BOOT_ESCAPE=1',
                'SETTINGS_OS_MODE=1',
                'NKRO_DEFAULT_OFF=1',
                'LATCH_KEYCODES=1',
                'USB_WAKE_ON_KEY=1',
                'USB_FEATURE_REPORT_STRICT=1',
                'RF_EUART0=1',
                'PWM4_MS_TICK=1',
                'BOARD_USB_BOOT_GATE=1',
                'KB_FN_LAYER_HOOK=1',
                'CONSUMER_USAGE_MAX=0x02FF',
                'USB_INIT_GATE=1',
                'USB_IRQ_ACTIVITY=1',
                'POWER_INT4_WOKE_API=1',
                'DELAY_NO_WATCHDOG_KICK=1',
                'USB_ISP_PREPARE=1',
                'STARTUP_LED_OFF=1',
                'MATRIX_DEBOUNCE_SCANS=4',
                'LED_SUBFRAMES_PER_SCAN=5',
                'SYSTICK_LED_SUBFRAME_RELOAD=0xFE6F',
                'FLASH_OP_WATCHDOG_KICK=1',
                'CLOCK_PLL_WAIT_BOUND=20000',
            ],
            'sinowisp_device' : 'yunzii-al71',
            'manufacturer' : 'SMK',
            'product' : 'YUNZII AL71 (SMK)',
        },
    },
}
