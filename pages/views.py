from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
import threading
import random

from .models import GeopoliticalNews

def home_view(request):
    world_qs = GeopoliticalNews.objects.filter(category="World").order_by("-published_at")[:10]
    bd_qs = GeopoliticalNews.objects.filter(category="BD").order_by("-published_at")[:10]
    
    # Inject randomized metrics since models are not added yet
    world_news = []
    for news in world_qs:
        news.random_bias = random.choice(["Left", "Center-Left", "Center", "Center-Right", "Right"])
        news.obj_score = random.randint(55, 98)
        news.score_class = "score-high" if news.obj_score >= 80 else ("score-med" if news.obj_score >= 70 else "score-low")
        world_news.append(news)
        
    bd_news = []
    for news in bd_qs:
        news.random_bias = random.choice(["Left", "Center-Left", "Center", "Center-Right", "Right"])
        news.obj_score = random.randint(55, 98)
        news.score_class = "score-high" if news.obj_score >= 80 else ("score-med" if news.obj_score >= 70 else "score-low")
        bd_news.append(news)

    context = {
        "world_news": world_news,
        "bd_news": bd_news,
    }
    return render(request, "pages/home.html", context)


def get_model_predictions(text):
    """
    SKELETON FUNCTION: 
    This is where you will load your .joblib or .h5 models from Colab.
    For now, it returns mock data that matches the dashboard UI.
    """
    import random
    
    # Example logic you will add later:
    # model = joblib.load('pages/ml_models/bias_model.joblib')
    # prediction = model.predict([text])
    
    mock_bias = random.choice(["Left", "Center", "Right", "Center-Left", "Center-Right"])
    mock_obj = random.randint(60, 99)
    
    return {
        "bias": mock_bias,
        "objectivity": mock_obj,
        "score_class": "score-high" if mock_obj >= 80 else ("score-med" if mock_obj >= 70 else "score-low")
    }

def analyze_view(request):
    result = None
    if request.method == "POST":
        input_type = request.POST.get("input_type") # 'url' or 'text'
        content = request.POST.get("content")
        
        analysis_text = content
        
        # If it's a URL, we should ideally scrape it first
        if input_type == "url" and content.startswith("http"):
            from pages.management.commands.fetch import Command
            fetcher = Command()
            scraped_text = fetcher.scrape_full_text(content)
            if scraped_text:
                analysis_text = scraped_text
        
        # Get predictions from our skeleton function
        predictions = get_model_predictions(analysis_text)
        
        result = {
            "text_preview": analysis_text[:200] + "...",
            "metrics": predictions
        }
        
    return render(request, "pages/input.html", {"result": result})


@csrf_exempt
def trigger_fetch(request):
    if request.method == "POST":
        thread = threading.Thread(target=call_command, args=("fetch",))
        thread.start()
        return JsonResponse({"status": "fetch started"})
    return JsonResponse({"error": "POST only"}, status=405)
