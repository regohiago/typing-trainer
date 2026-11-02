import curses
import json
import random
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def screen(win, lines):
    win.erase()
    height, width = win.getmaxyx()
    for row, line in enumerate(lines[:height]):
        win.addnstr(row, 0, line, max(0, width - 1))
    win.refresh()


def menu(win):
    while True:
        screen(win, ['Typing Trainer', '', '1 - 15 segundos', '2 - Personalizado', '', 'Escolha:'])
        key = win.getch()
        if key == ord('1'):
            return 15
        if key == ord('2'):
            digits = ''
            while True:
                screen(win, ['Tempo em segundos (inteiro positivo):', '', digits])
                key = win.getch()
                if key in (10, 13, curses.KEY_ENTER) and digits and int(digits) > 0:
                    return int(digits)
                if key in (8, 127, curses.KEY_BACKSPACE):
                    digits = digits[:-1]
                elif ord('0') <= key <= ord('9') and len(digits) < 9:
                    digits += chr(key)


def load_content():
    try:
        content = json.loads(ROOT.joinpath('content.json').read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise ValueError('content.json não encontrado.') from None
    except json.JSONDecodeError:
        raise ValueError('content.json contém JSON inválido.') from None
    if not isinstance(content, dict) or not isinstance(content.get('settings'), dict):
        raise ValueError('content.json precisa de settings.')
    weights = content['settings'].get('weights')
    if not isinstance(weights, dict) or not weights:
        raise ValueError('content.json precisa de settings.weights.')
    for category, weight in weights.items():
        data = content.get(category)
        if not isinstance(data, dict) or isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight <= 0:
            raise ValueError(f'Categoria ou peso inválido: {category}.')
        for field, pattern in [('words', r'[a-z]+'), ('sentences', r'[a-z]+(?: [a-z]+)*')]:
            items = data.get(field)
            if not isinstance(items, list) or not items or any(
                not isinstance(item, str) or re.fullmatch(pattern, item) is None for item in items
            ):
                raise ValueError(f'Categoria {category}: {field} deve conter texto em minúsculas, sem pontuação.')
    return content


def generate_round_content(content, mode, duration):
    weights = content['settings']['weights']
    categories = list(weights)
    field = 'sentences' if mode == 'SENTENCES' else 'words'
    count = max(1000, duration * 20)
    chosen = random.choices(categories, weights=[weights[name] for name in categories], k=count)
    return ' '.join(random.choice(content[name][field]) for name in chosen)


def draw(win, target, index, duration, remaining):
    height, width = win.getmaxyx()
    columns = max(1, width - 1)
    rows = max(1, height - 4)
    page = columns * rows
    start = (index // page) * page
    shown = target[start:start + page]
    lines = [f'Tempo restante: {remaining:.2f} s / {duration} s', '', 'Digite o texto:', '']
    lines += [shown[i:i + columns] for i in range(0, len(shown), columns)]
    screen(win, lines)
    y, x = 4 + (index - start) // columns, (index - start) % columns
    if y < height:
        win.move(y, x)
        win.refresh()


def test(win, target, duration):
    index = total = 0
    started = None
    error = None
    win.timeout(10)
    try:
        while True:
            elapsed = 0.0 if started is None else time.perf_counter() - started
            if started is not None and elapsed >= duration:
                elapsed = float(duration)
                break
            draw(win, target, index, duration, duration - elapsed)
            key = win.getch()
            if key < 0 or key > 255:
                continue
            if started is not None and time.perf_counter() - started >= duration:
                elapsed = float(duration)
                break
            char = chr(key)
            expected = target[index]
            if started is None and char == expected:
                started = time.perf_counter()
            total += 1
            if char != expected:
                error = (expected, char)
                elapsed = 0.0 if started is None else min(time.perf_counter() - started, duration)
                break
            index += 1
    finally:
        win.timeout(-1)
    return {
        'configured_duration': duration,
        'actual_duration': round(elapsed, 4),
        'wpm': round((index / 5) / (max(elapsed, 1e-9) / 60), 1),
        'accuracy': round(index / total * 100, 1) if total else 0.0,
        'correct_characters': index,
        'typed_characters': total,
        'reason': 'Erro de digitação' if error else 'Tempo encerrado',
        'expected_character': error[0] if error else None,
        'typed_character': error[1] if error else None,
    }


def report(win, result):
    error = result['expected_character'] is not None
    lines = [
        'TESTE ENCERRADO' if error else 'TESTE CONCLUÍDO', '',
        f"WPM:                  {result['wpm']:.1f}",
        f"Precisão:             {result['accuracy']:.1f}%",
        f"Caracteres corretos:  {result['correct_characters']}",
        f"Caracteres digitados: {result['typed_characters']}",
        f"Tempo:                {result['actual_duration']:.2f} s",
        f"Motivo:               {result['reason']}",
    ]
    if error:
        lines += ['', f"Esperado:             {repr(result['expected_character'])}",
                  f"Digitado:             {repr(result['typed_character'])}"]
    lines += ['', 'ENTER - Novo teste', 'M     - Alterar tempo', 'Q     - Sair']
    while True:
        screen(win, lines)
        key = win.getch()
        if key in (10, 13, curses.KEY_ENTER):
            return 'repeat'
        if key in (ord('m'), ord('M')):
            return 'menu'
        if key in (ord('q'), ord('Q')):
            return 'quit'


def main(win):
    curses.curs_set(1)
    win.keypad(True)
    content = load_content()
    duration = menu(win)
    round_number = 0
    while True:
        mode = 'SENTENCES' if round_number % 2 == 0 else 'WORDS'
        target = generate_round_content(content, mode, duration)
        result = test(win, target, duration)
        round_number += 1
        action = report(win, result)
        if action == 'quit':
            return
        if action == 'menu':
            duration = menu(win)


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except ValueError as error:
        print(error)
