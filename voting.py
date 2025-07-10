import sqlite3
from collections import Counter

def t_n_minus_1(answers, n, t):
    # Реализация t/(n-1)-алгоритма на основе примера преподавателя
    # Подсчёт максимального числа совпадений с использованием Counter для отличия
    answer_counts = Counter(answers)
    max_group_count = max(answer_counts.values(), default=0)

    # Вычисляем количество выходов и шаг индексов
    output_count = n - t
    if output_count <= 1:
        return answers[-1] if answers else None
    output_indexes_step = (n - 1) // (output_count - 1)
    output_indexes = {i: answers[i] for i in range(0, n - 1, output_indexes_step)}
    output_indexes[n - 1] = answers[n - 1]

    # Строим группы совпадений по соседним версиям
    max_count_indexes = {}
    cur_start_index = -1
    cur_group_count = 0
    for i in range(n - 1):
        if abs(answers[i] - answers[i + 1]) < 1e-6:
            if cur_group_count == 0:
                cur_start_index = i
                cur_group_count = 2
            else:
                cur_group_count += 1
        else:
            if cur_start_index != -1:
                end_index = i
                if cur_group_count not in max_count_indexes:
                    max_count_indexes[cur_group_count] = [(cur_start_index, end_index)]
                else:
                    max_count_indexes[cur_group_count].append((cur_start_index, end_index))
            cur_start_index = -1
            cur_group_count = 0

    # Проверяем последнюю группу
    if cur_start_index != -1:
        end_index = n - 1
        if cur_group_count not in max_count_indexes:
            max_count_indexes[cur_group_count] = [(cur_start_index, end_index)]
        else:
            max_count_indexes[cur_group_count].append((cur_start_index, end_index))

    # Выбор правильного результата по правилам
    if max_group_count >= t:
        if max_group_count in max_count_indexes and len(max_count_indexes[max_group_count]) == 1:
            group_start, group_end = max_count_indexes[max_group_count][0]
            for key, val in output_indexes.items():
                if group_start <= key <= group_end:
                    return val
            # Если не найдено в output_indexes, берём первый из группы
            return answers[group_start]
        else:
            return output_indexes[n - 1]
    else:
        return output_indexes[n - 1]

def get_version_names(db_path, module_name):
    # Извлекает имена версий (V1, V2, ...) из таблицы version
    module_map = {'Module3': 1, 'Module5': 2, 'Module7': 3, 'Module9': 4, 'Module11': 5}
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM version WHERE module = ?", (module_map[module_name],))
        return {row[0]: row[1] for row in cursor.fetchall()}

def process_module(db_path, module_name, experiment_names, n, t, version_id_map):
    # Подключение к базе
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # Получаем имена версий
        version_name_map = get_version_names(db_path, module_name)
        # Статистика экспериментов и счётчик правильных версий
        exp_stats = {exp: {'matches': 0, 'total': 0} for exp in experiment_names if exp.startswith(f'M{module_name[6:]}')}
        version_correct_counts = Counter()

        for exp_name in exp_stats:
            # Запрашиваем все данные эксперимента
            cursor.execute(
                "SELECT module_iteration_num, version_id, version_answer, correct_answer FROM experiment_data WHERE module_name = ? AND experiment_name = ? ORDER BY module_iteration_num, version_id",
                (module_name, exp_name))
            rows = cursor.fetchall()
            if not rows:
                continue

            # Группируем данные по итерациям
            iterations = {}
            for iter_num, version_id, version_answer, correct_answer in rows:
                if version_id not in version_id_map:
                    continue
                idx = version_id_map[version_id]
                if iter_num not in iterations:
                    iterations[iter_num] = {'answers': [None] * n, 'correct': correct_answer}
                iterations[iter_num]['answers'][idx] = version_answer

            # Обрабатываем итерации
            for iter_num, data in iterations.items():
                answers = data['answers']
                if None in answers:
                    continue
                result = t_n_minus_1(answers, n, t)
                if result is None:
                    continue
                is_correct = abs(result - data['correct']) < 1e-6
                exp_stats[exp_name]['matches'] += 1 if is_correct else 0
                exp_stats[exp_name]['total'] += 1
                if is_correct:
                    for idx, answer in enumerate(answers):
                        if abs(answer - result) < 1e-6:
                            version_id = [vid for vid, i in version_id_map.items() if i == idx][0]
                            version_correct_counts[version_id] += 1

            # Вывод статистики эксперимента
            matches = exp_stats[exp_name]['matches']
            total = exp_stats[exp_name]['total']
            if total > 0:
                print(f"Experiment {exp_name}: {matches / total * 100:.2f}% ({matches}/{total} итераций)")

        # Вывод лучшей версии
        if version_correct_counts:
            best_version_id = version_correct_counts.most_common(1)[0][0]
            print(
                f"Лучшая версия для {module_name}: {version_name_map.get(best_version_id, f'Version_{best_version_id}')} (правильных: {version_correct_counts[best_version_id]})")
        else:
            print(f"Лучшая версия для {module_name}: Не определена (нет правильных результатов)")

def main():
    # Путь к базе и список экспериментов
    db_path = "C:/ePrograms/Python/voting 0.1/experiment_edu.db"
    experiment_names = ['M3_i10', 'M3_I10', 'M3_I100', 'M3_I50000', 'M5_I10', 'M5_I100', 'M5_I50000', 'M7_I10',
                        'M7_I100', 'M7_I50000', 'M9_I10', 'M9_I100', 'M9_I50000', 'M11_I10', 'M11_I100', 'M11_I50000']

    # Модули: имя, число версий (n), порог ошибок (t), маппинг version_id
    modules = [
        {'name': 'Module3', 'n': 3, 't': 1, 'version_id_map': {1: 0, 2: 1, 3: 2}},
        {'name': 'Module5', 'n': 5, 't': 2, 'version_id_map': {4: 0, 5: 1, 6: 2, 7: 3, 8: 4}},
        {'name': 'Module7', 'n': 7, 't': 3, 'version_id_map': {9: 0, 10: 1, 11: 2, 12: 3, 13: 4, 14: 5, 15: 6}},
        {'name': 'Module9', 'n': 9, 't': 4,
         'version_id_map': {16: 0, 17: 1, 18: 2, 19: 3, 20: 4, 21: 5, 22: 6, 23: 7, 24: 8}},
        {'name': 'Module11', 'n': 11, 't': 5,
         'version_id_map': {25: 0, 26: 1, 27: 2, 28: 3, 29: 4, 30: 5, 31: 6, 32: 7, 33: 8, 34: 9, 35: 10}}
    ]

    # Обрабатываем каждый модуль
    for module in modules:
        process_module(db_path, module['name'], experiment_names, module['n'], module['t'], module['version_id_map'])


if __name__ == "__main__":
    main()