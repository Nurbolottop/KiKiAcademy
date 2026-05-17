import re


def normalize_phone(raw: str) -> str:
    if raw is None:
        return ''
    digits = re.sub(r'\D+', '', str(raw))
    if not digits:
        return ''

    if digits.startswith('00'):
        digits = digits[2:]

    if len(digits) == 10 and digits.startswith('0'):
        digits = '996' + digits[1:]
    elif len(digits) == 9:
        digits = '996' + digits

    return f'+{digits}'
