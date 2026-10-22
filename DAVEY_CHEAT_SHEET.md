# MPC2000XL DAVEY OS – Cheat Sheet / Шпаргалка

Build: DAVEY preset of the DAVEY MPC PATCHER (experimental line EXP6, emulator-tested). Base: VU features without REGIONS.

## ENGLISH

### 1. ZONE CHOP (waveform chop screen)

**Open:** SHIFT+5 (TRIM) → F3 (ZONE) → **F3 again**. The header reads `ZONE CHOP  Zones:nn  Taps:nn`.
Patcher options: **Chop: even split** and/or **Lazy chop** (with only one, F3 offers only that kind).

| Key | Action |
|-----|--------|
| F1 BACK | leave, put back the zones you had before |
| F2 EVEN / CLEAN | redo the even split / start the lazy chop over |
| F3 16 → 8 → 4 → LAZY | even slices, or LAZY |
| F4 UNDO | LAZY: take back the last tap |
| F5 APPLY | stock Edit window opens with SLICE SOUND: DO IT makes one sound per slice and a drum program |
| F6 PLAY (hold) | hear the current slice; release stops it |
| Pad n | select slice n and hear it |
| Cursor → `End:` / `Zone:` + DATA wheel | move the slice end / step through slices |
| SHIFT + ←/→ on `St:`/`End:` | wheel step 1 / 10 / 100 / 1000 (as in stock TRIM) |
| WINDOW | leave, keep the slices as plain zones |

**LAZY:** hit any pad to start the sample, then tap pads where each new slice starts. The zones follow every tap. When it stops, pads preview the slices; trim them, then APPLY.

16 LEVELS stays free. Up to 16 slices.

### 2. TRIM: PAD SELECTS ITS SOUND

On the TRIM page a pad hit switches `Snd:` to **the sound on that pad** (name, St/End and waveform) and plays it. After an APPLY, hit pad 3 to fix slice 3. A pad with no sound plays the current sound, as before.

### 3. PROGRAM MONO (newer-MPC style)

SHIFT+6 → F2 (PARAMS) → `Voice overlap: MONO`. **MONO pads choke each other.** Set MONO on all pads (ALL / param copy) and the whole program is monophonic. One MONO pad among POLY pads behaves as stock (cuts only itself). Programs on disk are unchanged.

### 4. MUTE GROUPS

SHIFT+6 → F1 (ASSIGN) → `Mode:` → `MUTE 1`…`MUTE 4` (`MUTE 5`…`8` with the Mute 1-8 option). Pads in the same group choke each other: use it for open/closed hi-hat. NORMAL = no group.
Whole bank / program: cursor on `Mode:` → WINDOW → ALL FOR: BANK / PROGRAM.

### 4b. 1/4 TIMING

`Timing:` / `Note value:` now goes up to `1/4` and `1/4(3)` (after `1/32(3)`, nothing removed). Saved .ALL files read as 1/8 / 1/8(3) on a stock unit.

### 5. SAMPLING MODE

SHIFT+4 (SAMPLE) → cursor on `Mode:` → WINDOW. Preset OFF / SP1200 (26.04 kHz, 12-bit) / S900 (30 kHz), or `Sample Rate` 8000–44100 Hz. F5 DO IT. Record as usual; a black "processing" box shows until it is done, then KEEP / RETRY. OFF = stock recording.

Tip: TRIM shows one channel of a stereo sound (`View: LEFT` / `RIGHT`). A mono source on one input leaves the other channel empty.

### 6. RESTORE THE ORIGINAL OS

Keep the original `MPC2KXL.BIN` at the root of the card. LOAD → pick it → DO IT. (Boot-from-disk also works.)

**Important: the file's time stamp.** On some units (those with a newer 16-bit flash chip) the OS reads the OS file's
*time of day* as a version number and refuses files stamped before **01:14** with "OS version too old".
The Mac and Windows patcher apps handle this for you. With the browser version, don't save between midnight and 1:14 AM.
When copying the original `MPC2KXL.BIN`, keep its time stamp (Finder copy or `cp -p`).

---

## РУССКИЙ

### 1. ZONE CHOP (экран нарезки с волной)

