from rest_framework.decorators import api_view
from django.http import HttpResponse
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from .models import (
    mUser,
    Week,
    mSetting,
    Category,
    mUserCategoryRelation,
    CategoryMemberShip,
    Section,
    Task,
    SubTask,
    Label,
    Karma,
    DefaultCategory,
)
from .serializers import (
    UserSerializer,
    SettingSerializer,
    CategorySerializer,
    CategoryMemberShipSerializer,
    SectionSerializer,
    TaskSerializer,
    LabelSerializer,
    KarmaSerializer,
    DefaultCategorySerializer,
)

from .mixins import (
    GetLoginUserMixin,
)
import logging

logger = logging.getLogger(__name__)


class SignupView(generics.CreateAPIView, GetLoginUserMixin):
    permission_classes = (permissions.AllowAny,)
    queryset = mUser.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        self.auth0_id = request.data['auth0_id']
        serializer = self.get_serializer(data=request.data)
        if (serializer.is_valid()):
            self.perform_create(serializer)
            user = mUser.objects.get(auth0_id=serializer.data['auth0_id'])
            mSetting.objects.create(
                target_user=user
            )
            categorys = []
            req_categorys = request.data['categorys']
            for i, category in enumerate(req_categorys, 1):
                categorys.append(Category(
                    creator=user,
                    name=category['name'],
                    color=category['color'],
                    icon=category['icon'],
                    index=i,
                ))
            Category.objects.bulk_create(categorys)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.info(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppInitView(generics.ListAPIView, GetLoginUserMixin):
    permission_classes = (permissions.AllowAny,)

    def list(self, request, *args, **kwargs):
        self.set_auth0_id(request)
        try:
            user = mUser.objects.get(auth0_id=request.query_params['auth0_id'])
            categorys = Category.objects.filter(creator=user).order_by('index')
            category_serializer = CategorySerializer(categorys, many=True, context={ 'view' : self })
            labels = Label.objects.filter(author=user)
            label_serializer = LabelSerializer(labels, many=True, context={ 'view' : self })
            karmas = Karma.objects.filter(target_user=user)
            karma_serializer = KarmaSerializer(karmas, many=True, context={ 'view' : self })
            return Response(
                {
                    'categorys': category_serializer.data,
                    'labels': label_serializer.data,
                    'karma': karma_serializer.data,
                    'result': True,
                },
                status=status.HTTP_200_OK
            )
        except:
            logger.info('初期化が完了していない')
            return Response(
                {
                    'result': False,
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class DefaultCategorysView(generics.ListAPIView, GetLoginUserMixin):
    permission_classes = (permissions.AllowAny,)
    queryset = DefaultCategory.objects.all()
    serializer_class = DefaultCategorySerializer

    def list(self, request, *args, **kwargs):
        self.set_auth0_id(request)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        try:
            user = mUser.objects.get(auth0_id=request.query_params['auth0_id'])
            logger.info('初期化が完了している')
            return Response(
                {
                    'result': False,
                },
                status=status.HTTP_200_OK
            )
        except mUser.DoesNotExist:
            logger.info('初期化が完了していない')
            return Response(
                {
                    'default_categorys': serializer.data,
                    'result': True,
                },
                status=status.HTTP_200_OK
            )


