from django.urls import path, include
from . import views, viewsets
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('user', viewsets.UserViewSet)
router.register('category', viewsets.CategoryViewSet)
router.register('section', viewsets.SectionViewSet)
router.register('task', viewsets.TaskViewSet)
router.register('label', viewsets.LabelViewSet)
router.register('karma', viewsets.KarmaViewSet)


app_name = 'api'
urlpatterns = [
    path('', include(router.urls)),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('appinit/', views.AppInitView.as_view(), name='appinit'),
    path('default-categorys/', views.DefaultCategorysView.as_view(), name='default-categorys'),
]
