from django.http import HttpRequest, JsonResponse


def is_ajax(request: HttpRequest) -> bool:
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def ajax_ok(message: str = '', **data) -> JsonResponse:
    return JsonResponse({'ok': True, 'message': message, **data})


def ajax_error(message: str, status: int = 400, **data) -> JsonResponse:
    return JsonResponse({'ok': False, 'message': message, **data}, status=status)