**Открыть:** SHIFT+5 (TRIM) → F3 (ZONE) → **ещё раз F3**. В заголовке `ZONE CHOP  Zones:nn  Taps:nn`.
Опции патчера: **Chop: even split** и/или **Lazy chop** (если выбрана одна, F3 предлагает только её).

| Клавиша | Действие |
|---------|----------|
| F1 BACK | выйти, вернуть прежние зоны |
| F2 EVEN / CLEAN | заново ровное деление / начать lazy заново |
| F3 16 → 8 → 4 → LAZY | ровные слайсы или LAZY |
| F4 UNDO | LAZY: отменить последний тап |
| F5 APPLY | стандартное окно Edit со SLICE SOUND: DO IT создаёт звук на каждый слайс и drum-программу |
| F6 PLAY (держать) | слушать текущий слайс; отпустить = стоп |
| Пэд n | выбрать слайс n и прослушать |
| Курсор → `End:` / `Zone:` + колесо DATA | сдвинуть конец слайса / листать слайсы |
| SHIFT + ←/→ на `St:`/`End:` | шаг колеса 1 / 10 / 100 / 1000 (как в стоковом TRIM) |
| WINDOW | выйти, оставить слайсы обычными зонами |

**LAZY:** ударьте любой пэд, чтобы запустить сэмпл, затем тапайте пэды в начале каждого слайса. Зоны следуют за тапами. После остановки пэды прослушивают слайсы; подрежьте и нажмите APPLY.

16 LEVELS свободен. До 16 слайсов.

### 2. TRIM: ПЭД ВЫБИРАЕТ СВОЙ ЗВУК

На странице TRIM удар по пэду переключает `Snd:` на **звук этого пэда** (имя, St/End, волна) и играет его. После APPLY ударьте пэд 3, чтобы подправить слайс 3. Пэд без звука играет текущий звук, как раньше.

### 3. PROGRAM MONO (как на новых MPC)

SHIFT+6 → F2 (PARAMS) → `Voice overlap: MONO`. **MONO-пэды глушат друг друга.** MONO на всех пэдах (ALL / копия параметра) = вся программа монофоническая. Один MONO-пэд среди POLY работает как в стоке (глушит только себя). Программы на диске не меняются.

### 4. MUTE-ГРУППЫ

SHIFT+6 → F1 (ASSIGN) → `Mode:` → `MUTE 1`…`MUTE 4` (`MUTE 5`…`8` с опцией Mute 1-8). Пэды одной группы глушат друг друга: для открытого/закрытого хэта. NORMAL = без группы.
Весь банк / программа: курсор на `Mode:` → WINDOW → ALL FOR: BANK / PROGRAM.

### 4b. ТАЙМИНГ 1/4

`Timing:` / `Note value:` теперь доходит до `1/4` и `1/4(3)` (после `1/32(3)`, ничего не убрано). Сохранённые .ALL на стоковом MPC читаются как 1/8 / 1/8(3).

### 5. SAMPLING MODE

SHIFT+4 (SAMPLE) → курсор на `Mode:` → WINDOW. Пресет OFF / SP1200 (26.04 кГц, 12 бит) / S900 (30 кГц) или `Sample Rate` 8000–44100 Гц. F5 DO IT. Записывайте как обычно; чёрное окно "processing" до конца обработки, затем KEEP / RETRY. OFF = стоковая запись.

Совет: TRIM показывает один канал стерео-звука (`View: LEFT` / `RIGHT`). Моно-источник на одном входе оставляет второй канал пустым.

### 6. ВОССТАНОВЛЕНИЕ ОРИГИНАЛЬНОЙ OS

Держите оригинальный `MPC2KXL.BIN` в корне карты. LOAD → выбрать → DO IT. (Загрузка с диска тоже работает.)

**Важно: время файла.** На некоторых приборах (с новой 16-битной флеш-памятью) OS считывает *время* файла OS как номер версии
и отказывается от файлов со временем раньше **01:14** («OS version too old»). Приложения патчера для Mac и Windows это учитывают.
В браузерной версии не сохраняйте файл между полуночью и 1:14. Копируя оригинальный `MPC2KXL.BIN`, сохраняйте его время (копия в Finder или `cp -p`).
