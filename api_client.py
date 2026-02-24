# -*- coding: utf-8 -*-
"""
Задание 3: Скрипт отправки POST-запроса к API с персональными данными пациента.
Обработка ответа: проверка 200/201, парсинг JSON, вывод данных, обработка ошибок.
"""
import json
import sys
from datetime import datetime

import requests

API_URL = 'https://test/client'
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Token',
}


def parse_fio(fio_str):
    parts = (fio_str or '').strip().split()
    last = parts[0] if len(parts) > 0 else ''
    first = parts[1] if len(parts) > 1 else ''
    patr = parts[2] if len(parts) > 2 else ''
    return last, first, patr


def birth_date_to_iso(date_str):
    """Конвертирует дату из формата DD.MM.YYYY в ISO '2019-11-11T11:16:32'."""
    try:
        dt = datetime.strptime(date_str.strip(), '%d.%m.%Y')
        return dt.strftime('%Y-%m-%dT%H:%M:%S')
    except (ValueError, AttributeError):
        return date_str


def build_payload(last_name, first_name, patr_name, birth_date, status=True):
    return {
        'lastName': last_name,
        'firstName': first_name,
        'patrName': patr_name,
        'birthDate': birth_date_to_iso(birth_date),
        'status': bool(status),
    }


def send_client(client_data, base_url=API_URL, headers=None):
    """
    Отправляет POST с данными пациента. client_data: dict с ключами fio, birth_date.
    Возвращает (success: bool, result: dict или сообщение об ошибке).
    """
    headers = headers or HEADERS.copy()
    last, first, patr = parse_fio(client_data.get('fio', ''))
    payload = build_payload(
        last, first, patr,
        client_data.get('birth_date', ''),
        client_data.get('status', True),
    )
    try:
        resp = requests.post(base_url, json=payload, headers=headers, timeout=30)
    except requests.exceptions.Timeout:
        return False, {'error': 'Таймаут запроса'}
    except requests.exceptions.ConnectionError as e:
        return False, {'error': f'Ошибка соединения: {e}'}
    except requests.exceptions.RequestException as e:
        return False, {'error': str(e)}

    try:
        data = resp.json()
    except ValueError:
        return False, {'error': 'Невалидный JSON в ответе', 'body': resp.text[:500]}

    if resp.status_code not in (200, 201):
        return False, {
            'status': data.get('status', 'error'),
            'code': resp.status_code,
            'message': data.get('message', resp.reason),
            'data': data.get('data'),
        }

    return True, data


def print_response(success, result):
    """Вывод ответа в читаемом формате."""
    if success:
        print('Успешный ответ:')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if 'data' in result and result['data']:
            d = result['data']
            print('\nДанные:')
            print(f"  id: {d.get('id')}")
            print(f"  FIO: {d.get(' FIO ', d.get('FIO', ''))}")
            print(f"  age: {d.get('age')}")
    else:
        print('Ошибка:')
        if isinstance(result, dict):
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result)


def main():
    # Пример: данные одного пациента (можно передать из задачи 2 / clientList)
    if len(sys.argv) > 1:
        # Вызов: python api_client.py '{"fio":"Иванов Иван Иванович","birth_date":"01.01.1990"}'
        try:
            client_data = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            client_data = {'fio': 'Иванов Иван Иванович', 'birth_date': '01.01.1990'}
    else:
        client_data = {'fio': 'Иванов Иван Иванович', 'birth_date': '01.01.1990'}

    success, result = send_client(client_data)
    print_response(success, result)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
