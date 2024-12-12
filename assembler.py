import sys
import struct
import json
import argparse
import re

# Опкоды, соответствующие заданию
OPCODES = {
    'LOAD_CONST': 57,
    'READ_MEM': 28,
    'WRITE_MEM': 61,
    'LEQ': 19
}

def parse_arguments():
    parser = argparse.ArgumentParser(description='Ассемблер для учебной виртуальной машины (УВМ)')
    parser.add_argument('-i', '--input', required=True, help='Путь к входному ассемблерному файлу')
    parser.add_argument('-o', '--output', required=True, help='Путь к выходному бинарному файлу')
    parser.add_argument('-l', '--log', required=True, help='Путь к выходному JSON-файлу лога')
    return parser.parse_args()

def encode_instruction(mnemonic, operands, line_num):
    """Кодирование инструкции в байты в соответствии с форматом."""
    if mnemonic not in OPCODES:
        raise ValueError(f"Строка {line_num}: Неизвестный мнемоник '{mnemonic}'")

    A = OPCODES[mnemonic]

    if mnemonic == 'LOAD_CONST':
        # Формат: 6 байт, биты:
        # 0–5: A(6 бит) [бит 0 – MSB первого байта]
        # 6–36: B(31 бит)
        # 37–41: C(5 бит)
        if len(operands) != 2:
            raise ValueError(f"Строка {line_num}: LOAD_CONST требует 2 операнда: B C")
        B, C = map(int, operands)
        if B < 0 or B > (1 << 31) - 1:
            raise ValueError(f"Строка {line_num}: Значение B выходит за пределы 31 бита")
        if C < 0 or C > 31:
            raise ValueError(f"Строка {line_num}: Значение C выходит за пределы 5 бит")

        instruction = (A & 0x3F) << 42 | (B & 0x7FFFFFFF) << 11 | (C & 0x1F) << 6

        encoded = instruction.to_bytes(6, byteorder='big')

        log_entry = {'mnemonic': mnemonic, 'A': A, 'B': B, 'C': C}
        return encoded, log_entry

    elif mnemonic == 'READ_MEM':
        # Формат: 2 байта, биты:
        # 0–5: A(6 бит)
        # 6–10: B(5 бит)
        # 11–15: C(5 бит)
        if len(operands) != 2:
            raise ValueError(f"Строка {line_num}: READ_MEM требует 2 операнда: B C")
        B, C = map(int, operands)
        if B < 0 or B > 31:
            raise ValueError(f"Строка {line_num}: B должен быть от 0 до 31")
        if C < 0 or C > 31:
            raise ValueError(f"Строка {line_num}: C должен быть от 0 до 31")

        instruction = (A & 0x3F) << 10 | (B & 0x1F) <<5 | (C & 0x1F)

        encoded = instruction.to_bytes(2, byteorder='big')

        log_entry = {'mnemonic': mnemonic, 'A': A, 'B': B, 'C': C}
        return encoded, log_entry

    elif mnemonic == 'WRITE_MEM':
        # Формат: 3 байта, биты:
        # 0–5: A(6 бит)
        # 6–10: B(5 бит)
        # 11–15: C(5 бит)
        # 16–20: D(5 бит)
        if len(operands) != 3:
            raise ValueError(f"Строка {line_num}: WRITE_MEM требует 3 операнда: B C D")
        B, C, D = map(int, operands)
        for val in (B, C, D):
            if val < 0 or val > 31:
                raise ValueError(f"Строка {line_num}: Значения B, C, D должны быть от 0 до 31")

        instruction = (A & 0x3F) << 18 | (B & 0x1F) << 13 | (C & 0x1F) <<8 | (D &0x1F) <<3

        encoded = instruction.to_bytes(3, byteorder='big')

        log_entry = {'mnemonic': mnemonic, 'A': A, 'B': B, 'C': C, 'D': D}
        return encoded, log_entry

    elif mnemonic == 'LEQ':
        # Формат: 3 байта, биты:
        # 0–5: A(6 бит)
        # 6–10: B(5 бит)
        # 11–15: C(5 бит)
        # 16–20: D(5 бит)
        if len(operands) != 3:
            raise ValueError(f"Строка {line_num}: LEQ требует 3 операнда: B C D")
        B, C, D = map(int, operands)
        for val in (B, C, D):
            if val < 0 or val > 31:
                raise ValueError(f"Строка {line_num}: Значения B, C, D должны быть от 0 до 31")

        instruction = (A & 0x3F) << 18 | (B & 0x1F) << 13 | (C & 0x1F) <<8 | (D &0x1F) <<3

        encoded = instruction.to_bytes(3, byteorder='big')

        log_entry = {'mnemonic': mnemonic, 'A': A, 'B': B, 'C': C, 'D': D}
        return encoded, log_entry

    else:
        raise ValueError(f"Строка {line_num}: Неизвестная команда '{mnemonic}'")

def assemble(input_path, output_path, log_path):
    binary_output = bytearray()
    log_output = {}

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        # Удаляем комментарии и лишние пробелы
        line = line.split('#', 1)[0].strip()
        if not line:
            continue  # Пропускаем пустые строки

        tokens = re.split(r'\s+', line)
        mnemonic = tokens[0].upper()
        operands = tokens[1:]

        try:
            encoded, log_entry = encode_instruction(mnemonic, operands, line_num)
            if encoded:
                binary_output.extend(encoded)
                log_output[f'instruction_{line_num}'] = log_entry
        except ValueError as ve:
            print(f"Ошибка при обработке строки {line_num}: {ve}", file=sys.stderr)
            sys.exit(1)

    # Запись бинарного файла
    with open(output_path, 'wb') as f:
        f.write(binary_output)

    # Запись файла лога
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_output, f, ensure_ascii=False, indent=2)

def main():
    args = parse_arguments()
    assemble(args.input, args.output, args.log)

if __name__ == '__main__':
    main()
