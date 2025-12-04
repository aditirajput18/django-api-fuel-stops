# routeapi/views_ui.py
from django.views import View
from django.shortcuts import render
from django.conf import settings
import requests
import json

class RouteUI(View):
    template_name = "routeapi/ui_index.html"

    def get(self, request):
        return render(request, self.template_name, {'result': None, 'error': None})

    def post(self, request):
        start = request.POST.get('start', '').strip()
        finish = request.POST.get('finish', '').strip()

        if not start or not finish:
            return render(request, self.template_name, {
                'result': None,
                'error': 'Please provide both start and finish locations.'
            })

        # Build full absolute URL for internal API endpoint
        api_path = request.build_absolute_uri('/api/route/')  # adjust if your API path is different
        try:
            r = requests.post(api_path, json={'start': start, 'finish': finish}, timeout=20)
            r.raise_for_status()
            data = r.json()
            return render(request, self.template_name, {'result': data, 'error': None, 'start': start, 'finish': finish})
        except requests.RequestException as e:
            return render(request, self.template_name, {
                'result': None,
                'error': f'Error calling routing API: {e}'
            })
        except ValueError:
            return render(request, self.template_name, {
                'result': None,
                'error': 'Invalid JSON returned from API.'
            })

