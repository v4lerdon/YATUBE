from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    current_year = datetime.now()
    return {
        'year': current_year.year
    }
