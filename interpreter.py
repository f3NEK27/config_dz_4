import sys
import struct
import json
import argparse
import re

def parse_arguments():
    parser = argparse.ArgumentParser(description='Интерпретатор для учебной виртуальной машины (УВМ)')
    parser.add_argument('-i', '--input', required=True, help='Путь к входному бинарному файлу')
    parser.add_argument('-r', '--range', required=True, help='Диапазон памяти для сохранения в формате start:end')
    parser.add_argument('-o', '--output', required=True, help='Путь к выходному JSON-файлу результата')
    return parser.parse_args()

class VirtualMachine:
    def __init__(self, memory_size=256):
        self.registers = [0]*32  # 32 регистра
        self.memory = [0]*memory_size
        self.program = []
        self.pc = 0

    def load_program(self, binary_data):
        self.program = list(binary_data)
        print(f"Загружена программа: {self.program}")

    def execute(self):
        while self.pc < len(self.program):
            # Определяем тип команды по opcode
            # Для этого считываем A из соответствующих бит
            if self.program[self.pc] >> 2 == 0x3F:  # Example check, need to extract A correctly
                pass  # Placeholder
            # Для каждой инструкции читаем A и определяем размер команды
            # Читаем A из первых 6 бит первого байта
            current_byte = self.program[self.pc]
            A = (current_byte & 0xFC) >> 2  # Первые 6 бит

            if A == 57:  # LOAD_CONST
                if self.pc +6 > len(self.program):
                    raise ValueError("Недостаточно байт для LOAD_CONST")
                instr_bytes = self.program[self.pc:self.pc+6]
                instr_val = int.from_bytes(instr_bytes, 'big')
                A_extracted = (instr_val >> 42) &0x3F
                B = (instr_val >>11) &0x7FFFFFFF
                C = (instr_val >>6) &0x1F
                self.registers[C] = B
                print(f"LOAD_CONST: Регистр {C} загружен значением {B}")
                self.pc +=6

            elif A ==28:  # READ_MEM
                if self.pc +2 > len(self.program):
                    raise ValueError("Недостаточно байт для READ_MEM")
                instr_bytes = self.program[self.pc:self.pc+2]
                instr_val = int.from_bytes(instr_bytes, 'big')
                A_extracted = (instr_val >>10) &0x3F
                B = (instr_val >>5) &0x1F
                C = instr_val &0x1F
                addr = self.registers[C]
                if addr <0 or addr >= len(self.memory):
                    raise ValueError(f"Адрес вне памяти: {addr}")
                self.registers[B] = self.memory[addr]
                print(f"READ_MEM: Читаем значение {self.memory[addr]} из адреса {addr} в регистр {B}")
                self.pc +=2

            elif A ==61:  # WRITE_MEM
                if self.pc +3 > len(self.program):
                    raise ValueError("Недостаточно байт для WRITE_MEM")
                instr_bytes = self.program[self.pc:self.pc+3]
                instr_val = int.from_bytes(instr_bytes, 'big')
                A_extracted = (instr_val >>18) &0x3F
                B = (instr_val >>13) &0x1F
                C = (instr_val >>8) &0x1F
                D = (instr_val >>3) &0x1F
                base_addr = self.registers[C]
                addr = base_addr + D
                val = self.registers[B]
                if addr <0 or addr >= len(self.memory):
                    raise ValueError(f"Адрес вне памяти: {addr}")
                self.memory[addr] = val
                print(f"WRITE_MEM: Записываем значение {val} в адрес {addr} (База: {base_addr}, Смещение: {D})")
                self.pc +=3

            elif A ==19:  # LEQ
                if self.pc +3 > len(self.program):
                    raise ValueError("Недостаточно байт для LEQ")
                instr_bytes = self.program[self.pc:self.pc+3]
                instr_val = int.from_bytes(instr_bytes, 'big')
                A_extracted = (instr_val >>18) &0x3F
                B = (instr_val >>13) &0x1F
                C = (instr_val >>8) &0x1F
                D = (instr_val >>3) &0x1F
                val1 = self.registers[B]
                val2 = self.registers[D]
                self.registers[C] = 1 if val1 <= val2 else 0
                print(f"LEQ: Сравниваем {val1} (R{B}) <= {val2} (R{D}) -> R{C} = {self.registers[C]}")
                self.pc +=3

            else:
                raise ValueError(f"Неизвестный opcode: {A} при PC={self.pc}")

            # Вывод состояния регистров после каждой команды
            print(f"Состояние регистров: {self.registers}")

    def get_memory_slice(self, start, end):
        return self.memory[start:end +1]

def parse_memory_range(memory_range_str, memory_size):
    match = re.match(r'^(\d+):(\d+)$', memory_range_str)
    if not match:
        raise ValueError("Диапазон памяти должен быть в формате start:end")
    start, end = map(int, match.groups())
    if start <0 or end >= memory_size or start >end:
        raise ValueError("Некорректный диапазон памяти")
    return start, end

def main():
    args = parse_arguments()

    # Чтение бинарного файла
    try:
        with open(args.input, 'rb') as f:
            binary_data = f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл {args.input} не найден.", file=sys.stderr)
        sys.exit(1)

    # Инициализация виртуальной машины
    vm = VirtualMachine(memory_size=256)
    vm.load_program(binary_data)

    # Выполнение программы
    try:
        vm.execute()
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    # Парсинг диапазона памяти
    try:
        start, end = parse_memory_range(args.range, len(vm.memory))
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    # Извлечение диапазона памяти
    memory_slice = vm.get_memory_slice(start, end)

    # Сохранение результата в JSON
    result = {'memory': memory_slice}
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Выполнение программы завершено. Результат сохранен в {args.output}")

if __name__ == '__main__':
    main()
