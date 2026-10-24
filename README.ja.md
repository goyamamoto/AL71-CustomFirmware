# YUNZII AL71 カスタムファームウェア

[English](README.md)

YUNZII AL71 キーボード用のオープンソースファームウェアです。ケースを開けずに USB で書き込めます。

> [!WARNING]
> メーカーのファームウェアを置き換えます。元に戻すには自分の基板のバックアップ（手順 3）が必要で、メーカーのファームウェアはここでは配っていません。このファームウェアでは、Esc を押しながらケーブルを挿すと、その USB の処理が動く前にブートローダが起動するので、ファームウェアの USB が動かなくてもブートローダに入れます。使用は自己責任です。

> [!CAUTION]
> このファームウェアは、USB のバージョンが 20.02 の AL71 用に作り、その実機で確かめたものです（手順 1 で分かります）。別のバージョンの基板は配線が違うかもしれません。書く前に同じように確かめてください。

## できること

- 71 キーすべて、Win / Mac スイッチによる Windows と Mac のレイヤー、電源を切っても設定が残る
- USB、Bluetooth（3 スロット、名前は "AL71-1"、"AL71-2"、"AL71-3" で、ホストからどのスロットか分かる）、2.4 GHz ドングル。キーボードの無線モジュールを通して
- バックライトの効果（14 種）、色、明るさ、速さ、サイドライト。状態表示（Caps Lock、Fn を押している間のリンクのキー、ペアリング、Fn+B での電池残量、電池低下、充電）をバックライトとケースの 3 つの LED に表示
- 電池駆動で約 1 分操作がないとスリープ（キーで起きる）、電池駆動で 30 秒操作がないとバックライトを消灯、電池低下時の停止
- US-JIS（Fn+Tab、`usjis` 系のレイアウト）: ホストを日本語配列にしたまま、US の刻印どおりに入力できる（Windows レイヤー）
- スペースの両隣の IME キー（`usjis` 系のレイアウト）: 単押しで無変換 / 変換（Windows）、英数 / かな（Mac）、長押しで Alt と右 Ctrl（Windows）、Command と右 Command（Mac）
- VIA（`-via` のレイアウト）: [VIA](https://usevia.app) から USB でキー配置を変えられ、フラッシュに保存される。レイヤータップとマウスキーも使える
- ブートエスケープ: Esc を押しながら電源を入れると、このファームウェアの USB の処理が動く前にブートローダが起動する
- 有線では元の USB ID のままなので、`sinowisp` が `yunzii-al71` として見つける

## レイアウトを選ぶ

どのイメージも、ハードウェアの対応、ブートエスケープ、Bluetooth の名前、スリープは同じです。

| レイアウト | 追加されるもの | イメージ |
| --- | --- | --- |
| `ansi` | なし: 刻印どおりの US ANSI | `firmware/` の `yunzii-al71_ansi_smk.hex` |
| `usjis` | US-JIS（Fn+Tab）、スペースの両隣の IME キー、Caps Lock と左 Ctrl の入れ替え | `firmware/` の `yunzii-al71_usjis_smk.hex` |
| `usjis-via` | `usjis` に、VIA でキー配置を変える機能 | `firmware/` の `yunzii-al71_usjis-via_smk.hex` |
| `ansi-via` | `ansi` に、VIA でキー配置を変える機能 | `firmware/` の `yunzii-al71_ansi-via_smk.hex` |

VIA のレイアウトは、最初は `ansi` / `usjis` と同じキー配置です。[VIA を使う](#via-を使う)を見てください。実機で確かめたのは `usjis-via` のこのイメージです。`ansi` は前のビルド（キーは同じで、ケースの真ん中の LED の表示と、スロットごとの Bluetooth の名前の前）を実機で確かめています。`usjis` と `ansi-via` はシミュレータで確かめています。

## 対応キーボード

| キーボード | USB ID | 状態 |
| --- | --- | --- |
| YUNZII AL71、USB のバージョン 20.02 | 258a:010c、manufacturer "BY Tech"、product "Gaming Keyboard" | 動作。macOS のホストで USB、Bluetooth、2.4 GHz ドングルを実機で確認 |

## 手順

裏のスイッチで接続先を選びます。裏から見て左から Bluetooth、Line（USB）、2.4 GHz です。以下の手順はどれも Line の位置で、ケーブルを挿して行います。元のファームウェアから始めた sinowisp のコマンドの後は、ケーブルを抜いて挿し直すまでキーボードが USB に出てきません（バックライトも消えたまま）。次のコマンドの前に挿し直してください。このファームウェアが動いているときは、数秒で自分で戻ってきます。

1. キーボードを確かめる。USB ID `258a:010c`、manufacturer "BY Tech"、product "Gaming Keyboard"、バージョン 20.02 と出ます（macOS: システム情報 > USB）。
2. ツールを入れる。[sinowisp](https://github.com/carlossless/sinowisp) を `cargo install sinowisp` で入れます（[Rust](https://rustup.rs/) が必要。sinowisp はキーボードのブートローダを通して USB でフラッシュを読み書きします）。macOS では、入力監視の許可があるターミナルから実行します（システム設定 > プライバシーとセキュリティ > 入力監視）。許可がないとキーボードを開けません。USB ID 258a:010c の他のキーボードは外しておきます（多くのキーボードが同じ ID で、sinowisp は最後に見つけたものを使うため）。
3. 元のファームウェアをバックアップする。1 つ目のファイルが元に戻す手段になります。コマンドごとにケーブルを挿し直します。
   ```sh
   sinowisp read -d yunzii-al71 al71-stock.hex                        # ファームウェア。戻すときに使う（手順 8）
   sinowisp read -d yunzii-al71 -s full --format bin al71-full.bin    # ファームウェアとブートローダ。下の確認に使う
   tail -c 4096 al71-full.bin | md5                                   # Linux では md5sum
   ```
   最後の行が `2d169670eae0d36eae8188562c1f66e8`（sinowisp が載せている AL71 のブートローダ）を出すこと。ファームウェアを 2 回読んでファイルを比べると、読み出しが安定しているか分かります。
4. ファームウェアを用意する。レイアウトを選び（上の表）、[firmware/yunzii-al71](firmware/yunzii-al71) のイメージを使うか（`shasum -a 256 -c SHA256SUMS` で確認）、自分でビルドします（[ビルド](#ビルド)）。
5. 書き込んで、ケーブルを挿し直す。
   ```sh
   sinowisp write -d yunzii-al71 --force yunzii-al71_usjis-via_smk.hex    # または他のイメージ
   ```
   イメージがフラッシュより小さいので `--force` が要ります。sinowisp は残りを 0 で埋めるので、設定と VIA で変えたキー配置も初期値に戻ります（書くたびに、使うなら Fn+Tab で US-JIS。VIA のキー配置は先に VIA の Save + Load で保存しておく）。
6. 戻り道を確かめる。
   - 新しいファームウェアが動いている状態で `sinowisp read -d yunzii-al71 check.hex` ができ、キーボードが自分で戻ってくる。
   - ケーブルを抜き（Line の位置なら電源が切れる）、数秒待ち、Esc を押したまま挿して 2 秒後に離すと、ブートローダの `0603:1020`（文字列なし）として見える。Esc なしで挿し直せばファームウェアに戻る。

   2 つ目の方法はこのファームウェアの USB の処理に依存しません。無線の位置からは、先にスイッチを Line にします（でないと電池で動き続けます）。
7. 使う。[キーマップ](#キーマップ)を見てください。ドングルは 2.4 GHz の位置で Fn+R を 3 秒、Bluetooth のスロットは Bluetooth の位置で Fn+Q / W / E を 3 秒押してペアリングします。
8. 元のファームウェアに戻す（いつでも。Line の位置で）:
   ```sh
   sinowisp write -d yunzii-al71 al71-stock.hex
   ```

## キーマップ

| 場所 | 働き |
| --- | --- |
| ベースレイヤー | 印字どおりの US ANSI 65% と、右の Ins / Home、End / PgUp、Del / PgDn。Win / Mac スイッチでレイヤーが決まる（電源投入時と、スイッチを動かしたとき。押しているキーは先に離される） |
| 一番下の列 | Windows: 印字どおり Ctrl、Win、Alt、Space、Alt、Fn、App、Ctrl。Mac: Ctrl、Option、Command、Space、Command、Fn、Option、Ctrl |
| Space の両隣 | `usjis`: 短く押すか押したままかで変わるキー。Windows: 左 = 短く押すと無変換、押したままだと Alt。右（印字の右 Alt）= 短く押すと変換、押したままだと右 Ctrl。Mac: 左 = 英数 / Command、右 = かな / 右 Command。約 0.4 秒押し続けるか、他のキーを押した時点で修飾キーになる。Fn は印字の位置のまま。Caps Lock と左 Ctrl の位置が入れ替わる |
| Fn + 1 … = | Windows: F1〜F12。Mac: 明るさ、Mission Control、Launchpad、前 / 再生 / 次、消音、音量（Apple の並び） |
| Fn + 右 Shift + 1 … = | もう一方の組。Windows ではメディアキー、Mac では F1〜F12 |
| Fn + Esc | `` ` ``（Shift と一緒で `~`） |
| Fn + Tab | `usjis`: US-JIS のオン / オフ（保存される。Windows レイヤーのみ）。`ansi`: Tab |
| Fn + Q / W / E | Bluetooth スロット 1 / 2 / 3（Bluetooth の位置）: 短く押すと選択、3 秒押すとペアリング（キーが青く点滅） |
| Fn + R | 2.4 GHz: 3 秒押すとドングルとペアリング（キーが点滅） |
| Fn（押している間） | 今つながっているリンクのキーが点く: Y 白（USB）、R 緑（2.4 GHz）、スロットのキー 青（Bluetooth） |
| Fn + B（押している間） | 数字列に電池残量（無線の位置、電池のとき） |
| Fn + \\ , ] , [ | 次の効果（消灯を含めて一周）、次の色（7 色と虹色）、光を全部消す / 戻す |
| Fn + ↑ ↓ ← → | 明るさ（5 段階）と速さ（5 段階。サイドライトも従う） |
| Fn + / . , | サイドライト: 次の効果、色、明るさ |
| Fn + U / I / O | PrtSc / ScrLk / Pause |
| Fn + Backspace を押したまま Fn + V | 設定の初期化（US-JIS オフ、光の初期値。VIA のレイアウトでは組み込みのキー配置にも戻る） |

ケースの 3 つの LED: 一番上は Caps Lock です。一番下（RGB）は充電中に赤く点き、電池低下で赤く点滅し、ペアリング中と再接続中は点滅し（2.4 GHz は水色、Bluetooth は青）、つながると 3 秒点きます。真ん中は、レイヤータップのキー（VIA）でその層に入っている間に点きます。`usjis` 系のレイアウトでは、Fn を押している間（と Fn+Tab の後の約 1 秒）、Tab キーと同じく US-JIS を見せます（オンで点灯、オフで点滅）。

どれも USB でも無線でも同じに働きます。光の設定は最後に変えてから約 3 秒で保存され、その瞬間にバックライト全体が一度またたきます（フラッシュへの書き込み）。

## VIA を使う

`-via` のイメージを書き、スイッチを Line（USB）にして:

1. WebHID が使えるブラウザ（Chrome、Edge）で [usevia.app](https://usevia.app) を開く。
2. Settings で「Show Design tab」をオンにし、Design でこのリポジトリの [via.json](src/keyboards/yunzii-al71/via.json) を読み込む。
3. Configure で「Authorize device」を押し、「YUNZII AL71 (SMK)」を選ぶ。

4 つのレイヤーは Windows の基本、Mac の基本、Windows の Fn、Mac の Fn です。変更は最後の変更から約 0.5 秒後にフラッシュに保存され、Bluetooth と 2.4 GHz でも使われます。VIA で設定できるのは、普通のキー、修飾付きのキー（Ctrl+C など）、モッドタップ、`MO`、レイヤータップ（`LT`。例えば Space を押している間だけマウスキーの層にする）、マウスキー、メディアキー、このキーボードのキー（US-JIS、リンク、電池、Fn の数字列、照明）です。トグル、ワンショット、マクロには対応しておらず、照明は Fn のキーで操作します。VIA は USB ID ごとに定義を 1 つしか持たず、他のキーボード（F65 など）も 258a:010c を使います。それらで VIA を使った後は、このファイルをもう一度読み込んでください。詳しくは [docs/keyboards/yunzii-al71.md](docs/keyboards/yunzii-al71.md) と [docs/keyboards/aula-f65-v1.md](docs/keyboards/aula-f65-v1.md#via)（英語）。

## ビルド

`firmware/` のイメージは、下の手順で macOS で作ったリリースビルドです。同じコミットを同じようにビルドするとバイト単位で同じものができるので、配布物を自分のビルドと突き合わせて確かめられます（別のプラットフォームでのビルドは数バイト違うことがあります）。

### リリースビルドの手順

1. ソースを取る。
   ```sh
   git clone https://github.com/goyamamoto/AL71-CustomFirmware.git
   cd AL71-CustomFirmware
   ```
2. ツールチェーンを入れる。SDCC は 4.5.0 ちょうどが必要です（他の版では smk の `--Werror` で止まるか、違うイメージになります）。ほかに meson、ninja、Python 3。
   - [Nix](https://nixos.org/)（Linux か macOS）: リポジトリで `nix develop`。sinowisp とシミュレータを含めて全部そろいます。
   - Nix なしの macOS: [Homebrew](https://brew.sh/) を入れたうえで、[tools/macos/setup-toolchain.sh](tools/macos/setup-toolchain.sh) を一度実行します。meson と ninja を Homebrew で入れ、SDCC 4.5.0 とシミュレータを `~/.local/smk` にビルドします（時間がかかります）。その後、新しいターミナルを開くたびに:
     ```sh
     . ~/.local/smk/env.sh
     sdcc --version    # 4.5.0 と出ること
     ```
   - それ以外: meson、ninja、Python 3、SDCC 4.5.0 を入れます（パッケージマネージャの版が違うならソースから）。
3. リリースビルドを設定する（一度だけ）。`build-release` が出力フォルダ、`--buildtype=release` がデバッグコンソールとログを外す指定です。
   ```sh
   meson setup build-release --buildtype=release
   ```
4. 欲しいレイアウトをビルドする:
   ```sh
   meson compile -C build-release yunzii-al71_usjis_smk.hex yunzii-al71_ansi_smk.hex yunzii-al71_usjis-via_smk.hex yunzii-al71_ansi-via_smk.hex
   ```
   イメージは `build-release/` にできます。ソースを変えたらこの手順だけをやり直します（手順 3 は不要）。
5. 確かめる（任意、macOS）。ソースを変えていなければ `firmware/` と同じファイルになります。ビルドしたイメージがそれぞれ `OK` と出ること:
   ```sh
   (cd build-release && shasum -a 256 --ignore-missing -c ../firmware/yunzii-al71/SHA256SUMS)
   ```
6. 書き込む。[手順](#手順)の 5 と 6 のとおり、自分のイメージのパスで。例: `sinowisp write -d yunzii-al71 --force build-release/yunzii-al71_usjis_smk.hex`。

### リリースビルドとデバッグビルド

| | リリース | デバッグ |
| --- | --- | --- |
| 設定 | `meson setup build-release --buildtype=release` | `meson setup build`（meson の既定） |
| 用途 | 普段使い。`firmware/` のイメージ | 開発 |
| HID デバッグコンソール（`tools/smk-console`） | なし | あり。チップ ID、モードの変化、設定をホストに報告する |
| ログ | なし | あり |
| ソースレベルのシミュレータテスト | スキップ（`.cdb` がない） | 実行 |

キーボードは打ったものを全部見ています。デバッグビルドはコンソールでホストに報告し、リリースビルドにはコンソールがありません。

### 技術メモとテスト

ピン、LED、無線リンク、VIA、スリープ、復旧と、シミュレータのテストの走らせ方は、[docs/keyboards/yunzii-al71.md](docs/keyboards/yunzii-al71.md) と [docs/keyboards/aula-f65-v1.md](docs/keyboards/aula-f65-v1.md)（どちらも英語）にあります。

## 既知の制限

- どのイメージを書いても設定は初期値に戻ります（sinowisp がフラッシュを消去し、イメージを 0 で埋めて書くため）: US-JIS オフ、光の初期値、VIA で変えたキー配置。
- 含めていないもの: メーカーのドライバのプロトコル（キーごとのカスタム発光、メーカーのソフトからの設定）。
- バックライトは元のファームウェアより暗めです。既定の明るさが 4 段階中 2（元は 4）で、同じ段でも LED が点いている時間の割合が小さいためです（見積もりで半分ほど）。
- US-JIS は Windows レイヤーだけで働きます。macOS は一部の置き換えに必要な JIS 専用キーを捨ててしまうためです。
- VIA: マクロと照明のメニューはありません。キー配置を変えられるのは USB（Line の位置）のときだけです。同じキーを送る 2 つのキー（例: C と Ctrl+C）はそのキーを共有し、片方を離すと両方とも離したことになります。
- 実機でまだ見ていないもの: USB の電源だけがありホストがないときのスリープ、US-JIS での入力（オン / オフの切り替えは見ています）。ファームウェアのそれ以外の機能は、文書に書いたとおり実機かシミュレータで確かめています。
- 分かっているのは ANSI の AL71 だけです。

## ソース

SinoWealth のキーボード用のオープンなファームウェア [smk](https://github.com/carlossless/smk) の [69373bb](https://github.com/carlossless/smk/commit/69373bbb633bd1159f4541f486ff7506563a38ec)（2026-09-16）に、2026 年 9 月から 10 月に手を加えたものです。AL71 は `src/keyboards/yunzii-al71/` にあり、基板のコードを EPOMAKER x AULA F65 V1（`src/keyboards/aula-f65-v1/`、[goyamamoto/F65-CustomFirmware](https://github.com/goyamamoto/F65-CustomFirmware)）と共有しています。smk が対応する他のキーボードもこのツリーからビルドできます。上流の README は [docs/README-smk.md](docs/README-smk.md) にあります。

## クレジットとライセンス

- Karolis Stasaitis 氏の [smk](https://github.com/carlossless/smk)、[sinowisp](https://github.com/carlossless/sinowisp)、[sinodude](https://github.com/carlossless/sinodude)。SinoWealth のキーボードに関する氏の仕事がこの移植を可能にしました。
- [Thaolia/smk_aulaF75](https://github.com/Thaolia/smk_aulaF75)（AULA F75 の smk 移植）は、この系統の無線モジュールが EUART0 でどう話すかを示してくれました。
- VIA のコマンド処理とキー配置のインタフェースは QMK の `quantum/via.c` と `quantum/dynamic_keymap.c` に、マウスキーは QMK の加速つきマウスキーに従います（[QMK](https://github.com/qmk/qmk_firmware)、GPL-2.0-or-later）。設定ツールは [VIA](https://github.com/the-via/app) です。
- US-JIS の規則は [goyamamoto/zmk-kb1-usjis](https://github.com/goyamamoto/zmk-kb1-usjis) に従います。
- ライセンス: smk と同じ GPL-2.0（[LICENSE](LICENSE)）。

YUNZII、EPOMAKER、AULA はそれぞれの所有者の商標です。このプロジェクトはそれらと関係なく、承認も受けていません。
