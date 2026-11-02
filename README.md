# Typing Trainer

Typing Trainer is a terminal application for typing practice and repeated exposure to English vocabulary. Its content covers common English and vocabulary used in trading, Python, and Bash. Rounds alternate automatically between short, predefined sentences and isolated words. The application is a typing trainer, not a language course.

## Quick start

Run from the repository root on macOS or Linux with Python 3:

```sh
cd typing-trainer
python3 main.py
```

The application uses only Python's standard library, including `curses`. No package installation or account is required. A terminal with `curses` support is needed. There is no separate launcher in this repository.

## How it works

Choose `1` for a 15-second test or `2` to enter a positive whole number of seconds. The first round uses sentences; the next uses words; subsequent rounds continue alternating. The text is prepared before each round and remains fixed while that round is in progress.

The timer starts only when the first correct character is typed. Every character, including spaces, must match the displayed text. An incorrect character ends the round immediately; Backspace does not correct it. A round also ends when the selected time expires. The report shows words per minute (WPM), accuracy, character counts, elapsed time, and the reason the round ended. On an error, it also shows the expected and typed characters.

WPM uses five correct characters per word. Accuracy is the number of correct characters divided by the number of typed characters. Results exist only during the current run; the application does not save test history.

### Controls

| Screen | Key | Action |
| --- | --- | --- |
| Time menu | `1` | Select 15 seconds |
| Time menu | `2` | Enter a custom duration, then press Enter |
| Report | Enter | Start another round with the same duration |
| Report | `M` or `m` | Return to the time menu |
| Report | `Q` or `q` | Quit |

The content type changes when a new round starts, including after returning to the time menu. The time menu does not offer a content or category choice.

## Content system

`typing-trainer/content.json` contains the content and its selection weights. It is loaded and validated once when the application starts. The current categories are `common`, `trading`, `python`, and `bash`. Each category has nonempty `words` and `sentences` lists. The category names used for selection are the keys under `settings.weights`.

A shortened example of the actual structure is:

```json
{
  "settings": {
    "weights": {
      "trading": 40,
      "common": 25,
      "python": 20,
      "bash": 15
    }
  },
  "common": {
    "words": ["before", "after"],
    "sentences": ["we can check the result"]
  },
  "trading": {
    "words": ["market", "price"],
    "sentences": ["we can watch the price near support"]
  },
  "python": {
    "words": ["function", "variable"],
    "sentences": ["we can return the current value"]
  },
  "bash": {
    "words": ["shell", "command"],
    "sentences": ["we can run the command in the terminal"]
  }
}
```

This example illustrates the schema; the actual file contains more entries. In word rounds, the program chooses individual words and joins them with spaces. In sentence rounds, it chooses complete sentences already stored in the JSON and joins them with spaces. It does not construct sentences from random words. Repetition is possible in either type of round.

### Customizing words and sentences

Edit the relevant `words` or `sentences` array in `typing-trainer/content.json`, then restart the application. A word must contain only lowercase `a` through `z`. A sentence must contain lowercase words separated by single spaces, with no leading or trailing space. Punctuation, digits, symbols, and empty entries are rejected. Keep sentences short and grammatical. Neither list has a fixed required size, but every weighted category must have at least one entry in each list. Adding or removing valid entries requires no Python changes.

### Changing category weights

Edit `settings.weights` in `typing-trainer/content.json`. Each selected category needs a positive numeric weight and a matching category object with valid `words` and `sentences` lists. For example, changing `trading` from `40` to `70` makes it more likely to be selected relative to the other categories. The numbers are relative weights, not guaranteed percentages of a round.

Only categories listed in `settings.weights` participate in selection. A category object without a weight is not selected.

### Adding or modifying contexts

To add a context, add a new top-level object with nonempty `words` and `sentences` arrays, then add its name with a positive weight under `settings.weights`. The selection code reads the category names from that mapping, so no Python change is required for a context that follows the existing schema. Removing a context from the weight mapping stops selecting it. Restart after editing the JSON because it is read only at startup.

## Code structure and modification points

```text
type-terminal/
├── README.md
└── typing-trainer/
    ├── main.py
    └── content.json
```

- `README.md` documents use and modification.
- `typing-trainer/content.json` stores weights, words, and predefined sentences.
- `typing-trainer/main.py` contains content loading, selection, terminal interaction, timing, and reporting.

In `main.py`, `load_content()` reads and validates the JSON. `generate_round_content(content, mode, duration)` selects weighted categories, picks a word or sentence from each selected category, and returns one text string. It generates at least 1,000 items, or 20 items per configured second for longer rounds. To change selection order, repetition, or weighting behavior, edit this function. The typing test receives only the resulting string, not category data.

`main()` tracks the round number and alternates `SENTENCES` and `WORDS`. `test()` handles immediate key capture with `curses`, starts its `time.perf_counter()` timer on the first correct key, and calculates the result. `report()` displays the result and handles Enter, M, and Q. Changes to vocabulary or weights can stay in `content.json`; changes to the selection algorithm can stay in `generate_round_content()` without changing the keyboard and timing code.

The program is intended for a local terminal on macOS or Linux. Content is stored locally in JSON and supports lowercase English letters and spaces during training. It has no persistent history or external dependencies.
