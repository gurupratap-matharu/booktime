from django.shortcuts import get_object_or_404, render
from django.views.generic import FormView, ListView

from main import forms, models


def home(request):
    return render(request, "home.html", {})


class ContactUsView(FormView):
    template_name = "contact_form.html"
    form_class = forms.ContactForm
    success_url = "/"

    def form_valid(self, form):
        form.send_mail()
        return super().form_valid(form)


class ProductListView(ListView):
    template_name = "main/product_list.html"
    paginate_by = 4

    def get_queryset(self):
        tag = self.kwargs['tag']
        self.tag = None
        if tag != "all":
            self.tag = get_object_or_404(models.ProductTag, slug=tag)

        if self.tag:
            products = models.Product.objects.active().filter(tag=self.tag)
        else:
            products = models.Product.objects.active()
        return products.order_by("name")
