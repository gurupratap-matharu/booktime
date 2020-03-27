from . import models


def basket_middleware(get_response):
    def middleware(request):
        if 'basket_id' in request.session:
            basket_id = request.session['basket_id']
            try:
                basket = models.Basket.objects.get(id=basket_id)
            except models.Basket.DoesNotExist:
                basket = None
            request.basket = basket
        else:
            request.basket = None
        response = get_response(request)
        return response
    return middleware
